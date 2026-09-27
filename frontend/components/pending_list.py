from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


LIST_TITLE = "待确认"
EMPTY_TEXT = "没有待确认的创作者"


def pending_list_html(items: list[dict[str, Any]]) -> str:
    rows = "".join(
        '<div class="cp-pending-row">'
        f'<code>{escape(item["creator_id"])}</code>'
        f'<span class="cp-pending-reason">{escape(item["pending_reason"])}</span>'
        f'<span class="cp-pill cp-pill-rule">{escape(item.get("source") or "")}</span>'
        "</div>"
        for item in items
    )
    return (
        f'<div class="cp-pending-list"><h4>{LIST_TITLE}</h4>'
        f"{rows or f'<p class=\"cp-evidence-muted\">{EMPTY_TEXT}</p>'}"
        "</div>"
    )


def render_pending_list(items: list[dict[str, Any]] | None, target: Any = st) -> None:
    """Secondary「待确认」list, separate from the fit-ranked main table."""
    if not items:
        return
    target.markdown(pending_list_html(items), unsafe_allow_html=True)
