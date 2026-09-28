from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from collabpilot.campaign.drafts import DRAFTS_HEADING
from collabpilot.campaign.follow_up import FOLLOW_UP_HEADING
from collabpilot.campaign.goal import stated_creator_niche
from collabpilot.campaign.verdict import CANDIDATES_HEADING
from collabpilot.domain.models import Message, ModelResponse, ToolCall
from collabpilot.providers.base import Provider


GOAL_WORDS = ("达人", "创作者", "博主", "合作", "推广", "触达", "草稿", "审核")
UNIT = r"\s*(?:位|个|名)"
# Tried in order; the first alternative wins over positional order.
OUTREACH_PATTERNS = [
    re.compile(rf"(?:触达|邀请|草稿)[^\d\n]{{0,8}}(\d+){UNIT}"),
    re.compile(rf"(\d+){UNIT}[^。\n]{{0,24}}?(?:草稿|邀请|触达)"),
]
TARGET_PATTERNS = [
    re.compile(rf"找[^\d\n]{{0,6}}(\d+){UNIT}"),
    re.compile(rf"(\d+){UNIT}[^。\n]{{0,24}}?(?:创作者|达人|博主)"),
    re.compile(rf"(\d+){UNIT}"),
]


def looks_like_goal(text: str) -> bool:
    return any(word in text for word in GOAL_WORDS)


def _find_count(
    text: str, patterns: list[re.Pattern[str]], skip_offset: int | None = None
) -> tuple[int | None, int | None]:
    """(value, digit offset) of the first pattern hit not sitting at skip_offset."""
    for pattern in patterns:
        for match in pattern.finditer(text):
            if match.start(1) != skip_offset:
                return int(match.group(1)), match.start(1)
    return None, None


def mock_parse_goal(text: str) -> dict[str, Any]:
    outreach, outreach_at = _find_count(text, OUTREACH_PATTERNS)
    target, _ = _find_count(text, TARGET_PATTERNS, skip_offset=outreach_at)

    approval: bool | None = None
    if any(word in text for word in ("不用审核", "无需审核", "不需要审核", "不审核")):
        approval = False
    elif any(word in text for word in ("审核", "审批", "我确认", "过我")):
        approval = True

    platforms = [p for p in ("tiktok", "instagram") if p in text.lower()]
    allow_recontact = any(
        marker in text
        for marker in (
            "可以再次联系",
            "可以再次取得联系",
            "再次取得联系",
            "不排除已合作",
            "不排除已经合作",
            "不排除已联系",
            "允许再次联系",
            "可以和已经联系",
            "可以和已联系",
            "可以和已合作",
            "可以和已经合作",
        )
    )
    inclusion: list[str] = []
    if "持续" in text:
        inclusion.append("最近持续发布相关内容")
    if allow_recontact:
        inclusion.append("可以再次联系已合作过的账号")
    exclude_past = (not allow_recontact) and (
        "排除已合作" in text
        or "排除已经合作" in text
        or "排除合作过" in text
        or "排除已经合作过" in text
        or (("合作过" in text or "已合作" in text) and "不排除" not in text)
    )
    return {
        "brand": None,
        "product": (
            "AI 翻译工具"
            if "翻译工具" in text or ("翻译" in text and "AI" in text)
            else ("翻译" if "翻译" in text else stated_creator_niche(text))
        ),
        "target_audience": ["中文用户"] if "中文" in text else [],
        "platforms": platforms,
        "target_count": target,
        "inclusion_criteria": inclusion,
        "exclusion_criteria": (["已经合作过的账号"] if exclude_past else []),
        "outreach_count": outreach,
        "needs_user_approval": approval,
        "assumptions": [],
        "missing_critical": [],
        "grill": None,
    }


