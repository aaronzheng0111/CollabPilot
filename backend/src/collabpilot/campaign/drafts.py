"""Outreach drafts: schema, validation and pending save/approve (T10).

The model writes one draft for the chosen creator that has a real contact
channel; this module checks they cite real posts, quote at least 8 characters
of original text, and name the auto-picked channel. Creators with no usable
channel get a card that says so. UI generate is per creator; multiple drafts
may be merged into the campaign over successive clicks. Nothing here sends.
"""

from __future__ import annotations

import json
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from collabpilot.campaign import mock_store
from collabpilot.campaign.channels import (
    CHANNEL_LABELS,
    ConfirmableChannel,
    pick_channel,
)
from collabpilot.campaign.goal import Campaign
from collabpilot.campaign.mock_store import MergedCreator
from collabpilot.campaign.selection import creator_display_name
from collabpilot.campaign.verdict import Verdict


DRAFT_ORIGIN = "real_model_output"
LLM_LABEL = "[LLM]"
SAVE_DRAFTS = "save_drafts"
APPROVE_DRAFT = "approve_draft"
REJECT_DRAFT = "reject_draft"
DRAFTS_HEADING = "【邀请草稿】"
DRAFT_STEP = "generate_drafts"
NEED_SELECTION = "need_selection"
NEED_THREE_CREATORS = "need_three_creators"  # legacy alias used by older docs/tests
CHANNEL_UNCONFIRMED = "channel_unconfirmed"  # no longer blocking; kept for message maps
CHANNEL_MISMATCH = "channel_mismatch"
QUOTE_NOT_FOUND = "quote_not_found"
CITED_POST_INVALID = "cited_post_invalid"
BODIES_NOT_UNIQUE = "bodies_not_unique"
POSTS_NOT_UNIQUE = "posts_not_unique"
DRAFTS_INVALID = "drafts_invalid"
MIN_QUOTE_CHARS = 8
NO_CHANNEL_DRAFT_TEXT = "没有可用渠道"
NO_SEND_CAPTION = "草稿不会发送 [MOCK-SEND]"
PICK_CREATOR_FOR_DRAFT = "请在表里选合适达人后点「生成草稿」。"
STATUS_LABELS: dict[str, str] = {
    "pending_review": "待审核",
    "approved": "已批准",
    "rejected": "已退回",
}
DraftStatus = Literal["pending_review", "approved", "rejected"]


class Draft(BaseModel):
    id: str
    campaign_id: str
    creator_id: str
    body: str
    cited_post_id: str
    channel: ConfirmableChannel | None = None
    status: DraftStatus = "pending_review"
    data_origin: Literal["real_model_output"] = DRAFT_ORIGIN
    model_name: str


class RawDraft(BaseModel):
    creator_id: str
    body: str
    cited_post_id: str
    channel: ConfirmableChannel


class DraftBatch(BaseModel):
    accepted: list[Draft] = Field(default_factory=list)
    error_code: str | None = None
    model_called: bool = False
    model_name: str | None = None
    expected_count: int = 0

    @property
    def ok(self) -> bool:
        if self.error_code is not None:
            return False
        if self.expected_count:
            return len(self.accepted) == self.expected_count
        return bool(self.accepted)


def display_name_of(campaign: Campaign, creator_id: str) -> str:
    creator = mock_store.load().get(creator_id)
    if creator is not None:
        return creator.display_name
    return creator_display_name(campaign, creator_id)


def save_drafts_label(campaign: Campaign | None = None) -> str:
    payload = (campaign.pending_payload if campaign else None) or {}
    drafts = payload.get("drafts") or []
    count = len(drafts) or ((campaign and len(campaign.drafts)) or 0)
    if count:
        return f"保存 {count} 封草稿供审核"
    return "保存草稿供审核"


def approve_draft_label(campaign: Campaign) -> str:
    payload = campaign.pending_payload or {}
    creator_id = str(payload.get("creator_id") or "")
    name = display_name_of(campaign, creator_id) if creator_id else ""
    return f"审核草稿：{name}".rstrip("：")


def reject_draft_label(campaign: Campaign) -> str:
    payload = campaign.pending_payload or {}
    creator_id = str(payload.get("creator_id") or "")
    name = display_name_of(campaign, creator_id) if creator_id else ""
    return f"退回草稿：{name}".rstrip("：")


