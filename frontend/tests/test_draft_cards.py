"""T10 verify cases 11–13. Fixture drafts; generate uses mock provider."""

from __future__ import annotations

from collabpilot.bootstrap import create_application
from collabpilot.campaign import mock_store
from collabpilot.campaign.channels import CHANNEL_LABELS, pick_channel
from collabpilot.campaign.drafts import Draft, apply_save_drafts, queue_save_drafts
from components.draft_cards import (
    EMPTY_SELECTION,
    OPEN_KEY,
    PANEL_TITLE,
    REOPEN_BUTTON,
    SEND_LABELS,
    WILL_NOT_SEND,
)
from components.main_table import DRAFT_SELECT_KEY, GENERATE_BUTTON, GENERATE_KEY
from components.pending_decisions import EMPTY_TEXT, REJECT_DRAFT_BUTTON
from test_evidence_panel import judged_session, markup, open_session


IDS = ["creator_001", "creator_002", "creator_003"]
MODEL = "deepseek-chat"


def ready_session():
    session_id = judged_session()
    application = create_application()
    campaign = application.campaign(session_id)
    application.save_campaign(
        campaign.model_copy(
            update={
                "stage": "SELECTED",
                "saved_creator_ids": list(IDS),
                "confirmed_channels": {},
            }
        )
    )
    return session_id


def fixture_drafts(campaign) -> list[Draft]:
    creators = mock_store.load()
    drafts = []
    for creator_id in IDS:
        channel = pick_channel(creators[creator_id])
        post = creators[creator_id].posts()[0]
        snippet = mock_store.post_text(post)[:12]
        label = CHANNEL_LABELS[channel]
        drafts.append(
            Draft(
                id=f"draft-{creator_id}",
                campaign_id=str(campaign.campaign_id),
                creator_id=creator_id,
                body=f"专属邀请 {creator_id}：你写的「{snippet}」很具体，将通过{label}联系。",
                cited_post_id=post["post_id"],
                channel=channel,
                status="pending_review",
                model_name=MODEL,
            )
        )
    return drafts


def saved_drafts_session():
    session_id = ready_session()
    application = create_application()
    campaign = application.campaign(session_id)
    drafts = fixture_drafts(campaign)
    queued = queue_save_drafts(campaign, drafts)
    saved, _ = apply_save_drafts(queued, drafts)
    application.save_campaign(saved)
    return session_id


def _generate_button(at):
    return next(button for button in at.button if str(button.key) == GENERATE_KEY)


def _draft_select(at):
    return next(box for box in at.selectbox if str(box.key) == DRAFT_SELECT_KEY)


def test_draft_cards_show_creator_channel_quote_body_pending_and_llm() -> None:
    at = open_session(saved_drafts_session())
    html = markup(at)
    assert PANEL_TITLE in html
    assert "[LLM]" in html
    assert MODEL in html
    assert "Amy学翻译" in html
    assert "TikTok 私信" in html
    assert "待审核" in html
    excerpt = mock_store.post_text(mock_store.load()["creator_001"].posts()[0])[:12]
    assert excerpt in html or excerpt in "\n".join(item.value for item in at.markdown)


def test_generate_one_creator_persists_opens_dialog_and_review_row() -> None:
    session_id = ready_session()
    at = open_session(session_id)
    assert _draft_select(at)
    generate = _generate_button(at)
    assert generate.label == GENERATE_BUTTON
    generate.click().run()
    assert not at.exception
    campaign = create_application().campaign(session_id)
    assert campaign.pending_decision != "save_drafts"
    assert len(campaign.drafts) == 1
    assert at.session_state[OPEN_KEY] is True
    html = markup(at)
    assert "待审核" in html
    assert "审核草稿：" in html
    assert REOPEN_BUTTON in [button.label for button in at.button]
    assert REJECT_DRAFT_BUTTON in [button.label for button in at.button]
    assert WILL_NOT_SEND in html or WILL_NOT_SEND in "\n".join(
        item.value for item in at.caption
    )

    first_approve = next(button for button in at.button if button.label == "批准")
    first_approve.click().run()
    assert not at.exception
    reviewed = create_application().campaign(session_id)
    assert any(item["status"] == "approved" for item in reviewed.drafts)
    assert "已批准" in markup(at)


