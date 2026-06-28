"""mneme —— 带类人记忆的本地 coding agent。

分层结构：
    cli/         接口层（命令行）
    core/        核心运行时（控制循环 / 任务状态 / 上下文工程 / 能力装配）
    memory/      记忆层（分层记忆 / 遗忘 / 混合检索 / 自反思）
    models/      模型后端（Ollama / OpenAI / Anthropic / DeepSeek）
    tools/       工具层（受约束的动作白名单）
    skills/      技能层（SKILL.md 渐进式披露）
    mcp/         MCP 集成层（接入外部 MCP server）
    workspace/   工作区快照
    config/      配置（.env 加载）
    store/       运行工件持久化
    evaluation/  基准与指标
"""

__version__ = "0.2.0"

# 常用入口（保持简单的顶层导入）
from mneme.core.runtime import MiniAgent, Mneme, SessionStore  # noqa: F401,E402
from mneme.workspace import WorkspaceContext  # noqa: F401,E402
from mneme.models import (  # noqa: F401,E402
    AnthropicCompatibleModelClient,
    DeepSeekModelClient,
    FakeModelClient,
    OllamaModelClient,
    OpenAICompatibleModelClient,
)
from mneme.cli import build_agent, build_arg_parser, build_welcome, main  # noqa: F401,E402

# 子模块/能力的便捷别名（向后兼容扁平时期的引用习惯）
from mneme.memory import decay as memory_decay  # noqa: F401,E402
from mneme.memory import reflection, retrieval  # noqa: F401,E402
from mneme import mcp, models, skills  # noqa: F401,E402

__all__ = [
    "Mneme",
    "MiniAgent",
    "SessionStore",
    "WorkspaceContext",
    "FakeModelClient",
    "OllamaModelClient",
    "OpenAICompatibleModelClient",
    "AnthropicCompatibleModelClient",
    "DeepSeekModelClient",
    "build_agent",
    "build_arg_parser",
    "build_welcome",
    "main",
    "memory_decay",
    "reflection",
    "retrieval",
    "skills",
    "mcp",
    "models",
]
