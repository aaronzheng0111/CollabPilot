"""Follow-up items after an approved draft (T14).

The model writes next_step and must copy the confirmed channel. This module
only checks the draft is approved and the channel matches. Nothing here sends.
"""

from __future__ import annotations

import json
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from collabpilot.campaign.channels import CHANNEL_LABELS, ConfirmableChannel
from collabpilot.campaign.drafts import Draft, display_name_of
from collabpilot.campaign.goal import Campaign


FOLLOW_ORIGIN = "real_model_output"
LLM_LABEL = "[LLM]"
SAVE_FOLLOW_UP = "save_follow_up"
NOTE_FOLLOW_UP = "note_follow_up"
FOLLOW_UP_HEADING = "【跟进事项】"
FOLLOW_STEP = "generate_follow_up"
DRAFT_NOT_APPROVED = "draft_not_approved"
CHANNEL_MISMATCH = "channel_mismatch"
FOLLOW_UP_INVALID = "follow_up_invalid"
FOLLOW_UP_EXISTS = "follow_up_exists"
NOTE_LABEL = "记下"
SAVE_FOLLOW_UP_TEMPLATE = "记录对 {display_name} 的跟进"
NOTE_FOLLOW_UP_TEMPLATE = "记下对 {display_name} 的跟进"
NO_SEND_CAPTION = "记下不等于发送 [MOCK-SEND]"
FollowStatus = Literal["waiting_user", "noted"]
STATUS_LABELS: dict[str, str] = {
    "waiting_user": "等你记下",
    "noted": "已记下",
}


class FollowUp(BaseModel):
    id: str
    campaign_id: str
    creator_id: str
    draft_id: str
    channel: ConfirmableChannel
    next_step: str
    follow_status: FollowStatus = "waiting_user"
    data_origin: Literal["real_model_output"] = FOLLOW_ORIGIN
    model_name: str


class RawFollowUp(BaseModel):
    creator_id: str
    draft_id: str
    channel: ConfirmableChannel
    next_step: str


class FollowUpBatch(BaseModel):
    accepted: FollowUp | None = None
    error_code: str | None = None
    model_called: bool = False
    model_name: str | None = None

    @property
    def ok(self) -> bool:
        return self.error_code is None and self.accepted is not None


def _draft_list(campaign: Campaign) -> list[Draft]:
    return [Draft.model_validate(item) for item in campaign.drafts]


def _follow_list(campaign: Campaign) -> list[FollowUp]:
    return [FollowUp.model_validate(item) for item in campaign.follow_ups]


def draft_by_id(campaign: Campaign, draft_id: str) -> Draft | None:
    return next((item for item in _draft_list(campaign) if item.id == draft_id), None)


def follow_up_for_draft(campaign: Campaign, draft_id: str) -> FollowUp | None:
    return next((item for item in _follow_list(campaign) if item.draft_id == draft_id), None)


def follow_up_prerequisites(campaign: Campaign, draft_id: str) -> str | None:
    draft = draft_by_id(campaign, draft_id)
    if draft is None or draft.status != "approved":
        return DRAFT_NOT_APPROVED
    if follow_up_for_draft(campaign, draft_id) is not None:
        return FOLLOW_UP_EXISTS
    channel = draft.channel or campaign.confirmed_channels.get(draft.creator_id)
    if channel is None:
        return CHANNEL_MISMATCH
    return None


def _parse_raw(obj: Any) -> RawFollowUp | None:
    if not isinstance(obj, dict):
        return None
    payload = obj.get("follow_up") if "follow_up" in obj else obj
    if not isinstance(payload, dict):
        return None
    try:
        return RawFollowUp.model_validate(payload)
    except ValidationError:
        return None


def validate_follow_up(
    obj: Any,
    campaign: Campaign,
    *,
    draft_id: str,
    model_name: str,
) -> FollowUpBatch:
    """Return one FollowUp or an error. Channel must equal the draft channel."""
    draft = draft_by_id(campaign, draft_id)
    if draft is None or draft.status != "approved":
        return FollowUpBatch(error_code=DRAFT_NOT_APPROVED, model_name=model_name)
    raw = _parse_raw(obj)
    if raw is None or not raw.next_step.strip():
        return FollowUpBatch(error_code=FOLLOW_UP_INVALID, model_name=model_name)
    if raw.draft_id != draft.id or raw.creator_id != draft.creator_id:
        return FollowUpBatch(error_code=FOLLOW_UP_INVALID, model_name=model_name)
    expected = draft.channel or campaign.confirmed_channels.get(draft.creator_id)
    if expected is None or raw.channel != expected:
        return FollowUpBatch(error_code=CHANNEL_MISMATCH, model_name=model_name)
    return FollowUpBatch(
        accepted=FollowUp(
            id=str(uuid4()),
            campaign_id=str(campaign.campaign_id),
            creator_id=draft.creator_id,
            draft_id=draft.id,
            channel=raw.channel,
            next_step=raw.next_step.strip(),
            follow_status="waiting_user",
            model_name=model_name,
        ),
        model_name=model_name,
    )


