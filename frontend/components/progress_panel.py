from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from collabpilot.campaign.verdict import LLM_LABEL


PANEL_TITLE = "进度"
CHANGES_TITLE = "调整了什么"


def progress_html(view: dict[str, Any]) -> str:
    title = f"{PANEL_TITLE} · {view['stage_label']}"
    return f'<h4>{escape(title)}</h4>'


def render_progress_panel(view: dict[str, Any] | None, target: Any = st) -> None:
    if not view:
        return
    target.markdown(progress_html(view), unsafe_allow_html=True)
    rounds = view["rounds"]
    frame = pd.DataFrame(
        [
            {
                "轮次": item["index"],
                "关键词": item["keywords"],
                "窗口天数": item["window_days"],
                "粉丝门槛": "无" if item["min_followers"] is None else item["min_followers"],
                "合格": f"{item['fit_count']}/{item['fit_count'] + item['gap']}",
                "缺口": item["gap"],
            }
            for item in rounds
        ]
    )
    target.dataframe(frame, hide_index=True, width="stretch")
    changes = view.get("changes") or []
    if not changes:
        return
    model = view.get("strategy_model") or ""
    target.markdown(
        f"#### {CHANGES_TITLE} "
        f'<span class="cp-pill cp-pill-llm">{escape(LLM_LABEL)}</span> '
        f'<span class="cp-pill"><code>{escape(model)}</code></span>',
        unsafe_allow_html=True,
    )
    change_frame = pd.DataFrame(
        [
            {
                "字段": item["field"],
                "旧值": item["old_value"],
                "新值": item["new_value"],
                "理由": item["reason"],
            }
            for item in changes
        ]
    )
    target.dataframe(change_frame, hide_index=True, width="stretch")