def review_draft_label(campaign: Campaign, draft: Draft) -> str:
    return f"审核草稿：{display_name_of(campaign, draft.creator_id)}"


def outreach_ids(
    campaign: Campaign, creator_ids: list[str] | None = None
) -> list[str]:
    if creator_ids is not None:
        return list(creator_ids)
    pending = (campaign.pending_payload or {}).get("draft_creator_ids")
    if isinstance(pending, list) and pending:
        return [str(item) for item in pending]
    return list(campaign.saved_creator_ids)


def resolve_channels(
    creator_ids: list[str],
    creators: dict[str, MergedCreator] | None = None,
) -> dict[str, ConfirmableChannel | None]:
    pool = creators if creators is not None else mock_store.load()
    return {creator_id: pick_channel(pool.get(creator_id)) for creator_id in creator_ids}


def draft_prerequisites(
    campaign: Campaign, creator_ids: list[str] | None = None
) -> str | None:
    ids = outreach_ids(campaign, creator_ids)
    if not ids:
        return NEED_SELECTION
    return None


def _post_by_id(creator: MergedCreator, post_id: str) -> dict[str, Any] | None:
    return next((post for post in creator.posts() if post.get("post_id") == post_id), None)


def cited_post_text(creator_id: str, post_id: str) -> str:
    creator = mock_store.load().get(creator_id)
    if creator is None:
        return ""
    post = _post_by_id(creator, post_id)
    return mock_store.post_text(post) if post else ""


def quote_found(body: str, post: dict[str, Any]) -> bool:
    """True when body contains ≥8 consecutive characters from title or caption."""
    for field in ("title", "caption"):
        text = str(post.get(field) or "")
        if len(text) < MIN_QUOTE_CHARS:
            continue
        for index in range(len(text) - MIN_QUOTE_CHARS + 1):
            if text[index : index + MIN_QUOTE_CHARS] in body:
                return True
    combined = mock_store.post_text(post)
    if len(combined) < MIN_QUOTE_CHARS:
        return False
    for index in range(len(combined) - MIN_QUOTE_CHARS + 1):
        if combined[index : index + MIN_QUOTE_CHARS] in body:
            return True
    return False


def _parse_raw(obj: Any, expected: int) -> list[RawDraft] | None:
    if isinstance(obj, dict):
        obj = obj.get("drafts")
    if not isinstance(obj, list) or len(obj) != expected:
        return None
    try:
        return [RawDraft.model_validate(item) for item in obj]
    except ValidationError:
        return None


def placeholder_draft(
    campaign: Campaign, creator_id: str, *, model_name: str
) -> Draft:
    return Draft(
        id=str(uuid4()),
        campaign_id=str(campaign.campaign_id),
        creator_id=creator_id,
        body=NO_CHANNEL_DRAFT_TEXT,
        cited_post_id="",
        channel=None,
        status="pending_review",
        model_name=model_name,
    )


