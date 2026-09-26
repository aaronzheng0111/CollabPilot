from pathlib import Path

import pytest

from collabpilot.agent.context import ContextBuilder
from collabpilot.agent.runtime import AgentRuntime
from collabpilot.application import ApplicationService
from collabpilot.infrastructure.session_store import SQLiteSessionStore
from collabpilot.providers.registry import ProviderRegistry
from collabpilot.settings import AgentSettings, load_settings
from collabpilot.tools.policy import ToolPolicy
from collabpilot.tools.registry import ToolRegistry


@pytest.fixture
def settings(tmp_path: Path) -> AgentSettings:
    loaded = load_settings("config/config.example.yaml")
    loaded.project_root = tmp_path
    loaded.app.database_url = "sqlite:///agent.db"
    identity = tmp_path / "agent.md"
    identity.write_text("# Identity\nTest Agent", encoding="utf-8")
    prompt = tmp_path / "system.md"
    prompt.write_text("Identity:\n{identity}", encoding="utf-8")
    loaded.app.identity_path = "agent.md"
    return loaded


@pytest.fixture
def application(settings: AgentSettings, tmp_path: Path) -> ApplicationService:
    store = SQLiteSessionStore(settings.app.database_url, settings.project_root)
    providers = ProviderRegistry(settings)
    tools = ToolRegistry(settings.tools.enabled)
    runtime = AgentRuntime(
        tools,
        ToolPolicy(settings.tools.allow_risk_levels),
        settings.runtime,
    )
    context = ContextBuilder(tmp_path / "agent.md", tmp_path / "system.md")
    return ApplicationService(settings, store, providers, runtime, context)

