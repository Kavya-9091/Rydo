from app.ai.providers.base import LLMProvider
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.providers.local_provider import LocalFallbackProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.settings import get_settings


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.ai_default_provider == "claude":
        if not settings.anthropic_api_key:
            return LocalFallbackProvider()
        return ClaudeProvider()
    if not settings.openai_api_key:
        return LocalFallbackProvider()
    return OpenAIProvider()
