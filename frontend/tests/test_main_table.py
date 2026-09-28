"""T03 verify cases 10–11. Backend runs with the mock provider; no DeepSeek."""

from __future__ import annotations

import asyncio
from uuid import UUID

from conftest import FRONTEND, main_layout_columns
from streamlit.testing.v1 import AppTest

from collabpilot.bootstrap import create_application
from collabpilot.campaign.workbench import main_table_rows, search_caption
from components.tool_status import initial_status

APP = str(FRONTEND / "app.py")
SAMPLE_TEXT = (
    "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
    "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
    "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。"
)


def searched_session() -> UUID:
    application = create_application()
    first = asyncio.run(application.chat(SAMPLE_TEXT))
    asyncio.run(application.chat("开始搜索", session_id=first.session_id))
    campaign = application.campaign(first.session_id)
    assert campaign.last_search is not None
    # The mock provider chains the T04 filter and T05 judgment; roll back to "search only".
    application.save_campaign(
        campaign.model_copy(update={"stage": "SEARCHING", "last_filter": None, "verdicts": None})
    )
    return first.session_id


def open_session(session_id: UUID, tool_status: dict | None = None) -> AppTest:
    at = AppTest.from_file(APP)
    at.query_params["session"] = str(session_id)
    if tool_status is not None:
        at.session_state["tool_status"] = tool_status
    at.run()
    assert not at.exception
    return at


def main_frame(at: AppTest):
    left, _right = main_layout_columns(at)
    return left.dataframe[0].value


def test_search_success_shows_m_rows_with_mock_and_params() -> None:
    from collabpilot.campaign.workbench import CATALOG_PAGE_SIZE

    session_id = searched_session()
    campaign = create_application().campaign(session_id)
    expected = len(campaign.last_search.creators)

    at = open_session(session_id)

    frame = main_frame(at)
    assert expected >= 20
    assert len(frame) == min(CATALOG_PAGE_SIZE, expected)
    assert {"creator_id", "display_name", "platforms", "source"} <= set(frame.columns)
    assert {"followers", "category", "topics", "audience_summary", "contact", "last_post"} <= set(
        frame.columns
    )
    assert (frame["source"] == "[MOCK]").all()
    captions = "\n".join(item.value for item in at.caption)
    assert "关键词 翻译" in captions and "窗口 30 天" in captions and "粉丝门槛 无" in captions
    assert f"共 {expected} 位" in captions
    assert "正在执行" not in "\n".join(item.value for item in at.markdown)
    # Paginate through all pages — every search hit is reachable, none dropped.
    seen: set[str] = set(frame["creator_id"].astype(str))
    while True:
        next_btns = [b for b in at.button if b.label == "下一页" and not b.disabled]
        if not next_btns:
            break
        next_btns[0].click().run()
        assert not at.exception
        seen.update(main_frame(at)["creator_id"].astype(str))
    assert seen == {c.creator_id for c in campaign.last_search.creators}
    assert "creator_001" in seen
    # Platforms for the dual-platform creator still merge when that row is shown.
    at = open_session(session_id)
    while "creator_001" not in set(main_frame(at)["creator_id"].astype(str)):
        nxt = [b for b in at.button if b.label == "下一页" and not b.disabled]
        assert nxt
        nxt[0].click().run()
    row = main_frame(at)
    assert row.loc[row["creator_id"] == "creator_001", "platforms"].item() == "tiktok、instagram"


def test_running_search_keeps_old_rows_and_shows_loading_layer() -> None:
    from collabpilot.campaign.workbench import CATALOG_PAGE_SIZE

    session_id = searched_session()
    campaign = create_application().campaign(session_id)
    expected = len(campaign.last_search.creators)
    running = {**initial_status(), "state": "running", "name": "search_creators"}

    at = open_session(session_id, tool_status=running)

    frame = main_frame(at)
    assert expected >= 20
    assert len(frame) == min(CATALOG_PAGE_SIZE, expected), "previous result stays while the tool runs"
    markup = "\n".join(item.value for item in at.markdown)
    assert "正在执行 search_creators" in markup and "cp-table-loading" in markup


def test_redraw_running_table_does_not_reuse_fixed_key() -> None:
    """Tool events call draw_table again in one run; a fixed key would crash."""
    from components.main_table import render_main_table

    rows = [{"display_name": "示例", "platforms": "tiktok", "followers": 1}]
    status = {**initial_status(), "state": "running", "name": "search_creators"}
    render_main_table(rows=rows, tool_status=status)
    render_main_table(rows=rows, tool_status=status)


