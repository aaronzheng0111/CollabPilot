"""T10 verify cases 1–9. Mock provider for generation; no DeepSeek."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from collabpilot.campaign import mock_store
from collabpilot.campaign.channels import CHANNEL_LABELS, pick_channel
from collabpilot.campaign.drafts import (
    BODIES_NOT_UNIQUE,
    CHANNEL_MISMATCH,
    CITED_POST_INVALID,
    NEED_SELECTION,
    QUOTE_NOT_FOUND,
    apply_save_drafts,
    draft_prerequisites,
    queue_save_drafts,
    resolve_channels,
    validate_drafts,
)
from collabpilot.campaign.goal import Campaign
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.approve_draft import ApproveDraftTool
from collabpilot.tools.builtin.save_drafts import SaveDraftsTool


SRC = Path(__file__).resolve().parents[2] / "src" / "collabpilot"
IDS = ["creator_001", "creator_002", "creator_003"]
CHANNELS = {
    "creator_001": "tiktok_dm",
    "creator_002": "instagram_dm",
    "creator_003": "email",
}


def selected_campaign(**updates) -> Campaign:
    payload = {
        "campaign_id": uuid4(),
        "stage": "SELECTED",
        "saved_creator_ids": list(IDS),
        "confirmed_channels": dict(CHANNELS),
    }
    payload.update(updates)
    return Campaign(**payload)


def valid_raw(creator_ids: list[str] | None = None) -> list[dict]:
    creators = mock_store.load()
    targets = creator_ids or IDS
    channels = resolve_channels(targets, creators)
    drafts = []
    for creator_id in targets:
        channel = channels[creator_id] or CHANNELS.get(creator_id, "tiktok_dm")
        post = creators[creator_id].posts()[0]
        snippet = mock_store.post_text(post)[:12]
        label = CHANNEL_LABELS[channel]
        drafts.append(
            {
                "creator_id": creator_id,
                "body": f"专属邀请 {creator_id}：你写的「{snippet}」很具体，将通过{label}联系。",
                "cited_post_id": post["post_id"],
                "channel": channel,
            }
        )
    return drafts


class CountingProvider:
    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    async def complete(self, *args, **kwargs):
        self.calls += 1
        return await self.inner.complete(*args, **kwargs)


def test_empty_selection_is_need_selection() -> None:
    campaign = selected_campaign(saved_creator_ids=[])
    assert draft_prerequisites(campaign, []) == NEED_SELECTION


async def test_empty_selection_does_not_call_model(application) -> None:
    campaign = selected_campaign(saved_creator_ids=[])
    application.save_campaign(campaign)
    spy = CountingProvider(application.providers.get("mock"))
    batch = await application.generate_drafts(
        campaign, spy, "deepseek-chat", creator_ids=[]
    )
    assert batch.error_code == NEED_SELECTION
    assert batch.model_called is False
    assert spy.calls == 0


async def test_auto_channel_without_confirm_calls_model(application) -> None:
    campaign = selected_campaign(confirmed_channels={})
    spy = CountingProvider(application.providers.get("mock"))
    batch = await application.generate_drafts(
        campaign, spy, "deepseek-chat", creator_ids=IDS
    )
    assert batch.ok, batch.error_code
    assert batch.model_called is True
    assert spy.calls >= 1
    for item in batch.accepted:
        assert item.channel == pick_channel(mock_store.load()[item.creator_id])


async def test_chat_generate_drafts_asks_for_table_click_and_does_not_batch(
    application,
) -> None:
    session_id = application.store.ensure_session(None)
    application.save_campaign(selected_campaign(campaign_id=session_id))

    result = await application.chat(
        "生成草稿",
        session_id=session_id,
        provider_name="mock",
        creator_ids=IDS,
    )
    stored = application.campaign(session_id)
    assert stored.drafts == []
    assert "请在表里选合适达人后点「生成草稿」" in result.content

    explained = await application.chat(
        "生成草稿", session_id=session_id, provider_name="mock", creator_ids=[]
    )
    assert "请在表里选合适达人后点「生成草稿」" in explained.content
    assert application.campaign(session_id).drafts == []


async def test_generate_one_creator_saves_single_draft(application) -> None:
    session_id = application.store.ensure_session(None)
    application.save_campaign(selected_campaign(campaign_id=session_id))
    updated, batch = await application.generate_and_queue_drafts(
        session_id, provider_name="mock", creator_ids=["creator_001"]
    )
    assert batch.ok, batch.error_code
    assert len(batch.accepted) == 1
    saved = application.approve_pending(session_id, "save_drafts", True)
    assert len(saved.campaign.drafts) == 1
    assert saved.campaign.drafts[0]["creator_id"] == "creator_001"


def test_bodies_and_cited_posts_must_be_unique() -> None:
    campaign = selected_campaign()
    creators = mock_store.load()
    raw = valid_raw()
    raw[2]["body"] = raw[0]["body"]
    assert (
        validate_drafts(
            {"drafts": raw},
            campaign,
            creators,
            model_name="deepseek-chat",
            creator_ids=IDS,
        ).error_code
        == BODIES_NOT_UNIQUE
    )
    raw = valid_raw()
    raw[2]["cited_post_id"] = raw[0]["cited_post_id"]
    batch = validate_drafts(
        {"drafts": raw},
        campaign,
        creators,
        model_name="deepseek-chat",
        creator_ids=IDS,
    )
    assert batch.error_code in ("posts_not_unique", CITED_POST_INVALID)


def test_cited_post_not_on_creator_drops_batch() -> None:
    campaign = selected_campaign()
    raw = valid_raw()
    raw[0]["cited_post_id"] = "tt_video_002_2"
    batch = validate_drafts(
        {"drafts": raw},
        campaign,
        mock_store.load(),
        model_name="deepseek-chat",
        creator_ids=IDS,
    )
    assert batch.error_code == CITED_POST_INVALID
    assert batch.accepted == []


def test_channel_mismatch_and_labels() -> None:
    campaign = selected_campaign()
    creators = mock_store.load()
    raw = valid_raw()
    for item in raw:
        assert CHANNEL_LABELS[item["channel"]] in item["body"]
    raw[0]["channel"] = "email"
    batch = validate_drafts(
        {"drafts": raw},
        campaign,
        creators,
        model_name="deepseek-chat",
        creator_ids=IDS,
    )
    assert batch.error_code == CHANNEL_MISMATCH


def test_quote_not_found_drops_batch() -> None:
    campaign = selected_campaign()
    raw = valid_raw()
    label = CHANNEL_LABELS[raw[1]["channel"]]
    raw[1]["body"] = f"这封只有渠道名 {label}，没有引用帖子原文。"
    batch = validate_drafts(
        {"drafts": raw},
        campaign,
        mock_store.load(),
        model_name="deepseek-chat",
        creator_ids=IDS,
    )
    assert batch.error_code == QUOTE_NOT_FOUND


async def test_unapproved_save_is_rejected(application) -> None:
    campaign = selected_campaign()
    application.save_campaign(campaign)
    mock = application.providers.get("mock")
    batch = await application.generate_drafts(
        campaign, mock, "deepseek-chat", creator_ids=IDS
    )
    assert batch.ok, batch.error_code
    queued = queue_save_drafts(campaign, batch.accepted)
    application.save_campaign(queued)
    tool = SaveDraftsTool(application.campaigns)
    result = await tool.execute(
        {},
        ToolContext(session_id=campaign.campaign_id, turn_id=uuid4()),
    )
    assert result.error_code == "approval_required"
    stored = application.campaign(campaign.campaign_id)
    assert stored.drafts == []
    assert stored.stage == "DRAFTING"


async def test_approved_save_writes_three_pending_review_and_has_no_send(
    application,
) -> None:
    campaign = selected_campaign()
    application.save_campaign(campaign)
    mock = application.providers.get("mock")
    batch = await application.generate_drafts(
        campaign, mock, "deepseek-chat", creator_ids=IDS
    )
    assert batch.ok, batch.error_code
    bodies = [item.body for item in batch.accepted]
    posts = [item.cited_post_id for item in batch.accepted]
    assert len(set(bodies)) == 3
    assert len(set(posts)) == 3
    creators = mock_store.load()
    for item in batch.accepted:
        assert item.cited_post_id in creators[item.creator_id].post_ids()
        assert CHANNEL_LABELS[item.channel] in item.body
        assert item.channel == pick_channel(creators[item.creator_id])
        assert item.data_origin == "real_model_output"
        assert item.model_name == "deepseek-chat"
        assert item.status == "pending_review"
    queued = queue_save_drafts(campaign, batch.accepted)
    application.save_campaign(queued)
    tool = SaveDraftsTool(application.campaigns)
    result = await tool.execute(
        {},
        ToolContext(
            session_id=campaign.campaign_id, turn_id=uuid4(), user_approved=True
        ),
    )
    assert result.ok
    stored = application.campaign(campaign.campaign_id)
    assert stored.stage == "DRAFT_REVIEW"
    assert len(stored.drafts) == 3
    assert {item["status"] for item in stored.drafts} == {"pending_review"}
    reopened = application.campaign(campaign.campaign_id)
    assert len(reopened.drafts) == 3
    blob = (SRC / "campaign" / "drafts.py").read_text(encoding="utf-8")
    blob += (SRC / "tools" / "builtin" / "save_drafts.py").read_text(encoding="utf-8")
    blob += (SRC / "tools" / "builtin" / "approve_draft.py").read_text(encoding="utf-8")
    lowered = blob.lower()
    assert "smtp" not in lowered
    assert "send_mail" not in lowered
    assert "send_message" not in lowered
    assert "SENDING" not in (SRC / "campaign" / "goal.py").read_text(encoding="utf-8")


async def test_approve_draft_changes_status_only(application) -> None:
    campaign = selected_campaign()
    application.save_campaign(campaign)
    batch = await application.generate_drafts(
        campaign, application.providers.get("mock"), "deepseek-chat", creator_ids=IDS
    )
    queued = queue_save_drafts(campaign, batch.accepted)
    saved, _ = apply_save_drafts(queued, batch.accepted)
    application.save_campaign(saved)
    draft_id = saved.drafts[0]["id"]
    tool = ApproveDraftTool(application.campaigns)
    denied = await tool.execute(
        {"draft_id": draft_id},
        ToolContext(session_id=saved.campaign_id, turn_id=uuid4()),
    )
    assert denied.error_code == "approval_required"
    assert application.campaign(saved.campaign_id).drafts[0]["status"] == "pending_review"
    ok = await tool.execute(
        {"draft_id": draft_id},
        ToolContext(session_id=saved.campaign_id, turn_id=uuid4(), user_approved=True),
    )
    assert ok.ok
    stored = application.campaign(saved.campaign_id)
    assert stored.drafts[0]["status"] == "approved"
    assert stored.stage == "DRAFT_REVIEW"
