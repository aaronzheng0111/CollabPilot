"""T13 verify cases 1–6. Mock contact only; no DeepSeek."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from collabpilot.campaign import mock_store
from collabpilot.campaign.channels import (
    CHANNEL_LABELS,
    CHANNEL_NOT_ON_PROFILE,
    CHANNEL_UNKNOWN,
    UNKNOWN,
    list_contacts,
    validate_channel,
)
from collabpilot.campaign.goal import Campaign
from collabpilot.campaign.mock_store import MergedCreator
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.confirm_channel import ConfirmChannelTool


SRC = Path(__file__).resolve().parents[2] / "src" / "collabpilot"


def unknown_creator() -> MergedCreator:
    return MergedCreator(
        creator_id="creator_ghost",
        display_name="无渠道",
        platforms=["tiktok"],
        tiktok={
            "contact": {
                "preferred_channel": "unknown",
                "dm_available": False,
                "email": None,
                "consent_status": "unknown",
            }
        },
    )


def test_list_contacts_matches_mock_preferred_and_is_mock() -> None:
    rows = [row for row in list_contacts(["creator_001"]) if row.platform == "tiktok"]
    assert len(rows) == 1
    view = rows[0]
    assert view.preferred_channel == "tiktok_dm"
    assert view.source == "[MOCK]"
    assert view.data_origin == "mock_seed"
    live = mock_store.load()["creator_001"].tiktok["contact"]
    assert live["preferred_channel"] == "tiktok_dm"


def test_unknown_consent_is_the_string_unknown() -> None:
    view = list_contacts(["creator_001"])[0]
    assert view.consent_status == "unknown"
    assert view.consent_label == UNKNOWN
    assert view.consent_label not in ("已同意", "已拒绝")


def test_unknown_channel_cannot_be_confirmed() -> None:
    creator = unknown_creator()
    rows = list_contacts(["creator_ghost"], {"creator_ghost": creator})
    assert rows[0].preferred_channel == "unknown"
    assert rows[0].email_display == UNKNOWN
    assert not rows[0].can_confirm
    assert validate_channel(creator, "tiktok_dm") == CHANNEL_UNKNOWN
    assert validate_channel(creator, "unknown") == CHANNEL_UNKNOWN


def test_channel_not_on_profile() -> None:
    creator = mock_store.load()["creator_001"]
    assert validate_channel(creator, "email") is None
    assert validate_channel(creator, "tiktok_dm") is None
    slim = MergedCreator(
        creator_id="creator_slim",
        display_name="Slim",
        platforms=["tiktok"],
        tiktok={"contact": {"preferred_channel": "tiktok_dm", "email": None, "consent_status": "unknown"}},
    )
    assert validate_channel(slim, "instagram_dm") == CHANNEL_NOT_ON_PROFILE
    assert validate_channel(slim, "email") == CHANNEL_NOT_ON_PROFILE


async def test_unapproved_confirm_is_rejected(application) -> None:
    session_id = application.store.create_session()
    application.save_campaign(
        Campaign(campaign_id=session_id, saved_creator_ids=["creator_001"], stage="SELECTED")
    )
    tool = ConfirmChannelTool(application.campaigns)
    result = await tool.execute(
        {"creator_id": "creator_001", "channel": "tiktok_dm"},
        ToolContext(session_id=session_id, turn_id=uuid4()),
    )
    assert result.error_code == "approval_required"
    stored = application.campaign(session_id)
    assert stored.confirmed_channels == {}


async def test_approved_confirm_writes_channel_and_has_no_send(application) -> None:
    session_id = application.store.create_session()
    application.save_campaign(
        Campaign(campaign_id=session_id, saved_creator_ids=["creator_001"], stage="SELECTED")
    )
    tool = ConfirmChannelTool(application.campaigns)
    result = await tool.execute(
        {"creator_id": "creator_001", "channel": "tiktok_dm"},
        ToolContext(session_id=session_id, turn_id=uuid4(), user_approved=True),
    )
    assert result.ok
    stored = application.campaign(session_id)
    assert stored.confirmed_channels["creator_001"] == "tiktok_dm"
    reopened = application.campaign(session_id)
    assert reopened.confirmed_channels["creator_001"] == "tiktok_dm"
    blob = (SRC / "campaign" / "channels.py").read_text(encoding="utf-8")
    blob += (SRC / "tools" / "builtin" / "confirm_channel.py").read_text(encoding="utf-8")
    lowered = blob.lower()
    assert "smtp" not in lowered
    assert "send_mail" not in lowered
    assert "send_message" not in lowered
    assert CHANNEL_LABELS["tiktok_dm"] == "TikTok 私信"
