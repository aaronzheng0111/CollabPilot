"""`save_drafts`: persist three pending_review drafts after user approval (T10)."""

from __future__ import annotations

from typing import Any

from collabpilot.campaign.drafts import (
    Draft,
    apply_save_drafts,
    queue_save_drafts,
)
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


class SaveDraftsTool(Tool):
    name = "save_drafts"
    description = (
        "把已生成的 3 封邀请草稿写入活动，状态为 pending_review。"
        "需要用户批准。不会发送私信或邮件。"
    )
    risk_level = "write"
    input_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        del arguments
        campaign = self.campaigns.get(context.session_id)
        payload = campaign.pending_payload or {}
        raw = payload.get("drafts") if campaign.pending_decision == "save_drafts" else None
        if not raw:
            return ToolResult(
                ok=False,
                error_code="drafts_not_ready",
                display="还没有通过校验的草稿可保存。",
            )
        drafts = [Draft.model_validate(item) for item in raw]
        if not context.user_approved:
            queued = queue_save_drafts(campaign, drafts)
            self.campaigns.save(queued)
            return ToolResult(
                ok=False,
                error_code="approval_required",
                display="保存草稿需要你批准，尚未写入。",
                data={"drafts": []},
            )
        updated, display = apply_save_drafts(campaign, drafts)
        self.campaigns.save(updated)
        return ToolResult(
            ok=True,
            data={"drafts": updated.drafts, "stage": updated.stage},
            display=display,
        )
