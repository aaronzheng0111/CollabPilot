"""`confirm_channel`: record a user-approved outreach channel (T13). Never sends."""

from __future__ import annotations

from typing import Any

from collabpilot.campaign import mock_store
from collabpilot.campaign.channels import (
    CHANNEL_UNKNOWN,
    apply_confirm_channel,
    queue_confirm_channel,
    validate_channel,
)
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


class ConfirmChannelTool(Tool):
    name = "confirm_channel"
    description = (
        "确认用模拟资料里已有的渠道联系一位已保存创作者。"
        "需要用户批准。不会发送私信或邮件。"
    )
    risk_level = "write"
    input_schema = {
        "type": "object",
        "properties": {
            "creator_id": {"type": "string"},
            "channel": {
                "type": "string",
                "enum": ["tiktok_dm", "instagram_dm", "email"],
            },
        },
        "required": ["creator_id", "channel"],
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        creator_id = str(arguments.get("creator_id") or "").strip()
        channel = str(arguments.get("channel") or "").strip()
        if not creator_id or not channel:
            return ToolResult(
                ok=False, error_code="arguments_required", display="缺少 creator_id 或 channel"
            )
        creator = mock_store.load().get(creator_id)
        error = validate_channel(creator, channel)
        if error:
            display = (
                "资料中没有可用渠道，未写入确认。"
                if error == CHANNEL_UNKNOWN
                else "该渠道不在创作者资料上，未写入确认。"
            )
            return ToolResult(
                ok=False,
                error_code=error,
                display=display,
                data={"confirmed_channel": campaign.confirmed_channels.get(creator_id)},
            )
        if not context.user_approved:
            queued = queue_confirm_channel(campaign, creator_id, channel)
            self.campaigns.save(queued)
            return ToolResult(
                ok=False,
                error_code="approval_required",
                display="确认渠道需要你批准，尚未写入。",
                data={"confirmed_channel": campaign.confirmed_channels.get(creator_id)},
            )
        updated, display = apply_confirm_channel(campaign, creator_id, channel)
        self.campaigns.save(updated)
        return ToolResult(
            ok=True,
            data={
                "creator_id": creator_id,
                "channel": channel,
                "confirmed_channels": updated.confirmed_channels,
            },
            display=display,
        )
