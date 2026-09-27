"""Save / exclude / recommend helpers (T09).

Pure functions plus the pending-payload labels. Persistence lives in the
campaign store; approval lives in ``decisions.py`` and the write tools.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from collabpilot.campaign.goal import Campaign, ParsedGoal


SAVE_SELECTION = "save_selection"
EXCLUDE_CREATOR = "exclude_creator"
ALREADY_SAVED = "已在名单中"
SKIP_TEMPLATE = (
    "已在名单中 {already_saved} 位，已排除 {excluded} 位，"
    "此前判定不符 {topic_rejected} 位，均未重复推荐"
)
ELSEWHERE_HINT = "位已在其他活动名单中"


class SkipCounts(BaseModel):
    already_saved: int = 0
    excluded: int = 0
    topic_rejected: int = 0

    @property
    def total(self) -> int:
        return self.already_saved + self.excluded + self.topic_rejected

    def note(self) -> str | None:
        if self.total <= 0:
            return None
        return SKIP_TEMPLATE.format(
            already_saved=self.already_saved,
            excluded=self.excluded,
            topic_rejected=self.topic_rejected,
        )


def fingerprint_goal(goal: ParsedGoal) -> str:
    """Normalize brand / headcount / platforms / criteria, then hash."""
    payload = {
        "brand": (goal.brand or "").strip().lower(),
        "target_count": goal.target_count,
        "platforms": sorted(goal.platforms),
        "inclusion_criteria": sorted(item.strip().lower() for item in goal.inclusion_criteria),
        "exclusion_criteria": sorted(item.strip().lower() for item in goal.exclusion_criteria),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def creator_display_name(campaign: Campaign, creator_id: str) -> str:
    if campaign.last_filter is not None:
        for item in campaign.last_filter.kept:
            if item.creator_id == creator_id:
                return item.display_name
    if campaign.last_search is not None:
        for item in campaign.last_search.creators:
            if item.creator_id == creator_id:
                return item.display_name
    return creator_id


def pending_creator_ids(campaign: Campaign) -> list[str]:
    payload = campaign.pending_payload or {}
    ids = payload.get("creator_ids")
    if isinstance(ids, list):
        return [str(item) for item in ids if str(item).strip()]
    creator_id = payload.get("creator_id")
    return [str(creator_id)] if creator_id else []


def save_selection_label(campaign: Campaign) -> str:
    ids = pending_creator_ids(campaign)
    names = "、".join(creator_display_name(campaign, creator_id) for creator_id in ids)
    suffix = f"：{names}" if names else ""
    return f"保存 {len(ids)} 位到活动{suffix}"


def exclude_creator_label(campaign: Campaign) -> str:
    ids = pending_creator_ids(campaign)
    name = creator_display_name(campaign, ids[0]) if ids else ""
    return f"排除 {name}" if name else "排除创作者"


def recommend(candidates: list[str], campaign: Campaign) -> tuple[list[str], SkipCounts]:
    """Drop saved / excluded / topic-rejected ids; count each skip class."""
    saved = set(campaign.saved_creator_ids)
    excluded = set(campaign.excluded_creator_ids)
    rejected = set(campaign.topic_rejected_ids)
    counts = SkipCounts()
    kept: list[str] = []
    for creator_id in candidates:
        if creator_id in saved:
            counts.already_saved += 1
            continue
        if creator_id in excluded:
            counts.excluded += 1
            continue
        if creator_id in rejected:
            counts.topic_rejected += 1
            continue
        kept.append(creator_id)
    return kept, counts


def apply_save_selection(campaign: Campaign, creator_ids: list[str]) -> tuple[Campaign, str]:
    """Union into ``saved_creator_ids``. Pending verdicts stay pending."""
    ordered: list[str] = []
    seen: set[str] = set()
    for creator_id in [*campaign.saved_creator_ids, *creator_ids]:
        if creator_id in seen:
            continue
        seen.add(creator_id)
        ordered.append(creator_id)
    already = [creator_id for creator_id in creator_ids if creator_id in set(campaign.saved_creator_ids)]
    pending_ids = {
        verdict.creator_id
        for verdict in campaign.verdicts or []
        if verdict.decision == "pending"
    }
    accepted = list(campaign.accepted_from_pending)
    for creator_id in creator_ids:
        if creator_id in pending_ids and creator_id not in accepted:
            accepted.append(creator_id)
    # Drop from excluded if the user is putting them back on the list.
    excluded = [item for item in campaign.excluded_creator_ids if item not in seen]
    updated = campaign.model_copy(
        update={
            "saved_creator_ids": ordered,
            "excluded_creator_ids": excluded,
            "accepted_from_pending": accepted,
            "stage": "SELECTED",
            "pending_payload": None,
        }
    )
    names = "、".join(creator_display_name(campaign, creator_id) for creator_id in creator_ids)
    display = f"已保存 {len(ordered)} 位到活动"
    if names:
        display = f"{display}：{names}"
    if already:
        display = f"{display}。{len(already)} 位{ALREADY_SAVED}"
    return updated, display


def apply_exclude_creator(campaign: Campaign, creator_id: str) -> tuple[Campaign, str]:
    saved = [item for item in campaign.saved_creator_ids if item != creator_id]
    excluded = list(campaign.excluded_creator_ids)
    if creator_id not in excluded:
        excluded.append(creator_id)
    accepted = [item for item in campaign.accepted_from_pending if item != creator_id]
    updated = campaign.model_copy(
        update={
            "saved_creator_ids": saved,
            "excluded_creator_ids": excluded,
            "accepted_from_pending": accepted,
            "pending_payload": None,
        }
    )
    name = creator_display_name(campaign, creator_id)
    return updated, f"已将 {name} 从活动名单移出并排除。"


def queue_save_selection(campaign: Campaign, creator_ids: list[str]) -> Campaign:
    unique: list[str] = []
    seen: set[str] = set()
    for creator_id in creator_ids:
        if creator_id in seen:
            continue
        seen.add(creator_id)
        unique.append(creator_id)
    return campaign.model_copy(
        update={
            "pending_decision": SAVE_SELECTION,
            "pending_payload": {"creator_ids": unique},
            "stage": "USER_REVIEW",
        }
    )


def queue_exclude_creator(campaign: Campaign, creator_id: str) -> Campaign:
    return campaign.model_copy(
        update={
            "pending_decision": EXCLUDE_CREATOR,
            "pending_payload": {"creator_id": creator_id, "creator_ids": [creator_id]},
        }
    )


def elsewhere_hint(count: int) -> str | None:
    if count <= 0:
        return None
    return f"另有 {count} {ELSEWHERE_HINT}，未自动排除。"


def skip_counts_dict(counts: SkipCounts) -> dict[str, int]:
    return counts.model_dump()


def skip_counts_of(campaign: Campaign) -> SkipCounts:
    raw: dict[str, Any] = campaign.skip_counts or {}
    return SkipCounts(
        already_saved=int(raw.get("already_saved") or 0),
        excluded=int(raw.get("excluded") or 0),
        topic_rejected=int(raw.get("topic_rejected") or 0),
    )


def skip_caption(campaign: Campaign | None) -> str | None:
    if campaign is None:
        return None
    return skip_counts_of(campaign).note()
