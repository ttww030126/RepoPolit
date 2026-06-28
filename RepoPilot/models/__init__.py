"""模型后端层：把不同 provider 抹平成统一的 complete() 接口。"""
from mneme.models.clients import (  # noqa: F401
    AnthropicCompatibleModelClient,
    DeepSeekModelClient,
    FakeModelClient,
    OllamaModelClient,
    OpenAICompatibleModelClient,
)
