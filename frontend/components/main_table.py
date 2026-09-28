from __future__ import annotations

from collections.abc import Callable
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from collabpilot.campaign.goal import CLARIFYING_TABLE_TEXT
from collabpilot.campaign.workbench import CATALOG_PAGE_SIZE


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
# Longest typical cell: 「TikTok 私信、邮件、Instagram 私信」— do not clip/ellipsis.
CONTACT_COLUMN_WIDTH_PX = 280
# 「US、东南亚、中国大陆」 must fit inside 地区 without spilling into 互动率.
REGION_COLUMN_WIDTH_PX = 180
# Floor so the scroll host always overflows the ~3/5 left column.
TABLE_MIN_WIDTH_PX = 1600
# Pixel mins per column; sum is the table content width inside the H-scroll host.
COLUMN_MIN_WIDTHS_PX: dict[str, int] = {
    "选中": 52,
    "creator_id": 100,
    "display_name": 140,
    "platforms": 110,
    "followers": 80,
    "category": 90,
    "topics": 160,
    "audience_summary": 140,
    "region": REGION_COLUMN_WIDTH_PX,
    "engagement": 80,
    "contact": CONTACT_COLUMN_WIDTH_PX,
    "last_post": 100,
    "source": 80,
    "filter": 80,
    "decision": 80,
    "rank": 60,
    "topic": 100,
    "audience": 100,
    "channel": 80,
    "saved": 60,
}
# Checkbox picker owns selection UI; keep it out of the H-scroll HTML table.
PICKER_ONLY_COLUMNS = ("选中",)
HIDDEN_COLUMNS = ("can_select",)
SCROLL_KEY = "cp-table-scroll"
PICKER_KEY = "cp-selection-picker"


def table_content_width(columns: list[str]) -> int:
    """Sum of column min-widths (excludes hidden / picker-only). Drives table pixel width."""
    total = sum(
        COLUMN_MIN_WIDTHS_PX.get(name, 100)
        for name in columns
        if name not in HIDDEN_COLUMNS and name not in PICKER_ONLY_COLUMNS
    )
    return max(TABLE_MIN_WIDTH_PX, total)


def table_column_config(**extra: Any) -> dict[str, Any]:
    """Column labels/widths (kept for tests; visible table is HTML)."""
    typed: dict[str, Any] = {
        "display_name": st.column_config.TextColumn(
            COLUMN_LABELS["display_name"], width=COLUMN_MIN_WIDTHS_PX["display_name"]
        ),
        "platforms": st.column_config.TextColumn(
            COLUMN_LABELS["platforms"], width=COLUMN_MIN_WIDTHS_PX["platforms"]
        ),
        "followers": st.column_config.TextColumn(
            COLUMN_LABELS["followers"], width=COLUMN_MIN_WIDTHS_PX["followers"]
        ),
        "category": st.column_config.TextColumn(
            COLUMN_LABELS["category"], width=COLUMN_MIN_WIDTHS_PX["category"]
        ),
        "topics": st.column_config.TextColumn(
            COLUMN_LABELS["topics"], width=COLUMN_MIN_WIDTHS_PX["topics"]
        ),
        "audience_summary": st.column_config.TextColumn(
            COLUMN_LABELS["audience_summary"],
            width=COLUMN_MIN_WIDTHS_PX["audience_summary"],
        ),
        "region": st.column_config.TextColumn(
            COLUMN_LABELS["region"], width=COLUMN_MIN_WIDTHS_PX["region"]
        ),
        "engagement": st.column_config.TextColumn(
            COLUMN_LABELS["engagement"], width=COLUMN_MIN_WIDTHS_PX["engagement"]
        ),
        "contact": st.column_config.TextColumn(
            "可触达",
            width=CONTACT_COLUMN_WIDTH_PX,
        ),
        "last_post": st.column_config.TextColumn(
            "最近发布", width=COLUMN_MIN_WIDTHS_PX["last_post"]
        ),
    }
    return {**COLUMN_LABELS, **typed, **extra}


def _cell_text(value: Any, column: str) -> str:
    if column == "选中":
        return "☑" if bool(value) else "☐"
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    text = str(value).strip()
    return text if text else "—"


def _row_selected(row: pd.Series) -> bool:
    if "选中" not in row.index:
        return False
    value = row.get("选中")
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return bool(value)


# Identity columns stay pinned while the rest of the row scrolls sideways.
_STICKY_COLUMNS = ("creator_id", "display_name")


