"""`approve_draft` / `reject_draft`: change one draft's status. Never sends."""

from __future__ import annotations

from typing import Any

from collabpilot.campaign.drafts import (
    APPROVE_DRAFT,
    REJECT_DRAFT,
    apply_approve_draft,
    apply_reject_draft,
    queue_review_draft,
)
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


class ApproveDraftTool(Tool):
    name = "approve_draft"
    description = "把一封草稿标为已批准。需要用户批准。不会发送。"
    risk_level = "write"
    input_schema = {
        "type": "object",
        "properties": {"draft_id": {"type": "string"}},
        "required": ["draft_id"],
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        draft_id = str(arguments.get("draft_id") or "").strip()
        if not draft_id:
            return ToolResult(ok=False, error_code="draft_id_required", display="缺少 draft_id")
        if not context.user_approved:
            queued = queue_review_draft(campaign, draft_id, APPROVE_DRAFT)
            self.campaigns.save(queued)
            return ToolResult(
                ok=False,
                error_code="approval_required",
                display="批准草稿需要你确认，状态未改。",
            )
        updated, display = apply_approve_draft(campaign, draft_id)
        self.campaigns.save(updated)
        return ToolResult(ok=True, data={"drafts": updated.drafts}, display=display)


class RejectDraftTool(Tool):
    name = "reject_draft"
    description = "把一封草稿标为已退回。需要用户批准。不会发送。"
    risk_level = "write"
    input_schema = {
        "type": "object",
        "properties": {"draft_id": {"type": "string"}},
        "required": ["draft_id"],
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        draft_id = str(arguments.get("draft_id") or "").strip()
        if not draft_id:
            return ToolResult(ok=False, error_code="draft_id_required", display="缺少 draft_id")
        if not context.user_approved:
            queued = queue_review_draft(campaign, draft_id, REJECT_DRAFT)
            self.campaigns.save(queued)
            return ToolResult(
                ok=False,
                error_code="approval_required",
                display="退回草稿需要你确认，状态未改。",
            )
        updated, display = apply_reject_draft(campaign, draft_id)
        self.campaigns.save(updated)
        return ToolResult(ok=True, data={"drafts": updated.drafts}, display=display)
