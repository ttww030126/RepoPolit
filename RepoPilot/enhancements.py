"""增强能力装配层（仅 Skill + MCP）。

把 Skill 系统与 MCP 工具以“可选挂载”的方式接到一个已经构造好的 agent 上，
而不侵入 runtime 的核心构造流程。这样原有 runtime 仍可独立工作，
增强能力是纯叠加的。

说明：本项目保留 repopilot 原版的记忆设计（分层工作记忆 + 遗忘 + 混合检索），
但**刻意不引入**记忆的反思 / 巩固（reflection / consolidation）回路。
因此这里只装配 Skill 与 MCP，不做任何记忆反思。

调用点：cli.build_agent() 在返回 agent 前调用 attach_enhancements()。
"""

import os

from .mcp import MCPManager, load_mcp_config
from .skills import SkillRegistry


def attach_enhancements(agent, start_mcp=True):
    """给 agent 挂上 Skill 注册表与 MCP 工具，并重建工具表 / prefix。

    返回一个 summary dict，便于在欢迎界面或日志里展示加载了什么。
    """
    repopilot_root = agent.root / ".repopilot"
    summary = {"skills": [], "mcp": {}}

    # 1. Skill 注册表
    registry = SkillRegistry(repopilot_root)
    registry.discover()
    agent.skill_registry = registry
    summary["skills"] = list(registry.skills)

    # 2. MCP servers（来自 .env 的 REPOPILOT_MCP_SERVERS）
    agent.mcp_manager = None
    agent.mcp_tool_specs = {}
    raw = os.environ.get("REPOPILOT_MCP_SERVERS", "")
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
