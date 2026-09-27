"""T14 verify cases 1–6. Mock provider for generation; no DeepSeek."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from collabpilot.campaign.channels import CHANNEL_LABELS
from collabpilot.campaign.drafts import Draft
from collabpilot.campaign.follow_up import (
    CHANNEL_MISMATCH,
    DRAFT_NOT_APPROVED,
    apply_save_follow_up,
    follow_up_prerequisites,
    queue_save_follow_up,
    validate_follow_up,
)
from collabpilot.campaign.goal import Campaign
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.save_follow_up import NoteFollowUpTool, SaveFollowUpTool


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
        "stage": "DRAFT_REVIEW",
        "saved_creator_ids": list(IDS),
        "confirmed_channels": dict(CHANNELS),
    }
    payload.update(updates)
    return Campaign(**payload)


def approved_draft(campaign: Campaign, creator_id: str = "creator_003") -> Draft:
    return Draft(
        id=f"draft-{creator_id}",
        campaign_id=str(campaign.campaign_id),
        creator_id=creator_id,
        body=f"邀请 {creator_id}，将通过{CHANNEL_LABELS[CHANNELS[creator_id]]}联系。原文片段补齐。",
        cited_post_id="tt_video_003_1",
        channel=CHANNELS[creator_id],  # type: ignore[arg-type]
        status="approved",
        model_name="deepseek-chat",
    )


def with_approved_draft(campaign: Campaign, creator_id: str = "creator_003") -> Campaign:
    draft = approved_draft(campaign, creator_id)
    return campaign.model_copy(update={"drafts": [draft.model_dump(mode="json")]})


class CountingProvider:
    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    async def complete(self, *args, **kwargs):
        self.calls += 1
        return await self.inner.complete(*args, **kwargs)


def test_unapproved_draft_is_draft_not_approved() -> None:
    campaign = selected_campaign()
    draft = approved_draft(campaign).model_copy(update={"status": "pending_review"})
    campaign = campaign.model_copy(update={"drafts": [draft.model_dump(mode="json")]})
    draft_id = draft.id
    assert follow_up_prerequisites(campaign, draft_id) == DRAFT_NOT_APPROVED
    batch = validate_follow_up(
        {
            "creator_id": "creator_003",
            "draft_id": draft_id,
            "channel": "email",
            "next_step": "三天后发邮件再问一次",
        },
        campaign,
        draft_id=draft_id,
        model_name="deepseek-chat",
    )
    assert batch.error_code == DRAFT_NOT_APPROVED
    assert batch.accepted is None


async def test_unapproved_draft_does_not_call_model(application) -> None:
    campaign = with_approved_draft(selected_campaign())
    campaign.drafts[0]["status"] = "pending_review"
    spy = CountingProvider(application.providers.get("mock"))
    batch = await application.generate_follow_up(
        campaign, spy, "deepseek-chat", campaign.drafts[0]["id"]
    )
    assert batch.error_code == DRAFT_NOT_APPROVED
    assert batch.model_called is False
    assert spy.calls == 0


def test_channel_mismatch_is_not_saved() -> None:
    campaign = with_approved_draft(selected_campaign(), "creator_003")
    draft_id = campaign.drafts[0]["id"]
    assert campaign.confirmed_channels["creator_003"] == "email"
    batch = validate_follow_up(
        {
            "creator_id": "creator_003",
            "draft_id": draft_id,
            "channel": "tiktok_dm",
            "next_step": "改用 TikTok 私信跟进",
        },
        campaign,
        draft_id=draft_id,
        model_name="deepseek-chat",
    )
    assert batch.error_code == CHANNEL_MISMATCH
    assert batch.accepted is None


async def test_approved_save_writes_waiting_user_and_origin(application) -> None:
    campaign = with_approved_draft(selected_campaign())
    application.save_campaign(campaign)
    mock = application.providers.get("mock")
    batch = await application.generate_follow_up(
        campaign, mock, "deepseek-chat", campaign.drafts[0]["id"]
    )
    assert batch.ok, batch.error_code
    assert batch.accepted is not None
    assert batch.accepted.follow_status == "waiting_user"
    assert batch.accepted.data_origin == "real_model_output"
    assert batch.accepted.model_name == "deepseek-chat"
    assert batch.accepted.next_step
    assert batch.accepted.channel == "email"
    queued = queue_save_follow_up(campaign, batch.accepted)
    application.save_campaign(queued)
    tool = SaveFollowUpTool(application.campaigns)
    result = await tool.execute(
        {},
        ToolContext(
            session_id=campaign.campaign_id, turn_id=uuid4(), user_approved=True
        ),
    )
    assert result.ok
    stored = application.campaign(campaign.campaign_id)
    assert stored.stage == "FOLLOW_UP"
    assert len(stored.follow_ups) == 1
    assert stored.follow_ups[0]["follow_status"] == "waiting_user"
    assert stored.follow_ups[0]["data_origin"] == "real_model_output"
    assert stored.follow_ups[0]["model_name"] == "deepseek-chat"
    reopened = application.campaign(campaign.campaign_id)
    assert len(reopened.follow_ups) == 1


async def test_unapproved_save_is_approval_required(application) -> None:
    campaign = with_approved_draft(selected_campaign())
    application.save_campaign(campaign)
    mock = application.providers.get("mock")
    batch = await application.generate_follow_up(
        campaign, mock, "deepseek-chat", campaign.drafts[0]["id"]
    )
    assert batch.ok, batch.error_code
    queued = queue_save_follow_up(campaign, batch.accepted)
    application.save_campaign(queued)
    tool = SaveFollowUpTool(application.campaigns)
    result = await tool.execute(
        {},
        ToolContext(session_id=campaign.campaign_id, turn_id=uuid4()),
    )
    assert result.error_code == "approval_required"
    stored = application.campaign(campaign.campaign_id)
    assert stored.follow_ups == []
    assert stored.stage == "FOLLOW_UP"


async def test_note_changes_status_and_has_no_send(application) -> None:
    campaign = with_approved_draft(selected_campaign())
    application.save_campaign(campaign)
    batch = await application.generate_follow_up(
        campaign,
        application.providers.get("mock"),
        "deepseek-chat",
        campaign.drafts[0]["id"],
    )
    queued = queue_save_follow_up(campaign, batch.accepted)
    saved, _ = apply_save_follow_up(queued, batch.accepted)
    application.save_campaign(saved)
    follow_id = saved.follow_ups[0]["id"]
    tool = NoteFollowUpTool(application.campaigns)
    denied = await tool.execute(
        {"follow_up_id": follow_id},
        ToolContext(session_id=saved.campaign_id, turn_id=uuid4()),
    )
    assert denied.error_code == "approval_required"
    assert application.campaign(saved.campaign_id).follow_ups[0]["follow_status"] == (
        "waiting_user"
    )
    ok = await tool.execute(
        {"follow_up_id": follow_id},
        ToolContext(session_id=saved.campaign_id, turn_id=uuid4(), user_approved=True),
    )
    assert ok.ok
    stored = application.campaign(saved.campaign_id)
    assert stored.follow_ups[0]["follow_status"] == "noted"
    blob = (SRC / "campaign" / "follow_up.py").read_text(encoding="utf-8")
    blob += (SRC / "tools" / "builtin" / "save_follow_up.py").read_text(encoding="utf-8")
    lowered = blob.lower()
    assert "smtp" not in lowered
    assert "send_mail" not in lowered
    assert "send_message" not in lowered
    assert "tiktok.com" not in lowered
    assert "instagram.com" not in lowered
    assert "SENDING" not in (SRC / "campaign" / "goal.py").read_text(encoding="utf-8")
