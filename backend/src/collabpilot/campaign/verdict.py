"""Verdict schema, validation, ordering and prompt payloads (T05).

Pure module: no model calls, no storage. The model returns ``Verdict[]`` as
a fenced JSON block; ``validate_verdicts`` checks every evidence id against
the creator's own posts / evidence, enforces the rank contract and computes
``recency``. Nothing here scores or ranks creators on its own.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from collabpilot.campaign import mock_store
from collabpilot.campaign.mock_store import BrandInfo, MergedCreator
from collabpilot.domain.errors import AgentError


VERDICT_ORIGIN = "real_model_output"
LLM_LABEL = "[LLM]"
EVALUATE_STEP = "evaluate_candidates"
Decision = Literal["fit", "unfit", "pending"]
TopicMatch = Literal["match", "mismatch", "unclear"]
DECISION_LABELS: dict[str, str] = {"fit": "合适", "pending": "待确认", "unfit": "不合适"}
DECISION_ORDER: dict[str, int] = {"fit": 0, "pending": 1, "unfit": 2}
CANDIDATES_HEADING = "【候选创作者】"


class ModelUnavailable(AgentError):
    code = "model_unavailable"


class Recency(BaseModel):
    """Computed by the application layer from `related_post_ids`, never by the model."""

    recent_related_count: int
    latest_related_age_days: int | None


class Verdict(BaseModel):
    creator_id: str
    decision: Decision
    reasons: list[str] = Field(min_length=1)
    evidence_ids: list[str]
    related_post_ids: list[str] = Field(default_factory=list)
    topic_match: TopicMatch = "unclear"
    mismatch_topic: str | None = None
    quote: str | None = None
    unknowns: list[str] = Field(default_factory=list)
    rank: int | None = None
    recency: Recency | None = None
    rule_override: str | None = None
    data_origin: Literal["real_model_output"] = VERDICT_ORIGIN
    model_name: str


class RawVerdict(BaseModel):
    """What the model must send. Anything else is a schema failure."""

    creator_id: str
    decision: Decision
    reasons: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    related_post_ids: list[str] = Field(default_factory=list)
    topic_match: TopicMatch = "unclear"
    mismatch_topic: str | None = None
    quote: str | None = None
    unknowns: list[str] = Field(default_factory=list)
    rank: int | None = None


RejectCode = Literal[
    "schema_invalid",
    "not_in_candidates",
    "evidence_not_found",
    "evidence_required",
    "topic_conflict",
    "quote_not_found",
]
BatchCode = Literal["verdicts_invalid", "rank_invalid"]


class RejectedVerdict(BaseModel):
    creator_id: str | None
    error_code: RejectCode
    detail: str = ""


class VerdictBatch(BaseModel):
    accepted: list[Verdict]
    rejected: list[RejectedVerdict] = Field(default_factory=list)
    error_code: BatchCode | None = None  # set → the whole batch is dropped

    @property
    def ok(self) -> bool:
        return self.error_code is None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _raw_items(raw: Any) -> list[Any] | None:
    if isinstance(raw, dict):
        raw = raw.get("verdicts")
    return raw if isinstance(raw, list) else None


def _post_age(creator: MergedCreator) -> dict[str, int | None]:
    return {post["post_id"]: post.get("age_days") for post in creator.posts()}


def compute_recency(
    creator: MergedCreator, related_post_ids: list[str], window_days: int
) -> Recency:
    ages = _post_age(creator)
    related = [ages[pid] for pid in related_post_ids if pid in ages and ages[pid] is not None]
    return Recency(
        recent_related_count=sum(1 for age in related if age <= window_days),
        latest_related_age_days=min(related) if related else None,
    )


def data_unknowns(creator: MergedCreator) -> list[str]:
    """Fields the creator's data genuinely lacks. Merged into the verdict so
    the UI shows「未知：gpm」even when the model forgot to list it."""
    unknowns: list[str] = []
    accounts = [account for _, account in creator.accounts()]
    if accounts and all(mock_store.gpm(account) is None for account in accounts):
        unknowns.append("gpm")
    if any(account.get("audience", {}).get("status") == "unknown" for account in accounts):
        unknowns.append("audience")
    return unknowns


def validate_verdicts(
    raw: Any,
    candidates: dict[str, MergedCreator],
    *,
    window_days: int,
    model_name: str,
) -> VerdictBatch:
    items = _raw_items(raw)
    if items is None:
        return VerdictBatch(accepted=[], error_code="verdicts_invalid")

    accepted: list[Verdict] = []
    rejected: list[RejectedVerdict] = []
    for item in items:
        try:
            parsed = RawVerdict.model_validate(item)
        except ValidationError as exc:
            creator_id = item.get("creator_id") if isinstance(item, dict) else None
            fields = ", ".join(str(error["loc"][0]) for error in exc.errors() if error["loc"])
            rejected.append(
                RejectedVerdict(creator_id=creator_id, error_code="schema_invalid", detail=fields)
            )
            continue
        creator = candidates.get(parsed.creator_id)
        if creator is None:
            rejected.append(
                RejectedVerdict(creator_id=parsed.creator_id, error_code="not_in_candidates")
            )
            continue
        known = creator.post_ids() | creator.evidence_ids()
        missing = [eid for eid in parsed.evidence_ids if eid not in known]
        missing += [pid for pid in parsed.related_post_ids if pid not in creator.post_ids()]
        if missing:
            rejected.append(
                RejectedVerdict(
                    creator_id=parsed.creator_id,
                    error_code="evidence_not_found",
                    detail=", ".join(missing),
                )
            )
            continue
        if parsed.decision == "fit" and (not parsed.evidence_ids or not parsed.related_post_ids):
            rejected.append(
                RejectedVerdict(
                    creator_id=parsed.creator_id,
                    error_code="evidence_required",
                    detail="fit 需要 evidence_ids 与 related_post_ids",
                )
            )
            continue
        if parsed.decision != "fit" and parsed.rank is not None:
            return VerdictBatch(accepted=[], rejected=rejected, error_code="rank_invalid")
        unknowns = list(parsed.unknowns)
        for field in data_unknowns(creator):
            if field not in unknowns:
                unknowns.append(field)
        accepted.append(
            Verdict(
                **parsed.model_dump(exclude={"unknowns"}),
                unknowns=unknowns,
                recency=compute_recency(creator, parsed.related_post_ids, window_days),
                model_name=model_name,
            )
        )

    ranks = [v.rank for v in accepted if v.decision == "fit"]
    if any(rank is None for rank in ranks) or sorted(ranks) != list(range(1, len(ranks) + 1)):  # type: ignore[type-var]
        return VerdictBatch(accepted=[], rejected=rejected, error_code="rank_invalid")
    return VerdictBatch(accepted=accepted, rejected=rejected)


def sort_verdicts(verdicts: list[Verdict]) -> list[Verdict]:
    """fit by rank ascending, then pending, then unfit (input order inside
    each group). No other scoring."""
    ordered = sorted(
        enumerate(verdicts),
        key=lambda pair: (
            DECISION_ORDER[pair[1].decision],
            pair[1].rank if pair[1].rank is not None else 0,
            pair[0],
        ),
    )
    return [verdict for _, verdict in ordered]


def renumber_fit_ranks(verdicts: list[Verdict]) -> list[Verdict]:
    """Reassign fit ranks 1..n in current sort order; non-fits keep rank None."""
    ordered = sort_verdicts(verdicts)
    rank = 0
    out: list[Verdict] = []
    for verdict in ordered:
        if verdict.decision == "fit":
            rank += 1
            out.append(verdict.model_copy(update={"rank": rank}))
        else:
            out.append(verdict.model_copy(update={"rank": None}))
    return out


def retain_prior_fits(
    previous: list[Verdict] | None,
    new: list[Verdict],
    kept_ids: list[str],
) -> list[Verdict]:
    """Keep prior ``fit`` rows still in the kept set when a later judgment demotes them.

    A fresh ``fit`` or a hard ``topic_match=mismatch`` unfit replaces the prior row.
    Prevents a flaky second-round batch from wiping the accept-card count to 0.
    """
    kept = set(kept_ids)
    by_id = {verdict.creator_id: verdict for verdict in new}
    for old in previous or []:
        if old.decision != "fit" or old.creator_id not in kept:
            continue
        current = by_id.get(old.creator_id)
        if current is None:
            by_id[old.creator_id] = old
            continue
        if current.decision == "fit":
            continue
        if current.topic_match == "mismatch":
            continue
        by_id[old.creator_id] = old
    return renumber_fit_ranks(list(by_id.values()))


# ---------------------------------------------------------------------------
# Prompt payloads
# ---------------------------------------------------------------------------


def candidate_payload(creator: MergedCreator) -> dict[str, Any]:
    """Compact, model-facing view of one creator. Only data the model may see."""
    accounts = []
    for platform, account in creator.accounts():
        metrics = account.get("metrics", {})
        accounts.append(
            {
                "platform": platform,
                "handle": account.get("handle"),
                "followers": mock_store.follower_count(account),
                "bio": mock_store.bio(account),
                "content_topics": account.get("content_topics", []),
                "audience": account.get("audience"),
                "gpm": mock_store.gpm(account),
                "gpm_origin": metrics.get("gpm_origin"),
                "engagement_rate_30d": metrics.get("engagement_rate_30d"),
                "posts": [
                    {
                        "post_id": post["post_id"],
                        "age_days": post.get("age_days"),
                        "text": mock_store.post_text(post),
                    }
                    for post in account.get("recent_posts", [])
                ],
                "evidence": [
                    {
                        "evidence_id": item.get("evidence_id"),
                        "evidence_type": item.get("evidence_type"),
                        "product_name": item.get("product_name"),
                        "text": item.get("evidence_text"),
                        "source_post_id": item.get("source_post_id"),
                    }
                    for item in account.get("product_usage_evidence", [])
                ],
                "cooperation": [
                    {
                        "brand_name": item.get("brand_name"),
                        "product": item.get("product"),
                        "is_current_brand": item.get("is_current_brand"),
                        "content_published_at": item.get("content_published_at"),
                    }
                    for item in account.get("cooperation_history", [])
                ],
            }
        )
    return {
        "creator_id": creator.creator_id,
        "display_name": creator.display_name,
        "platforms": creator.platforms,
        "accounts": accounts,
    }


def render_campaign_prompt(
    template: str,
    *,
    brand: BrandInfo,
    goal_brand: str | None,
    goal_product: str | None,
    target_audience: list[str],
    inclusion_criteria: list[str],
    exclusion_criteria: list[str],
    target_count: int | None,
    window_days: int,
    base_date: str | None = None,
) -> str:
    named_brand = (goal_brand or "").strip()
    use_catalog = bool(named_brand) and named_brand == brand.name
    exclusion_rules = list(
        dict.fromkeys([*exclusion_criteria, *(brand.exclusion_rules if use_catalog else [])])
    )
    audience = list(
        dict.fromkeys([*target_audience, *(brand.target_audience if use_catalog else [])])
    )
    features = brand.key_features if use_catalog else []
    display_brand = named_brand or "未指定"
    display_product = (goal_product or "").strip() or (
        brand.product if use_catalog else "未指定"
    )
    return (
        template.replace("{brand}", display_brand)
        .replace("{product}", display_product)
        .replace("{key_features}", "、".join(features) or "—")
        .replace("{exclusion_rules}", "；".join(exclusion_rules) or "—")
        .replace("{target_audience}", "、".join(audience) or "—")
        .replace("{inclusion_criteria}", "；".join(inclusion_criteria) or "—")
        .replace("{target_count}", str(target_count or "—"))
        .replace("{window_days}", str(window_days))
        .replace("{base_date}", base_date or mock_store.generated_at().date().isoformat())
    )


def render_candidates_message(candidates: list[MergedCreator]) -> str:
    payload = [candidate_payload(creator) for creator in candidates]
    return (
        f"{CANDIDATES_HEADING}共 {len(payload)} 位，每条帖子带 age_days（距基准日的天数）。\n"
        "```json\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n```\n"
        "请对以上每一位输出判断，只回复一个 ```json 代码块：{\"verdicts\": [Verdict, ...]}。"
    )


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def evidence_excerpts(creator: MergedCreator, evidence_ids: list[str]) -> list[dict[str, Any]]:
    """Original post text + age_days for each cited id (post id or evidence id)."""
    posts: dict[str, tuple[str, dict[str, Any]]] = {
        post["post_id"]: (platform, post)
        for platform, account in creator.accounts()
        for post in account.get("recent_posts", [])
    }
    evidence: dict[str, tuple[str, dict[str, Any]]] = {
        item["evidence_id"]: (platform, item)
        for platform, account in creator.accounts()
        for item in account.get("product_usage_evidence", [])
    }
    excerpts: list[dict[str, Any]] = []
    for cited in evidence_ids:
        if cited in posts:
            platform, post = posts[cited]
            excerpts.append(
                {
                    "id": cited,
                    "kind": "post",
                    "platform": platform,
                    "text": mock_store.post_text(post),
                    "age_days": post.get("age_days"),
                }
            )
        elif cited in evidence:
            platform, item = evidence[cited]
            source = posts.get(str(item.get("source_post_id")))
            excerpts.append(
                {
                    "id": cited,
                    "kind": "evidence",
                    "platform": platform,
                    "text": item.get("evidence_text"),
                    "age_days": source[1].get("age_days") if source else None,
                }
            )
    return excerpts
