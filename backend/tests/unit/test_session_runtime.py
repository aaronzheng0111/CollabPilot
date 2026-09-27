import socket
from uuid import uuid4

import httpx
import pytest
from openai import AuthenticationError

from collabpilot.agent.runtime import AgentRuntime, RuntimeEvent
from collabpilot.domain.errors import MissingApiKeyError, ProviderError
from collabpilot.domain.models import Message, ModelResponse, ToolCall
from collabpilot.infrastructure.session_store import SQLiteSessionStore
from collabpilot.providers.base import Provider
from collabpilot.providers.mock import MockProvider
from collabpilot.providers.openai_compatible import OpenAICompatibleProvider
from collabpilot.settings import RuntimeConfig, load_settings
from collabpilot.tools.policy import ToolPolicy
from collabpilot.tools.registry import ToolRegistry


FAKE_KEY = "sk-test-not-a-real-key-7f3a"


class ScriptedProvider(Provider):
    name = "scripted"

    def __init__(self, responses: list[ModelResponse]):
        self.responses = list(responses)
        self.requests: list[list[Message]] = []

    async def complete(self, messages, model, tools, on_delta=None) -> ModelResponse:
        self.requests.append([message.model_copy() for message in messages])
        return self.responses.pop(0)

    async def health(self, model: str) -> tuple[bool, str]:
        return True, "scripted"


class RecordingMockProvider(MockProvider):
    def __init__(self):
        self.requests: list[list[Message]] = []

    async def complete(self, messages, model, tools, on_delta=None) -> ModelResponse:
        self.requests.append([message.model_copy() for message in messages])
        return await super().complete(messages, model, tools, on_delta)


def distinct_offsets(count: int) -> list[str]:
    offsets = [f"+{hour:02d}:00" for hour in range(13)]
    offsets += [f"-{hour:02d}:00" for hour in range(1, 12)]
    return offsets[:count]


async def test_new_session_is_readable_from_sqlite(application, settings) -> None:
    result = await application.chat("你好", provider_name="mock")

    reopened = SQLiteSessionStore(settings.app.database_url, settings.project_root)
    messages = reopened.list_messages(result.session_id)
    assert [(message.role, message.content) for message in messages] == [
        ("user", "你好"),
        ("assistant", result.content),
    ]


async def test_second_turn_sends_first_turn_history(application, monkeypatch) -> None:
    provider = RecordingMockProvider()
    monkeypatch.setattr(application.providers, "get", lambda name: provider)

    first = await application.chat("你好")
    await application.chat("现在几点？", session_id=first.session_id)

    second_request = provider.requests[1]
    assert [(message.role, message.content) for message in second_request[1:]] == [
        ("user", "你好"),
        ("assistant", first.content),
        ("user", "现在几点？"),
    ]


async def test_tool_messages_are_stored_but_not_resent(application, monkeypatch) -> None:
    provider = RecordingMockProvider()
    monkeypatch.setattr(application.providers, "get", lambda name: provider)

    first = await application.chat("现在几点？")
    await application.chat("你好", session_id=first.session_id)

    stored = application.history(first.session_id)
    assert [message.role for message in stored] == [
        "user",
        "tool",
        "assistant",
        "user",
        "assistant",
    ]
    assert stored[1].name == "get_current_time"
    assert all(message.role != "tool" for message in provider.requests[-1])


def test_example_config_defaults_to_deepseek_and_budget() -> None:
    settings = load_settings("config/config.example.yaml")

    assert settings.model.default_provider == "deepseek"
    assert settings.model.default_model == "deepseek-chat"
    assert settings.providers["deepseek"].api_key_env == "DEEPSEEK_API_KEY"
    assert (
        settings.runtime.max_model_calls,
        settings.runtime.max_tool_calls,
        settings.runtime.max_seconds,
    ) == (12, 24, 180)
    defaults = RuntimeConfig()
    assert (defaults.max_model_calls, defaults.max_tool_calls, defaults.max_seconds) == (
        12,
        24,
        180,
    )


async def test_chat_without_provider_uses_deepseek(
    application, settings, monkeypatch
) -> None:
    (settings.project_root / ".env").write_text(
        f"DEEPSEEK_API_KEY={FAKE_KEY}\n", encoding="utf-8"
    )

    async def fake_complete(self, messages, model, tools, on_delta=None):
        return ModelResponse(content="好的", provider=self.name, model=model)

    monkeypatch.setattr(OpenAICompatibleProvider, "complete", fake_complete)

    result = await application.chat("你好")

    assert (result.provider, result.model) == ("deepseek", "deepseek-chat")


