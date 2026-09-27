"""Contact views and channel confirmation (T13).

Channels come only from mock ``contact``. This module never guesses a
channel and never sends a message.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import Campaign
from collabpilot.campaign.mock_store import MOCK_ORIGIN, MergedCreator, Platform
from collabpilot.campaign.selection import creator_display_name


CONFIRM_CHANNEL = "confirm_channel"
CHANNEL_UNKNOWN = "channel_unknown"
CHANNEL_NOT_ON_PROFILE = "channel_not_on_profile"
UNKNOWN = "未知"
MOCK_LABEL = "[MOCK]"
CONFIRMABLE = ("tiktok_dm", "instagram_dm", "email")
PreferredChannel = Literal["tiktok_dm", "instagram_dm", "email", "unknown"]
ConfirmableChannel = Literal["tiktok_dm", "instagram_dm", "email"]
ConsentStatus = Literal["granted", "denied", "unknown"]

CHANNEL_LABELS: dict[str, str] = {
    "tiktok_dm": "TikTok 私信",
    "instagram_dm": "Instagram 私信",
    "email": "邮件",
    "unknown": UNKNOWN,
}
CONSENT_LABELS: dict[str, str] = {
    "granted": "已同意",
    "denied": "已拒绝",
    "unknown": UNKNOWN,
}
NO_CHANNEL_TEXT = "资料中没有可用渠道"


class ContactView(BaseModel):
    creator_id: str
    display_name: str
    platform: Platform
    preferred_channel: PreferredChannel
    dm_available: bool
    email: str | None
    consent_status: ConsentStatus
    data_origin: Literal["mock_seed"] = MOCK_ORIGIN
    source: str = MOCK_LABEL

    @property
    def preferred_label(self) -> str:
        return CHANNEL_LABELS.get(self.preferred_channel, UNKNOWN)

    @property
    def email_display(self) -> str:
        return self.email if self.email else UNKNOWN

    @property
    def consent_label(self) -> str:
        return CONSENT_LABELS.get(self.consent_status, UNKNOWN)

    @property
    def available_channels(self) -> list[str]:
        return available_channels_from_contact(
            {
                "preferred_channel": self.preferred_channel,
                "email": self.email,
            }
        )

    @property
    def can_confirm(self) -> bool:
        return bool(self.available_channels)


class ConfirmedChannel(BaseModel):
    creator_id: str
    channel: ConfirmableChannel
    user_approved: Literal[True] = True


def normalize_preferred(value: Any) -> PreferredChannel:
    if value in CONFIRMABLE or value == "unknown":
        return value
    return "unknown"


def normalize_consent(value: Any) -> ConsentStatus:
    if value in CONSENT_LABELS:
        return value
    return "unknown"


def available_channels_from_contact(contact: dict[str, Any]) -> list[str]:
    channels: list[str] = []
    preferred = normalize_preferred(contact.get("preferred_channel"))
    if preferred in CONFIRMABLE:
        channels.append(preferred)
    email = contact.get("email")
    if email and "email" not in channels:
        channels.append("email")
    return channels


def available_channels(creator: MergedCreator) -> list[str]:
    seen: list[str] = []
    for _, account in creator.accounts():
        for channel in available_channels_from_contact(account.get("contact") or {}):
            if channel not in seen:
                seen.append(channel)
    return seen


def pick_channel(creator: MergedCreator | None) -> ConfirmableChannel | None:
    """Auto-pick outreach channel from contact data. Never invents an address.

    Preferred channel wins when it is a real confirmable value; otherwise the
    first available real channel (tiktok_dm / instagram_dm / email).
    """
    if creator is None:
        return None
    preferred: PreferredChannel | None = None
    for _, account in creator.accounts():
        contact = account.get("contact") or {}
        value = normalize_preferred(contact.get("preferred_channel"))
        if value in CONFIRMABLE:
            preferred = value
            break
    if preferred in CONFIRMABLE:
        return preferred  # type: ignore[return-value]
    channels = available_channels(creator)
    if not channels:
        return None
    return channels[0]  # type: ignore[return-value]


def list_contacts(
    creator_ids: list[str],
    creators: dict[str, MergedCreator] | None = None,
) -> list[ContactView]:
    """One row per platform account. Does not merge into a guessed channel."""
    pool = creators if creators is not None else mock_store.load()
    rows: list[ContactView] = []
    for creator_id in creator_ids:
        creator = pool.get(creator_id)
        if creator is None:
            continue
        for platform, account in creator.accounts():
            contact = account.get("contact") or {}
            rows.append(
                ContactView(
                    creator_id=creator_id,
                    display_name=creator.display_name,
                    platform=platform,
                    preferred_channel=normalize_preferred(contact.get("preferred_channel")),
                    dm_available=bool(contact.get("dm_available")),
                    email=contact.get("email") or None,
                    consent_status=normalize_consent(contact.get("consent_status")),
                )
            )
    return rows


def validate_channel(creator: MergedCreator | None, channel: str) -> str | None:
    """Return an error_code, or None if the channel may be confirmed."""
    if channel not in CONFIRMABLE:
        return CHANNEL_UNKNOWN
    if creator is None:
        return CHANNEL_UNKNOWN
    allowed = available_channels(creator)
    if not allowed:
        return CHANNEL_UNKNOWN
    if channel not in allowed:
        return CHANNEL_NOT_ON_PROFILE
    return None


def apply_confirm_channel(
    campaign: Campaign, creator_id: str, channel: str
) -> tuple[Campaign, str]:
    channels = dict(campaign.confirmed_channels)
    channels[creator_id] = channel
    updated = campaign.model_copy(
        update={"confirmed_channels": channels, "pending_payload": None}
    )
    name = creator_display_name(campaign, creator_id)
    label = CHANNEL_LABELS.get(channel, channel)
    return updated, f"已确认用{label}联系 {name}。"


def queue_confirm_channel(campaign: Campaign, creator_id: str, channel: str) -> Campaign:
    return campaign.model_copy(
        update={
            "pending_decision": CONFIRM_CHANNEL,
            "pending_payload": {
                "creator_id": creator_id,
                "channel": channel,
                "creator_ids": [creator_id],
            },
        }
    )


def confirm_channel_label(campaign: Campaign) -> str:
    payload = campaign.pending_payload or {}
    creator_id = str(payload.get("creator_id") or "")
    channel = str(payload.get("channel") or "")
    name = creator_display_name(campaign, creator_id) if creator_id else ""
    label = CHANNEL_LABELS.get(channel, channel)
    return f"用 {label} 联系 {name}".strip()


def channel_label(channel: str | None) -> str:
    if not channel:
        return ""
    return CHANNEL_LABELS.get(channel, channel)