def test_reopen_drafts_dialog_after_close() -> None:
    session_id = saved_drafts_session()
    at = open_session(session_id)
    assert OPEN_KEY in at.session_state
    at.session_state[OPEN_KEY] = False
    at.run()
    assert "Amy学翻译" in markup(at)
    reopen = next(button for button in at.button if button.label == REOPEN_BUTTON)
    reopen.click().run()
    assert at.session_state[OPEN_KEY] is True
    assert "Amy学翻译" in markup(at)
    assert WILL_NOT_SEND in markup(at) or WILL_NOT_SEND in "\n".join(
        item.value for item in at.caption
    )


def test_generate_button_writes_only_that_creator() -> None:
    session_id = ready_session()
    at = open_session(session_id)
    select = _draft_select(at)
    label = select.value
    creators = mock_store.load()
    name_to_id = {creators[cid].display_name: cid for cid in creators}
    expected_id = name_to_id[label]
    _generate_button(at).click().run()
    assert not at.exception
    campaign = create_application().campaign(session_id)
    assert len(campaign.drafts) == 1
    assert campaign.drafts[0]["creator_id"] == expected_id
    assert EMPTY_SELECTION not in markup(at)


def test_second_generate_merges_without_wiping_first() -> None:
    session_id = ready_session()
    at = open_session(session_id)
    select = _draft_select(at)
    options = list(select.options)
    assert len(options) >= 2
    first_label, second_label = options[0], options[1]
    creators = mock_store.load()
    name_to_id = {creators[cid].display_name: cid for cid in creators}
    first_id = name_to_id[first_label]
    second_id = name_to_id[second_label]

    _generate_button(at).click().run()
    at = open_session(session_id)
    select = _draft_select(at)
    select.select(second_label).run()
    _generate_button(at).click().run()
    campaign = create_application().campaign(session_id)
    assert len(campaign.drafts) == 2
    assert {item["creator_id"] for item in campaign.drafts} == {first_id, second_id}


def test_draft_area_has_no_send_buttons_and_states_will_not_send() -> None:
    at = open_session(saved_drafts_session())
    labels = [button.label for button in at.button if button.key != "cp-chat-send"]
    for forbidden in SEND_LABELS:
        assert forbidden not in labels
    captions = "\n".join(item.value for item in at.caption)
    html = markup(at)
    assert WILL_NOT_SEND in captions or WILL_NOT_SEND in html
    assert "[MOCK-SEND]" in captions or "[MOCK-SEND]" in html
    assert EMPTY_TEXT not in captions


def test_empty_selection_explains_without_crash() -> None:
    session_id = ready_session()
    application = create_application()
    campaign = application.campaign(session_id)
    application.save_campaign(
        campaign.model_copy(
            update={
                "verdicts": [],
                "last_filter": None,
                "saved_creator_ids": list(IDS),
                "stage": "SELECTED",
            }
        )
    )
    at = open_session(session_id)
    assert EMPTY_SELECTION
    assert not at.exception
    # No 合适 rows → no per-creator draft stack / select control.
    assert not any(str(button.key) == GENERATE_KEY for button in at.button)


def test_no_long_per_name_generate_stack() -> None:
    at = open_session(ready_session())
    generate_labels = [
        str(button.label)
        for button in at.button
        if GENERATE_BUTTON in str(button.label)
    ]
    assert generate_labels == [GENERATE_BUTTON]
    captions = "\n".join(item.value for item in at.caption)
    assert "每位达人单独点" not in captions
