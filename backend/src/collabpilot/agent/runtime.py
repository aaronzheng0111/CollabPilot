from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from collabpilot.domain.errors import RuntimeBudgetExceeded, ToolPolicyError
from collabpilot.domain.models import Message, ModelResponse
from collabpilot.observability.logging import get_logger
from collabpilot.providers.base import Provider
from collabpilot.settings import RuntimeConfig
from collabpilot.tools.base import ToolContext
from collabpilot.tools.policy import ToolPolicy
from collabpilot.tools.registry import ToolRegistry


RuntimeEventType = Literal["model.requested", "tool.started", "tool.completed"]


class RuntimeEvent(BaseModel):
    type: RuntimeEventType
    session_id: UUID
    turn_id: UUID
    name: str
    ok: bool | None = None
    error_code: str | None = None


EventHandler = Callable[[RuntimeEvent], Awaitable[None]]


class AgentRuntime:
    def __init__(
        self,
        tools: ToolRegistry,
        policy: ToolPolicy,
        budget: RuntimeConfig,
    ):
        self.tools = tools
        self.policy = policy
        self.budget = budget

    async def run(
        self,
        provider: Provider,
        model: str,
        messages: list[Message],
        session_id: UUID,
        turn_id: UUID,
        on_delta: Callable[[str], Awaitable[None]] | None = None,
        on_event: EventHandler | None = None,
        temperature: float | None = None,
        disabled_tools: frozenset[str] = frozenset(),
    ) -> tuple[ModelResponse, list[Message], int]:
        """`disabled_tools` are hidden from the model and rejected if called
        anyway (e.g. search tools while the goal is still CLARIFYING)."""
        started = monotonic()
        schemas = [
            schema
            for schema in self.tools.schemas()
            if schema["function"]["name"] not in disabled_tools
        ]
        model_calls = 0
        tool_calls = 0
        repeated_calls: dict[str, int] = {}
        generated: list[Message] = []
        logger = get_logger(session_id=str(session_id), turn_id=str(turn_id))

        async def emit(
            event_type: RuntimeEventType,
            name: str,
            ok: bool | None = None,
            error_code: str | None = None,
        ) -> None:
            if on_event:
                await on_event(
                    RuntimeEvent(
                        type=event_type,
                        session_id=session_id,
                        turn_id=turn_id,
                        name=name,
                        ok=ok,
                        error_code=error_code,
                    )
                )

        while model_calls < self.budget.max_model_calls:
            if monotonic() - started > self.budget.max_seconds:
                raise RuntimeBudgetExceeded("Maximum run time exceeded")
            model_calls += 1
            logger.info(
                "model.requested",
                provider=provider.name,
                model=model,
                model_call=model_calls,
            )
            await emit("model.requested", model)
            response = await provider.complete(
                messages,
                model,
                schemas,
                # Content deltas only (providers must not stream tool JSON).
                # Tool-call rounds typically emit no content; final text streams live.
                on_delta=on_delta,
                temperature=temperature,
            )
            logger.info(
                "model.completed",
                provider=response.provider,
                model=response.model,
                tool_call_count=len(response.tool_calls),
                usage=response.usage,
            )
            if not response.tool_calls:
                if not response.content:
                    response.content = "The model returned an empty response."
                    if on_delta:
                        await on_delta(response.content)
                return response, generated, tool_calls

            messages.append(
                Message(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                )
            )
            for call in response.tool_calls:
                if tool_calls >= self.budget.max_tool_calls:
                    raise RuntimeBudgetExceeded("Maximum tool calls exceeded")
                signature = f"{call.name}:{json.dumps(call.arguments, sort_keys=True)}"
                repeated_calls[signature] = repeated_calls.get(signature, 0) + 1
                if repeated_calls[signature] > 2:
                    raise RuntimeBudgetExceeded(
                        f"Repeated identical tool call detected: {call.name}"
                    )
                await emit("tool.started", call.name)
                ok = False
                error_code: str | None
                tool = self.tools.get(call.name)
                if call.name in disabled_tools:
                    error_code = "tool_disabled"
                    result_text = json.dumps(
                        {"ok": False, "error_code": error_code},
                        ensure_ascii=False,
                    )
                elif tool is None:
                    error_code = "unknown_tool"
                    result_text = json.dumps(
                        {"ok": False, "error_code": error_code},
                        ensure_ascii=False,
                    )
                else:
                    try:
                        self.policy.check(tool)
                        logger.info(
                            "tool.requested",
                            tool=tool.name,
                            risk_level=tool.risk_level,
                        )
                        result = await asyncio.wait_for(
                            tool.execute(
                                call.arguments,
                                ToolContext(session_id=session_id, turn_id=turn_id),
                            ),
                            timeout=self.budget.tool_timeout_seconds,
                        )
                        ok, error_code = result.ok, result.error_code
                        result_text = result.model_dump_json()
                        logger.info(
                            "tool.completed",
                            tool=tool.name,
                            ok=result.ok,
                            error_code=result.error_code,
                        )
                    except ToolPolicyError as exc:
                        error_code = exc.code
                        result_text = json.dumps(
                            {"ok": False, "error_code": exc.code, "display": str(exc)},
                            ensure_ascii=False,
                        )
                    except TimeoutError:
                        error_code = "tool_timeout"
                        result_text = json.dumps(
                            {"ok": False, "error_code": error_code},
                            ensure_ascii=False,
                        )
                await emit("tool.completed", call.name, ok=ok, error_code=error_code)
                result_text = result_text[: self.budget.max_tool_result_chars]
                tool_message = Message(
                    role="tool",
                    content=result_text,
                    name=call.name,
                    tool_call_id=call.id,
                )
                messages.append(tool_message)
                generated.append(tool_message)
                tool_calls += 1

        raise RuntimeBudgetExceeded("Maximum model calls exceeded")
