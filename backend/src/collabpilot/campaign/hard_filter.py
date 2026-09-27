"""Rule-based exclusion (T04). No model, no oracle fields.

Reads only ``cooperation_history[].is_current_brand`` and each account's
platform. Own-brand exclusion follows the parsed goal: default on, off when
the user explicitly allows recontacting past collaborators.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from collabpilot.campaign.mock_store import MergedCreator, Platform


RULE_ORIGIN = "rule"
RULE_LABEL = "[RULE]"
RemovalReason = Literal["own_brand_cooperated", "platform_mismatch"]
REASON_LABELS: dict[str, str] = {
    "own_brand_cooperated": "已合作本品牌",
    "platform_mismatch": "平台不在目标内",
}


class CooperationEvidence(BaseModel):
    cooperation_id: str | None
    brand_name: str | None
    content_published_at: str | None
    platform: str | None = None


class KeptCreator(BaseModel):
    creator_id: str
    display_name: str
    platforms: list[Platform]
    account_ids: list[str]


class RemovedCreator(BaseModel):
    creator_id: str
    display_name: str
    reason: RemovalReason
    evidence: CooperationEvidence | None = None


class FilterOutcome(BaseModel):
    kept: list[KeptCreator]
    removed: list[RemovedCreator]
    data_origin: str = RULE_ORIGIN


def own_brand_cooperation(creator: MergedCreator) -> tuple[str, dict[str, Any]] | None:
    """First cooperation record with is_current_brand=true on any platform."""
    for platform, account in creator.accounts():
        for record in account.get("cooperation_history", []):
            if record.get("is_current_brand") is True:
                return platform, record
    return None


def hard_filter(
    merged: list[MergedCreator],
    platforms: list[Platform],
    *,
    exclude_own_brand: bool = True,
) -> tuple[list[KeptCreator], list[RemovedCreator]]:
    """own_brand_cooperated is checked first (when enabled), then platform_mismatch.
    Only the first matching reason is recorded per creator."""
    kept: list[KeptCreator] = []
    removed: list[RemovedCreator] = []
    for creator in merged:
        if exclude_own_brand:
            hit = own_brand_cooperation(creator)
            if hit is not None:
                platform, record = hit
                removed.append(
                    RemovedCreator(
                        creator_id=creator.creator_id,
                        display_name=creator.display_name,
                        reason="own_brand_cooperated",
                        evidence=CooperationEvidence(
                            cooperation_id=record.get("cooperation_id"),
                            brand_name=record.get("brand_name"),
                            content_published_at=record.get("content_published_at"),
                            platform=platform,
                        ),
                    )
                )
                continue
        matching = [
            (platform, account)
            for platform, account in creator.accounts()
            if platform in platforms
        ]
        if not matching:
            removed.append(
                RemovedCreator(
                    creator_id=creator.creator_id,
                    display_name=creator.display_name,
                    reason="platform_mismatch",
                )
            )
            continue
        kept.append(
            KeptCreator(
                creator_id=creator.creator_id,
                display_name=creator.display_name,
                platforms=[platform for platform, _ in matching],
                account_ids=[
                    f"{platform}:{account['handle']}" for platform, account in matching
                ],
            )
        )
    return kept, removed
