from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


COLUMNS = ["creator_id", "display_name", "platforms"]


def render_main_table(rows: list[dict[str, Any]] | None = None) -> None:
    frame = pd.DataFrame(rows or [], columns=COLUMNS)
    st.dataframe(frame, hide_index=True, width="stretch")
