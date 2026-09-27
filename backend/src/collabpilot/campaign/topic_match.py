"""Topic-mismatch validation and lock (T06).

The model decides whether a keyword hit is actually about the product.
This module only checks self-consistency of that judgment, verifies the
quoted text against the creator's own posts, and locks mismatch creators
so later rounds do not re-judge or recommend them. No keyword blacklist.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import Campaign, TopicLock
from collabpilot.campaign.hard_filter import RULE_LABEL, RULE_ORIGIN
from collabpilot.campaign.mock_store import MergedCreator
from collabpilot.campaign.verdict import LLM_LABEL, Verdict


QUOTE_MAX_CHARS = 80
TOPIC_CONFLICT = "topic_conflict"
QUOTE_NOT_FOUND = "quote_not_found"
LOCKED_TEXT = "已锁定，不再推荐"
TopicErrorCode = Literal["topic_conflict", "quote_not_found"]


class TopicRejected(BaseModel):
    creator_id: str
    error_code: TopicErrorCode
    detail: str = ""


class TopicBatch(BaseModel):
    accepted: list[Verdict]
    rejected: list[TopicRejected] = Field(default_factory=list)


def cited_posts(creator: MergedCreator, evidence_ids: list[str]) -> list[dict]:
    wanted = set(evidence_ids)
    return [post for post in creator.posts() if post.get("post_id") in wanted]


def matching_post_ids(creator: MergedCreator, evidence_ids: list[str], quote: str) -> list[str]:
    return [
        post["post_id"]
        for post in cited_posts(creator, evidence_ids)
        if quote and quote in mock_store.post_text(post)
    ]


def quoted_post_id(creator: MergedCreator, verdict: Verdict) -> str | None:
    if not verdict.quote:
        return None
    hits = matching_post_ids(creator, verdict.evidence_ids, verdict.quote)
    return hits[0] if hits else None


def validate_topic_verdicts(
    verdicts: list[Verdict], merged_creators: dict[str, MergedCreator]
) -> TopicBatch:
    """Drop internally inconsistent mismatch / unclear judgments.

    ``topic_match=mismatch`` requires ``decision=unfit``, a non-empty
    ``mismatch_topic``, and a quote of at most 80 characters that is a
    substring of a cited ``recent_posts`` title or caption. ``unclear``
    cannot be ``fit``. Failures do not enter the candidate list.
    """
    accepted: list[Verdict] = []
    rejected: list[TopicRejected] = []
    for verdict in verdicts:
        creator = merged_creators.get(verdict.creator_id)
        if verdict.topic_match == "unclear" and verdict.decision == "fit":
            rejected.append(
                TopicRejected(
                    creator_id=verdict.creator_id,
                    error_code=TOPIC_CONFLICT,
                    detail="topic_match=unclear 时 decision 只能是 pending 或 unfit",
                )
            )
            continue
        if verdict.topic_match != "mismatch":
            accepted.append(verdict)
            continue
        if verdict.decision != "unfit":
            rejected.append(
                TopicRejected(
                    creator_id=verdict.creator_id,
                    error_code=TOPIC_CONFLICT,
                    detail="topic_match=mismatch 必须 decision=unfit",
                )
            )
            continue
        topic = (verdict.mismatch_topic or "").strip()
        quote = verdict.quote or ""
        posts = cited_posts(creator, verdict.evidence_ids) if creator is not None else []
        if (
            not topic
            or not quote
            or len(quote) > QUOTE_MAX_CHARS
            or not posts
            or not matching_post_ids(creator, verdict.evidence_ids, quote)
        ):
            rejected.append(
                TopicRejected(
                    creator_id=verdict.creator_id,
                    error_code=QUOTE_NOT_FOUND,
                    detail="mismatch 需要非空 mismatch_topic，以及属于本创作者帖子原文的 quote（≤80 字）",
                )
            )
            continue
        accepted.append(verdict)
    return TopicBatch(accepted=accepted, rejected=rejected)


def lock_topic_rejections(campaign: Campaign, accepted: list[Verdict]) -> Campaign:
    """Append mismatch creator ids to ``topic_rejected_ids`` with a rule lock."""
    locked = list(campaign.topic_rejected_ids)
    locks = list(campaign.topic_locks)
    known = set(locked)
    creators = mock_store.load()
    for verdict in accepted:
        if verdict.topic_match != "mismatch" or verdict.creator_id in known:
            continue
        creator = creators.get(verdict.creator_id)
        locked.append(verdict.creator_id)
        known.add(verdict.creator_id)
        locks.append(
            TopicLock(
                creator_id=verdict.creator_id,
                mismatch_topic=verdict.mismatch_topic,
                quote=verdict.quote,
                quoted_post_id=quoted_post_id(creator, verdict) if creator else None,
                rule=True,
                data_origin=RULE_ORIGIN,
            )
        )
    return campaign.model_copy(update={"topic_rejected_ids": locked, "topic_locks": locks})


def ids_excluded_from_judgment(campaign: Campaign) -> set[str]:
    """Locked mismatch ids plus T04 own-brand cooperations. Never re-judge."""
    excluded = set(campaign.topic_rejected_ids)
    if campaign.last_filter is not None:
        excluded |= {
            item.creator_id
            for item in campaign.last_filter.removed
            if item.reason == "own_brand_cooperated"
        }
    return excluded


def drop_locked_ids(creator_ids: list[str], rejected_ids: list[str]) -> tuple[list[str], int]:
    rejected = set(rejected_ids)
    kept = [creator_id for creator_id in creator_ids if creator_id not in rejected]
    return kept, len(creator_ids) - len(kept)


def fit_creator_ids(campaign: Campaign) -> list[str]:
    """Final fit list: model ``fit`` minus locked mismatch ids. GPM is ignored."""
    rejected = set(campaign.topic_rejected_ids)
    return [
        verdict.creator_id
        for verdict in campaign.verdicts or []
        if verdict.decision == "fit" and verdict.creator_id not in rejected
    ]


def skipped_locked_note(count: int) -> str | None:
    if count <= 0:
        return None
    return f"已有 {count} 位此前判定不符，未重复评估。"


def locked_rule_note(count: int) -> str | None:
    if count <= 0:
        return None
    return f"{RULE_LABEL} {LOCKED_TEXT}：{count} 位。"


def rejudge_note(rejected: list[TopicRejected]) -> str | None:
    if not rejected:
        return None
    names = "、".join(f"{item.creator_id}（{item.error_code}）" for item in rejected)
    return f"以下创作者的主题判断未通过校验，需要重新判断：{names}。"


def topic_badge(verdict: Verdict) -> str:
    if verdict.topic_match != "mismatch" or not verdict.mismatch_topic:
        return ""
    return f"主题不符：{verdict.mismatch_topic}"


def lock_for(campaign: Campaign | None, creator_id: str) -> TopicLock | None:
    if campaign is None:
        return None
    return next((item for item in campaign.topic_locks if item.creator_id == creator_id), None)


# Labels used by the workbench / evidence panel.
JUDGMENT_SOURCE = LLM_LABEL
LOCK_SOURCE = RULE_LABEL
