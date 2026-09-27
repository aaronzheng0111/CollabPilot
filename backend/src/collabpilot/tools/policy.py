from collabpilot.domain.errors import ToolPolicyError
from collabpilot.tools.base import Tool


# Write tools that the model / UI may call; still gated by user_approved.
# Dangerous is never in this set.
WRITE_TOOLS = frozenset(
    {
        "save_campaign_selection",
        "exclude_creator",
        "confirm_channel",
        "save_drafts",
        "approve_draft",
        "reject_draft",
        "save_follow_up",
        "note_follow_up",
    }
)


class ToolPolicy:
    def __init__(
        self,
        allowed_risk_levels: list[str],
        extra_write_tools: frozenset[str] | None = None,
    ):
        self.allowed_risk_levels = set(allowed_risk_levels)
        self.extra_write_tools = extra_write_tools if extra_write_tools is not None else WRITE_TOOLS

    def check(self, tool: Tool) -> None:
        if tool.risk_level in self.allowed_risk_levels:
            return
        if tool.risk_level == "write" and tool.name in self.extra_write_tools:
            return
        raise ToolPolicyError(
            f"Tool '{tool.name}' risk level '{tool.risk_level}' is not allowed"
        )

