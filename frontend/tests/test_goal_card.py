"""T02 verify cases 11–13. Backend runs with the mock provider; no DeepSeek."""

from __future__ import annotations

import asyncio
import re
from uuid import UUID, uuid4

from conftest import FRONTEND, main_layout_columns
from streamlit.testing.v1 import AppTest

from collabpilot.bootstrap import create_application
from collabpilot.campaign.goal import (
    CLARIFYING_TABLE_TEXT,
    CONFIRM_ASSUMPTIONS,
    Campaign,
    ParsedGoal,
    validate_parsed_goal,
)
from components.pending_decisions import EMPTY_TEXT

APP = str(FRONTEND / "app.py")
SAMPLE_TEXT = (
    "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
    "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
    "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。"
)


def fixture_goal(**overrides) -> ParsedGoal:
    goal = validate_parsed_goal(
        {
            "brand": None,
            "product": "AI 翻译工具",
            "target_audience": ["中文用户"],
            "platforms": [],
            "target_count": 10,
            "inclusion_criteria": ["最近持续发布相关内容"],
            "exclusion_criteria": ["已经合作过的账号"],
            "outreach_count": 3,
            "needs_user_approval": True,
            **overrides,
        }
    )
    assert isinstance(goal, ParsedGoal)
    return goal


def goal_card_script(goal_json: str, model_name: str) -> None:
    import streamlit as st

    from collabpilot.campaign.goal import Campaign, ParsedGoal
    from components.goal_card import render_goal_card

    campaign = Campaign(
        campaign_id="00000000-0000-0000-0000-000000000001",
        goal_status="PARSED",
        parsed_goal=ParsedGoal.model_validate_json(goal_json),
        goal_origin="real_model_output",
        goal_model_name=model_name,
    )
    render_goal_card(campaign)
    st.write("done")


def open_session(session_id: UUID) -> AppTest:
    at = AppTest.from_file(APP)
    at.query_params["session"] = str(session_id)
    at.run()
    assert not at.exception
    return at


def markup(at: AppTest) -> str:
    return "\n".join(item.value for item in at.markdown)


def test_goal_card_lists_fields_with_assumption_pills_and_llm_tag() -> None:
    goal = fixture_goal()
    at = AppTest.from_function(
        goal_card_script, kwargs={"goal_json": goal.model_dump_json(), "model_name": "deepseek-chat"}
    ).run()

    assert not at.exception
    html = markup(at)
    assert "合作目标" in html
    for label in ["品牌", "受众", "平台", "人数", "触达人数", "筛选标准", "排除条件"]:
        assert label in html
    assert "LinguaGo AI 翻译" in html and "tiktok、instagram" in html
    assert html.count("cp-pill-assumed") == 2  # brand + platforms
    brand = next(item for item in goal.assumptions if item.field == "brand")
    assert brand.reason in html
    assert "[LLM]" in html and "deepseek-chat" in html


def test_goal_card_is_hidden_until_parsed() -> None:
    at = AppTest.from_file(APP).run()

    assert "合作目标" not in markup(at)
    assert EMPTY_TEXT in "\n".join(item.value for item in at.caption)


def test_clarifying_shows_fixed_text_and_numbered_questions() -> None:
    application = create_application()
    result = asyncio.run(application.chat("帮我找达人"))
    assert result.goal_status == "CLARIFYING"

    at = open_session(result.session_id)

    left, _right = main_layout_columns(at)
    assert not left.dataframe
    assert CLARIFYING_TABLE_TEXT in markup(at)
    assistant = at.chat_message[1]
    assert assistant.name == "assistant"
    reply = "\n".join(item.value for item in assistant.markdown)
    assert len(re.findall(r"^\d+[.、)]\s", reply, flags=re.MULTILINE)) >= 2


def test_parsed_session_shows_goal_card_and_table() -> None:
    application = create_application()
    result = asyncio.run(application.chat(SAMPLE_TEXT))
    assert result.goal_status == "PARSED"

    at = open_session(result.session_id)

    left, _right = main_layout_columns(at)
    assert len(left.dataframe[0].value) == 12
    html = markup(at)
    assert "合作目标" in html and "collabpilot-mock" in html and "假设" in html
    assert "示例达人" in "\n".join(item.value for item in at.caption)


def test_pending_decision_row_approves_and_disappears() -> None:
    application = create_application()
    session_id = application.store.create_session()
    application.save_campaign(
        Campaign(
            campaign_id=session_id,
            goal_status="CLARIFYING",
            parsed_goal=fixture_goal(target_count=None, outreach_count=None),
            goal_origin="real_model_output",
            goal_model_name="collabpilot-mock",
            grill_rounds=3,
            pending_decision=CONFIRM_ASSUMPTIONS,
        )
    )

    at = open_session(session_id)
    labels = [button.label for button in at.button]
    assert labels[:2] == ["批准", "拒绝"]
    assert at.button[0].proto.type == "primary"
    assert "确认以上假设" in "\n".join(item.value for item in at.markdown)

    at.button[0].click().run()

    assert not at.exception
    remaining = [button.label for button in at.button]
    assert "批准" not in remaining and "拒绝" not in remaining
    assert EMPTY_TEXT in "\n".join(item.value for item in at.caption)
    campaign = application.campaign(session_id)
    assert campaign.goal_status == "PARSED" and campaign.pending_decision is None
    assert "合作目标" in markup(at)


def test_reject_keeps_pending_row() -> None:
    application = create_application()
    session_id = application.store.create_session()
    application.save_campaign(
        Campaign(
            campaign_id=session_id,
            goal_status="CLARIFYING",
            grill_rounds=3,
            pending_decision=CONFIRM_ASSUMPTIONS,
        )
    )

    at = open_session(session_id)
    at.button[1].click().run()

    assert [button.label for button in at.button][:2] == ["批准", "拒绝"]
    assert application.campaign(session_id).pending_decision == CONFIRM_ASSUMPTIONS
    assert "未获批准" in "\n".join(item.value for item in at.info)


def test_unknown_session_renders_empty_shell() -> None:
    at = open_session(uuid4())
    assert EMPTY_TEXT in "\n".join(item.value for item in at.caption)
