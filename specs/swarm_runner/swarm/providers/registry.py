from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from swarm.providers.anthropic_provider import AnthropicProvider
from swarm.providers.base import ProviderClient
from swarm.providers.gemini_provider import GeminiProvider
from swarm.providers.openai_compatible_provider import OpenAICompatibleProvider
from swarm.providers.openai_provider import OpenAIProvider
from swarm.providers.xai_provider import XAIProvider


@dataclass
class ModelRuntime:
    provider: str
    model: str
    base_url: Optional[str]
    params: Dict[str, object]
    fallback_models: list[str]


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, ProviderClient] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "xai": XAIProvider(),
            "openai_compatible": OpenAICompatibleProvider(),
        }

    def get(self, provider: str, api_key_override: Optional[str] = None) -> ProviderClient:
        if provider not in self._providers:
            return self._providers["openai"]
        if api_key_override and provider == "openai":
            return OpenAIProvider(api_key_override)
        if api_key_override and provider == "openai_compatible":
            return OpenAICompatibleProvider(api_key_override)
        return self._providers[provider]
