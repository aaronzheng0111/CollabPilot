from functools import lru_cache

from collabpilot.agent.context import ContextBuilder
from collabpilot.agent.runtime import AgentRuntime
from collabpilot.application import ApplicationService
from collabpilot.campaign.store import CampaignStore
from collabpilot.infrastructure.session_store import SQLiteSessionStore
from collabpilot.observability.logging import configure_logging
from collabpilot.providers.registry import ProviderRegistry
from collabpilot.settings import AgentSettings, load_settings
from collabpilot.tools.policy import ToolPolicy
from collabpilot.tools.registry import ToolRegistry


@lru_cache
def get_settings() -> AgentSettings:
    return load_settings()


@lru_cache
def create_application() -> ApplicationService:
    settings = get_settings()
    configure_logging(settings.resolve_path(settings.app.log_path))
    store = SQLiteSessionStore(settings.app.database_url, settings.project_root)
    providers = ProviderRegistry(settings)
    tools = ToolRegistry(
        settings.tools.enabled,
        CampaignStore(store),
        settings.runtime.max_tool_result_chars,
    )
    policy = ToolPolicy(settings.tools.allow_risk_levels)
    runtime = AgentRuntime(tools, policy, settings.runtime)
    context = ContextBuilder(
        settings.resolve_path(settings.app.identity_path),
        settings.project_root / "config/prompts/system.md",
    )
    return ApplicationService(
        settings=settings,
        store=store,
        providers=providers,
        runtime=runtime,
        context=context,
    )

