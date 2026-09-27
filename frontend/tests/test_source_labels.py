"""T12 verify cases 2–7: source labels on rows/cards, no API key in the UI."""

from __future__ import annotations

from collabpilot.bootstrap import create_application
from components.source_badge import LEGEND_ITEMS, LLM, MOCK, MOCK_SEND, RULE, legend_html
from test_draft_cards import saved_drafts_session
from test_evidence_panel import judged_session, markup, open_session
from test_follow_up_table import waiting_follow_up_session
from streamlit.testing.v1 import AppTest
from conftest import FRONTEND


APP = str(FRONTEND / "app.py")
KEY_MARKERS = ("sk-", "DEEPSEEK_API_KEY=")


def test_legend_strip_is_not_on_empty_page() -> None:
    """Top explanatory legend removed; helper still documents the four labels."""
    at = AppTest.from_file(APP).run()
    html = markup(at)
    assert "cp-legend" not in html
    assert "模拟数据" not in html
    assert "应用层规则" not in html
    assert "DeepSeek 实时输出" not in html
    helper = legend_html()
    assert "cp-legend" in helper
    for label, meaning, _css in LEGEND_ITEMS:
        assert label in helper
        assert meaning in helper


def test_creator_rows_are_tagged_mock() -> None:
    session_id = judged_session()
    at = open_session(session_id)
    from collabpilot.campaign.workbench import main_table_rows

    rows = main_table_rows(create_application().campaign(session_id))
    assert rows
    assert all(MOCK in row.get("source", "") for row in rows)
    html = markup(at)
    assert MOCK in html or MOCK in str(rows[0]["source"])


def test_llm_on_verdict_strategy_drafts_and_follow_up() -> None:
    session_id = waiting_follow_up_session()
    at = open_session(session_id)
    html = markup(at)
    campaign = create_application().campaign(session_id)
    assert campaign.verdicts
    assert all(item.data_origin == "real_model_output" for item in campaign.verdicts)
    assert campaign.drafts
    assert all(item.get("data_origin") == "real_model_output" for item in campaign.drafts)
    assert campaign.follow_ups
    assert LLM in html
    assert "deepseek-chat" in html
    assert MOCK_SEND in html
    assert "不会发送" in html or "草稿不会发送" in html


def test_rule_on_excluded_lock_and_audience() -> None:
    session_id = judged_session()
    at = open_session(session_id)
    html = markup(at)
    from collabpilot.campaign.workbench import excluded_rows, main_table_rows

    campaign = create_application().campaign(session_id)
    excluded = excluded_rows(campaign)
    assert excluded
    assert all(RULE in row["source"] for row in excluded)
    rows = main_table_rows(campaign)
    audience_unknown = [row for row in rows if row.get("audience") == "受众未知"]
    assert audience_unknown
    assert any(RULE in row.get("source", "") for row in audience_unknown)
    locked = [row for row in rows if "不符" in str(row.get("topic", ""))]
    assert locked
    assert RULE in html


def test_drafts_state_will_not_send() -> None:
    at = open_session(saved_drafts_session())
    html = markup(at)
    assert MOCK_SEND in html
    assert "不会发送" in html or "草稿不会发送" in html
    assert "发送" not in [
        button.label for button in at.button if button.key != "cp-chat-send"
    ]


def test_ui_does_not_contain_api_key() -> None:
    at = open_session(judged_session())
    html = markup(at)
    captions = "\n".join(item.value for item in at.caption)
    errors = "\n".join(item.value for item in at.error)
    blob = html + captions + errors
    for marker in KEY_MARKERS:
        assert marker not in blob
    app_src = (FRONTEND / "app.py").read_text(encoding="utf-8")
    assert "sk-" not in app_src
    assert "DEEPSEEK_API_KEY=" not in app_src