def validate_drafts(
    obj: Any,
    campaign: Campaign,
    creators: dict[str, MergedCreator],
    *,
    model_name: str,
    creator_ids: list[str] | None = None,
    channels: dict[str, ConfirmableChannel | None] | None = None,
) -> DraftBatch:
    """Return Drafts for every target, or a batch-level error.

    Targets without a real channel become placeholder cards; the model is only
    responsible for targets that have a channel.
    """
    targets = outreach_ids(campaign, creator_ids)
    resolved = channels if channels is not None else resolve_channels(targets, creators)
    with_channel = [cid for cid in targets if resolved.get(cid)]
    without_channel = [cid for cid in targets if not resolved.get(cid)]
    expected = len(with_channel)
    raw_items = _parse_raw(obj, expected) if expected else []
    if expected and raw_items is None:
        return DraftBatch(
            error_code=DRAFTS_INVALID,
            model_name=model_name,
            expected_count=len(targets),
        )
    target_set = set(with_channel)
    if expected and {item.creator_id for item in raw_items} != target_set:
        return DraftBatch(
            error_code=DRAFTS_INVALID,
            model_name=model_name,
            expected_count=len(targets),
        )
    if expected:
        bodies = [item.body.strip() for item in raw_items]
        if any(not body for body in bodies) or len(set(bodies)) != expected:
            return DraftBatch(
                error_code=BODIES_NOT_UNIQUE,
                model_name=model_name,
                expected_count=len(targets),
            )
        post_ids = [item.cited_post_id for item in raw_items]
        if len(set(post_ids)) != expected:
            return DraftBatch(
                error_code=POSTS_NOT_UNIQUE,
                model_name=model_name,
                expected_count=len(targets),
            )
    accepted: list[Draft] = []
    for item in raw_items or []:
        expected_channel = resolved.get(item.creator_id)
        label = CHANNEL_LABELS.get(item.channel, "") if item.channel else ""
        if item.channel != expected_channel or not label or label not in item.body:
            return DraftBatch(
                error_code=CHANNEL_MISMATCH,
                model_name=model_name,
                expected_count=len(targets),
            )
        creator = creators.get(item.creator_id)
        post = _post_by_id(creator, item.cited_post_id) if creator is not None else None
        if post is None:
            return DraftBatch(
                error_code=CITED_POST_INVALID,
                model_name=model_name,
                expected_count=len(targets),
            )
        if not quote_found(item.body, post):
            return DraftBatch(
                error_code=QUOTE_NOT_FOUND,
                model_name=model_name,
                expected_count=len(targets),
            )
        accepted.append(
            Draft(
                id=str(uuid4()),
                campaign_id=str(campaign.campaign_id),
                creator_id=item.creator_id,
                body=item.body,
                cited_post_id=item.cited_post_id,
                channel=item.channel,
                status="pending_review",
                model_name=model_name,
            )
        )
    for creator_id in without_channel:
        accepted.append(placeholder_draft(campaign, creator_id, model_name=model_name))
    # Keep the same order as the user's selection.
    by_id = {item.creator_id: item for item in accepted}
    ordered = [by_id[cid] for cid in targets if cid in by_id]
    return DraftBatch(
        accepted=ordered, model_name=model_name, expected_count=len(targets)
    )


def drafts_payload(
    campaign: Campaign,
    creators: dict[str, MergedCreator],
    creator_ids: list[str] | None = None,
    channels: dict[str, ConfirmableChannel | None] | None = None,
) -> list[dict[str, Any]]:
    verdicts = {item.creator_id: item for item in (campaign.verdicts or [])}
    targets = outreach_ids(campaign, creator_ids)
    resolved = channels if channels is not None else resolve_channels(targets, creators)
    rows: list[dict[str, Any]] = []
    for creator_id in targets:
        channel = resolved.get(creator_id)
        if channel is None:
            continue
        creator = creators.get(creator_id)
        if creator is None:
            continue
        verdict: Verdict | None = verdicts.get(creator_id)
        rows.append(
            {
                "creator_id": creator_id,
                "display_name": creator.display_name,
                "channel": channel,
                "channel_label": CHANNEL_LABELS[channel],
                "reasons": list(verdict.reasons) if verdict else [],
                "posts": [
                    {
                        "post_id": post.get("post_id"),
                        "title": post.get("title"),
                        "caption": post.get("caption"),
                        "age_days": post.get("age_days"),
                    }
                    for post in creator.posts()
                ],
            }
        )
    return rows


def render_drafts_prompt(template: str, *, brand: str, product: str) -> str:
    return template.replace("{brand}", brand).replace("{product}", product)


def render_drafts_message(payload: list[dict[str, Any]]) -> str:
    return (
        f"{DRAFTS_HEADING}为以下 {len(payload)} 位创作者各写一封邀请草稿。"
        "渠道已从资料自动选定，必须原样使用。\n"
        "```json\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n```\n"
        "请只回复一个 ```json 代码块：{\"drafts\": [Draft, ...]}。"
    )


def queue_save_drafts(campaign: Campaign, drafts: list[Draft]) -> Campaign:
    return campaign.model_copy(
        update={
            "pending_decision": SAVE_DRAFTS,
            "pending_payload": {
                "drafts": [item.model_dump(mode="json") for item in drafts],
            },
            "stage": "DRAFTING",
            "draft_error": None,
        }
    )


