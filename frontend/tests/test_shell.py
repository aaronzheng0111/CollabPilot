from __future__ import annotations

import asyncio
import tomllib
from uuid import uuid4

import httpx
import pytest
import yaml
from conftest import FRONTEND, main_layout_columns, use_config, write_config
from openai import AuthenticationError
from openai.resources.chat.completions import AsyncCompletions
from streamlit.testing.v1 import AppTest

from collabpilot.agent.runtime import RuntimeEvent
from collabpilot.bootstrap import create_application
from components.tool_status import apply_event, initial_status, status_html


APP = str(FRONTEND / "app.py")
FAKE_KEY = "sk-test-not-a-real-key-7f3a"


def event(event_type: str, name: str, ok: bool | None = None) -> RuntimeEvent:
    return RuntimeEvent(
        type=event_type, session_id=uuid4(), turn_id=uuid4(), name=name, ok=ok
    )


def test_layout_is_three_to_two_with_projects_history_input() -> None:
    at = AppTest.from_file(APP).run()

    assert not at.exception
    left, right = main_layout_columns(at)
    assert (left.proto.weight, right.proto.weight) == pytest.approx((0.6, 0.4))
    left_children = list(left.children.values())
    assert [child.type for child in left_children] == ["flex_container"]
    from collabpilot.campaign.workbench import CATALOG_PAGE_SIZE

    idle = left_children[0].dataframe[0].value
    assert len(idle) == CATALOG_PAGE_SIZE
    assert {"display_name", "platforms", "followers"} <= set(idle.columns)
    assert {"category", "topics", "audience_summary", "region", "engagement", "contact", "last_post"} <= set(
        idle.columns
    )
    assert "示例达人" in "\n".join(item.value for item in at.caption)
    right_children = list(right.children.values())
    assert [child.type for child in right_children] == ["flex_container"]
    frame = right_children[0]
    body = list(frame.children.values())
    assert [child.type for child in body] == ["flex_container"]
    thread = list(body[0].children.values())
    assert [child.type for child in thread] == [
        "flex_container",
        "flex_container",
        "flex_container",
    ]
    assert "新建项目" in [button.label for button in at.button]
    assert any(button.key == "cp-chat-send" and button.label == "发送" for button in at.button)
    assert len(at.chat_input) == 0
    assert any(item.key == "cp-chat-prompt" for item in at.text_input)
    assert not any(
        isinstance(item.value, str) and item.value.startswith('<div class="cp-status')
        for item in at.markdown
    )
    prev = next(b for b in at.button if b.label == "上一页")
    nxt = next(b for b in at.button if b.label == "下一页")
    assert prev.disabled and not nxt.disabled
    assert any("第 1–12 / 共 40 位" in c.value for c in at.caption)


def _send_chat(at: AppTest, text: str) -> AppTest:
    prompt = next(item for item in at.text_input if item.key == "cp-chat-prompt")
    prompt.set_value(text)
    send = next(button for button in at.button if button.key == "cp-chat-send")
    return send.click().run()


def test_theme_matches_design_tokens() -> None:
    config = tomllib.loads(
        (FRONTEND / ".streamlit/config.toml").read_text(encoding="utf-8")
    )
    design = (FRONTEND / "DESIGN.md").read_text(encoding="utf-8")
    colors = yaml.safe_load(design.split("---")[1])["colors"]

    theme = config["theme"]
    assert theme["backgroundColor"] == colors["canvas"] == "#faf9f5"
    assert theme["primaryColor"] == colors["primary"] == "#cc785c"
    assert theme["textColor"] == colors["ink"] == "#141413"


def test_status_helper_goes_idle_running_done() -> None:
    assert "空闲" in status_html(initial_status())

    running = apply_event(initial_status(), event("tool.started", "get_current_time"))
    markup = status_html(running)
    assert "get_current_time" in markup
    assert "cp-spinner" in markup

    done = apply_event(running, event("tool.completed", "get_current_time", ok=True))
    markup = status_html(done)
    assert "get_current_time" in markup
    assert "完成" in markup
    assert "cp-spinner" not in markup


def test_chat_turn_sets_session_and_shows_messages() -> None:
    at = AppTest.from_file(APP).run()

    at = _send_chat(at, "现在几点？")

    assert not at.exception
    assert at.query_params["session"]
    assert [message.name for message in at.chat_message] == ["user", "assistant"]
    tool_lines = [
        item.value
        for item in at.markdown
        if isinstance(item.value, str) and 'class="cp-tool-line' in item.value
    ]
    assert tool_lines
    assert "get_current_time" in tool_lines[0]
    assert "调用完成" in tool_lines[0]
    assert "cp-tool-line-succeeded" in tool_lines[0]
    assert "cp-spinner" not in tool_lines[0]


def test_reopened_session_shows_previous_turn() -> None:
    result = asyncio.run(create_application().chat("你好"))

    at = AppTest.from_file(APP)
    at.query_params["session"] = str(result.session_id)
    at.run()

    messages = at.chat_message
    assert [message.name for message in messages] == ["user", "assistant"]
    assert messages[0].markdown[0].value == "你好"
    assert messages[1].markdown[0].value == result.content


def test_provider_error_is_rendered_without_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
    use_config(monkeypatch, write_config(tmp_path))

    async def rejecting_create(self, **kwargs):
        raise AuthenticationError(
            f"Incorrect API key provided: {FAKE_KEY}",
            response=httpx.Response(
                401, request=httpx.Request("POST", "https://example.test/v1")
            ),
            body=None,
        )

    monkeypatch.setattr(AsyncCompletions, "create", rejecting_create)

    at = AppTest.from_file(APP).run()
    at = _send_chat(at, "你好")

    assert not at.exception
    rendered = "\n".join(item.value for item in at.error)
    assert "provider_authentication_error" in rendered
    assert FAKE_KEY not in rendered
    assert all(FAKE_KEY not in item.value for item in at.markdown)


def test_missing_key_is_reported(monkeypatch, tmp_path) -> None:
    use_config(monkeypatch, write_config(tmp_path))

    at = AppTest.from_file(APP).run()
    at = _send_chat(at, "你好")

    assert "missing_api_key" in at.error[0].value