def follow_up_payload(campaign: Campaign, draft_id: str) -> dict[str, Any] | None:
    draft = draft_by_id(campaign, draft_id)
    if draft is None:
        return None
    channel = draft.channel or campaign.confirmed_channels.get(draft.creator_id)
    if channel is None:
        return None
    return {
        "creator_id": draft.creator_id,
        "display_name": display_name_of(campaign, draft.creator_id),
        "draft_id": draft.id,
        "draft_body": draft.body,
        "channel": channel,
        "channel_label": CHANNEL_LABELS[channel],
    }


def render_follow_up_prompt(template: str, *, brand: str) -> str:
    return template.replace("{brand}", brand)


def render_follow_up_message(payload: dict[str, Any]) -> str:
    return (
        f"{FOLLOW_UP_HEADING}为这位创作者写一条跟进事项。渠道已确认，必须原样使用。\n"
        "```json\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n```\n"
        "请只回复一个 ```json 代码块。"
    )


def save_follow_up_label(campaign: Campaign) -> str:
    payload = campaign.pending_payload or {}
    follow = payload.get("follow_up") or {}
    creator_id = str(follow.get("creator_id") or payload.get("creator_id") or "")
    name = display_name_of(campaign, creator_id) if creator_id else ""
    return SAVE_FOLLOW_UP_TEMPLATE.format(display_name=name)


def note_follow_up_label(campaign: Campaign) -> str:
    payload = campaign.pending_payload or {}
    creator_id = str(payload.get("creator_id") or "")
    name = display_name_of(campaign, creator_id) if creator_id else ""
    return NOTE_FOLLOW_UP_TEMPLATE.format(display_name=name)


def note_row_label(campaign: Campaign, item: FollowUp) -> str:
    return NOTE_FOLLOW_UP_TEMPLATE.format(
        display_name=display_name_of(campaign, item.creator_id)
    )


def queue_save_follow_up(campaign: Campaign, follow_up: FollowUp) -> Campaign:
    return campaign.model_copy(
        update={
            "pending_decision": SAVE_FOLLOW_UP,
            "pending_payload": {"follow_up": follow_up.model_dump(mode="json")},
            "stage": "FOLLOW_UP",
            "follow_error": None,
        }
    )


def apply_save_follow_up(
    campaign: Campaign, follow_up: FollowUp | None = None
) -> tuple[Campaign, str]:
    payload = campaign.pending_payload or {}
    raw = follow_up or FollowUp.model_validate(payload.get("follow_up") or {})
    stored = raw.model_copy(
        update={
            "follow_status": "waiting_user",
            "campaign_id": str(campaign.campaign_id),
        }
    )
    existing = [
        item.model_dump(mode="json")
        for item in _follow_list(campaign)
        if item.draft_id != stored.draft_id
    ]
    existing.append(stored.model_dump(mode="json"))
    name = display_name_of(campaign, stored.creator_id)
    updated = campaign.model_copy(
        update={
            "follow_ups": existing,
            "stage": "FOLLOW_UP",
            "pending_payload": None,
            "follow_error": None,
        }
    )
    return updated, f"已记录对 {name} 的跟进。等你记下。仍未发送。"


def apply_note_follow_up(campaign: Campaign, follow_up_id: str) -> tuple[Campaign, str]:
    found: FollowUp | None = None
    rows: list[dict[str, Any]] = []
    for item in _follow_list(campaign):
        if item.id == follow_up_id:
            found = item.model_copy(update={"follow_status": "noted"})
            rows.append(found.model_dump(mode="json"))
        else:
            rows.append(item.model_dump(mode="json"))
    if found is None:
        return campaign, "没有这条跟进。"
    name = display_name_of(campaign, found.creator_id)
    updated = campaign.model_copy(
        update={"follow_ups": rows, "pending_payload": None, "stage": "FOLLOW_UP"}
    )
    return updated, f"已记下对 {name} 的跟进。仍未发送。"


def queue_note_follow_up(campaign: Campaign, follow_up_id: str) -> Campaign:
    item = next((row for row in _follow_list(campaign) if row.id == follow_up_id), None)
    return campaign.model_copy(
        update={
            "pending_decision": NOTE_FOLLOW_UP,
            "pending_payload": {
                "follow_up_id": follow_up_id,
                "creator_id": item.creator_id if item else "",
            },
        }
    )


def waiting_user_follow_ups(campaign: Campaign) -> list[FollowUp]:
    return [item for item in _follow_list(campaign) if item.follow_status == "waiting_user"]


def follow_up_table_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    if campaign is None or not campaign.follow_ups:
        return []
    rows: list[dict[str, Any]] = []
    for item in _follow_list(campaign):
        rows.append(
            {
                "id": item.id,
                "creator_id": item.creator_id,
                "display_name": display_name_of(campaign, item.creator_id),
                "channel": item.channel,
                "channel_label": CHANNEL_LABELS.get(item.channel, item.channel),
                "next_step": item.next_step,
                "follow_status": item.follow_status,
                "status_label": STATUS_LABELS.get(item.follow_status, item.follow_status),
                "model_name": item.model_name,
                "data_origin": item.data_origin,
                "source": f"{LLM_LABEL} {item.model_name}",
            }
        )
    return rows
