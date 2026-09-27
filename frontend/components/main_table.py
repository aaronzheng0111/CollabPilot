from __future__ import annotations

from collections.abc import Callable
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from collabpilot.campaign.goal import CLARIFYING_TABLE_TEXT


COLUMNS = [
    "display_name",
    "platforms",
    "followers",
    "category",
    "topics",
    "audience_summary",
    "region",
    "engagement",
    "contact",
    "last_post",
]
COLUMN_LABELS = {
    "creator_id": "creator_id",
    "display_name": "昵称",
    "platforms": "平台",
    "followers": "粉丝",
    "category": "品类",
    "topics": "内容主题",
    "audience_summary": "受众",
    "region": "地区",
    "engagement": "互动率",
    "contact": "可触达",
    "last_post": "最近发布",
    "filter": "filter",
    "decision": "decision",
    "rank": "rank",
    "topic": "主题判断",
    "audience": "受众判断",
    "选中": "选中",
    "saved": "saved",
    "channel": "channel",
    "source": "来源",
}
HIDDEN_COLUMNS = ("can_select",)
SAVE_BUTTON = "保存到活动"
GENERATE_BUTTON = "生成草稿"
DRAFT_SELECT_LABEL = "合适达人"
DRAFT_SELECT_KEY = "draft-creator-select"
GENERATE_KEY = "generate-draft"
SaveSelection = Callable[[list[str]], None]
GenerateDraft = Callable[[str], None]


def loading_html(tool_name: str) -> str:
    return (
        '<div class="cp-table-loading"><span class="cp-spinner"></span>'
        f"<span>正在执行 {escape(tool_name)}…</span></div>"
    )


def selected_creator_ids(frame: pd.DataFrame) -> list[str]:
    if frame.empty or "选中" not in frame.columns:
        return []
    selectable = frame["can_select"] if "can_select" in frame.columns else True
    picked = frame["选中"].fillna(False).astype(bool) & selectable.fillna(False).astype(bool)
    return [str(item) for item in frame.loc[picked, "creator_id"].tolist()]


def _fit_draft_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Only 合适 rows may get a draft control — never 待确认 / 不合适."""
    if frame.empty or "creator_id" not in frame.columns:
        return frame.iloc[0:0]
    if "decision" in frame.columns:
        return frame.loc[frame["decision"].astype(str) == "合适"]
    return frame.iloc[0:0]


def render_main_table(
    rows: list[dict[str, Any]] | None = None,
    goal_status: str | None = None,
    caption: str | None = None,
    skip_caption: str | None = None,
    tool_status: dict[str, Any] | None = None,
    on_save: SaveSelection | None = None,
    on_generate: GenerateDraft | None = None,
    target: Any = st,
) -> list[str]:
    """Rows are the last successful tool result. While a tool is `running`
    the old rows stay and a loading banner names the tool.

    The running overlay must not use a fixed Streamlit `key`: `draw_table`
    may run again on tool events in the same script run.

    ``on_generate`` receives exactly one ``creator_id`` per click — never a batch.
    """
    if goal_status == "CLARIFYING":
        # Old rows are dropped on purpose: no creators while the goal is unclear.
        target.markdown(
            f'<p class="cp-table-empty">{CLARIFYING_TABLE_TEXT}</p>', unsafe_allow_html=True
        )
        return []
    if caption:
        target.caption(caption)
    if skip_caption:
        target.caption(skip_caption)
    running = tool_status is not None and tool_status.get("state") == "running"
    columns = list(rows[0]) if rows else COLUMNS
    frame = pd.DataFrame(rows or [], columns=columns)
    if running:
        # No element key: mid-chat tool events redraw this slot in one run.
        with target.container():
            st.markdown(loading_html(tool_status["name"] or ""), unsafe_allow_html=True)
            st.dataframe(
                frame.drop(columns=[name for name in HIDDEN_COLUMNS if name in frame.columns]),
                hide_index=True,
                width="stretch",
                column_config=COLUMN_LABELS,
            )
        return []
    if "选中" in frame.columns:
        visible = [name for name in frame.columns if name not in HIDDEN_COLUMNS]
        disabled = [name for name in visible if name != "选中"]
        edited = target.data_editor(
            frame,
            hide_index=True,
            width="stretch",
            column_config={
                **COLUMN_LABELS,
                "选中": st.column_config.CheckboxColumn("选中", default=False),
            },
            column_order=visible,
            disabled=disabled,
            key="cp-selection-editor",
        )
        working = edited if isinstance(edited, pd.DataFrame) else frame
        selected = selected_creator_ids(working)
        if on_save is not None:
            if target.button(SAVE_BUTTON, type="secondary", key="save-to-campaign"):
                on_save(selected)
        if on_generate is not None:
            fit_rows = _fit_draft_rows(working)
            if not fit_rows.empty:
                options = [
                    str(row.get("display_name") or row["creator_id"])
                    for _, row in fit_rows.iterrows()
                ]
                id_by_label = {
                    str(row.get("display_name") or row["creator_id"]): str(row["creator_id"])
                    for _, row in fit_rows.iterrows()
                }
                chosen = target.selectbox(
                    DRAFT_SELECT_LABEL,
                    options,
                    key=DRAFT_SELECT_KEY,
                )
                if target.button(GENERATE_BUTTON, type="secondary", key=GENERATE_KEY):
                    on_generate(id_by_label[str(chosen)])
        return selected
    target.dataframe(frame, hide_index=True, width="stretch", column_config=COLUMN_LABELS)
    return []
