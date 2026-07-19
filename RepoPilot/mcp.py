"""MCP（Model Context Protocol）stdio 客户端。

让 repopilot 这个本地 agent 能够把外部 MCP server（如 filesystem、git、github、
fetch、sqlite 等社区 server）作为“可申请的工具”接入控制循环，而不需要把每个
集成都硬编码进 tools.py。

实现约束（延续 repopilot 的零依赖原则）：
- 只用标准库 subprocess + json + threading；
- 走 MCP 的 stdio 传输：按行分隔的 JSON-RPC 2.0 消息（newline-delimited）；
- 进程生命周期、初始化握手、工具发现、工具调用都封装在 MCPClient 里。

配置来源（.env）：
    REPOPILOT_MCP_SERVERS='{"fs": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]}}'

每个 MCP server 暴露的工具会被注册成 repopilot 工具，名字形如 mcp__<server>__<tool>。
所有 MCP 调用默认归类为 risky（需要审批），因为它们可能产生副作用。
"""

import json
import subprocess
import threading
import time


class MCPError(RuntimeError):
    pass


class MCPClient:
    """单个 MCP server 的 stdio 连接。线程安全的请求/响应。"""

    def __init__(self, name, command, args=None, env=None, timeout=30):
        self.name = name
        self.command = command
        self.args = list(args or [])
        self.env = env
        self.timeout = timeout
        self._proc = None
        self._lock = threading.Lock()
        self._next_id = 1
        self._server_tools = []

    def start(self):
        if self._proc is not None:
            return
        self._proc = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=self.env,
        )
        self._initialize()

    def _send(self, payload):
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        self._proc.stdin.write(line)
        self._proc.stdin.flush()

    def _read_message(self, deadline):
        # 跳过通知（没有 id 的消息），只返回带 id 的响应。
        while True:
            if time.monotonic() > deadline:
                raise MCPError(f"MCP server '{self.name}' timed out")
            raw = self._proc.stdout.readline()
            if raw == "":
                raise MCPError(f"MCP server '{self.name}' closed the connection")
            raw = raw.strip()
            if not raw:
                continue
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if "id" in message:
                return message

    def _request(self, method, params=None):
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            self._send(
                {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
            )
            deadline = time.monotonic() + self.timeout
            while True:
                message = self._read_message(deadline)
                if message.get("id") != request_id:
                    continue
                if "error" in message:
                    raise MCPError(f"{method} failed: {message['error']}")
                return message.get("result", {})

    def _notify(self, method, params=None):
        with self._lock:
            self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _initialize(self):
        self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "repopilot", "version": "0.2"},
            },
        )
        self._notify("notifications/initialized")
        self.refresh_tools()

    def refresh_tools(self):
        result = self._request("tools/list")
        self._server_tools = result.get("tools", [])
        return self._server_tools

    def list_tools(self):
        return list(self._server_tools)

    def call_tool(self, tool_name, arguments):
        result = self._request("tools/call", {"name": tool_name, "arguments": arguments or {}})
        # MCP 工具结果是一个 content 数组；这里抽成纯文本给 repopilot 的 runtime。
        parts = []
        for item in result.get("content", []):
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            else:
                parts.append(json.dumps(item, ensure_ascii=False))
        text = "\n".join(parts).strip()
        if result.get("isError"):
            raise MCPError(text or "MCP tool returned an error")
        return text or "(empty)"

    def stop(self):
        if self._proc is None:
            return
        try:
            self._proc.terminate()
            self._proc.wait(timeout=5)
        except Exception:
            self._proc.kill()
        finally:
            self._proc = None


class MCPManager:
    """管理多个 MCP server，并把它们的工具翻译成 repopilot 工具规格。"""

    def __init__(self, servers_config, timeout=30):
        self.clients = {}
        for name, spec in (servers_config or {}).items():
            self.clients[name] = MCPClient(
                name=name,
                command=spec["command"],
                args=spec.get("args", []),
                env=spec.get("env"),
                timeout=timeout,
            )

    def start_all(self):
        started = {}
        for name, client in self.clients.items():
            try:
                client.start()
                started[name] = len(client.list_tools())
            except Exception as exc:  # 单个 server 起不来不应该拖垮整个 agent
                started[name] = f"error: {exc}"
        return started

    def build_tool_specs(self):
        """返回 {repopilot_tool_name: spec} 供 runtime 注册。

        spec 的 run 是一个闭包：(agent, args) -> str。delegate-friendly。
        """
        specs = {}
        for server_name, client in self.clients.items():
            for tool in client.list_tools():
                repopilot_name = f"mcp__{server_name}__{tool['name']}"
                input_schema = tool.get("inputSchema", {}) or {}
                properties = input_schema.get("properties", {}) or {}
                schema = {key: "any" for key in properties}
                specs[repopilot_name] = {
                    "schema": schema or {"arguments": "json"},
                    "risky": True,  # 外部副作用，默认需要审批
                    "description": f"[MCP:{server_name}] {tool.get('description', tool['name'])}",
                    "run": self._make_runner(server_name, tool["name"]),
                }
        return specs

    def _make_runner(self, server_name, tool_name):
        client = self.clients[server_name]

        def run(agent, args):  # noqa: ARG001  - agent 留作未来注入上下文
            return client.call_tool(tool_name, args or {})

        return run

    def stop_all(self):
        for client in self.clients.values():
            client.stop()


def load_mcp_config(raw_json):
    """从 .env 的 REPOPILOT_MCP_SERVERS 字符串解析配置；非法或空时返回 {}。"""
    if not raw_json:
        return {}
    try:
        config = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise MCPError(f"REPOPILOT_MCP_SERVERS is not valid JSON: {exc}") from exc
    if not isinstance(config, dict):
        raise MCPError("REPOPILOT_MCP_SERVERS must be a JSON object")
    for name, spec in config.items():
        if not isinstance(spec, dict) or "command" not in spec:
            raise MCPError(f"MCP server '{name}' must define a 'command'")
    return config
