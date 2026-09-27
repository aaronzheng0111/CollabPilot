from __future__ import annotations

import asyncio
from uuid import UUID

import streamlit as st

from collabpilot.agent.runtime import RuntimeEvent
from collabpilot.bootstrap import create_application
from collabpilot.campaign.drafts import SAVE_DRAFTS
from collabpilot.campaign.workbench import (
    evidence_view,
    main_table_rows,
)
from collabpilot.application import is_generate_drafts_request
from collabpilot.domain.errors import AgentError
from components.chat_history import (
    render_history,
    render_assistant_body,
    replace_running_tool_line,
    tool_line_html_parts,
)
from components.draft_cards import (
    EMPTY_SELECTION,
    OPEN_KEY,
    open_drafts_dialog,
    render_draft_cards,
)
from components.evidence_panel import render_evidence_panel
from components.excluded_table import render_excluded_table
from components.follow_up_table import render_follow_up_table
from components.goal_card import render_goal_card
from components.main_table import render_main_table
from components.pending_decisions import render_pending_decisions
from components.pending_list import render_pending_list
from components.progress_panel import render_progress_panel
from components.project_list import EMPTY_NAME, render_project_list
from components.tool_status import apply_event, initial_status
from theme import inject_theme


def session_from_query() -> UUID | None:
    raw = st.query_params.get("session")
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def switch_project(session_id: UUID | None) -> None:
    st.session_state.tool_status = initial_status()
    st.session_state.table_rows = []
    st.session_state.chat_error = None
    st.session_state.rename_error = None
    if session_id is None:
        st.query_params.pop("session", None)
    else:
        st.query_params["session"] = str(session_id)
    st.rerun()


st.set_page_config(page_title="CollabPilot", layout="wide")
inject_theme()

application = create_application()
session_id = session_from_query()
st.session_state.setdefault("tool_status", initial_status())
st.session_state.setdefault("chat_error", None)
st.session_state.setdefault("decision_notice", None)
st.session_state.setdefault("table_rows", [])
st.session_state.setdefault("rename_error", None)
st.session_state.setdefault("selected_creator_ids", [])
st.session_state.setdefault("draft_selection_hint", None)
st.session_state.setdefault(OPEN_KEY, False)
state = application.get_workbench_state(session_id)
campaign = state.campaign
if st.session_state.tool_status.get("state") != "running" or not st.session_state.table_rows:
    st.session_state.table_rows = state.main_rows
projects = application.list_projects()


def decide(decision: str, user_approved: bool) -> None:
    """Button callback: runs before the rerun, so the card renders fresh state."""
    if session_id is None:
        return
    result = application.approve_pending(session_id, decision, user_approved)
    st.session_state.decision_notice = result.display
    if result.ok and decision == SAVE_DRAFTS and result.campaign.drafts:
        open_drafts_dialog()


def queue_save(creator_ids: list[str]) -> None:
    if session_id is None:
        return
    application.queue_save_selection(session_id, creator_ids)
    st.rerun()


def queue_generate(creator_id: str) -> None:
    """Write exactly one draft for ``creator_id``, then open the popup for that draft."""
    if session_id is None:
        return
    if not creator_id:
        st.session_state.decision_notice = EMPTY_SELECTION
        st.session_state.draft_selection_hint = EMPTY_SELECTION
        st.rerun()
        return
    st.session_state.draft_selection_hint = None
    before_ids = {
        item.get("id")
        for item in (application.campaign(session_id).drafts or [])
        if isinstance(item, dict)
    }
    asyncio.run(
        application.generate_and_queue_drafts(
            session_id, creator_ids=[creator_id]
        )
    )
    # Persist immediately so cards are not stuck behind an invisible approve step.
    queued = application.campaign(session_id)
    if queued.pending_decision == SAVE_DRAFTS:
        saved = application.approve_pending(session_id, SAVE_DRAFTS, True)
        st.session_state.decision_notice = saved.display
        new_ids = [
            item["id"]
            for item in (saved.campaign.drafts or [])
            if isinstance(item, dict)
            and item.get("creator_id") == creator_id
            and item.get("id") not in before_ids
        ]
        if not new_ids:
            new_ids = [
                item["id"]
                for item in (saved.campaign.drafts or [])
                if isinstance(item, dict) and item.get("creator_id") == creator_id
            ]
        if new_ids:
            open_drafts_dialog(new_ids)
    elif queued.drafts:
        open_drafts_dialog(
            [
                item["id"]
                for item in queued.drafts
                if isinstance(item, dict) and item.get("creator_id") == creator_id
            ]
        )
    st.rerun()


