from __future__ import annotations

from typing import Any

import streamlit as st

from collabpilot.campaign.drafts import LLM_LABEL, NO_CHANNEL_DRAFT_TEXT, PICK_CREATOR_FOR_DRAFT


PANEL_TITLE = "草稿"
GENERATE_HINT = PICK_CREATOR_FOR_DRAFT
EMPTY_SELECTION = PICK_CREATOR_FOR_DRAFT
REOPEN_BUTTON = "查看草稿"
CLOSE_BUTTON = "关闭"
OPEN_KEY = "open_drafts_dialog"
POPUP_DRAFT_IDS_KEY = "popup_draft_ids"
SEND_LABELS = ("发送",)
WILL_NOT_SEND = "草稿不会发送"


def open_drafts_dialog(draft_ids: list[str] | None = None) -> None:
    """Open the popup. Pass ``draft_ids`` to show only those (e.g. the one just written)."""
    st.session_state[OPEN_KEY] = True
    if draft_ids is not None:
        st.session_state[POPUP_DRAFT_IDS_KEY] = list(draft_ids)
    else:
        st.session_state.pop(POPUP_DRAFT_IDS_KEY, None)


def close_drafts_dialog() -> None:
    st.session_state[OPEN_KEY] = False
    st.session_state.pop(POPUP_DRAFT_IDS_KEY, None)


def _render_draft_bodies(
    rows: list[dict[str, Any]],
    *,
    model_name: str | None = None,
    target: Any = st,
) -> None:
    if rows:
        source_model = model_name or rows[0].get("model_name") or "deepseek-chat"
        target.markdown(f"`{LLM_LABEL}` `{source_model}`")
    for row in rows:
        channel_label = row.get("channel_label") or NO_CHANNEL_DRAFT_TEXT
        target.markdown(
            f'<div class="cp-draft-card">'
            f'<div class="cp-draft-header">'
            f'<strong>{row["display_name"]}</strong>'
            f'<span class="cp-pill">{channel_label}</span>'
            f'<span class="cp-pill cp-pill-decision">{row["status_label"]}</span>'
            f"</div></div>",
            unsafe_allow_html=True,
        )
        if row.get("cited_text"):
            target.markdown(f"> {row['cited_text']}")
        target.write(row["body"])
    if rows:
        target.markdown(
            f'<span class="cp-pill cp-pill-mock-send">[MOCK-SEND]</span> {WILL_NOT_SEND}',
            unsafe_allow_html=True,
        )


@st.dialog(PANEL_TITLE, width="large", on_dismiss=close_drafts_dialog)
def _drafts_popup(
    rows: list[dict[str, Any]], model_name: str | None = None
) -> None:
    """Modal for one or more drafts. Close via X / Esc / 「关闭」; reopen from 查看草稿."""
    _render_draft_bodies(rows, model_name=model_name)
    st.caption(WILL_NOT_SEND)
    if st.button(CLOSE_BUTTON, key="close-drafts-dialog", type="primary"):
        close_drafts_dialog()
        st.rerun()


def render_draft_cards(
    rows: list[dict[str, Any]] | None,
    *,
    can_generate: bool = False,
    model_name: str | None = None,
    draft_error: str | None = None,
    selection_hint: str | None = None,
    target: Any = st,
) -> None:
    """Chat-frame「草稿」: reopen button, list, and optional popup.

    Generate happens on the main-table per-creator button — never a batch
    control here. Never renders a send button. Popup opens when ``OPEN_KEY``
    is set (after generate / save-approve); cards stay listed so a closed
    popup is not a dead end and refresh still shows stored drafts.
    """
    rows = list(rows or [])
    if not rows and not can_generate and not draft_error and not selection_hint:
        return
    heading = f"#### {PANEL_TITLE}"
    if rows:
        source_model = model_name or rows[0].get("model_name") or "deepseek-chat"
        heading = f"#### {PANEL_TITLE} `{LLM_LABEL}` `{source_model}`"
    target.markdown(heading)
    if draft_error:
        target.caption(f"草稿未写入：{draft_error}")
    if selection_hint:
        target.caption(selection_hint)
    elif can_generate and not rows:
        target.caption(GENERATE_HINT)
    if rows:
        if target.button(REOPEN_BUTTON, type="secondary", key="reopen-drafts-dialog"):
            open_drafts_dialog()
            st.rerun()
        if st.session_state.get(OPEN_KEY):
            focus_ids = st.session_state.get(POPUP_DRAFT_IDS_KEY)
            popup_rows = (
                [row for row in rows if row.get("id") in focus_ids]
                if focus_ids
                else rows
            )
            _drafts_popup(popup_rows or rows, model_name)
        # Always keep an inline list so closing the modal is not a dead end.
        _render_draft_bodies(rows, model_name=model_name, target=target)