def mock_verdicts_reply(prompt: str) -> str:
    """Stand-in for the judgment call: every candidate becomes `pending`,
    citing its own first evidence id. No fit, no rank — the mock does not
    pretend to judge; it only exercises the schema and the UI."""
    match = re.search(r"```json\s*(.*?)```", prompt, re.DOTALL)
    try:
        candidates = json.loads(match.group(1)) if match else []
    except json.JSONDecodeError:
        candidates = []
    verdicts = []
    for candidate in candidates:
        accounts = candidate.get("accounts", [])
        evidence = [
            item["evidence_id"]
            for account in accounts
            for item in account.get("evidence", [])
            if item.get("evidence_id")
        ]
        posts = [post["post_id"] for account in accounts for post in account.get("posts", [])]
        verdicts.append(
            {
                "creator_id": candidate["creator_id"],
                "decision": "pending",
                "reasons": ["Mock 模式：未做真实判断，待人工确认"],
                "evidence_ids": evidence[:1] or posts[:1],
                "related_post_ids": [],
                "topic_match": "unclear",
                "mismatch_topic": None,
                "quote": None,
                "unknowns": [],
                "rank": None,
            }
        )
    return "```json\n" + json.dumps({"verdicts": verdicts}, ensure_ascii=False) + "\n```"


def mock_drafts_reply(prompt: str) -> str:
    """Stand-in for the creative draft call: unique bodies citing each creator's first post."""
    match = re.search(r"```json\s*(.*?)```", prompt, re.DOTALL)
    try:
        payload = json.loads(match.group(1)) if match else []
    except json.JSONDecodeError:
        payload = []
    if isinstance(payload, dict):
        payload = payload.get("creators") or payload.get("drafts") or []
    drafts = []
    for index, item in enumerate(payload):
        posts = item.get("posts") or []
        post = posts[0] if posts else {}
        snippet = str(post.get("title") or post.get("caption") or "")[:24]
        if len(snippet) < 8:
            snippet = (snippet + "原文片段补齐")[:8]
        label = item.get("channel_label") or "TikTok 私信"
        name = item.get("display_name") or item.get("creator_id")
        body = (
            f"你好{name}，我读到你写的「{snippet}」，想邀请你合作。"
            f"这封草稿专门写给你（第{index + 1}位），稍后通过{label}发你。不会群发模板。"
        )
        drafts.append(
            {
                "creator_id": item.get("creator_id"),
                "body": body,
                "cited_post_id": post.get("post_id"),
                "channel": item.get("channel") or "tiktok_dm",
            }
        )
    return "```json\n" + json.dumps({"drafts": drafts}, ensure_ascii=False) + "\n```"


def mock_follow_up_reply(prompt: str) -> str:
    """Stand-in for the follow-up call: copy the confirmed channel, write next_step."""
    match = re.search(r"```json\s*(.*?)```", prompt, re.DOTALL)
    try:
        payload = json.loads(match.group(1)) if match else {}
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    channel = payload.get("channel") or "tiktok_dm"
    label = payload.get("channel_label") or "TikTok 私信"
    name = payload.get("display_name") or payload.get("creator_id") or "创作者"
    return (
        "```json\n"
        + json.dumps(
            {
                "creator_id": payload.get("creator_id"),
                "draft_id": payload.get("draft_id"),
                "channel": channel,
                "next_step": (
                    f"三天后通过{label}再问一次 {name} 是否看到邀请，"
                    "仍不发送，只记下这件事。"
                ),
            },
            ensure_ascii=False,
        )
        + "\n```"
    )



