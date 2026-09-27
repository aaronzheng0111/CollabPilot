from __future__ import annotations

from uuid import UUID, uuid4
from collections.abc import Awaitable, Callable

from collabpilot.agent.context import ContextBuilder
from collabpilot.agent.runtime import AgentRuntime, EventHandler
from collabpilot.domain.models import ChatResult, Message
from collabpilot.infrastructure.session_store import SQLiteSessionStore
from collabpilot.observability.logging import get_logger
from collabpilot.providers.registry import ProviderRegistry
from collabpilot.settings import AgentSettings


class ApplicationService:
    def __init__(
        self,
        settings: AgentSettings,
        store: SQLiteSessionStore,
        providers: ProviderRegistry,
        runtime: AgentRuntime,
        context: ContextBuilder,
    ):
        self.settings = settings
        self.store = store
        self.providers = providers
        self.runtime = runtime
        self.context = context

    def history(self, session_id: UUID) -> list[Message]:
        return self.store.list_messages(session_id)

    async def chat(
        self,
        content: str,
        session_id: UUID | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        on_delta: Callable[[str], Awaitable[None]] | None = None,
        on_event: EventHandler | None = None,
        creative: bool = False,
    ) -> ChatResult:
        provider_name = provider_name or self.settings.model.default_provider
        model = model or self.settings.model.default_model
        provider = self.providers.get(provider_name)
        session_id = self.store.ensure_session(session_id)
        turn_id = uuid4()
        logger = get_logger(session_id=str(session_id), turn_id=str(turn_id))
        logger.info("turn.started")

        user_message = Message(role="user", content=content)
        self.store.add_message(session_id, turn_id, user_message)
        # Stored tool messages lack the assistant tool_calls they answer, so
        # providers would reject them as orphans.
        history = [
            message
            for message in self.store.list_messages(session_id)
            if message.role != "tool"
        ]
        messages = self.context.build(history)
        temperature = (
            self.settings.model.creative_temperature if creative else None
        )

        try:
            response, generated, tool_call_count = await self.runtime.run(
                provider=provider,
                model=model,
                messages=messages,
                session_id=session_id,
                turn_id=turn_id,
                on_delta=on_delta,
                on_event=on_event,
                temperature=temperature,
            )
            for message in generated:
                self.store.add_message(session_id, turn_id, message)
            assistant = Message(role="assistant", content=response.content or "")
            self.store.add_message(session_id, turn_id, assistant)
            logger.info(
                "turn.completed",
                provider=response.provider,
                model=response.model,
            )
            return ChatResult(
                session_id=session_id,
                turn_id=turn_id,
                content=assistant.content,
                provider=response.provider,
                model=response.model,
                tool_calls=tool_call_count,
            )
        except Exception as exc:
            logger.error(
                "turn.failed",
                error_code=getattr(exc, "code", "unexpected_error"),
                error_type=type(exc).__name__,
            )
            raise
