"""Audience-unknown display and the rule that blocks automatic fit (T08).

The model still judges. When the platform left `audience.status=unknown`,
this module turns a `fit` into `pending` and renders four「未知」fields.
It does not guess age, gender, region or language from the handle.
"""

from __future__ import annotations

from typing import Any

from collabpilot.campaign.hard_filter import RULE_LABEL
from collabpilot.campaign.mock_store import MOCK_ORIGIN, MergedCreator
from collabpilot.campaign.verdict import Verdict


UNKNOWN = "未知"
AUDIENCE_OVERRIDE = "audience_unknown"
AUDIENCE_FIELDS = ("age_range", "gender", "regions", "interests")
MOCK_LABEL = "[MOCK]"
OVERRIDE_LABELS = {
    AUDIENCE_OVERRIDE: "受众未知",
    "gpm": "GPM 未知",
    "audience": "受众未知",
}


def audience_of(creator: MergedCreator) -> dict[str, Any]:
    for _, account in creator.accounts():
        audience = account.get("audience") or {}
        if audience.get("status") == "unknown":
            return audience
    _, account = creator.accounts()[0] if creator.accounts() else (None, {})
    return (account or {}).get("audience") or {}


def audience_is_unknown(audience: dict[str, Any] | None) -> bool:
    return (audience or {}).get("status") == "unknown"


def _cell(value: Any) -> str:
    if value is None or value == [] or value == "" or value == 0 or value == "不限":
        return UNKNOWN
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or UNKNOWN
    return str(value)


def audience_view(audience: dict[str, Any] | None) -> dict[str, Any]:
    """Frontend-only view. Nulls become the string「未知」, never empty."""
    source = MOCK_LABEL
    unknown = audience_is_unknown(audience)
    values = {
        field: UNKNOWN if unknown else _cell((audience or {}).get(field))
        for field in AUDIENCE_FIELDS
    }
    return {
        **values,
        "status": (audience or {}).get("status"),
        "note": (audience or {}).get("note"),
        "source": source,
        "data_origin": MOCK_ORIGIN,
        "override_source": RULE_LABEL if unknown else None,
        "unknown": unknown,
    }


def apply_audience_overrides(
    verdicts: list[Verdict], candidates: dict[str, MergedCreator]
) -> list[Verdict]:
    return [
        enforce_audience_unknown(item, audience_of(candidates[item.creator_id]))
        if item.creator_id in candidates
        else item
        for item in verdicts
    ]


def fit_creators(campaign) -> list[str]:
    from collabpilot.campaign.topic_match import fit_creator_ids

    return fit_creator_ids(campaign)


def enforce_audience_unknown(verdict: Verdict, audience: dict[str, Any] | None) -> Verdict:
    """Unknown audience cannot stay `fit`. Rank is cleared; GPM is irrelevant."""
    if not audience_is_unknown(audience) or verdict.decision != "fit":
        return verdict
    unknowns = list(verdict.unknowns)
    if "audience" not in unknowns:
        unknowns.append("audience")
    return verdict.model_copy(
        update={
            "decision": "pending",
            "unknowns": unknowns,
            "rank": None,
            "rule_override": AUDIENCE_OVERRIDE,
        }
    )


def pending_reason(verdict: Verdict) -> str:
    if verdict.rule_override:
        return OVERRIDE_LABELS.get(verdict.rule_override, verdict.rule_override)
    if "audience" in verdict.unknowns:
        return OVERRIDE_LABELS["audience"]
    return verdict.reasons[0]


def pending_creators(campaign) -> list[dict[str, Any]]:
    from collabpilot.campaign.goal import Campaign

    assert isinstance(campaign, Campaign)
    items: list[dict[str, Any]] = []
    for verdict in campaign.verdicts or []:
        if verdict.decision != "pending":
            continue
        items.append(
            {
                "creator_id": verdict.creator_id,
                "decision": "待确认",
                "pending_reason": pending_reason(verdict),
                "rule_override": verdict.rule_override,
                "source": RULE_LABEL if verdict.rule_override else "[LLM]",
            }
        )
    return items


def audience_badge(verdict: Verdict) -> str:
    if verdict.rule_override == AUDIENCE_OVERRIDE or (
        verdict.decision == "pending" and "audience" in verdict.unknowns
    ):
        return "受众未知"
    return ""
