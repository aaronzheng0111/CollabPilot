"""Read-only projections of the campaign record for the Streamlit shell.

The main table shows the rows of the most recent successful tool result
(PLAN.md「左表何时变化」). The frontend only renders what comes out of here;
it never reads ``data/mock`` or re-implements a rule.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from collabpilot.campaign import mock_store
from collabpilot.campaign.audience import (
    audience_badge,
    audience_of,
    audience_view as audience_payload,
    pending_creators,
)
from collabpilot.campaign.goal import Campaign
from collabpilot.campaign.hard_filter import REASON_LABELS, RULE_LABEL
from collabpilot.campaign.selection import skip_caption as selection_skip_caption
from collabpilot.campaign.channels import (
    CHANNEL_LABELS,
    available_channels_from_contact,
    channel_label,
    list_contacts,
    pick_channel,
)
from collabpilot.campaign.drafts import (
    NO_CHANNEL_DRAFT_TEXT,
    can_generate_drafts,
    draft_card_rows,
    pending_review_drafts,
)
from collabpilot.campaign.follow_up import follow_up_table_rows, note_row_label, waiting_user_follow_ups
from collabpilot.campaign.topic_match import (
    JUDGMENT_SOURCE,
    LOCK_SOURCE,
    LOCKED_TEXT,
    lock_for,
    quoted_post_id,
    topic_badge,
)
from collabpilot.campaign.verdict import (
    DECISION_LABELS,
    LLM_LABEL,
    Verdict,
    evidence_excerpts,
    sort_verdicts,
)


MOCK_LABEL = "[MOCK]"
CATALOG_CAPTION = "示例达人"
CATALOG_PAGE_SIZE = 12
DASH = "—"

# Browse / catalog columns shared by idle list and real search rows.
PROFILE_KEYS = (
    "followers",
    "category",
    "topics",
    "audience_summary",
    "region",
    "engagement",
    "contact",
    "last_post",
)


def _unique_join(values: list[str]) -> str:
    seen: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.append(text)
    return "、".join(seen) if seen else DASH


def creator_table_fields(
    creator: mock_store.MergedCreator | None = None,
    *,
    creator_id: str | None = None,
) -> dict[str, Any]:
    """Flat mock-profile cells for the left table. Missing → —."""
    if creator is None and creator_id is not None:
        creator = mock_store.load().get(creator_id)
    if creator is None:
        return {key: DASH for key in PROFILE_KEYS}

    followers: int | None = None
    categories: list[str] = []
    topics: list[str] = []
    regions: list[str] = []
    audience_ages: list[str] = []
    audience_unknown = False
    audience_known = False
    engagement: float | None = None
    contacts: list[str] = []
    last_age: int | None = None

    for _platform, account in creator.accounts():
        count = mock_store.follower_count(account)
        if count is not None:
            followers = max(followers or 0, count)
        profile = account.get("profile") or {}
        if profile.get("category"):
            categories.append(str(profile["category"]))
        if profile.get("region"):
            regions.append(str(profile["region"]))
        for topic in account.get("content_topics") or []:
            topics.append(str(topic))
        audience = account.get("audience") or {}
        status = audience.get("status")
        if status == "unknown":
            audience_unknown = True
        elif status == "known":
            audience_known = True
            if audience.get("age_range"):
                audience_ages.append(str(audience["age_range"]))
            for region in audience.get("regions") or []:
                regions.append(str(region))
        metrics = account.get("metrics") or {}
        rate = metrics.get("engagement_rate_30d")
        if rate is not None:
            engagement = max(engagement or 0.0, float(rate))
        for channel in available_channels_from_contact(account.get("contact") or {}):
            contacts.append(CHANNEL_LABELS.get(channel, channel))
        for post in account.get("recent_posts") or []:
            age = post.get("age_days")
            if age is not None:
                last_age = int(age) if last_age is None else min(last_age, int(age))

    if audience_unknown and not audience_known:
        audience_summary = "未知"
    elif audience_ages:
        audience_summary = _unique_join(audience_ages)
    elif audience_known:
        audience_summary = "已知"
    else:
        audience_summary = DASH

    return {
        "followers": f"{followers:,}" if followers is not None else DASH,
        "category": _unique_join(categories),
        "topics": _unique_join(topics),
        "audience_summary": audience_summary,
        "region": _unique_join(regions),
        "engagement": f"{engagement:.1%}" if engagement is not None else DASH,
        "contact": _unique_join(contacts),
        "last_post": f"{last_age}天前" if last_age is not None else DASH,
    }


def catalog_browse_rows() -> list[dict[str, Any]]:
    """Idle browse list from read-only mock creators — no fit/rank/decision."""
    rows: list[dict[str, Any]] = []
    for creator in mock_store.load().values():
        rows.append(
            {
                "display_name": creator.display_name,
                "platforms": "、".join(creator.platforms),
                **creator_table_fields(creator),
            }
        )
    return rows


def search_caption(campaign: Campaign | None) -> str | None:
    """`关键词 … · 窗口 30 天 · 粉丝门槛 无` for the line above the table."""
    if campaign is None or campaign.last_search is None:
        return None
    search = campaign.last_search
    threshold = "无" if search.min_followers is None else f"{search.min_followers:,}"
    return (
        f"关键词 {'、'.join(search.keywords)} · 窗口 {search.window_days} 天 · "
        f"粉丝门槛 {threshold}"
    )


def skip_caption(campaign: Campaign | None) -> str | None:
    return selection_skip_caption(campaign)


def main_table_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    if campaign is None or campaign.goal_status == "CLARIFYING":
        return []
    if campaign.last_filter is not None and campaign.verdicts is not None:
        return verdict_rows(campaign)
    if campaign.last_filter is not None:
        return [
            {
                "creator_id": item.creator_id,
                "display_name": item.display_name,
                "platforms": "、".join(item.platforms),
                **creator_table_fields(creator_id=item.creator_id),
                "filter": "kept",
                "source": f"{MOCK_LABEL} {RULE_LABEL}",
            }
            for item in campaign.last_filter.kept
        ]
    if campaign.last_search is not None:
        return [
            {
                "creator_id": item.creator_id,
                "display_name": item.display_name,
                "platforms": "、".join(item.platforms),
                **creator_table_fields(creator_id=item.creator_id),
                "source": MOCK_LABEL,
            }
            for item in campaign.last_search.creators
        ]
    return []


def verdict_rows(campaign: Campaign) -> list[dict[str, Any]]:
    """Kept creators with `decision` / `rank`: fit by rank first, then
    pending, then unfit; creators whose verdict was rejected come last."""
    assert campaign.last_filter is not None
    kept = {item.creator_id: item for item in campaign.last_filter.kept}
    ordered = sort_verdicts(campaign.verdicts or [])
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    locked = set(campaign.topic_rejected_ids)
    saved = set(campaign.saved_creator_ids)
    show_saved = bool(saved)
    creators = mock_store.load()
    for verdict in ordered:
        item = kept.get(verdict.creator_id)
        if item is None:
            continue
        seen.add(verdict.creator_id)
        can_select = verdict.decision in ("fit", "pending") and verdict.creator_id not in locked
        row = {
            "creator_id": item.creator_id,
            "display_name": item.display_name,
            "platforms": "、".join(item.platforms),
            **creator_table_fields(creator_id=item.creator_id),
            "decision": DECISION_LABELS[verdict.decision],
            "rank": verdict.rank,
            "topic": topic_badge(verdict),
            "audience": audience_badge(verdict),
            "选中": verdict.decision == "fit" and can_select,
            "can_select": can_select,
            "source": f"{MOCK_LABEL} {RULE_LABEL} {LLM_LABEL}",
        }
        if show_saved:
            row["saved"] = verdict.creator_id in saved
        auto = pick_channel(creators.get(verdict.creator_id))
        confirmed = campaign.confirmed_channels.get(verdict.creator_id)
        row["channel"] = channel_label(confirmed or auto) or NO_CHANNEL_DRAFT_TEXT
        rows.append(row)
    for item in campaign.last_filter.kept:
        if item.creator_id not in seen:
            row = {
                "creator_id": item.creator_id,
                "display_name": item.display_name,
                "platforms": "、".join(item.platforms),
                **creator_table_fields(creator_id=item.creator_id),
                "decision": "—",
                "rank": None,
                "topic": "",
                "audience": "",
                "选中": False,
                "can_select": False,
                "source": f"{MOCK_LABEL} {RULE_LABEL}",
            }
            if show_saved:
                row["saved"] = item.creator_id in saved
            auto = pick_channel(creators.get(item.creator_id))
            confirmed = campaign.confirmed_channels.get(item.creator_id)
            row["channel"] = channel_label(confirmed or auto) or NO_CHANNEL_DRAFT_TEXT
            rows.append(row)
    return rows


def verdict_for(campaign: Campaign | None, creator_id: str) -> Verdict | None:
    if campaign is None or not campaign.verdicts:
        return None
    return next((item for item in campaign.verdicts if item.creator_id == creator_id), None)


def evidence_view(campaign: Campaign | None, creator_id: str) -> dict[str, Any] | None:
    """Everything the「判断依据」panel shows for one creator: reasons, cited
    post text with age_days, recency, unknowns and the model name."""
    verdict = verdict_for(campaign, creator_id)
    creator = mock_store.load().get(creator_id)
    if verdict is None or creator is None:
        return None
    lock = lock_for(campaign, creator_id)
    post_id = (lock.quoted_post_id if lock else None) or quoted_post_id(creator, verdict)
    return {
        "creator_id": creator_id,
        "display_name": creator.display_name,
        "decision": verdict.decision,
        "decision_label": DECISION_LABELS[verdict.decision],
        "rank": verdict.rank,
        "reasons": verdict.reasons,
        "excerpts": evidence_excerpts(creator, verdict.evidence_ids),
        "related_post_ids": verdict.related_post_ids,
        "recency": verdict.recency.model_dump() if verdict.recency else None,
        "unknowns": verdict.unknowns,
        "topic_match": verdict.topic_match,
        "mismatch_topic": verdict.mismatch_topic,
        "topic_badge": topic_badge(verdict),
        "quote": verdict.quote,
        "quoted_post_id": post_id,
        "locked": lock is not None or creator_id in (campaign.topic_rejected_ids if campaign else []),
        "lock_text": LOCKED_TEXT,
        "lock_source": LOCK_SOURCE,
        "judgment_source": JUDGMENT_SOURCE,
        "rule_override": verdict.rule_override,
        "audience_badge": audience_badge(verdict),
        "audience": audience_payload(audience_of(creator)),
        "model_name": verdict.model_name,
        "data_origin": verdict.data_origin,
        "can_restore": False,
    }


def pending_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    if campaign is None:
        return []
    return pending_creators(campaign)


def progress_view(campaign: Campaign | None) -> dict[str, Any] | None:
    """次级区「进度」：每轮一行，加上模型策略变更表。"""
    if campaign is None or not campaign.search_rounds:
        return None
    from collabpilot.campaign.retry import STAGE_LABELS

    strategy = campaign.retry_strategy
    return {
        "stage": campaign.stage,
        "stage_label": STAGE_LABELS.get(campaign.stage, campaign.stage),
        "rounds": [
            {
                "index": item.index,
                "keywords": "、".join(item.keywords),
                "window_days": item.window_days,
                "min_followers": item.min_followers,
                "fit_count": item.fit_count,
                "gap": item.gap,
                "qualified": f"{item.fit_count}/{item.fit_count + item.gap}" if item.fit_count + item.gap else f"{item.fit_count}/—",
            }
            for item in campaign.search_rounds
        ],
        "changes": (
            [
                {
                    "field": change.field,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "reason": strategy.reason,
                }
                for change in strategy.changes
            ]
            if strategy
            else []
        ),
        "strategy_model": strategy.model_name if strategy else None,
        "strategy_origin": strategy.data_origin if strategy else None,
        "drafts": list(campaign.drafts),
    }


def excluded_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    """Rows for the collapsible「已排除」table: reason in Chinese plus the
    cooperation record the rule relied on."""
    if campaign is None or campaign.last_filter is None:
        return []
    return [
        {
            "creator_id": item.creator_id,
            "display_name": item.display_name,
            "reason": REASON_LABELS[item.reason],
            "brand_name": item.evidence.brand_name if item.evidence else None,
            "content_published_at": (
                item.evidence.content_published_at if item.evidence else None
            ),
            "source": RULE_LABEL,
        }
        for item in campaign.last_filter.removed
    ]


def channel_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    """次级区「沟通渠道」：已保存创作者，每平台一行，全部来自 mock contact。"""
    if campaign is None or not campaign.saved_creator_ids:
        return []
    rows = []
    for view in list_contacts(campaign.saved_creator_ids):
        rows.append(
            {
                "creator_id": view.creator_id,
                "display_name": view.display_name,
                "platform": view.platform,
                "preferred_channel": view.preferred_channel,
                "preferred_label": view.preferred_label,
                "dm_available": view.dm_available,
                "email": view.email,
                "email_display": view.email_display,
                "consent_status": view.consent_status,
                "consent_label": view.consent_label,
                "source": view.source,
                "can_confirm": view.can_confirm,
                "available_channels": view.available_channels,
                "available_labels": {
                    channel: channel_label(channel) for channel in view.available_channels
                },
                "confirmed": campaign.confirmed_channels.get(view.creator_id),
            }
        )
    return rows


def draft_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    """右栏「草稿」卡片：已保存，或 ``save_drafts`` 待批准的 payload。"""
    return draft_card_rows(campaign)


def drafts_ready(campaign: Campaign | None) -> bool:
    return can_generate_drafts(campaign)


def follow_up_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    """次级区「跟进」表数据。未保存的 pending 跟进不在这里。"""
    return follow_up_table_rows(campaign)


class WorkbenchState(BaseModel):
    """Read-only page snapshot. No writes, no extra rules."""

    campaign: Campaign | None = None
    goal_status: str | None = None
    stage: str | None = None
    parsed_goal: dict[str, Any] | None = None
    pending_decision: str | None = None
    pending_decisions: list[dict[str, Any]] = Field(default_factory=list)
    main_rows: list[dict[str, Any]] = Field(default_factory=list)
    search_caption: str | None = None
    skip_caption: str | None = None
    search_rounds: list[dict[str, Any]] = Field(default_factory=list)
    verdicts: list[dict[str, Any]] = Field(default_factory=list)
    progress: dict[str, Any] | None = None
    excluded_rows: list[dict[str, Any]] = Field(default_factory=list)
    pending_rows: list[dict[str, Any]] = Field(default_factory=list)
    channel_rows: list[dict[str, Any]] = Field(default_factory=list)
    draft_rows: list[dict[str, Any]] = Field(default_factory=list)
    drafts_ready: bool = False
    draft_error: str | None = None
    follow_up_rows: list[dict[str, Any]] = Field(default_factory=list)
    follow_error: str | None = None
    goal_model_name: str | None = None
    clarifying: bool = False


def pending_decision_rows(campaign: Campaign | None) -> list[dict[str, Any]]:
    if campaign is None:
        return []
    from collabpilot.campaign.decisions import decision_label

    rows: list[dict[str, Any]] = []
    if campaign.pending_decision:
        rows.append(
            {
                "decision": campaign.pending_decision,
                "label": decision_label(campaign),
            }
        )
    for draft in pending_review_drafts(campaign):
        rows.append(
            {
                "decision": "approve_draft",
                "label": f"审核草稿：{draft.creator_id}",
                "draft_id": draft.id,
            }
        )
    for item in waiting_user_follow_ups(campaign):
        rows.append(
            {
                "decision": "note_follow_up",
                "label": note_row_label(campaign, item),
                "follow_up_id": item.id,
            }
        )
    return rows


def build_workbench_state(campaign: Campaign | None) -> WorkbenchState:
    if campaign is None:
        return WorkbenchState(
            main_rows=catalog_browse_rows(),
            search_caption=CATALOG_CAPTION,
        )
    rows = main_table_rows(campaign)
    caption = search_caption(campaign)
    if not rows and campaign.goal_status != "CLARIFYING":
        rows = catalog_browse_rows()
        caption = CATALOG_CAPTION
    return WorkbenchState(
        campaign=campaign,
        goal_status=campaign.goal_status,
        stage=campaign.stage,
        parsed_goal=(
            campaign.parsed_goal.model_dump(mode="json")
            if campaign.parsed_goal is not None
            else None
        ),
        pending_decision=campaign.pending_decision,
        pending_decisions=pending_decision_rows(campaign),
        main_rows=rows,
        search_caption=caption,
        skip_caption=skip_caption(campaign),
        search_rounds=[item.model_dump(mode="json") for item in campaign.search_rounds],
        verdicts=[item.model_dump(mode="json") for item in (campaign.verdicts or [])],
        progress=progress_view(campaign),
        excluded_rows=excluded_rows(campaign),
        pending_rows=pending_rows(campaign),
        channel_rows=channel_rows(campaign),
        draft_rows=draft_rows(campaign),
        drafts_ready=drafts_ready(campaign),
        draft_error=campaign.draft_error,
        follow_up_rows=follow_up_rows(campaign),
        follow_error=campaign.follow_error,
        goal_model_name=campaign.goal_model_name,
        clarifying=campaign.goal_status == "CLARIFYING",
    )
