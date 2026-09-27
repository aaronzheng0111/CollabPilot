"""Multi-project chat: list / switch / delete project and delete one message."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from conftest import FRONTEND
from streamlit.testing.v1 import AppTest

from collabpilot.bootstrap import create_application
from collabpilot.domain.models import Message, StoredMessage
from components.chat_history import DELETE_MESSAGE, group_entries, tool_line_html
from components.project_list import (
    CONFIRM_RENAME,
    DELETE_ICON,
    NEW_PROJECT,
    RENAME_ICON,
)


APP = str(FRONTEND / "app.py")


def session_param(at: AppTest) -> str | None:
    raw = at.query_params.get("session")
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw[0] if raw else None
    return str(raw)


def test_tool_line_is_short_and_shows_status() -> None:
    entry = StoredMessage(
        id=uuid4(),
        session_id=uuid4(),
        turn_id=uuid4(),
        message=Message(
            role="tool",
            name="search_creators",
            content='{"ok": true, "data": {"huge": true}}',
        ),
        created_at=datetime(2026, 9, 27, 6, 30, tzinfo=UTC),
    )
    html = tool_line_html(entry)
    assert "search_creators" in html
    assert "调用完成" in html
    assert "huge" not in html
    assert "cp-tool-line-succeeded" in html
    assert "#5db872" not in html  # color lives in theme CSS class


def test_tool_line_running_shows_spinner_without_widget_key() -> None:
    from components.chat_history import tool_line_html_parts

    html = tool_line_html_parts("search_creators", state="running")
    assert "正在调用" in html
    assert "search_creators" in html
    assert "cp-spinner" in html
    assert "cp-tool-line-running" in html
    assert "key=" not in html


def test_tool_line_failed_is_short_and_not_succeeded() -> None:
    from components.chat_history import tool_line_html_parts

    html = tool_line_html_parts("search_creators", state="failed")
    assert "失败" in html
    assert "调用完成" not in html
    assert "cp-tool-line-failed" in html
    assert "cp-tool-line-succeeded" not in html
    assert "cp-spinner" not in html


def test_replace_running_tool_line_swaps_matching_spinner() -> None:
    from components.chat_history import replace_running_tool_line, tool_line_html_parts

    running_a = tool_line_html_parts("search_creators", state="running")
    running_b = tool_line_html_parts("apply_hard_filters", state="running")
    done_a = tool_line_html_parts("search_creators", state="succeeded")
    lines = [running_a, running_b]
    updated = replace_running_tool_line(lines, "search_creators", done_a)
    assert updated[0] == done_a
    assert updated[1] == running_b
    assert "正在调用" in updated[1]
    assert "调用完成" in updated[0]


def test_group_entries_puts_tools_inside_assistant() -> None:
    session_id = uuid4()
    turn_id = uuid4()
    user = StoredMessage(
        id=uuid4(),
        session_id=session_id,
        turn_id=turn_id,
        message=Message(role="user", content="现在几点？"),
    )
    tool = StoredMessage(
        id=uuid4(),
        session_id=session_id,
        turn_id=turn_id,
        message=Message(role="tool", name="get_current_time", content='{"ok": true}'),
    )
    assistant = StoredMessage(
        id=uuid4(),
        session_id=session_id,
        turn_id=turn_id,
        message=Message(role="assistant", content="现在是下午三点。"),
    )
    blocks = group_entries([user, tool, assistant])
    assert [block.role for block in blocks] == ["user", "assistant"]
    assert blocks[1].tools == [tool]
    assert blocks[1].entry.message.content == "现在是下午三点。"


def test_rename_project_updates_sidebar_title() -> None:
    application = create_application()
    project = application.create_project("旧名称")
    at = AppTest.from_file(APP)
    at.query_params["session"] = str(project.session_id)
    at.run()
    assert not at.exception
    pencil = next(
        b for b in at.button if b.key == f"cp-rename-btn-{project.session_id}"
    )
    assert pencil.label == RENAME_ICON
    at = pencil.click().run()
    assert not at.exception
    rename_input = next(
        item for item in at.text_input if item.key == f"cp-rename-input-{project.session_id}"
    )
    rename_input.set_value("春季达人活动")
    confirm = next(
        b for b in at.button if b.key == f"cp-rename-confirm-{project.session_id}"
    )
    assert confirm.label == CONFIRM_RENAME
    at = confirm.click().run()
    assert not at.exception
    titles = [p.title for p in create_application().list_projects()]
    assert "春季达人活动" in titles
    assert any("春季达人活动" in (b.label or "") for b in at.button)


def test_new_project_and_switch_keeps_chats_separate() -> None:
    application = create_application()
    first = asyncio.run(application.chat("项目甲目标"))
    second = application.create_project()
    asyncio.run(application.chat("项目乙目标", session_id=second.session_id))

    at = AppTest.from_file(APP)
    at.query_params["session"] = str(first.session_id)
    at.run()
    assert not at.exception
    texts = [m.markdown[0].value for m in at.chat_message if m.markdown]
    assert "项目甲目标" in texts
    assert "项目乙目标" not in texts

    switch = next(
        button
        for button in at.button
        if button.key == f"cp-project-{second.session_id}"
    )
    switch.click().run()
    assert session_param(at) == str(second.session_id)
    texts = [m.markdown[0].value for m in at.chat_message if m.markdown]
    assert "项目乙目标" in texts
    assert "项目甲目标" not in texts


def test_delete_user_message_keeps_assistant() -> None:
    application = create_application()
    result = asyncio.run(application.chat("现在几点？"))
    entries = application.history_entries(result.session_id)
    assert any(e.message.role == "tool" for e in entries)
    user = next(e for e in entries if e.message.role == "user")
    assistant = next(e for e in entries if e.message.role == "assistant")

    at = AppTest.from_file(APP)
    at.query_params["session"] = str(result.session_id)
    at.run()
    assert [m.name for m in at.chat_message] == ["user", "assistant"]
    assert any('class="cp-tool-line' in item.value for item in at.markdown)
    assert any("调用完成" in item.value for item in at.markdown if isinstance(item.value, str))
    assert any(
        "cp-tool-line-succeeded" in item.value
        for item in at.markdown
        if isinstance(item.value, str)
    )

    delete_buttons = [b for b in at.button if b.label == DELETE_MESSAGE]
    assert len(delete_buttons) == 2
    next(b for b in delete_buttons if b.key == f"cp-del-msg-{user.id}").click().run()
    assert not at.exception
    assert [m.name for m in at.chat_message] == ["assistant"]
    remaining = application.history_entries(result.session_id)
    assert all(e.id != user.id for e in remaining)
    assert any(e.id == assistant.id for e in remaining)


def test_delete_assistant_message_keeps_user() -> None:
    application = create_application()
    result = asyncio.run(application.chat("现在几点？"))
    entries = application.history_entries(result.session_id)
    assistant = next(e for e in entries if e.message.role == "assistant")

    at = AppTest.from_file(APP)
    at.query_params["session"] = str(result.session_id)
    at.run()
    next(
        b for b in at.button if b.key == f"cp-del-msg-{assistant.id}"
    ).click().run()
    assert not at.exception
    assert [m.name for m in at.chat_message] == ["user"]
    remaining = application.history_entries(result.session_id)
    assert all(e.id != assistant.id for e in remaining)
    assert all(e.message.role != "tool" for e in remaining)
    assert any(e.message.role == "user" for e in remaining)


def test_delete_project_clears_campaign_and_switches() -> None:
    application = create_application()
    first = asyncio.run(application.chat("要删的项目"))
    application.save_campaign(application.campaign(first.session_id))
    other = application.create_project()
    asyncio.run(application.chat("保留的项目", session_id=other.session_id))

    at = AppTest.from_file(APP)
    at.query_params["session"] = str(first.session_id)
    at.run()
    delete = next(
        button
        for button in at.button
        if button.key == f"cp-del-project-{first.session_id}"
    )
    assert delete.label == DELETE_ICON
    delete.click().run()
    assert session_param(at) == str(other.session_id)
    assert application.store.get_project(first.session_id) is None
    texts = [m.markdown[0].value for m in at.chat_message if m.markdown]
    assert "保留的项目" in texts


def test_new_project_button_creates_empty_session() -> None:
    at = AppTest.from_file(APP).run()
    create = next(button for button in at.button if button.label == NEW_PROJECT)
    create.click().run()
    assert at.query_params["session"]
    assert at.chat_message == []
    projects = create_application().list_projects()
    assert len(projects) == 1
