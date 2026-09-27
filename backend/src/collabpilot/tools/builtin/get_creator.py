"""`get_creator`: full merged profile of one creator from ``data/mock`` (T03).

The payload handed to the model is shrunk to fit the runtime
``max_tool_result_chars``; when anything is dropped the result keeps
``creator_id`` and sets ``truncated=true``.
"""

from __future__ import annotations

from typing import Any

from collabpilot.campaign import mock_store
from collabpilot.campaign.mock_store import MergedCreator
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


# Dropped in order until the serialized result fits. Post-level keys first
# (media plumbing), then engagement stats, then cooperation details.
POST_NOISE = (
    "cover_urls",
    "music_info",
    "share_url",
    "media_url",
    "permalink",
    "region",
    "duration",
    "media_type",
    "hashtag_names",
)
POST_STATS = ("stats", "like_count", "comments_count")
COOPERATION_NOISE = ("performance", "notes", "sample_sent_at", "sample_received_at")
ACCOUNT_NOISE = ("raw_api_snapshot_ref", "data_quality", "is_new_creator")


def creator_payload(creator: MergedCreator) -> dict[str, Any]:
    return {
        "creator_id": creator.creator_id,
        "display_name": creator.display_name,
        "platforms": creator.platforms,
        "tiktok": creator.tiktok,
        "instagram": creator.instagram,
        "data_origin": mock_store.MOCK_ORIGIN,
        "is_mock": True,
        "truncated": False,
    }


def _drop(
    account: dict[str, Any] | None,
    post_keys: tuple[str, ...] = (),
    coop_keys: tuple[str, ...] = (),
    account_keys: tuple[str, ...] = (),
) -> None:
    if account is None:
        return
    for key in account_keys:
        account.pop(key, None)
    for post in account.get("recent_posts", []):
        for key in post_keys:
            post.pop(key, None)
    for item in account.get("cooperation_history", []):
        for key in coop_keys:
            item.pop(key, None)


def _trim_posts(account: dict[str, Any] | None, keep: int) -> None:
    if account is not None:
        account["recent_posts"] = account.get("recent_posts", [])[:keep]


def fit_result(result: ToolResult, limit: int) -> ToolResult:
    """Shrink `result.data` until `result.model_dump_json()` fits in `limit`."""
    if len(result.model_dump_json()) <= limit:
        return result
    data = result.data
    steps = [
        lambda a: _drop(a, account_keys=ACCOUNT_NOISE, post_keys=POST_NOISE),
        lambda a: _drop(a, post_keys=POST_STATS, coop_keys=COOPERATION_NOISE),
        lambda a: _trim_posts(a, 2),
        lambda a: _trim_posts(a, 1),
    ]
    for step in steps:
        for platform in ("tiktok", "instagram"):
            step(data.get(platform))
        data["truncated"] = True
        if len(result.model_dump_json()) <= limit:
            return result
    result.data = {
        "creator_id": data["creator_id"],
        "display_name": data["display_name"],
        "platforms": data["platforms"],
        "data_origin": mock_store.MOCK_ORIGIN,
        "is_mock": True,
        "truncated": True,
    }
    return result


class GetCreatorTool(Tool):
    name = "get_creator"
    description = (
        "读取一位创作者在 TikTok 与 Instagram 的完整模拟资料（[MOCK]，只读）："
        "账号、recent_posts（每条带 age_days）、cooperation_history、audience、metrics、"
        "contact、product_usage_evidence。缺失字段保持原值，不补造。"
    )
    risk_level = "read"
    input_schema = {
        "type": "object",
        "properties": {
            "creator_id": {"type": "string", "description": "例如 creator_001"},
        },
        "required": ["creator_id"],
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore, max_result_chars: int):
        self.campaigns = campaigns
        self.max_result_chars = max_result_chars

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        if campaign.goal_status != "PARSED":
            return ToolResult(
                ok=False, error_code="goal_not_ready", display="合作目标尚未解析完成。"
            )
        creator_id = str(arguments.get("creator_id") or "")
        creator = mock_store.load().get(creator_id)
        if creator is None:
            return ToolResult(
                ok=False, error_code="not_found", display=f"未找到创作者 {creator_id}"
            )
        result = ToolResult(
            ok=True,
            data=creator_payload(creator.model_copy(deep=True)),
            display=f"[MOCK] {creator.creator_id} {creator.display_name} · {'、'.join(creator.platforms)}",
            metadata={"is_mock": True},
        )
        return fit_result(result, self.max_result_chars)
