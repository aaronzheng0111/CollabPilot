from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from html import escape
from uuid import UUID
from zoneinfo import ZoneInfo

import streamlit as st

from collabpilot.domain.models import Message, StoredMessage

DELETE_MESSAGE = "删除"
LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def format_time(when: datetime) -> str:
    if when.tzinfo is None:
        when = when.replace(tzinfo=ZoneInfo("UTC"))
    return when.astimezone(LOCAL_TZ).strftime("%H:%M")


def tool_line_state(message: Message) -> str:
    """Map a stored tool message to running | succeeded | failed."""
    try:
        payload = json.loads(message.content)
    except (TypeError, ValueError, json.JSONDecodeError):
        return "succeeded"
    if not isinstance(payload, dict):
        return "succeeded"
    if payload.get("ok") is False:
        return "failed"
    return "succeeded"


def tool_line_html_parts(
    name: str,
    when: datetime | str | None = None,
    status: str | None = None,
    *,
    state: str | None = None,
) -> str:
    """One short tool line inside the assistant bubble.

    ``state`` is preferred (running / succeeded / failed). Legacy callers may
    still pass ``status`` text; succeeded/failed are inferred from it.
    """
    resolved = state
    if resolved is None:
        if status == "running" or (status and status.startswith("正在调用")):
            resolved = "running"
        elif status and status.startswith("失败"):
            resolved = "failed"
        else:
            resolved = "succeeded"
    safe_name = escape(name)
    if resolved == "running":
        return (
            f'<div class="cp-tool-line cp-tool-line-running">'
            f'<span class="cp-spinner"></span>'
            f"<span>正在调用 <code>{safe_name}</code></span>"
            f"</div>"
        )
    if resolved == "failed":
        return (
            f'<div class="cp-tool-line cp-tool-line-failed">'
            f"<code>{safe_name}</code>"
            f"<span>失败</span>"
            f"</div>"
        )
    return (
        f'<div class="cp-tool-line cp-tool-line-succeeded">'
        f"<code>{safe_name}</code>"
        f"<span>调用完成</span>"
        f"</div>"
    )


def tool_line_html(entry: StoredMessage) -> str:
    return tool_line_html_parts(
        entry.message.name or "tool",
        entry.created_at,
        state=tool_line_state(entry.message),
    )


def replace_running_tool_line(
    lines: list[str],
    name: str,
    finished_html: str,
) -> list[str]:
    """Swap the matching running spinner line for a finished line."""
    marker = f"<code>{escape(name)}</code>"
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index]
        if "cp-tool-line-running" in line and marker in line:
            lines[index] = finished_html
            return lines
    lines.append(finished_html)
    return lines


@dataclass
class ChatBlock:
    """One visible bubble. Tools belong to the assistant block, never alone."""

    role: str
    entry: StoredMessage
    tools: list[StoredMessage] = field(default_factory=list)


def group_entries(entries: list[StoredMessage]) -> list[ChatBlock]:
    """Fold tool rows into the following assistant message of the same turn."""
    blocks: list[ChatBlock] = []
    pending: list[StoredMessage] = []
    for entry in entries:
        role = entry.message.role
        if role == "tool":
            pending.append(entry)
            continue
        if role == "user":
            pending = []
            blocks.append(ChatBlock(role="user", entry=entry))
            continue
        if role == "assistant":
            owned = [
                item
                for item in pending
                if item.turn_id == entry.turn_id
            ]
            blocks.append(ChatBlock(role="assistant", entry=entry, tools=owned))
            pending = []
    return blocks


def render_assistant_body(
    tools: list[StoredMessage] | list[str],
    content: str,
) -> None:
    """Tool short-lines first, then the natural-language reply."""
    for item in tools:
        html = item if isinstance(item, str) else tool_line_html(item)
        st.markdown(html, unsafe_allow_html=True)
    if content:
        st.write(content)


def render_history(
    entries: list[StoredMessage],
    on_delete_message: Callable[[UUID], None] | None = None,
) -> None:
    for block in group_entries(entries):
        with st.chat_message(block.role):
            if block.role == "assistant":
                render_assistant_body(block.tools, block.entry.message.content)
            else:
                st.write(block.entry.message.content)
            if on_delete_message is not None:
                if st.button(
                    DELETE_MESSAGE,
                    key=f"cp-del-msg-{block.entry.id}",
                    help="删除这条消息",
                    type="tertiary",
                ):
                    on_delete_message(block.entry.id)
