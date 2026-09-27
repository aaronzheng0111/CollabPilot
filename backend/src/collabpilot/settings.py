from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from collabpilot.domain.errors import ConfigurationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AppConfig(BaseModel):
    name: str = "CollabPilot"
    environment: str = "development"
    database_url: str = "sqlite:///data/agent.db"
    log_path: str = "logs/agent.jsonl"
    identity_path: str = "docs/agent.md"


class ModelConfig(BaseModel):
    default_provider: str = "deepseek"
    default_model: str = "deepseek-chat"
    temperature: float = 0.2
    # Used for outreach drafts / follow-up copy, not for tool orchestration.
    creative_temperature: float = 0.85
    timeout_seconds: float = 60
    max_retries: int = 2
    # Upper bound for one reply. The judgment step returns ~20 verdicts in one
    # JSON block, which overflows DeepSeek's 4096-token default.
    max_output_tokens: int | None = 8192


class ProviderConfig(BaseModel):
    type: Literal["mock", "openai_compatible"]
    base_url: str | None = None
    api_key_env: str | None = None
    stream: bool = False
    thinking: Literal["enabled", "disabled"] | None = None


class RuntimeConfig(BaseModel):
    max_model_calls: int = Field(default=12, ge=1, le=50)
    max_tool_calls: int = Field(default=24, ge=0, le=100)
    max_seconds: float = Field(default=180, gt=0)
    tool_timeout_seconds: float = Field(default=10, gt=0)
    max_tool_result_chars: int = Field(default=12000, ge=100)


class ToolsConfig(BaseModel):
    enabled: list[str] = Field(
        default_factory=lambda: [
            "get_current_time",
            "search_creators",
            "get_creator",
            "apply_hard_filters",
            "save_campaign_selection",
            "exclude_creator",
            "confirm_channel",
            "save_drafts",
            "approve_draft",
            "reject_draft",
            "save_follow_up",
            "note_follow_up",
        ]
    )
    allow_risk_levels: list[str] = Field(default_factory=lambda: ["read"])


class AgentSettings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    providers: dict[str, ProviderConfig]
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    project_root: Path = PROJECT_ROOT

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.project_root / path

    def provider_api_key(self, provider_name: str) -> str | None:
        provider = self.providers[provider_name]
        if not provider.api_key_env:
            return None
        current = os.getenv(provider.api_key_env)
        if current:
            return current
        env_path = self.project_root / ".env"
        if not env_path.exists():
            return None
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == provider.api_key_env:
                return value.strip().strip("\"'")
        return None


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    collabpilot_config: str | None = None


def load_settings(config_path: str | Path | None = None) -> AgentSettings:
    env = EnvironmentSettings()
    selected = config_path or env.collabpilot_config or "config/config.yaml"
    path = Path(selected)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        example = PROJECT_ROOT / "config/config.example.yaml"
        path = example if example.exists() else path
    if not path.exists():
        raise ConfigurationError(f"Config file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = AgentSettings.model_validate(raw)
    if settings.model.default_provider not in settings.providers:
        raise ConfigurationError(
            f"Unknown default provider: {settings.model.default_provider}"
        )
    return settings