def creator_table_html(frame: pd.DataFrame, columns: list[str]) -> str:
    """Fixed min-width HTML table so the scroll container (not Glide) can pan."""
    cols = [
        name
        for name in columns
        if name not in HIDDEN_COLUMNS and name not in PICKER_ONLY_COLUMNS
    ]
    width = table_content_width(cols)
    # Style block survives markdown sanitizers that drop inline style attrs.
    # Per-column width rules matter: without them table-layout:fixed collapses
    # columns and nowrap text paints over neighbors.
    col_rules = "".join(
        (
            f".st-key-cp-table-scroll .cp-creator-table .cp-col-{name},"
            f".st-key-cp-table-scroll .cp-creator-table .cp-td-{name},"
            f".cp-table-scroll-inline .cp-creator-table .cp-col-{name},"
            f".cp-table-scroll-inline .cp-creator-table .cp-td-{name}"
            f"{{width:{COLUMN_MIN_WIDTHS_PX.get(name, 100)}px!important;"
            f"min-width:{COLUMN_MIN_WIDTHS_PX.get(name, 100)}px!important;"
            f"max-width:{COLUMN_MIN_WIDTHS_PX.get(name, 100)}px!important}}"
        )
        for name in cols
    )
    sticky = [name for name in _STICKY_COLUMNS if name in cols]
    left = 0
    sticky_rules: list[str] = []
    for name in sticky:
        sticky_rules.append(
            f".st-key-cp-table-scroll .cp-creator-table .cp-col-{name},"
            f".st-key-cp-table-scroll .cp-creator-table .cp-td-{name},"
            f".cp-table-scroll-inline .cp-creator-table .cp-col-{name},"
            f".cp-table-scroll-inline .cp-creator-table .cp-td-{name}"
            f"{{position:sticky;left:{left}px;z-index:2}}"
        )
        sticky_rules.append(
            f".st-key-cp-table-scroll .cp-creator-table th.cp-col-{name},"
            f".cp-table-scroll-inline .cp-creator-table th.cp-col-{name}"
            f"{{z-index:4;background:#f5f0e8}}"
        )
        left += COLUMN_MIN_WIDTHS_PX.get(name, 100)
    sizing = (
        f"<style>"
        f".st-key-cp-table-scroll .cp-table-inner,"
        f".st-key-cp-table-scroll .cp-creator-table,"
        f".cp-table-scroll-inline .cp-table-inner,"
        f".cp-table-scroll-inline .cp-creator-table{{"
        f"min-width:{width}px!important;width:{width}px!important;max-width:none!important}}"
        f"{col_rules}"
        f"{''.join(sticky_rules)}"
        f"</style>"
    )
    colgroup = "".join(f'<col class="cp-col-{escape(name)}" />' for name in cols)
    lead = sticky[0] if sticky else None
    edge = sticky[-1] if sticky else None

    def _head_class(name: str) -> str:
        parts = [f"cp-col-{name}"]
        if name in sticky:
            parts.append("cp-sticky")
        if name == lead:
            parts.append("cp-sticky-lead")
        if name == edge:
            parts.append("cp-sticky-edge")
        return " ".join(parts)

    heads = "".join(
        f'<th scope="col" class="{_head_class(name)}">'
        f"{escape(str(COLUMN_LABELS.get(name, name)))}</th>"
        for name in cols
    )
    body_rows: list[str] = []
    for _, row in frame.iterrows():
        cells = "".join(
            f'<td class="{_head_class(name).replace("cp-col-", "cp-td-", 1)}">'
            f"{escape(_cell_text(row.get(name), name))}</td>"
            for name in cols
        )
        row_cls = ' class="cp-row-selected"' if _row_selected(row) else ""
        body_rows.append(f"<tr{row_cls}>{cells}</tr>")
    if not body_rows:
        span = len(cols) or 1
        body_rows.append(f'<tr><td colspan="{span}">—</td></tr>')
    return (
        f"{sizing}"
        f'<div class="cp-table-inner" style="min-width:{width}px;width:{width}px">'
        f'<table class="cp-creator-table" style="min-width:{width}px;width:{width}px">'
        f"<colgroup>{colgroup}</colgroup>"
        f"<thead><tr>{heads}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        f"</table></div>"
    )


