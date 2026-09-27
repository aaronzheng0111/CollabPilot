from __future__ import annotations

import asyncio
from uuid import UUID

import streamlit as st

from collabpilot.agent.runtime import RuntimeEvent
from collabpilot.bootstrap import create_application
from collabpilot.domain.errors import AgentError
from collabpilot.domain.models import Message
from components.main_table import render_main_table
from components.tool_status import apply_event, initial_status, render_tool_status
from theme import inject_theme


def session_from_query() -> UUID | None:
    raw = st.query_params.get("session")
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def render_message(message: Message) -> None:
    if message.role == "tool":
        with st.expander(f"工具结果 · {message.name}"):
            st.code(message.content, language="json")
    elif message.role in ("user", "assistant"):
        st.chat_message(message.role).write(message.content)


st.set_page_config(page_title="CollabPilot", layout="wide")
inject_theme()

application = create_application()
session_id = session_from_query()
st.session_state.setdefault("tool_status", initial_status())
st.session_state.setdefault("chat_error", None)

st.title("CollabPilot 达人合作工作台")
left, right = st.columns([3, 2])

with left:
    render_main_table()
    with st.container(key="cp-secondary"):
        st.caption("暂无内容")

with right:
    status_slot = st.empty()
    render_tool_status(st.session_state.tool_status, status_slot)
    history = st.container(height=480, border=False)
    with history:
        for message in application.history(session_id) if session_id else []:
            render_message(message)
        if st.session_state.chat_error:
            st.error(st.session_state.chat_error)
    prompt = st.chat_input("描述你的合作目标")

if prompt:
    with history:
        st.chat_message("user").write(prompt)
    st.session_state.tool_status = initial_status()
    render_tool_status(st.session_state.tool_status, status_slot)

    async def on_event(event: RuntimeEvent) -> None:
        st.session_state.tool_status = apply_event(st.session_state.tool_status, event)
        render_tool_status(st.session_state.tool_status, status_slot)

    try:
        result = asyncio.run(
            application.chat(prompt, session_id=session_id, on_event=on_event)
        )
    except AgentError as exc:
        st.session_state.chat_error = f"{exc.code}: {exc}"
        if st.session_state.tool_status["state"] == "running":
            st.session_state.tool_status = {
                **st.session_state.tool_status,
                "state": "failed",
                "error_code": exc.code,
            }
    else:
        st.session_state.chat_error = None
        st.query_params["session"] = str(result.session_id)
    st.rerun()
