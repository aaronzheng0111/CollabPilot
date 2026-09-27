"""`approve_pending`: the single entry point for every「待你决定」item.

Later tasks register their own branch with ``@register_decision``. T02 only
ships ``confirm_assumptions``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel

from collabpilot.campaign.goal import (
    CONFIRM_ASSUMPTIONS,
    GOAL_ORIGIN,
    Campaign,
    apply_confirm_assumptions,
    goal_summary,
)
from collabpilot.campaign.retry import (
    ACCEPT_SHORT_LIST,
    accept_fit_count,
    accept_short_list_label,
)
from collabpilot.campaign.selection import (
    EXCLUDE_CREATOR,
    SAVE_SELECTION,
    apply_exclude_creator,
    apply_save_selection,
    exclude_creator_label,
    fingerprint_goal,
    pending_creator_ids,
    save_selection_label,
)
from collabpilot.campaign.channels import (
    CONFIRM_CHANNEL,
    apply_confirm_channel,
    confirm_channel_label,
)
from collabpilot.campaign.drafts import (
    APPROVE_DRAFT,
    REJECT_DRAFT,
    SAVE_DRAFTS,
    apply_approve_draft,
    apply_reject_draft,
    apply_save_drafts,
    approve_draft_label,
    reject_draft_label,
    save_drafts_label,
)
from collabpilot.campaign.follow_up import (
    NOTE_FOLLOW_UP,
    SAVE_FOLLOW_UP,
    apply_note_follow_up,
    apply_save_follow_up,
    note_follow_up_label,
    save_follow_up_label,
)


DecisionStatus = Literal[
    "applied", "approval_required", "not_pending", "unknown_decision"
]
DecisionHandler = Callable[[Campaign], tuple[Campaign, str]]


class DecisionResult(BaseModel):
    decision: str
    status: DecisionStatus
    campaign: Campaign
    display: str

    @property
    def ok(self) -> bool:
        return self.status == "applied"


_HANDLERS: dict[str, DecisionHandler] = {}

DECISION_LABELS: dict[str, str] = {
    CONFIRM_ASSUMPTIONS: "确认以上假设",
    ACCEPT_SHORT_LIST: "当前合格人数少于目标，是否接受",
    SAVE_SELECTION: "保存到活动",
    EXCLUDE_CREATOR: "排除创作者",
    CONFIRM_CHANNEL: "确认渠道",
    SAVE_DRAFTS: "保存 3 封草稿供审核",
    APPROVE_DRAFT: "审核草稿",
    REJECT_DRAFT: "退回草稿",
    SAVE_FOLLOW_UP: "记录跟进",
    NOTE_FOLLOW_UP: "记下跟进",
}


def register_decision(name: str) -> Callable[[DecisionHandler], DecisionHandler]:
    def decorator(handler: DecisionHandler) -> DecisionHandler:
        _HANDLERS[name] = handler
        return handler

    return decorator


def registered_decisions() -> list[str]:
    return sorted(_HANDLERS)


def decision_label(campaign: Campaign) -> str:
    pending = campaign.pending_decision
    if pending == ACCEPT_SHORT_LIST:
        return accept_short_list_label(campaign)
    if pending == SAVE_SELECTION:
        return save_selection_label(campaign)
    if pending == EXCLUDE_CREATOR:
        return exclude_creator_label(campaign)
    if pending == CONFIRM_CHANNEL:
        return confirm_channel_label(campaign)
    if pending == SAVE_DRAFTS:
        return save_drafts_label(campaign)
    if pending == APPROVE_DRAFT:
        return approve_draft_label(campaign)
    if pending == REJECT_DRAFT:
        return reject_draft_label(campaign)
    if pending == SAVE_FOLLOW_UP:
        return save_follow_up_label(campaign)
    if pending == NOTE_FOLLOW_UP:
        return note_follow_up_label(campaign)
    return DECISION_LABELS.get(pending or "", pending or "")


def approve_pending(
    campaign: Campaign, decision: str, user_approved: bool
) -> DecisionResult:
    handler = _HANDLERS.get(decision)
    if handler is None:
        return DecisionResult(
            decision=decision,
            status="unknown_decision",
            campaign=campaign,
            display=f"未知的待决定事项：{decision}",
        )
    if campaign.pending_decision != decision:
        return DecisionResult(
            decision=decision,
            status="not_pending",
            campaign=campaign,
            display=f"当前没有待决定的「{DECISION_LABELS.get(decision, decision)}」",
        )
    if not user_approved:
        if decision == ACCEPT_SHORT_LIST:
            notice = (
                f"「{accept_short_list_label(campaign)}」未获批准。"
                "没有把不合适或待确认的人改成合适，也没有写草稿。"
            )
        elif decision == SAVE_SELECTION:
            notice = (
                f"「{save_selection_label(campaign)}」未获批准，活动名单未改动。"
            )
        elif decision == EXCLUDE_CREATOR:
            notice = (
                f"「{exclude_creator_label(campaign)}」未获批准，活动名单未改动。"
            )
        elif decision == CONFIRM_CHANNEL:
            notice = (
                f"「{confirm_channel_label(campaign)}」未获批准，未写入渠道。"
            )
        elif decision == SAVE_DRAFTS:
            notice = (
                f"「{save_drafts_label(campaign)}」未获批准，草稿未写入。"
            )
        elif decision == APPROVE_DRAFT:
            notice = (
                f"「{approve_draft_label(campaign)}」未获批准，草稿状态未改。"
            )
        elif decision == REJECT_DRAFT:
            notice = (
                f"「{reject_draft_label(campaign)}」未获批准，草稿状态未改。"
            )
        elif decision == SAVE_FOLLOW_UP:
            notice = (
                f"「{save_follow_up_label(campaign)}」未获批准，跟进未写入。"
            )
        elif decision == NOTE_FOLLOW_UP:
            notice = (
                f"「{note_follow_up_label(campaign)}」未获批准，跟进状态未改。"
            )
        else:
            notice = (
                f"「{DECISION_LABELS.get(decision, decision)}」未获批准，未做任何改动。"
                "你可以在对话里直接补充缺少的字段。"
            )
        return DecisionResult(
            decision=decision,
            status="approval_required",
            campaign=campaign,
            display=notice,
        )
    updated, display = handler(campaign)
    return DecisionResult(
        decision=decision,
        status="applied",
        campaign=updated.model_copy(update={"pending_decision": None}),
        display=display,
    )


@register_decision(CONFIRM_ASSUMPTIONS)
def confirm_assumptions(campaign: Campaign) -> tuple[Campaign, str]:
    goal = apply_confirm_assumptions(campaign.parsed_goal)
    model_name = campaign.goal_model_name or "unknown"
    updated = campaign.model_copy(
        update={
            "parsed_goal": goal,
            "goal_status": "PARSED",
            "goal_fingerprint": fingerprint_goal(goal),
            "goal_origin": campaign.goal_origin
            or (GOAL_ORIGIN if campaign.parsed_goal is not None else None),
        }
    )
    return updated, f"已按假设确认。{goal_summary(goal, model_name)}"


@register_decision(ACCEPT_SHORT_LIST)
def accept_short_list(campaign: Campaign) -> tuple[Campaign, str]:
    n = accept_fit_count(campaign)
    updated = campaign.model_copy(update={"stage": "CANDIDATES_READY"})
    return updated, f"已接受当前合格 {n} 位，少于目标人数。不会把不合适或待确认的人改成合适。"


@register_decision(SAVE_SELECTION)
def save_selection(campaign: Campaign) -> tuple[Campaign, str]:
    return apply_save_selection(campaign, pending_creator_ids(campaign))


@register_decision(EXCLUDE_CREATOR)
def exclude_creator(campaign: Campaign) -> tuple[Campaign, str]:
    ids = pending_creator_ids(campaign)
    creator_id = ids[0] if ids else ""
    return apply_exclude_creator(campaign, creator_id)


@register_decision(CONFIRM_CHANNEL)
def confirm_channel(campaign: Campaign) -> tuple[Campaign, str]:
    payload = campaign.pending_payload or {}
    return apply_confirm_channel(
        campaign,
        str(payload.get("creator_id") or ""),
        str(payload.get("channel") or ""),
    )


@register_decision(SAVE_DRAFTS)
def save_drafts(campaign: Campaign) -> tuple[Campaign, str]:
    return apply_save_drafts(campaign)


@register_decision(APPROVE_DRAFT)
def approve_draft(campaign: Campaign) -> tuple[Campaign, str]:
    payload = campaign.pending_payload or {}
    return apply_approve_draft(campaign, str(payload.get("draft_id") or ""))


@register_decision(REJECT_DRAFT)
def reject_draft(campaign: Campaign) -> tuple[Campaign, str]:
    payload = campaign.pending_payload or {}
    return apply_reject_draft(campaign, str(payload.get("draft_id") or ""))


@register_decision(SAVE_FOLLOW_UP)
def save_follow_up(campaign: Campaign) -> tuple[Campaign, str]:
    return apply_save_follow_up(campaign)


@register_decision(NOTE_FOLLOW_UP)
def note_follow_up(campaign: Campaign) -> tuple[Campaign, str]:
    payload = campaign.pending_payload or {}
    return apply_note_follow_up(campaign, str(payload.get("follow_up_id") or ""))
