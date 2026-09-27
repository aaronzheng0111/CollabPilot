"""Eval fixtures: real DeepSeek, real `backend/.env`, throwaway SQLite."""

from __future__ import annotations

from pathlib import Path

import pytest

from collabpilot.agent.context import ContextBuilder
from collabpilot.agent.runtime import AgentRuntime
from collabpilot.application import ApplicationService
from collabpilot.campaign.store import CampaignStore
from collabpilot.infrastructure.session_store import SQLiteSessionStore
from collabpilot.providers.registry import ProviderRegistry
from collabpilot.settings import PROJECT_ROOT, load_settings
from collabpilot.tools.policy import ToolPolicy
from collabpilot.tools.registry import ToolRegistry


@pytest.fixture(autouse=True)
def offline_deepseek() -> None:
    """Override the unit-test guard: eval is allowed to reach api.deepseek.com."""


@pytest.fixture
def eval_application(tmp_path: Path) -> ApplicationService:
    settings = load_settings("config/config.example.yaml")
    if not settings.provider_api_key(settings.model.default_provider):
        pytest.skip("DEEPSEEK_API_KEY not configured (env or backend/.env)")
    settings.app.database_url = f"sqlite:///{tmp_path / 'eval.db'}"
    store = SQLiteSessionStore(settings.app.database_url, settings.project_root)
    tools = ToolRegistry(
        settings.tools.enabled, CampaignStore(store), settings.runtime.max_tool_result_chars
    )
    runtime = AgentRuntime(tools, ToolPolicy(settings.tools.allow_risk_levels), settings.runtime)
    context = ContextBuilder(
        settings.resolve_path(settings.app.identity_path),
        PROJECT_ROOT / "config/prompts/system.md",
    )
    return ApplicationService(settings, store, ProviderRegistry(settings), runtime, context)