def test_deepseek_host_is_blocked_in_tests() -> None:
    with pytest.raises(AssertionError):
        socket.getaddrinfo("api.deepseek.com", 443)


async def test_budget_allows_twelve_model_calls_and_twenty_four_tools() -> None:
    budget = load_settings("config/config.example.yaml").runtime
    offsets = distinct_offsets(24)
    batches = [offsets[0:3], offsets[3:6]] + [
        offsets[index : index + 2] for index in range(6, 24, 2)
    ]
    responses = [
        ModelResponse(
            provider="scripted",
            model="scripted",
            tool_calls=[
                ToolCall(
                    id=f"call-{offset}",
                    name="get_current_time",
                    arguments={"timezone": offset},
                )
                for offset in batch
            ],
        )
        for batch in batches
    ]
    responses.append(ModelResponse(content="done", provider="scripted", model="scripted"))
    provider = ScriptedProvider(responses)
    runtime = AgentRuntime(
        ToolRegistry(["get_current_time"]), ToolPolicy(["read"]), budget
    )

    response, generated, tool_calls = await runtime.run(
        provider=provider,
        model="scripted",
        messages=[Message(role="user", content="go")],
        session_id=uuid4(),
        turn_id=uuid4(),
    )

    assert len(provider.requests) == 12
    assert tool_calls == 24
    assert len(generated) == 24
    assert response.content == "done"


async def test_tool_call_emits_events_in_order(application) -> None:
    events: list[RuntimeEvent] = []

    async def on_event(event: RuntimeEvent) -> None:
        events.append(event)

    result = await application.chat(
        "现在几点？",
        provider_name="mock",
        model="collabpilot-mock",
        on_event=on_event,
    )

    assert [(event.type, event.name) for event in events] == [
        ("model.requested", "collabpilot-mock"),
        ("tool.started", "get_current_time"),
        ("tool.completed", "get_current_time"),
        ("model.requested", "collabpilot-mock"),
    ]
    assert events[2].ok is True
    assert all(event.session_id == result.session_id for event in events)
    assert all(event.turn_id == result.turn_id for event in events)


async def test_failed_tool_emits_completed_with_error_code() -> None:
    events: list[RuntimeEvent] = []

    async def on_event(event: RuntimeEvent) -> None:
        events.append(event)

    provider = ScriptedProvider(
        [
            ModelResponse(
                provider="scripted",
                model="scripted",
                tool_calls=[ToolCall(id="call-1", name="missing_tool")],
            ),
            ModelResponse(content="done", provider="scripted", model="scripted"),
        ]
    )
    runtime = AgentRuntime(
        ToolRegistry(["get_current_time"]), ToolPolicy(["read"]), RuntimeConfig()
    )

    await runtime.run(
        provider=provider,
        model="scripted",
        messages=[Message(role="user", content="go")],
        session_id=uuid4(),
        turn_id=uuid4(),
        on_event=on_event,
    )

    completed = [event for event in events if event.type == "tool.completed"]
    assert [(event.ok, event.error_code) for event in completed] == [
        (False, "unknown_tool")
    ]


async def test_missing_key_raises_missing_api_key(application) -> None:
    with pytest.raises(MissingApiKeyError) as raised:
        await application.chat("你好")

    assert raised.value.code == "missing_api_key"


async def test_provider_error_does_not_leak_key(
    application, monkeypatch, capsys, caplog
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)

    async def rejecting_create(**kwargs):
        raise AuthenticationError(
            f"Incorrect API key provided: {FAKE_KEY}",
            response=httpx.Response(
                401, request=httpx.Request("POST", "https://example.test/v1")
            ),
            body=None,
        )

    original_get = application.providers.get

    def get(name: str):
        provider = original_get(name)
        provider.client.chat.completions.create = rejecting_create
        return provider

    monkeypatch.setattr(application.providers, "get", get)

    with pytest.raises(ProviderError) as raised:
        await application.chat("你好")

    captured = capsys.readouterr()
    assert raised.value.code == "provider_authentication_error"
    assert FAKE_KEY not in str(raised.value)
    assert FAKE_KEY not in captured.out + captured.err + caplog.text
