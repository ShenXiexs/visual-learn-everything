"""Selects and instantiates the configured GenAI provider."""

from __future__ import annotations

from functools import lru_cache

from .. import config
from .base import LLMProvider


@lru_cache(maxsize=1)
def get_provider() -> LLMProvider:
    name = config.resolve_provider()
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    if name == "mock":
        from .mock_provider import MockProvider

        return MockProvider()
    raise ValueError(f"Unknown LLM_PROVIDER '{name}'. Use anthropic | openai | mock.")
