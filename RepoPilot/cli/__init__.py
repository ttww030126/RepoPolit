"""接口层：命令行入口。

除了 CLI 入口函数，这里还 re-export 了模型客户端类与 WorkspaceContext。
原因有二：
1. 让 `mneme.cli.<ClientName>` 成为稳定的公共/测试接口（测试通过
   `patch("mneme.cli.OllamaModelClient", ...)` 注入假客户端，避免真实构造）。
2. `app._build_model_client` 在运行时通过本包命名空间解析客户端类，因此上述
   patch 能真正生效——这修复了「扁平模块 -> 分层包」重构后断裂的注入点。
"""
from mneme.models import (  # noqa: F401
    AnthropicCompatibleModelClient,
    DeepSeekModelClient,
    OllamaModelClient,
    OpenAICompatibleModelClient,
)
from mneme.workspace import WorkspaceContext  # noqa: F401
from mneme.cli.app import build_agent, build_arg_parser, build_welcome, main  # noqa: F401

__all__ = [
    "AnthropicCompatibleModelClient",
    "DeepSeekModelClient",
    "OllamaModelClient",
    "OpenAICompatibleModelClient",
    "WorkspaceContext",
    "build_agent",
    "build_arg_parser",
    "build_welcome",
    "main",
]