async def emit_text_chunks(
    content: str,
    on_delta: Callable[[str], Awaitable[None]] | None,
    *,
    parts: int = 3,
) -> None:
    """Yield a few chunks that concatenate to `content` (for tests / UI)."""
    if not on_delta or not content:
        return
    size = max(1, (len(content) + parts - 1) // parts)
    for start in range(0, len(content), size):
        await on_delta(content[start : start + size])


class MockProvider(Provider):
    name = "mock"

    async def complete(
        self,
        messages: list[Message],
        model: str,
        tools: list[dict[str, Any]],
        on_delta: Callable[[str], Awaitable[None]] | None = None,
        temperature: float | None = None,
    ) -> ModelResponse:
        del temperature
        last = messages[-1]
        offered = {tool["function"]["name"] for tool in tools}
        if last.role == "tool":
            if (
                last.name == "search_creators"
                and "apply_hard_filters" in offered
                and '"ok":true' in last.content.replace(" ", "")
            ):
                # Stand-in for the model chaining search → rule filter.
                return ModelResponse(
                    provider=self.name,
                    model=model,
                    tool_calls=[
                        ToolCall(
                            id=f"mock-filter-{int(datetime.now().timestamp())}",
                            name="apply_hard_filters",
                            arguments={},
                        )
                    ],
                )
            content = self._after_tools(messages)
            await emit_text_chunks(content, on_delta)
            return ModelResponse(
                content=content,
                provider=self.name,
                model=model,
            )

        text = last.content.strip()
        draft_source = next(
            (
                message.content
                for message in messages
                if message.role == "user" and message.content.startswith(DRAFTS_HEADING)
            ),
            None,
        )
        if draft_source is not None:
            content = mock_drafts_reply(draft_source)
            await emit_text_chunks(content, on_delta)
            return ModelResponse(content=content, provider=self.name, model=model)
        follow_source = next(
            (
                message.content
                for message in messages
                if message.role == "user" and message.content.startswith(FOLLOW_UP_HEADING)
            ),
            None,
        )
        if follow_source is not None:
            content = mock_follow_up_reply(follow_source)
            await emit_text_chunks(content, on_delta)
            return ModelResponse(content=content, provider=self.name, model=model)
        if text.startswith(CANDIDATES_HEADING):
            content = mock_verdicts_reply(text)
            await emit_text_chunks(content, on_delta)
            return ModelResponse(content=content, provider=self.name, model=model)
        if text.startswith("【再搜策略】"):
            content = "Mock 模式不提出再搜策略，请使用真实模型。"
            await emit_text_chunks(content, on_delta)
            return ModelResponse(content=content, provider=self.name, model=model)
        if "search_creators" in offered and any(
            word in text for word in ("搜索", "开始", "搜一下", "search")
        ):
            window = re.search(r"(\d+)\s*天", text)
            arguments: dict[str, Any] = {"keywords": ["翻译"], "window_days": 30}
            if window:
                arguments["window_days"] = int(window.group(1))
            return ModelResponse(
                provider=self.name,
                model=model,
                tool_calls=[
                    ToolCall(
                        id=f"mock-search-{int(datetime.now().timestamp())}",
                        name="search_creators",
                        arguments=arguments,
                    )
                ],
            )
        if any(word in text.lower() for word in ("time", "date", "几点", "时间", "日期")):
            if any(tool["function"]["name"] == "get_current_time" for tool in tools):
                timezone_match = re.search(r"(Asia/[A-Za-z_]+|UTC|[+-]\d{2}:\d{2})", text)
                timezone = timezone_match.group(1) if timezone_match else "Asia/Shanghai"
                return ModelResponse(
                    provider=self.name,
                    model=model,
                    tool_calls=[
                        ToolCall(
                            id=f"mock-{int(datetime.now().timestamp())}",
                            name="get_current_time",
                            arguments={"timezone": timezone},
                        )
                    ],
                )

        user_texts = [m.content for m in messages if m.role == "user"]
        if any(looks_like_goal(item) for item in user_texts):
            # Mock stand-in for DeepSeek: a crude regex read of everything the
            # user said so far. The application layer validates it exactly like
            # a real model reply.
            payload = mock_parse_goal(" ".join(user_texts))
            content = (
                "以下是我从需求里读出的合作目标。\n```json\n"
                + json.dumps(payload, ensure_ascii=False, indent=2)
                + "\n```"
            )
            await emit_text_chunks(content, on_delta)
            return ModelResponse(content=content, provider=self.name, model=model)

        content = (
                "我是 CollabPilot，面向品牌和增长团队的达人合作工作台 Agent。"
                "当前 Mock 模式可进行基础对话、保存会话，并在需要时调用只读时间工具。"
                "完整能力（解析合作目标、搜索达人、判断匹配、起草邀请）按 Task 逐步接入。"
            )
        await emit_text_chunks(content, on_delta)
        return ModelResponse(
            content=content,
            provider=self.name,
            model=model,
        )

    @staticmethod
    def _after_tools(messages: list[Message]) -> str:
        """Echo the `display` of every tool result since the last user turn."""
        lines: list[str] = []
        for message in reversed(messages):
            if message.role == "user":
                break
            if message.role != "tool":
                continue
            try:
                payload = json.loads(message.content)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict) and payload.get("display"):
                if payload.get("ok"):
                    lines.append(str(payload["display"]))
                else:
                    lines.append(
                        f"工具 {message.name} 失败：{payload.get('error_code')}。{payload['display']}"
                    )
            else:
                lines.append(f"工具返回：{message.content}")
        return "\n\n".join(reversed(lines))

    async def health(self, model: str) -> tuple[bool, str]:
        return True, f"Mock provider ready ({model})"
