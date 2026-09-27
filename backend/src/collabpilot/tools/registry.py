from __future__ import annotations

from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.errors import ConfigurationError
from collabpilot.tools.base import Tool
from collabpilot.tools.builtin.apply_hard_filters import ApplyHardFiltersTool
from collabpilot.tools.builtin.approve_draft import ApproveDraftTool, RejectDraftTool
from collabpilot.tools.builtin.confirm_channel import ConfirmChannelTool
from collabpilot.tools.builtin.exclude_creator import ExcludeCreatorTool
from collabpilot.tools.builtin.get_creator import GetCreatorTool
from collabpilot.tools.builtin.save_campaign_selection import SaveCampaignSelectionTool
from collabpilot.tools.builtin.save_drafts import SaveDraftsTool
from collabpilot.tools.builtin.save_follow_up import NoteFollowUpTool, SaveFollowUpTool
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool
from collabpilot.tools.builtin.time_tool import GetCurrentTimeTool


class ToolRegistry:
    def __init__(
        self,
        enabled: list[str],
        campaigns: CampaignStore | None = None,
        max_result_chars: int = 12000,
    ):
        """Campaign tools need the campaign store; without it only the
        campaign-free tools are available."""
        available: dict[str, Tool] = {
            GetCurrentTimeTool.name: GetCurrentTimeTool(),
        }
        if campaigns is not None:
            available[SearchCreatorsTool.name] = SearchCreatorsTool(campaigns)
            available[GetCreatorTool.name] = GetCreatorTool(campaigns, max_result_chars)
            available[ApplyHardFiltersTool.name] = ApplyHardFiltersTool(campaigns)
            available[SaveCampaignSelectionTool.name] = SaveCampaignSelectionTool(campaigns)
            available[ExcludeCreatorTool.name] = ExcludeCreatorTool(campaigns)
            available[ConfirmChannelTool.name] = ConfirmChannelTool(campaigns)
            available[SaveDraftsTool.name] = SaveDraftsTool(campaigns)
            available[ApproveDraftTool.name] = ApproveDraftTool(campaigns)
            available[RejectDraftTool.name] = RejectDraftTool(campaigns)
            available[SaveFollowUpTool.name] = SaveFollowUpTool(campaigns)
            available[NoteFollowUpTool.name] = NoteFollowUpTool(campaigns)
        unknown = set(enabled) - set(available)
        if unknown:
            raise ConfigurationError(f"Unknown enabled tools: {sorted(unknown)}")
        self._tools = {name: available[name] for name in enabled}

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict]:
        return [tool.schema() for tool in self.list()]
