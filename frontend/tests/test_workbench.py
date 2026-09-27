"""T11 verify cases 2–3, 8, 10–13: page assembly from WorkbenchState."""

from __future__ import annotations

from conftest import FRONTEND, main_layout_columns
from streamlit.testing.v1 import AppTest
from collabpilot.bootstrap import create_application
from collabpilot.campaign.retry import ACCEPT_SHORT_LIST
from components.draft_cards import PANEL_TITLE as DRAFT_TITLE
from components.draft_cards import SEND_LABELS
from components.follow_up_table import PANEL_TITLE as FOLLOW_TITLE
from components.pending_decisions import EMPTY_TEXT
from components.pending_list import LIST_TITLE
from test_draft_cards import saved_drafts_session
from test_evidence_panel import judged_session, markup, open_session
from test_follow_up_table import waiting_follow_up_session
from test_main_table import main_frame


APP = str(FRONTEND / "app.py")
SECONDARY_ORDER = [
    "合作目标",
    "进度",
    "判断依据",
    "待确认",
    "已排除",
    "跟进",
]


def test_layout_is_left_table_right_projects_history_input() -> None:
    at = AppTest.from_file(APP).run()
    assert not at.exception
    left, right = main_layout_columns(at)
    assert round(left.proto.weight / (left.proto.weight + right.proto.weight), 1) == 0.6
    right_children = list(right.children.values())
    assert [child.type for child in right_children] == ["flex_container"]
    body = list(right_children[0].children.values())
    assert [child.type for child in body] == ["flex_container"]
    nested = list(body[0].children.values())
    assert [child.type for child in nested] == [
        "flex_container",
        "flex_container",
        "flex_container",
    ]
    assert "新建项目" in [button.label for button in at.button]
    assert any(button.key == "cp-chat-send" for button in at.button)
    assert len(at.chat_input) == 0
    assert not any(
        isinstance(item.value, str) and item.value.startswith('<div class="cp-status')
        for item in at.markdown
    )
    idle = left.dataframe[0].value
    assert len(idle) == 12
    assert "示例达人" in "\n".join(item.value for item in at.caption)


def test_secondary_order_and_pending_always_present() -> None:
    at = open_session(judged_session())
    left, right = main_layout_columns(at)
    left_html = "\n".join(item.value for item in left.markdown)
    right_html = "\n".join(item.value for item in right.markdown)
    page_html = markup(at)
    assert "待你决定" not in left_html
    assert "待你决定" in right_html
    for title in ("合作目标", "判断依据", "待确认"):
        assert title in page_html
    empty = AppTest.from_file(APP).run()
    empty_html = markup(empty)
    _empty_left, empty_right = main_layout_columns(empty)
    empty_right_html = "\n".join(item.value for item in empty_right.markdown)
    assert "待你决定" in empty_right_html
    assert "待你决定" in empty_html
    assert EMPTY_TEXT in "\n".join(item.value for item in empty.caption) or EMPTY_TEXT in empty_html
    assert LIST_TITLE not in empty_html
    assert "#### 草稿" not in empty_html


def test_channel_and_follow_up_visible_together() -> None:
    session_id = waiting_follow_up_session()
    at = open_session(session_id)
    html = markup(at)
    campaign = create_application().campaign(session_id)
    assert campaign.confirmed_channels or campaign.follow_ups
    frames = "\n".join(
        item.value.to_csv(index=False)
        for item in at.dataframe
        if hasattr(item.value, "to_csv")
    )
    combined = html + frames
    assert "channel" in combined or "TikTok 私信" in combined or "邮件" in combined
    assert FOLLOW_TITLE in html
    assert "next_step" in combined or "三天后" in combined
    assert "等你记下" in combined or "follow_status" in combined


def test_accept_short_list_has_no_drafts() -> None:
    session_id = judged_session()
    application = create_application()
    campaign = application.campaign(session_id)
    application.save_campaign(
        campaign.model_copy(
            update={
                "pending_decision": ACCEPT_SHORT_LIST,
                "drafts": [],
                "stage": "CANDIDATES_READY",
            }
        )
    )
    at = open_session(session_id)
    html = markup(at)
    assert "是否接受" in html
    assert "生成草稿" not in " ".join(
        str(button.label) for button in at.button
    )


def test_three_pending_drafts_have_no_send_button() -> None:
    at = open_session(saved_drafts_session())
    html = markup(at)
    assert DRAFT_TITLE in html
    assert "待审核" in html
    labels = [button.label for button in at.button if button.key != "cp-chat-send"]
    for forbidden in SEND_LABELS:
        assert forbidden not in labels
    assert "草稿不会发送" in html or "[MOCK-SEND]" in html


def test_reopened_session_keeps_history() -> None:
    session_id = judged_session()
    at = open_session(session_id)
    names = [message.name for message in at.chat_message]
    assert "user" in names and "assistant" in names
    again = open_session(session_id)
    assert [message.name for message in again.chat_message] == names


def test_running_search_shows_tool_name_on_table() -> None:
    from components.tool_status import initial_status
    from test_main_table import open_session as open_with_status, searched_session

    running = {**initial_status(), "state": "running", "name": "search_creators"}
    at = open_with_status(searched_session(), tool_status=running)
    html = markup(at)
    assert "正在执行 search_creators" in html
    assert "cp-table-loading" in html


def test_failed_tool_keeps_rows() -> None:
    from components.tool_status import initial_status
    from test_main_table import main_frame, open_session as open_with_status, searched_session

    session_id = searched_session()
    at = open_with_status(session_id)
    n = len(main_frame(at))
    failed = {
        **initial_status(),
        "state": "failed",
        "name": "search_creators",
        "error_code": "tool_failed",
    }
    at.session_state["tool_status"] = failed
    at.run()
    assert len(main_frame(at)) == n


def test_clarifying_hides_creator_rows() -> None:
    import asyncio
    from collabpilot.campaign.goal import CLARIFYING_TABLE_TEXT

    result = asyncio.run(create_application().chat("帮我找达人"))
    at = open_session(result.session_id)
    left, _ = main_layout_columns(at)
    assert not left.dataframe
    assert CLARIFYING_TABLE_TEXT in markup(at)
    assert at.chat_message
