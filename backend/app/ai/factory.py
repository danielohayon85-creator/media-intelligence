from functools import lru_cache

from app.ai.base import AIProvider
from app.ai.mock_provider import MockAIProvider
from app.core.config import settings


@lru_cache
def get_ai_provider() -> AIProvider:
    if settings.ai_provider == "anthropic" and settings.anthropic_api_key:
        from app.ai.anthropic_provider import AnthropicAIProvider

        try:
            return AnthropicAIProvider()
        except Exception:
            return MockAIProvider()
    return MockAIProvider()
