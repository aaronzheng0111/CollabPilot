from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


COLUMN_LABELS = {
    "creator_id": "creator_id",
    "display_name": "display_name",
    "reason": "原因",
    "brand_name": "合作品牌",
    "content_published_at": "合作日期",
    "source": "来源",
}


def excluded_title(count: int) -> str:
    return f"已排除 {count} 位"


def render_excluded_table(rows: list[dict[str, Any]], target: Any = st) -> None:
    """Collapsed by default; the title carries the count. Rows come from
    `workbench.excluded_rows`, each already tagged [RULE]."""
    if not rows:
        return
    with target.expander(excluded_title(len(rows)), expanded=False):
        frame = pd.DataFrame(rows, columns=list(COLUMN_LABELS))
        st.dataframe(frame, hide_index=True, width="stretch", column_config=COLUMN_LABELS)
