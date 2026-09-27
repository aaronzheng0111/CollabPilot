from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from collabpilot.campaign.follow_up import LLM_LABEL


PANEL_TITLE = "跟进"
SEND_LABELS = ("发送",)
COLUMNS = {
    "display_name": "创作者",
    "channel_label": "渠道",
    "next_step": "下一步",
    "status_label": "状态",
}


def render_follow_up_table(
    rows: list[dict[str, Any]] | None,
    *,
    model_name: str | None = None,
    follow_error: str | None = None,
    target: Any = st,
) -> None:
    """Secondary「跟进」table. Never renders a send button."""
    if not rows and not follow_error:
        return
    heading = f"#### {PANEL_TITLE}"
    if rows:
        source_model = model_name or rows[0].get("model_name") or "deepseek-chat"
        heading = f"#### {PANEL_TITLE} `{LLM_LABEL}` `{source_model}`"
    target.markdown(heading)
    if follow_error:
        target.caption(f"跟进未写入：{follow_error}")
    if rows:
        frame = pd.DataFrame(
            [
                {
                    "display_name": row["display_name"],
                    "channel_label": row["channel_label"],
                    "next_step": row["next_step"],
                    "status_label": row["status_label"],
                }
                for row in rows
            ]
        )
        target.dataframe(frame, hide_index=True, width="stretch", column_config=COLUMNS)
    target.markdown(
        '<span class="cp-pill cp-pill-mock-send">[MOCK-SEND]</span> 记下不等于发送',
        unsafe_allow_html=True,
    )
