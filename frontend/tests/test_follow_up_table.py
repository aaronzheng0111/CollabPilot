"""T14 verify cases 7–9. Fixture follow-ups; generate uses mock provider."""

from __future__ import annotations

import asyncio

from collabpilot.bootstrap import create_application
from collabpilot.campaign.follow_up import (
    FollowUp,
    apply_save_follow_up,
    queue_save_follow_up,
)
from collabpilot.campaign.workbench import follow_up_rows
from components.follow_up_table import PANEL_TITLE, SEND_LABELS
from test_draft_cards import saved_drafts_session
from test_evidence_panel import markup, open_session


MODEL = "deepseek-chat"


def _frames(at) -> str:
    parts: list[str] = []
    for item in at.dataframe:
        value = item.value
        if hasattr(value, "to_csv"):
            parts.append(value.to_csv(index=False))
        else:
            parts.append(str(value))
    return "\n".join(parts)


def waiting_follow_up_session():
    session_id = saved_drafts_session()
    application = create_application()
    campaign = application.campaign(session_id)
    drafts = [{**item, "status": "approved"} for item in campaign.drafts]
    approved = campaign.model_copy(update={"drafts": drafts, "pending_decision": None})
    draft = drafts[0]
    follow = FollowUp(
        id="follow-001",
        campaign_id=str(approved.campaign_id),
        creator_id=draft["creator_id"],
        draft_id=draft["id"],
        channel=draft["channel"],
        next_step="三天后通过 TikTok 私信再问一次是否看到邀请。",
        follow_status="waiting_user",
        model_name=MODEL,
    )
    saved, _ = apply_save_follow_up(
        queue_save_follow_up(approved, follow), follow
    )
    application.save_campaign(
        saved.model_copy(update={"pending_decision": None, "pending_payload": None})
    )
    return session_id


def test_follow_up_table_shows_creator_channel_step_status_and_llm() -> None:
    session_id = waiting_follow_up_session()
    at = open_session(session_id)
    html = markup(at)
    assert PANEL_TITLE in html
    assert "[LLM]" in html
    assert MODEL in html
    rows = follow_up_rows(create_application().campaign(session_id))
    assert rows
    assert rows[0]["display_name"]
    assert rows[0]["channel_label"]
    assert "三天后" in rows[0]["next_step"]
    assert rows[0]["status_label"] == "等你记下"
    combined = html + _frames(at)
    assert rows[0]["display_name"] in combined
    assert rows[0]["channel_label"] in combined
    assert "等你记下" in combined


def test_pending_record_follow_up_then_table_waiting_user() -> None:
    session_id = saved_drafts_session()
    application = create_application()
    campaign = application.campaign(session_id)
    draft_id = campaign.drafts[0]["id"]
    asyncio.run(application.review_draft_and_follow_up(session_id, draft_id, True))
    at = open_session(session_id)
    body = markup(at)
    assert "记录对" in body and "的跟进" in body
    approve = next(button for button in at.button if button.label == "批准")
    approve.click().run()
    assert not at.exception
    stored = create_application().campaign(session_id)
    assert stored.follow_ups
    assert stored.follow_ups[0]["follow_status"] == "waiting_user"
    combined = markup(at) + _frames(at)
    assert "等你记下" in combined


def test_note_follow_up_shows_noted_and_has_no_send_buttons() -> None:
    session_id = waiting_follow_up_session()
    at = open_session(session_id)
    labels = [button.label for button in at.button if button.key != "cp-chat-send"]
    for forbidden in SEND_LABELS:
        assert forbidden not in labels
    assert "记下对" in markup(at)
    approve = next(button for button in at.button if button.label == "批准")
    approve.click().run()
    assert not at.exception
    stored = create_application().campaign(session_id)
    assert stored.follow_ups[0]["follow_status"] == "noted"
    combined = markup(at) + _frames(at)
    assert "已记下" in combined
    labels = [button.label for button in at.button if button.key != "cp-chat-send"]
    for forbidden in SEND_LABELS:
        assert forbidden not in labels
