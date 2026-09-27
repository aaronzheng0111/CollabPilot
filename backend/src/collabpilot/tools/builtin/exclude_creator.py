"""`exclude_creator`: move a creator from saved to excluded after approval (T09)."""

from __future__ import annotations

from typing import Any

from collabpilot.campaign.selection import apply_exclude_creator, queue_exclude_creator
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


class ExcludeCreatorTool(Tool):
    name = "exclude_creator"
    description = (
        "把一位创作者从当前活动名单移到排除集合。需要用户确认后才执行。"
    )
    risk_level = "write"
    input_schema = {
        "type": "object",
        "properties": {
            "creator_id": {
                "type": "string",
                "description": "要排除的 creator_id。",
            }
        },
        "required": ["creator_id"],
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        creator_id = str(arguments.get("creator_id") or "").strip()
        if not creator_id:
            return ToolResult(ok=False, error_code="creator_id_required", display="缺少 creator_id")
        if not context.user_approved:
            queued = queue_exclude_creator(campaign, creator_id)
            self.campaigns.save(queued)
            return ToolResult(
                ok=False,
                error_code="approval_required",
                display="排除创作者需要你确认，活动名单尚未改动。",
                data={
                    "saved_creator_ids": list(campaign.saved_creator_ids),
                    "excluded_creator_ids": list(campaign.excluded_creator_ids),
                },
            )
        updated, display = apply_exclude_creator(campaign, creator_id)
        self.campaigns.save(updated)
        return ToolResult(
            ok=True,
            data={
                "saved_creator_ids": updated.saved_creator_ids,
                "excluded_creator_ids": updated.excluded_creator_ids,
            },
            display=display,
        )