def review_draft(draft_id: str, approved: bool) -> None:
    if session_id is None:
        return
    _campaign, display = asyncio.run(
        application.review_draft_and_follow_up(session_id, draft_id, approved)
    )
    st.session_state.decision_notice = display


def note_follow_up(follow_up_id: str, approved: bool) -> None:
    if session_id is None:
        return
    _campaign, display = application.note_follow_up(session_id, follow_up_id, approved)
    st.session_state.decision_notice = display


def create_project() -> None:
    project = application.create_project()
    switch_project(project.session_id)


def select_project(target: UUID) -> None:
    switch_project(target)


def delete_project(target: UUID) -> None:
    application.delete_project(target)
    if session_id == target:
        remaining = application.list_projects()
        switch_project(remaining[0].session_id if remaining else None)
    else:
        st.rerun()


def delete_message(message_id: UUID) -> None:
    if session_id is None:
        return
    application.delete_message(session_id, message_id)
    st.rerun()


def rename_project(target: UUID, title: str) -> None:
    updated = application.rename_project(target, title)
    if updated is None:
        st.session_state.rename_error = EMPTY_NAME
        return
    st.session_state.rename_error = None
    st.session_state.pop("cp_editing_project", None)
    st.rerun()


st.title("CollabPilot 达人合作工作台")

with st.sidebar:
    render_project_list(
        projects,
        session_id,
        on_select=select_project,
        on_create=create_project,
        on_delete=delete_project,
        on_rename=rename_project,
        rename_error=st.session_state.rename_error,
    )

left, right = st.columns([3, 2])

with left:
    with st.container(key="cp-main-table"):
        table_slot = st.empty()

        def draw_table() -> None:
            """Rows come from the campaign loaded at the top of this run, so a
            running tool overlays the previous result until the rerun."""
            selected = render_main_table(
                rows=st.session_state.table_rows,
                goal_status=state.goal_status,
                caption=state.search_caption,
                skip_caption=state.skip_caption,
                tool_status=st.session_state.tool_status,
                on_save=queue_save if session_id is not None else None,
                on_generate=(
                    queue_generate
                    if session_id is not None and state.drafts_ready
                    else None
                ),
                target=table_slot.container(),
            )
            st.session_state.selected_creator_ids = selected

        draw_table()
    with st.container(key="cp-secondary"):
        render_goal_card(campaign)
        render_progress_panel(state.progress)
        if state.verdicts:
            judged = [
                (row["creator_id"], f'{row["creator_id"]} · {row["display_name"]} · {row["decision"]}')
                for row in main_table_rows(campaign)
                if row.get("decision") not in (None, "—")
            ]
            render_evidence_panel(judged, lambda cid: evidence_view(campaign, cid))
        render_pending_list(state.pending_rows)
        render_excluded_table(state.excluded_rows)
        render_follow_up_table(
            state.follow_up_rows,
            model_name=(
                state.follow_up_rows[0].get("model_name") if state.follow_up_rows else None
            ),
            follow_error=state.follow_error,
        )

CHAT_SEND = "发送"
CHAT_PLACEHOLDER = "描述你的合作目标"

