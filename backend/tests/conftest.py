import socket
from pathlib import Path

import pytest

from collabpilot.agent.context import ContextBuilder
from collabpilot.agent.runtime import AgentRuntime
from collabpilot.application import ApplicationService
from collabpilot.campaign.store import CampaignStore
from collabpilot.infrastructure.session_store import SQLiteSessionStore
from collabpilot.providers.registry import ProviderRegistry
from collabpilot.settings import AgentSettings, load_settings
from collabpilot.tools.policy import ToolPolicy
from collabpilot.tools.registry import ToolRegistry


BLOCKED_HOST = "api.deepseek.com"


@pytest.fixture(autouse=True)
def offline_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    real_getaddrinfo = socket.getaddrinfo

    def guarded_getaddrinfo(host, *args, **kwargs):
        name = host.decode() if isinstance(host, bytes) else str(host)
        if name == BLOCKED_HOST:
            raise AssertionError(f"Tests must not reach {BLOCKED_HOST}")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)


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
    tools = ToolRegistry(
        settings.tools.enabled,
        CampaignStore(store),
        settings.runtime.max_tool_result_chars,
    )
    runtime = AgentRuntime(
        tools,
        ToolPolicy(settings.tools.allow_risk_levels),
        settings.runtime,
    )
    context = ContextBuilder(tmp_path / "agent.md", tmp_path / "system.md")
    return ApplicationService(settings, store, providers, runtime, context)

