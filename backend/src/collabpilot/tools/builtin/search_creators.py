"""`search_creators`: keyword + time-window search over ``data/mock`` (T03).

Accounts are matched per platform, then merged by ``creator_id``. The tool
only runs once the goal is PARSED and records the call on the campaign as
``last_search`` (T07 reuses it as the round-1 parameters).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import CreatorRef, SearchRecord
from collabpilot.campaign.mock_store import PLATFORMS, MergedCreator, Platform
from collabpilot.campaign.selection import ALREADY_SAVED, elsewhere_hint, recommend
from collabpilot.campaign.store import CampaignStore
from collabpilot.campaign.topic_match import skipped_locked_note
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import Tool, ToolContext


class AccountHit(BaseModel):
    """`account_id` is `<platform>:<handle>`; `data_origin` lives in `meta`."""

    platform: Platform
    creator_id: str
    account_id: str
    follower_count: int | None


class SearchCreator(CreatorRef):
    account_ids: list[str] = []


class SearchMeta(BaseModel):
    is_mock: bool = True
    data_origin: str = mock_store.MOCK_ORIGIN
    platforms: list[Platform]
    keywords: list[str]
    window_days: int
    min_followers: int | None
    limit: int
    outside_window_hits: int
    generated_at: str


class SearchResult(BaseModel):
    accounts: list[AccountHit]
    creators: list[SearchCreator]
    meta: SearchMeta

    def record(self) -> SearchRecord:
        return SearchRecord(
            keywords=self.meta.keywords,
            window_days=self.meta.window_days,
            min_followers=self.meta.min_followers,
            platforms=self.meta.platforms,
            creators=[
                CreatorRef(
                    creator_id=item.creator_id,
                    display_name=item.display_name,
                    platforms=item.platforms,
                )
                for item in self.creators
            ],
            outside_window_hits=self.meta.outside_window_hits,
        )


def _keyword_fields(account: dict[str, Any], window_days: int) -> list[str]:
    fields = [
        str(account.get("display_name") or ""),
        *[str(topic) for topic in account.get("content_topics", [])],
        mock_store.bio(account),
    ]
    fields += [
        mock_store.post_text(post)
        for post in account["recent_posts"]
        if _in_window(post, window_days)
    ]
    return fields


def _in_window(post: dict[str, Any], window_days: int) -> bool:
    age = post.get("age_days")
    return age is not None and 0 <= age <= window_days


def _matches(account: dict[str, Any], keywords: list[str], window_days: int) -> bool:
    haystack = [field.lower() for field in _keyword_fields(account, window_days)]
    return any(keyword in field for keyword in keywords for field in haystack)


def run_search(
    creators: dict[str, MergedCreator],
    *,
    platforms: list[Platform],
    keywords: list[str],
    window_days: int,
    min_followers: int | None,
    limit: int,
    generated_at: str,
) -> SearchResult:
    """Pure search over merged creators. Defaults live on the tool schema."""
    normalized = [keyword.strip().lower() for keyword in keywords if keyword.strip()]
    hits: list[AccountHit] = []
    merged: dict[str, SearchCreator] = {}
    outside_window = 0
    for creator in creators.values():
        keyword_hit = False
        window_hit = False
        for platform, account in creator.accounts():
            if platform not in platforms:
                continue
            # Keyword match ignores the window so `outside_window_hits` can be
            # counted; the account itself must still post inside the window.
            if not _matches(account, normalized, window_days=10**6):
                continue
            keyword_hit = True
            if not any(_in_window(post, window_days) for post in account["recent_posts"]):
                continue
            if not _matches(account, normalized, window_days):
                continue
            window_hit = True
            followers = mock_store.follower_count(account)
            if min_followers is not None and (followers is None or followers < min_followers):
                continue
            hit = AccountHit(
                platform=platform,
                creator_id=creator.creator_id,
                account_id=mock_store.account_id(account),
                follower_count=followers,
            )
            hits.append(hit)
            ref = merged.setdefault(
                creator.creator_id,
                SearchCreator(
                    creator_id=creator.creator_id,
                    display_name=creator.display_name,
                    platforms=[],
                ),
            )
            ref.platforms.append(platform)
            ref.account_ids.append(hit.account_id)
        if keyword_hit and not window_hit:
            outside_window += 1
    kept_ids = list(merged)[:limit]
    return SearchResult(
        accounts=[hit for hit in hits if hit.creator_id in kept_ids],
        creators=[merged[creator_id] for creator_id in kept_ids],
        meta=SearchMeta(
            platforms=platforms,
            keywords=keywords,
            window_days=window_days,
            min_followers=min_followers,
            limit=limit,
            outside_window_hits=outside_window,
            generated_at=generated_at,
        ),
    )


class SearchCreatorsTool(Tool):
    name = "search_creators"
    description = (
        "在模拟达人库（[MOCK]，只读）中按关键词搜索 TikTok / Instagram 账号，"
        "并按 creator_id 合并跨平台账号。只返回在 window_days 天内发过帖子的账号。"
        "关键词匹配昵称、内容话题、简介和窗口内帖子的标题/caption（子串、不分大小写）。"
    )
    risk_level = "read"
    input_schema = {
        "type": "object",
        "properties": {
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": list(PLATFORMS)},
                "description": "要搜索的平台，默认两个都搜。",
                "default": list(PLATFORMS),
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "关键词列表，例如 [\"翻译\", \"LinguaGo\"]。",
            },
            "window_days": {
                "type": "integer",
                "minimum": 1,
                "default": 30,
                "description": "只保留最近 N 天内有帖子的账号。",
            },
            "min_followers": {
                "type": ["integer", "null"],
                "minimum": 0,
                "default": None,
                "description": "粉丝门槛；低于门槛的单个账号被去掉，不影响该创作者的其他账号。",
            },
            "limit": {"type": "integer", "minimum": 1, "default": 50},
        },
        "required": ["keywords"],
        "additionalProperties": False,
    }

    def __init__(self, campaigns: CampaignStore):
        self.campaigns = campaigns

    @classmethod
    def default(cls, field: str) -> Any:
        return cls.input_schema["properties"][field]["default"]

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        campaign = self.campaigns.get(context.session_id)
        if campaign.goal_status != "PARSED":
            return ToolResult(
                ok=False,
                error_code="goal_not_ready",
                display="合作目标尚未解析完成，暂不搜索。",
            )
        keywords = arguments.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [keywords]
        keywords = [str(item) for item in keywords if str(item).strip()]
        if not keywords:
            return ToolResult(ok=False, error_code="keywords_required", display="缺少关键词")
        platforms = [
            platform
            for platform in arguments.get("platforms") or self.default("platforms")
            if platform in PLATFORMS
        ]
        min_followers = arguments.get("min_followers", self.default("min_followers"))
        result = run_search(
            mock_store.load(),
            platforms=platforms or list(PLATFORMS),
            keywords=keywords,
            window_days=int(arguments.get("window_days") or self.default("window_days")),
            min_followers=int(min_followers) if min_followers is not None else None,
            limit=int(arguments.get("limit") or self.default("limit")),
            generated_at=mock_store.generated_at().isoformat(),
        )
        kept_ids, skips = recommend(
            [item.creator_id for item in result.creators], campaign
        )
        if skips.total:
            kept = set(kept_ids)
            result = result.model_copy(
                update={
                    "creators": [item for item in result.creators if item.creator_id in kept],
                    "accounts": [item for item in result.accounts if item.creator_id in kept],
                }
            )
        elsewhere = self.campaigns.saved_in_other_campaigns(
            kept_ids, campaign.campaign_id
        )
        self.campaigns.save(
            campaign.model_copy(
                update={
                    "stage": "SEARCHING",
                    "last_search": result.record(),
                    "skip_counts": skips.model_dump(),
                }
            )
        )
        meta = result.meta
        extra = skips.note()
        display = (
            f"[MOCK] 关键词 {'、'.join(keywords)} · 窗口 {meta.window_days} 天 · "
            f"粉丝门槛 {meta.min_followers if meta.min_followers is not None else '无'}："
            f"{len(result.accounts)} 个账号，合并为 {len(result.creators)} 位创作者；"
            f"另有 {meta.outside_window_hits} 位关键词命中但窗口内无帖子。"
        )
        if extra:
            display = f"{display} {extra}"
        locked_note = skipped_locked_note(skips.topic_rejected)
        if locked_note:
            display = f"{display} {locked_note}"
        if skips.already_saved:
            display = f"{display}（{ALREADY_SAVED}）"
        hint = elsewhere_hint(len(elsewhere))
        if hint:
            display = f"{display} {hint}"
        return ToolResult(
            ok=True,
            data={**result.model_dump(), "skip_counts": skips.model_dump()},
            display=display,
            metadata={"is_mock": True},
        )
