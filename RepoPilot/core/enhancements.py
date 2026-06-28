"""增强能力装配层。

把新增的几块能力（Skill 系统、MCP 工具、混合检索、反思巩固）以“可选挂载”的
方式接到一个已经构造好的 Mneme agent 上，而不侵入 runtime 的核心构造流程。
这样原有 runtime 仍可独立工作，增强能力是纯叠加的。

调用点：cli.build_agent() 在返回 agent 前调用 attach_enhancements()。
"""

import os

from mneme.mcp import MCPManager, load_mcp_config
from mneme.skills import SkillRegistry


def attach_enhancements(agent, start_mcp=True):
    """给 agent 挂上 Skill 注册表与 MCP 工具，并重建工具表 / prefix。

    返回一个 summary dict，便于在欢迎界面或日志里展示加载了什么。
    """
    mneme_root = agent.root / ".mneme"
    summary = {"skills": [], "mcp": {}}

    # 1. Skill 注册表
    registry = SkillRegistry(mneme_root)
    registry.discover()
    agent.skill_registry = registry
    summary["skills"] = list(registry.skills)

    # 2. MCP servers（来自 .env 的 MNEME_MCP_SERVERS）
    agent.mcp_manager = None
    agent.mcp_tool_specs = {}
    raw = os.environ.get("MNEME_MCP_SERVERS", "")
    if raw and start_mcp:
        config = load_mcp_config(raw)
        if config:
            manager = MCPManager(config)
            summary["mcp"] = manager.start_all()
            agent.mcp_manager = manager
            agent.mcp_tool_specs = manager.build_tool_specs()

    # 3. 重建工具表与 prefix（prefix 里会带上技能目录）
    agent.tools = agent.build_tools()
    agent.prefix_state = agent.build_prefix()
    agent.prefix = agent.prefix_state.text
    return summary


def reflect_agent_memory(agent, keep_top=None):
    """对 agent 当前工作记忆运行一次反思巩固，并把结果写回 session。

    供 REPL 的 /reflect 命令或会话结束钩子调用。返回可读 report 文本。
    """
    from mneme.memory import reflection

    state = agent.memory.to_dict()
    notes = list(state.get("episodic_notes", []))
    if not notes:
        return "Reflection: no episodic notes to consolidate."

    kept, archived, report = reflection.reflect(notes, keep_top=keep_top)

    # 写回工作记忆（只保留 kept），归档写入冷存储以便日后恢复。
    state["episodic_notes"] = kept
    state["notes"] = [note.get("text", "") for note in kept]
    agent.memory.state = state  # 直接回写巩固后的状态，保持引用一致
    agent.session["memory"] = state

    if archived:
        _append_archive(agent.root / ".mneme" / "memory" / "archive.jsonl", archived)
    return reflection.render_report(report)


def _append_archive(path, archived_notes):
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for note in archived_notes:
            handle.write(json.dumps(note, ensure_ascii=False) + "\n")