with right:
    with st.container(key="cp-chat-frame", border=True):
        with st.container(key="cp-chat-thread"):
            history = st.container(
                height=640, border=False, key="cp-chat-history"
            )
            with history:
                entries = (
                    application.history_entries(session_id) if session_id else []
                )
                render_history(
                    entries,
                    on_delete_message=delete_message if session_id else None,
                )
                if st.session_state.chat_error:
                    st.error(st.session_state.chat_error)
            with st.container(key="cp-chat-decisions"):
                render_pending_decisions(
                    campaign, decide, review_draft, note_follow_up
                )
                render_draft_cards(
                    state.draft_rows,
                    can_generate=state.drafts_ready,
                    model_name=(
                        state.draft_rows[0].get("model_name") if state.draft_rows else None
                    ),
                    draft_error=state.draft_error,
                    selection_hint=st.session_state.draft_selection_hint,
                )
                if st.session_state.decision_notice:
                    st.info(st.session_state.decision_notice)
                    st.session_state.decision_notice = None
            with st.container(key="cp-chat-composer"):
                with st.form(
                    key="cp-chat-form",
                    border=False,
                    clear_on_submit=True,
                ):
                    with st.container(
                        horizontal=True,
                        vertical_alignment="bottom",
                        gap="small",
                        wrap=False,
                    ):
                        prompt = st.text_input(
                            CHAT_PLACEHOLDER,
                            key="cp-chat-prompt",
                            placeholder=CHAT_PLACEHOLDER,
                            label_visibility="collapsed",
                        )
                        send_clicked = st.form_submit_button(
                            CHAT_SEND,
                            key="cp-chat-send",
                            type="primary",
                        )

if send_clicked and prompt and prompt.strip():
    message = prompt.strip()
    st.session_state.stream_buf = ""
    st.session_state.stream_tools = []
    with history:
        st.chat_message("user").write(message)
        stream_slot = st.empty()
    st.session_state.tool_status = initial_status()

    def paint_stream() -> None:
        with stream_slot.container():
            with st.chat_message("assistant"):
                render_assistant_body(
                    st.session_state.stream_tools,
                    st.session_state.stream_buf,
                )

    async def on_event(event: RuntimeEvent) -> None:
        st.session_state.tool_status = apply_event(st.session_state.tool_status, event)
        if event.type == "tool.started":
            # CSS spinner only — no Streamlit widget keys across redraws.
            st.session_state.stream_tools.append(
                tool_line_html_parts(event.name, state="running")
            )
            paint_stream()
        elif event.type == "tool.completed":
            finished = tool_line_html_parts(
                event.name,
                state="succeeded" if event.ok else "failed",
            )
            st.session_state.stream_tools = replace_running_tool_line(
                st.session_state.stream_tools,
                event.name,
                finished,
            )
            paint_stream()
        # Only redraw the loading banner while a tool runs. Success/idle wait
        # for the final st.rerun() so keyed selection widgets stay unique.
        if st.session_state.tool_status.get("state") == "running":
            draw_table()

    async def on_delta(text: str) -> None:
        st.session_state.stream_buf = st.session_state.get("stream_buf", "") + text
        paint_stream()

    try:
        selected = list(st.session_state.get("selected_creator_ids") or [])
        result = asyncio.run(
            application.chat(
                message,
                session_id=session_id,
                on_event=on_event,
                on_delta=on_delta,
                creator_ids=selected or None,
            )
        )
    except AgentError as exc:
        st.session_state.chat_error = f"{exc.code}: {exc}"
        if st.session_state.tool_status["state"] == "running":
            st.session_state.tool_status = {
                **st.session_state.tool_status,
                "state": "failed",
                "error_code": exc.code,
            }
    except Exception as exc:
        st.session_state.chat_error = f"unexpected_error: {type(exc).__name__}: {exc}"
        if st.session_state.tool_status.get("state") == "running":
            st.session_state.tool_status = {
                **st.session_state.tool_status,
                "state": "failed",
                "error_code": "unexpected_error",
            }
    else:
        st.session_state.chat_error = None
        st.session_state.stream_buf = ""
        st.session_state.stream_tools = []
        st.query_params["session"] = str(result.session_id)
        after = application.campaign(result.session_id)
        if is_generate_drafts_request(message) and after.drafts:
            # Chat never creates drafts; only reopen if drafts already exist.
            open_drafts_dialog()
    st.rerun()
