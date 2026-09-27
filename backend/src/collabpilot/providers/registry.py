from __future__ import annotations

from collabpilot.domain.errors import ConfigurationError, MissingApiKeyError
from collabpilot.providers.base import Provider
from collabpilot.providers.mock import MockProvider
from collabpilot.providers.openai_compatible import OpenAICompatibleProvider
from collabpilot.settings import AgentSettings


class ProviderRegistry:
    def __init__(self, settings: AgentSettings):
        self.settings = settings

    def names(self) -> list[str]:
        return sorted(self.settings.providers)

    def get(self, name: str) -> Provider:
        if name not in self.settings.providers:
            raise ConfigurationError(f"Unknown provider: {name}")
        config = self.settings.providers[name]
        if config.type == "mock":
            provider = MockProvider()
            provider.name = name
            return provider
        api_key = self.settings.provider_api_key(name)
        if not api_key:
            raise MissingApiKeyError(
                f"Missing API key environment variable: {config.api_key_env}"
            )
        if not config.base_url:
            raise ConfigurationError(f"Missing base_url for provider: {name}")
        return OpenAICompatibleProvider(
            name=name,
            base_url=config.base_url,
            api_key=api_key,
            timeout=self.settings.model.timeout_seconds,
            max_retries=self.settings.model.max_retries,
            temperature=self.settings.model.temperature,
            stream=config.stream,
            thinking=config.thinking,
        )
