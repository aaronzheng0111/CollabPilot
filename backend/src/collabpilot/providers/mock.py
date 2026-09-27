from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from collabpilot.domain.models import Message, ModelResponse, ToolCall
from collabpilot.providers.base import Provider


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
        if last.role == "tool":
            content = f"工具返回：{last.content}"
            if on_delta:
                await on_delta(content)
            return ModelResponse(
                content=content,
                provider=self.name,
                model=model,
            )

        text = last.content.strip()
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

        content = (
                "我是 CollabPilot，面向品牌和增长团队的达人合作工作台 Agent。"
                "当前 Mock 模式可进行基础对话、保存会话，并在需要时调用只读时间工具。"
                "完整能力（解析合作目标、搜索达人、判断匹配、起草邀请）按 Task 逐步接入。"
            )
        if on_delta:
            await on_delta(content)
        return ModelResponse(
            content=content,
            provider=self.name,
            model=model,
        )

    async def health(self, model: str) -> tuple[bool, str]:
        return True, f"Mock provider ready ({model})"