def apply_save_drafts(campaign: Campaign, drafts: list[Draft] | None = None) -> tuple[Campaign, str]:
    """Persist queued drafts, merging by creator_id so one-at-a-time generate keeps prior cards."""
    payload = campaign.pending_payload or {}
    raw = drafts or [Draft.model_validate(item) for item in payload.get("drafts") or []]
    incoming = [
        item.model_copy(
            update={
                "status": "pending_review",
                "campaign_id": str(campaign.campaign_id),
            }
        )
        for item in raw
    ]
    by_creator: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for item in _draft_list(campaign):
        by_creator[item.creator_id] = item.model_dump(mode="json")
        order.append(item.creator_id)
    for item in incoming:
        dump = item.model_dump(mode="json")
        if item.creator_id not in by_creator:
            order.append(item.creator_id)
        by_creator[item.creator_id] = dump
    stored = [by_creator[cid] for cid in order if cid in by_creator]
    updated = campaign.model_copy(
        update={
            "drafts": stored,
            "stage": "DRAFT_REVIEW",
            "pending_payload": None,
            "draft_error": None,
        }
    )
    return updated, f"已保存 {len(incoming)} 封草稿供审核。草稿不会发送。"


def _draft_list(campaign: Campaign) -> list[Draft]:
    return [Draft.model_validate(item) for item in campaign.drafts]


def _replace_draft(
    campaign: Campaign, draft_id: str, status: DraftStatus
) -> tuple[Campaign, Draft | None]:
    found: Draft | None = None
    rows: list[dict[str, Any]] = []
    for item in _draft_list(campaign):
        if item.id == draft_id:
            found = item.model_copy(update={"status": status})
            rows.append(found.model_dump(mode="json"))
        else:
            rows.append(item.model_dump(mode="json"))
    if found is None:
        return campaign, None
    return campaign.model_copy(update={"drafts": rows, "pending_payload": None}), found


def apply_approve_draft(campaign: Campaign, draft_id: str) -> tuple[Campaign, str]:
    updated, draft = _replace_draft(campaign, draft_id, "approved")
    if draft is None:
        return campaign, "没有这封草稿。"
    name = display_name_of(campaign, draft.creator_id)
    return updated, f"已批准 {name} 的草稿。仍未发送。"


def apply_reject_draft(campaign: Campaign, draft_id: str) -> tuple[Campaign, str]:
    updated, draft = _replace_draft(campaign, draft_id, "rejected")
    if draft is None:
        return campaign, "没有这封草稿。"
    name = display_name_of(campaign, draft.creator_id)
    return updated, f"已退回 {name} 的草稿。仍未发送。"


def queue_review_draft(campaign: Campaign, draft_id: str, decision: str) -> Campaign:
    draft = next((item for item in _draft_list(campaign) if item.id == draft_id), None)
    return campaign.model_copy(
        update={
            "pending_decision": decision,
            "pending_payload": {
                "draft_id": draft_id,
                "creator_id": draft.creator_id if draft else "",
            },
        }
    )


def pending_review_drafts(campaign: Campaign) -> list[Draft]:
    return [item for item in _draft_list(campaign) if item.status == "pending_review"]


def draft_card_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    """Cards for saved drafts, or queued ``save_drafts`` payload before approve."""
    if campaign is None:
        return []
    drafts = _draft_list(campaign)
    if not drafts and campaign.pending_decision == SAVE_DRAFTS:
        raw = (campaign.pending_payload or {}).get("drafts") or []
        drafts = [Draft.model_validate(item) for item in raw]
    if not drafts:
        return []
    rows: list[dict[str, Any]] = []
    for item in drafts:
        if item.channel:
            channel_label = CHANNEL_LABELS.get(item.channel, item.channel)
        else:
            channel_label = NO_CHANNEL_DRAFT_TEXT
        rows.append(
            {
                "id": item.id,
                "creator_id": item.creator_id,
                "display_name": display_name_of(campaign, item.creator_id),
                "channel": item.channel,
                "channel_label": channel_label,
                "cited_post_id": item.cited_post_id,
                "cited_text": (
                    cited_post_text(item.creator_id, item.cited_post_id)
                    if item.cited_post_id
                    else ""
                ),
                "body": item.body,
                "status": item.status,
                "status_label": STATUS_LABELS.get(item.status, item.status),
                "model_name": item.model_name,
                "data_origin": item.data_origin,
                "source": f"{LLM_LABEL} {item.model_name}",
            }
        )
    return rows


def can_generate_drafts(campaign: Campaign | None) -> bool:
    """True when the main table can offer per-creator 「生成草稿」 actions.

    Existing drafts do not block generating for another creator. Any pending
    decision (including mid-flight ``save_drafts``) hides the actions.
    """
    if campaign is None:
        return False
    if campaign.pending_decision:
        return False
    if campaign.verdicts or campaign.saved_creator_ids:
        return True
    return False
