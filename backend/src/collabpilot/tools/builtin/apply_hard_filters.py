"""`apply_hard_filters`: rule-based exclusion of the last search result (T04)."""

from __future__ import annotations

from typing import Any

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import FilterRecord, should_exclude_own_brand
from collabpilot.campaign.hard_filter import RULE_LABEL, RULE_ORIGIN, REASON_LABELS, hard_filter
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


class ApplyHardFiltersTool(Tool):
    name = "apply_hard_filters"
    description = (
        "对最近一次 search_creators 的结果做规则过滤（[RULE]，不调用模型）："
        "默认去掉已与本品牌合作过的创作者（cooperation_history.is_current_brand=true）；"
        "若合作目标已写明可再次联系已合作/已联系账号，则保留这些人。"
        "同时去掉平台不在目标 platforms 内的创作者。creator_ids 省略时处理搜索结果里的全部创作者。"
    )
    risk_level = "read"
    input_schema = {
        "type": "object",
        "properties": {
            "creator_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要过滤的 creator_id，必须来自最近一次搜索结果；省略则为全部。",
            }
        },
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        if campaign.goal_status != "PARSED" or campaign.parsed_goal is None:
            return ToolResult(ok=False, error_code="goal_not_ready", display="合作目标尚未解析完成。")
        if campaign.last_search is None:
            return ToolResult(
                ok=False, error_code="search_required", display="请先调用 search_creators。"
            )
        searched = campaign.last_search.creator_ids
        requested = [str(item) for item in arguments.get("creator_ids") or []] or searched
        unknown = [creator_id for creator_id in requested if creator_id not in searched]
        if unknown:
            return ToolResult(
                ok=False,
                error_code="not_in_search",
                display=f"以下 id 不在最近一次搜索结果中：{', '.join(unknown)}",
                data={"not_in_search": unknown},
            )
        creators = mock_store.load()
        kept, removed = hard_filter(
            [creators[creator_id] for creator_id in requested],
            campaign.parsed_goal.platforms,
            exclude_own_brand=should_exclude_own_brand(campaign.parsed_goal),
        )
        kept_ids = {item.creator_id for item in kept}
        # Keep prior fits that remain in the new kept set so a later judgment can
        # retain them (round-2 must not wipe the accept-card count to 0).
        retained = [
            verdict
            for verdict in campaign.verdicts or []
            if verdict.decision == "fit" and verdict.creator_id in kept_ids
        ]
        self.campaigns.save(
            campaign.model_copy(
                update={
                    "stage": "EVALUATING",
                    "last_filter": FilterRecord(kept=kept, removed=removed),
                    "verdicts": retained or None,
                    "verdict_rejected": [],
                    "verdict_error": None,
                }
            )
        )
        reasons = "、".join(
            f"{item.creator_id}（{REASON_LABELS[item.reason]}）" for item in removed
        )
        return ToolResult(
            ok=True,
            data={
                "kept": [item.model_dump() for item in kept],
                "removed": [item.model_dump() for item in removed],
                "data_origin": RULE_ORIGIN,
                "platforms": campaign.parsed_goal.platforms,
            },
            display=(
                f"{RULE_LABEL} 保留 {len(kept)} 位，排除 {len(removed)} 位"
                + (f"：{reasons}" if reasons else "")
            ),
            metadata={"data_origin": RULE_ORIGIN},
        )
