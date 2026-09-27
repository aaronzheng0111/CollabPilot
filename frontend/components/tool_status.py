from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from collabpilot.agent.runtime import RuntimeEvent


ToolStatus = dict[str, Any]


def initial_status() -> ToolStatus:
    return {"state": "idle", "name": None, "error_code": None}


def apply_event(status: ToolStatus, event: RuntimeEvent) -> ToolStatus:
    if event.type == "tool.started":
        return {"state": "running", "name": event.name, "error_code": None}
    if event.type == "tool.completed" and event.name == status["name"]:
        return {
            "state": "succeeded" if event.ok else "failed",
            "name": event.name,
            "error_code": event.error_code,
        }
    return status


def status_html(status: ToolStatus) -> str:
    state = status["state"]
    name = f"<code>{escape(status['name'] or '')}</code>"
    if state == "running":
        body = f'{name}<span class="cp-spinner"></span><span>运行中</span>'
    elif state == "succeeded":
        body = f"{name}<span>完成</span>"
    elif state == "failed":
        body = f"{name}<span>{escape(status['error_code'] or 'tool_failed')}</span>"
    else:
        body = "<span>空闲</span>"
    return (
        f'<div class="cp-status cp-status-{state}">'
        f'<span class="cp-dot"></span>{body}</div>'
    )


def render_tool_status(status: ToolStatus, target: Any = st) -> None:
    target.markdown(status_html(status), unsafe_allow_html=True)
