"""`save_campaign_selection`: write saved_creator_ids after user approval (T09)."""

from __future__ import annotations

from typing import Any

from collabpilot.campaign.selection import apply_save_selection, queue_save_selection
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


class SaveCampaignSelectionTool(Tool):
    name = "save_campaign_selection"
    description = (
        "把勾选的创作者写入当前活动名单。需要用户确认（对话里回复「确认」"
        "或界面批准）后才真正写入，未确认时返回 approval_required。"
    )
    risk_level = "write"
    input_schema = {
        "type": "object",
        "properties": {
            "creator_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "要保存的 creator_id 列表。",
            }
        },
        "required": ["creator_ids"],
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        creator_ids = [str(item) for item in arguments.get("creator_ids") or [] if str(item).strip()]
        if not creator_ids:
            return ToolResult(ok=False, error_code="creator_ids_required", display="缺少 creator_ids")
        if not context.user_approved:
            queued = queue_save_selection(campaign, creator_ids)
            self.campaigns.save(queued)
            return ToolResult(
                ok=False,
                error_code="approval_required",
                display="保存名单需要你确认，活动名单尚未改动。",
                data={"saved_creator_ids": list(campaign.saved_creator_ids)},
            )
        updated, display = apply_save_selection(campaign, creator_ids)
        self.campaigns.save(updated)
        return ToolResult(
            ok=True,
            data={
                "saved_creator_ids": updated.saved_creator_ids,
                "stage": updated.stage,
                "accepted_from_pending": updated.accepted_from_pending,
            },
            display=display,
        )
