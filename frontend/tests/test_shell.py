from __future__ import annotations

import asyncio
import sys
import tomllib
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import yaml
from openai import AuthenticationError
from openai.resources.chat.completions import AsyncCompletions
from streamlit.testing.v1 import AppTest

FRONTEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FRONTEND))

from collabpilot.agent.runtime import RuntimeEvent  # noqa: E402
from collabpilot.bootstrap import create_application, get_settings  # noqa: E402
from collabpilot.settings import PROJECT_ROOT  # noqa: E402
from components.tool_status import apply_event, initial_status  # noqa: E402


APP = str(FRONTEND / "app.py")
FAKE_KEY = "sk-test-not-a-real-key-7f3a"


def write_config(tmp_path: Path, **model: object) -> Path:
    raw = yaml.safe_load(
        (PROJECT_ROOT / "config/config.example.yaml").read_text(encoding="utf-8")
    )
    raw["app"]["database_url"] = f"sqlite:///{tmp_path / 'agent.db'}"
    raw["app"]["log_path"] = str(tmp_path / "agent.jsonl")
    raw["model"].update(model)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    return path


def use_config(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setenv("COLLABPILOT_CONFIG", str(path))
    get_settings.cache_clear()
    create_application.cache_clear()


@pytest.fixture(autouse=True)
def isolated_application(monkeypatch, tmp_path):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    use_config(
        monkeypatch,
        write_config(
            tmp_path, default_provider="mock", default_model="collabpilot-mock"
        ),
    )
    yield
    get_settings.cache_clear()
    create_application.cache_clear()


def event(event_type: str, name: str, ok: bool | None = None) -> RuntimeEvent:
    return RuntimeEvent(
        type=event_type, session_id=uuid4(), turn_id=uuid4(), name=name, ok=ok
    )


def status_markup(at: AppTest) -> str:
    return next(
        item.value for item in at.markdown if item.value.startswith('<div class="cp-status')
    )


def test_layout_is_three_to_two_with_status_history_input() -> None:
    at = AppTest.from_file(APP).run()

    assert not at.exception
    left, right = at.columns
    assert (left.proto.weight, right.proto.weight) == pytest.approx((0.6, 0.4))
    left_children = list(left.children.values())
    assert [child.type for child in left_children] == ["dataframe", "flex_container"]
    assert left.dataframe[0].value.empty
    right_children = list(right.children.values())
    assert [child.type for child in right_children] == [
        "markdown",
        "flex_container",
        "chat_input",
    ]
    assert "cp-status" in right_children[0].value


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


def test_status_goes_idle_running_done() -> None:
    at = AppTest.from_file(APP).run()
    assert "空闲" in status_markup(at)

    running = apply_event(initial_status(), event("tool.started", "get_current_time"))
    at.session_state["tool_status"] = running
    at.run()
    markup = status_markup(at)
    assert "get_current_time" in markup
    assert "cp-spinner" in markup

    at.session_state["tool_status"] = apply_event(
        running, event("tool.completed", "get_current_time", ok=True)
    )
    at.run()
    markup = status_markup(at)
    assert "get_current_time" in markup
    assert "完成" in markup
    assert "cp-spinner" not in markup


def test_chat_turn_drives_status_and_session_query() -> None:
    at = AppTest.from_file(APP).run()

    at.chat_input[0].set_value("现在几点？").run()

    assert not at.exception
    assert "完成" in status_markup(at)
    assert at.query_params["session"]
    assert [message.name for message in at.chat_message] == ["user", "assistant"]


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
    at.chat_input[0].set_value("你好").run()

    assert not at.exception
    rendered = "\n".join(item.value for item in at.error)
    assert "provider_authentication_error" in rendered
    assert FAKE_KEY not in rendered
    assert all(FAKE_KEY not in item.value for item in at.markdown)


def test_missing_key_is_reported(monkeypatch, tmp_path) -> None:
    use_config(monkeypatch, write_config(tmp_path))

    at = AppTest.from_file(APP).run()
    at.chat_input[0].set_value("你好").run()

    assert "missing_api_key" in at.error[0].value