def test_workbench_rows_follow_the_campaign() -> None:
    application = create_application()
    session_id = searched_session()
    campaign = application.campaign(session_id)

    rows = main_table_rows(campaign)
    assert [row["creator_id"] for row in rows] == campaign.last_search.creator_ids
    assert search_caption(campaign) == "关键词 翻译 · 窗口 30 天 · 粉丝门槛 无"
    assert main_table_rows(None) == [] and search_caption(None) is None
    assert main_table_rows(campaign.model_copy(update={"goal_status": "CLARIFYING"})) == []


def test_contact_column_config_keeps_full_channel_width() -> None:
    """可触达 must stay wide enough for「TikTok 私信、邮件、Instagram 私信」."""
    from components.main_table import (
        COLUMNS,
        CONTACT_COLUMN_WIDTH_PX,
        REGION_COLUMN_WIDTH_PX,
        TABLE_MIN_WIDTH_PX,
        creator_table_html,
        table_column_config,
        table_content_width,
    )
    import pandas as pd

    contact = table_column_config()["contact"]
    assert contact["label"] == "可触达"
    assert contact["width"] == CONTACT_COLUMN_WIDTH_PX
    assert CONTACT_COLUMN_WIDTH_PX >= 280
    assert REGION_COLUMN_WIDTH_PX >= 180
    width = table_content_width(list(COLUMNS))
    assert width >= TABLE_MIN_WIDTH_PX >= 1600
    assert width >= CONTACT_COLUMN_WIDTH_PX + 900
    html = creator_table_html(
        pd.DataFrame(
            [
                {
                    "display_name": "示例",
                    "region": "US、东南亚、中国大陆",
                    "engagement": "6%",
                    "contact": "TikTok 私信、邮件、Instagram 私信",
                    "last_post": "2026-01-01",
                }
            ]
        ),
        list(COLUMNS),
    )
    assert f"min-width:{width}px" in html
    assert "TikTok 私信、邮件、Instagram 私信" in html
    assert "US、东南亚、中国大陆" in html
    assert "可触达" in html and "最近发布" in html
    assert f"width:{REGION_COLUMN_WIDTH_PX}px!important" in html
    assert f"width:{CONTACT_COLUMN_WIDTH_PX}px!important" in html
    assert "选中" not in html  # checkbox picker owns selection UI


def test_selected_rows_highlight_and_identity_columns_stick() -> None:
    """After filtering, pinned identity columns stay put and checked creators are marked."""
    from components.main_table import COLUMN_MIN_WIDTHS_PX, creator_table_html
    import pandas as pd

    name_left = COLUMN_MIN_WIDTHS_PX["creator_id"]
    html = creator_table_html(
        pd.DataFrame(
            [
                {
                    "creator_id": "creator_001",
                    "display_name": "Amy学翻译",
                    "decision": "合适",
                    "选中": True,
                },
                {
                    "creator_id": "creator_020",
                    "display_name": "Tina工具箱",
                    "decision": "待确认",
                    "选中": False,
                },
            ]
        ),
        ["creator_id", "display_name", "decision", "选中"],
    )
    assert html.count('class="cp-row-selected"') == 1
    assert "Amy学翻译" in html and "Tina工具箱" in html
    assert "position:sticky;left:0px" in html
    assert f"position:sticky;left:{name_left}px" in html
    assert "cp-sticky-lead" in html and "cp-sticky-edge" in html


def test_idle_page_shows_catalog_not_blank() -> None:
    from collabpilot.campaign.workbench import CATALOG_PAGE_SIZE, catalog_browse_rows

    assert len(catalog_browse_rows()) == 40
    at = AppTest.from_file(APP).run()
    assert not at.exception
    frame = main_frame(at)
    assert len(frame) == CATALOG_PAGE_SIZE
    expected = {
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
    }
    assert expected <= set(frame.columns)
    assert "decision" not in frame.columns and "rank" not in frame.columns
    assert "示例达人" in "\n".join(item.value for item in at.caption)
    # Chinese headers via column_config; values are flat strings, not nested JSON.
    assert frame["topics"].astype(str).str.contains(r"[、—]|AI|翻译|护肤").any()
    assert not frame["followers"].astype(str).str.contains(r"\{").any()
    prev = next(b for b in at.button if b.label == "上一页")
    next_btns = [b for b in at.button if b.label == "下一页"]
    assert next_btns, "idle catalog must paginate beyond the first page"
    assert prev.disabled
    assert any(b.key == "cp-table-prev" for b in at.button)
    assert any(b.key == "cp-table-next" for b in at.button)
    next_btns[0].click().run()
    assert not at.exception
    page2 = main_frame(at)
    assert len(page2) > 0
    assert list(frame["display_name"]) != list(page2["display_name"])
    assert not next(b for b in at.button if b.label == "上一页").disabled