SAVE_BUTTON = "保存到活动"
GENERATE_BUTTON = "生成草稿"
DRAFT_SELECT_LABEL = "合适达人"
DRAFT_SELECT_KEY = "draft-creator-select"
GENERATE_KEY = "generate-draft"
PAGE_KEY = "cp-table-page"
PAGE_SIG_KEY = "cp-table-page-sig"
CHECK_KEY = "cp-table-checks"
# Header + rows tall enough for the checkbox picker when present.
_GRID_HEADER_PX = 40
_GRID_ROW_PX = 35
SaveSelection = Callable[[list[str]], None]
GenerateDraft = Callable[[str], None]


def _grid_height(row_count: int) -> int:
    return _GRID_HEADER_PX + max(row_count, 1) * _GRID_ROW_PX


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


def _rows_signature(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "0"
    ids = [str(row.get("creator_id") or row.get("display_name") or i) for i, row in enumerate(rows)]
    return f"{len(rows)}:{','.join(ids[:3])}:{ids[-1]}"


def _sync_page(total: int, signature: str) -> int:
    pages = max(1, (total + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE)
    if st.session_state.get(PAGE_SIG_KEY) != signature:
        st.session_state[PAGE_SIG_KEY] = signature
        st.session_state[PAGE_KEY] = 0
        st.session_state[CHECK_KEY] = {}
    page = int(st.session_state.get(PAGE_KEY, 0))
    page = max(0, min(page, pages - 1))
    st.session_state[PAGE_KEY] = page
    return page


def _render_pager(target: Any, total: int, page: int) -> None:
    if total <= CATALOG_PAGE_SIZE:
        return
    pages = max(1, (total + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE)
    start = page * CATALOG_PAGE_SIZE + 1
    end = min(total, (page + 1) * CATALOG_PAGE_SIZE)

    def go_prev() -> None:
        st.session_state[PAGE_KEY] = max(0, page - 1)

    def go_next() -> None:
        st.session_state[PAGE_KEY] = min(pages - 1, page + 1)

    # Horizontal row via container (not stacked full-width buttons). Avoid
    # nested st.columns so AppTest still finds the page 3:2 pair by weight.
    pager = target.container(
        horizontal=True,
        vertical_alignment="center",
        horizontal_alignment="distribute",
        gap="small",
        key="cp-table-pager",
    )
    pager.caption(f"第 {start}–{end} / 共 {total} 位 · 第 {page + 1}/{pages} 页")
    actions = pager.container(horizontal=True, gap="small", vertical_alignment="center")
    actions.button("上一页", disabled=page <= 0, key="cp-table-prev", on_click=go_prev)
    actions.button("下一页", disabled=page >= pages - 1, key="cp-table-next", on_click=go_next)


def _merge_page_checks(full: pd.DataFrame, page_edited: pd.DataFrame) -> list[str]:
    """Keep checkbox choices across pages; return selected creator ids."""
    checks: dict[str, bool] = dict(st.session_state.get(CHECK_KEY) or {})
    if "creator_id" in full.columns and "选中" in full.columns and checks == {}:
        for _, row in full.iterrows():
            checks[str(row["creator_id"])] = bool(row.get("选中"))
    if "creator_id" in page_edited.columns and "选中" in page_edited.columns:
        for _, row in page_edited.iterrows():
            checks[str(row["creator_id"])] = bool(row.get("选中"))
    st.session_state[CHECK_KEY] = checks
    if "can_select" in full.columns:
        return [
            cid
            for cid, picked in checks.items()
            if picked
            and not full.loc[full["creator_id"].astype(str) == cid, "can_select"].empty
            and bool(full.loc[full["creator_id"].astype(str) == cid, "can_select"].iloc[0])
        ]
    return [cid for cid, picked in checks.items() if picked]


def _apply_checks(page_frame: pd.DataFrame) -> pd.DataFrame:
    checks = st.session_state.get(CHECK_KEY) or {}
    if not checks or "creator_id" not in page_frame.columns or "选中" not in page_frame.columns:
        return page_frame
    out = page_frame.copy()
    out["选中"] = [
        bool(checks.get(str(cid), bool(val)))
        for cid, val in zip(out["creator_id"], out["选中"], strict=False)
    ]
    return out


def _html_source(page_frame: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Visible columns for the HTML grid. Keep ``选中`` on the frame so rows can highlight."""
    visible = [
        name
        for name in columns
        if name not in HIDDEN_COLUMNS
        and name not in PICKER_ONLY_COLUMNS
        and name in page_frame.columns
    ]
    shown = page_frame.loc[:, visible].copy() if visible else page_frame.iloc[:, 0:0].copy()
    if "选中" in page_frame.columns:
        shown["选中"] = list(page_frame["选中"])
    return shown, visible


def _render_scroll_table(target: Any, page_frame: pd.DataFrame, columns: list[str]) -> None:
    shown, visible = _html_source(page_frame, columns)
    target.markdown(creator_table_html(shown, visible), unsafe_allow_html=True)


def _render_selection_picker(target: Any, page_frame: pd.DataFrame, page: int) -> pd.DataFrame:
    """Narrow checkbox editor below the HTML table — never overlaid on it."""
    host = target.container(key=PICKER_KEY)
    picker_cols = [name for name in ("选中", "display_name", "creator_id") if name in page_frame.columns]
    picker = page_frame.loc[:, picker_cols].copy()
    disabled = [name for name in picker_cols if name != "选中"]
    visible_order = [name for name in ("选中", "display_name") if name in picker_cols]
    return host.data_editor(
        picker,
        hide_index=True,
        width="stretch",
        height=_grid_height(len(page_frame)),
        column_config={
            "选中": st.column_config.CheckboxColumn(
                "选中",
                default=False,
                width=COLUMN_MIN_WIDTHS_PX["选中"],
            ),
            "display_name": st.column_config.TextColumn(
                COLUMN_LABELS["display_name"],
                width=COLUMN_MIN_WIDTHS_PX["display_name"],
            ),
        },
        column_order=visible_order,
        disabled=disabled,
        key=f"cp-selection-editor-{page}",
    )


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
    Long lists (idle catalog or search) are paginated; nothing is dropped.

    The creator grid is an HTML table with a fixed min-width inside
    ``cp-table-scroll`` so the *container* scrollbar reveals every column
    (Glide/dataframe shrink-to-fit cannot drive that overflow).
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
    all_rows = list(rows or [])
    columns = list(all_rows[0]) if all_rows else COLUMNS
    frame = pd.DataFrame(all_rows, columns=columns)
    total = len(all_rows)
    page = _sync_page(total, _rows_signature(all_rows)) if total else 0
    start = page * CATALOG_PAGE_SIZE
    page_frame = frame.iloc[start : start + CATALOG_PAGE_SIZE].copy()
    def mirror_page(host: Any, rows: pd.DataFrame, *, keyed: bool) -> None:
        """Dataframe mirror for AppTest. Avoid fixed keys while a tool runs
        (draw_table may redraw in the same script run)."""
        drop = [name for name in HIDDEN_COLUMNS if name in rows.columns]
        shown = rows.drop(columns=drop)
        if keyed:
            mirror = host.container(key="cp-table-mirror")
            mirror.dataframe(shown, hide_index=True, width="stretch", height=1)
        else:
            host.dataframe(shown, hide_index=True, width="stretch", height=1)

    if running:
        # No fixed element keys: mid-chat tool events redraw this slot in one run.
        # Skip pager buttons here — fixed keys would collide with the first draw.
        with target.container():
            st.markdown(loading_html(tool_status["name"] or ""), unsafe_allow_html=True)
            shown, visible = _html_source(page_frame, list(page_frame.columns))
            table = creator_table_html(shown, visible)
            st.markdown(
                f'<div class="cp-table-scroll-inline">{table}</div>',
                unsafe_allow_html=True,
            )
            mirror_page(st, page_frame, keyed=False)
        return []
    # Idle catalog / search / judged: H-scroll host holds the wide HTML table.
    scroll = target.container(key=SCROLL_KEY)
    if "选中" in frame.columns:
        page_frame = _apply_checks(page_frame)
        _render_scroll_table(scroll, page_frame, list(page_frame.columns))
        mirror_page(target, page_frame, keyed=True)
        edited = _render_selection_picker(target, page_frame, page)
        working = edited if isinstance(edited, pd.DataFrame) else page_frame
        selected = _merge_page_checks(frame, working)
        _render_pager(target, total, page)
        if on_save is not None:
            if target.button(SAVE_BUTTON, type="secondary", key="save-to-campaign"):
                on_save(selected)
        if on_generate is not None:
            fit_rows = _fit_draft_rows(frame)
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
    _render_scroll_table(scroll, page_frame, list(page_frame.columns))
    mirror_page(target, page_frame, keyed=True)
    _render_pager(target, total, page)
    return []
