"""`save_follow_up` / `note_follow_up`: persist or note a follow-up. Never sends."""

from __future__ import annotations

from typing import Any

from collabpilot.campaign.follow_up import (
    FollowUp,
    apply_note_follow_up,
    apply_save_follow_up,
    queue_note_follow_up,
    queue_save_follow_up,
)
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


class SaveFollowUpTool(Tool):
    name = "save_follow_up"
    description = (
        "把已生成的跟进事项写入活动，状态为 waiting_user。"
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
        raw = (
            payload.get("follow_up")
            if campaign.pending_decision == "save_follow_up"
            else None
        )
        if not raw:
            return ToolResult(
                ok=False,
                error_code="follow_up_not_ready",
                display="还没有通过校验的跟进事项可保存。",
            )
        follow_up = FollowUp.model_validate(raw)
        if not context.user_approved:
            queued = queue_save_follow_up(campaign, follow_up)
            self.campaigns.save(queued)
            return ToolResult(
                ok=False,
                error_code="approval_required",
                display="记录跟进需要你批准，尚未写入。",
                data={"follow_ups": []},
            )
        updated, display = apply_save_follow_up(campaign, follow_up)
        self.campaigns.save(updated)
        return ToolResult(
            ok=True,
            data={"follow_ups": updated.follow_ups, "stage": updated.stage},
            display=display,
        )


class NoteFollowUpTool(Tool):
    name = "note_follow_up"
    description = "把一条跟进标为已记下。需要用户批准。不会发送。"
    risk_level = "write"
    input_schema = {
        "type": "object",
        "properties": {"follow_up_id": {"type": "string"}},
        "required": ["follow_up_id"],
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        follow_up_id = str(arguments.get("follow_up_id") or "").strip()
        if not follow_up_id:
            return ToolResult(
                ok=False,
                error_code="follow_up_id_required",
                display="缺少 follow_up_id",
            )
        if not context.user_approved:
            queued = queue_note_follow_up(campaign, follow_up_id)
            self.campaigns.save(queued)
            return ToolResult(
                ok=False,
                error_code="approval_required",
                display="记下跟进需要你确认，状态未改。",
            )
        updated, display = apply_note_follow_up(campaign, follow_up_id)
        self.campaigns.save(updated)
        return ToolResult(
            ok=True, data={"follow_ups": updated.follow_ups}, display=display
        )
