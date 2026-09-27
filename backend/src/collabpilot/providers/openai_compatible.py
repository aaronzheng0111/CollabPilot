from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

from collabpilot.domain.errors import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from collabpilot.domain.models import Message, ModelResponse, ToolCall
from collabpilot.providers.base import Provider


class OpenAICompatibleProvider(Provider):
    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        timeout: float,
        max_retries: int,
        temperature: float,
        stream: bool = False,
        thinking: str | None = None,
    ):
        self.name = name
        self.temperature = temperature
        self.stream = stream
        self.thinking = thinking
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def complete(
        self,
        messages: list[Message],
        model: str,
        tools: list[dict[str, Any]],
        on_delta: Callable[[str], Awaitable[None]] | None = None,
        temperature: float | None = None,
    ) -> ModelResponse:
        request_messages: list[dict[str, Any]] = []
        for message in messages:
            item: dict[str, Any] = {
                "role": message.role,
                "content": message.content,
            }
            if message.name:
                item["name"] = message.name
            if message.tool_call_id:
                item["tool_call_id"] = message.tool_call_id
            if message.tool_calls:
                item["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in message.tool_calls
                ]
            request_messages.append(item)
        selected_temperature = (
            self.temperature if temperature is None else temperature
        )
        try:
            extra_body = (
                {"thinking": {"type": self.thinking}}
                if self.thinking
                else None
            )
            if self.stream:
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=request_messages,  # type: ignore[arg-type]
                    tools=tools or None,  # type: ignore[arg-type]
                    temperature=selected_temperature,
                    stream=True,
                    extra_body=extra_body,
                )
                content_parts: list[str] = []
                call_parts: dict[int, dict[str, str]] = {}
                usage: dict[str, Any] = {}
                async for chunk in stream:
                    if chunk.usage:
                        usage = chunk.usage.model_dump()
                    for choice_item in chunk.choices:
                        delta = choice_item.delta
                        if delta.content:
                            content_parts.append(delta.content)
                            if on_delta:
                                await on_delta(delta.content)
                        for call in delta.tool_calls or []:
                            part = call_parts.setdefault(
                                call.index,
                                {"id": "", "name": "", "arguments": ""},
                            )
                            if call.id:
                                part["id"] = call.id
                            if call.function:
                                if call.function.name:
                                    part["name"] += call.function.name
                                if call.function.arguments:
                                    part["arguments"] += call.function.arguments
                calls = [
                    ToolCall(
                        id=part["id"] or f"stream-call-{index}",
                        name=part["name"],
                        arguments=json.loads(part["arguments"] or "{}"),
                    )
                    for index, part in sorted(call_parts.items())
                ]
                return ModelResponse(
                    content="".join(content_parts) or None,
                    tool_calls=calls,
                    provider=self.name,
                    model=model,
                    usage=usage,
                )
            response = await self.client.chat.completions.create(
                model=model,
                messages=request_messages,  # type: ignore[arg-type]
                tools=tools or None,  # type: ignore[arg-type]
                temperature=selected_temperature,
                extra_body=extra_body,
            )
        except AuthenticationError as exc:
            raise ProviderAuthenticationError("Provider authentication failed") from exc
        except RateLimitError as exc:
            raise ProviderRateLimitError("Provider rate limit reached") from exc
        except (APITimeoutError, APIConnectionError) as exc:
            raise ProviderTimeoutError("Provider connection timed out") from exc
        except Exception as exc:
            raise ProviderError(f"Provider request failed: {type(exc).__name__}") from exc

        choice = response.choices[0].message
        if choice.content and on_delta:
            await on_delta(choice.content)
        calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                arguments=json.loads(call.function.arguments or "{}"),
            )
            for call in (choice.tool_calls or [])
        ]
        usage = response.usage.model_dump() if response.usage else {}
        return ModelResponse(
            content=choice.content,
            tool_calls=calls,
            provider=self.name,
            model=model,
            usage=usage,
        )

    async def health(self, model: str) -> tuple[bool, str]:
        try:
            await self.complete(
                [Message(role="user", content="Reply with OK.")],
                model=model,
                tools=[],
            )
            return True, f"{self.name} responded successfully ({model})"
        except ProviderError as exc:
            return False, str(exc)
