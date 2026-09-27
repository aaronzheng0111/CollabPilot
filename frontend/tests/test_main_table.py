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
    session_id = searched_session()
    campaign = create_application().campaign(session_id)
    expected = len(campaign.last_search.creators)

    at = open_session(session_id)

    frame = main_frame(at)
    assert len(frame) == expected >= 20
    assert {"creator_id", "display_name", "platforms", "source"} <= set(frame.columns)
    assert {"followers", "category", "topics", "audience_summary", "contact", "last_post"} <= set(
        frame.columns
    )
    assert (frame["source"] == "[MOCK]").all()
    assert frame.loc[frame["creator_id"] == "creator_001", "platforms"].item() == "tiktok、instagram"
    captions = "\n".join(item.value for item in at.caption)
    assert "关键词 翻译" in captions and "窗口 30 天" in captions and "粉丝门槛 无" in captions
    assert "正在执行" not in "\n".join(item.value for item in at.markdown)


def test_running_search_keeps_old_rows_and_shows_loading_layer() -> None:
    session_id = searched_session()
    running = {**initial_status(), "state": "running", "name": "search_creators"}

    at = open_session(session_id, tool_status=running)

    frame = main_frame(at)
    assert len(frame) >= 20, "previous result stays while the tool runs"
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


def test_idle_page_shows_catalog_not_blank() -> None:
    at = AppTest.from_file(APP).run()
    assert not at.exception
    frame = main_frame(at)
    assert len(frame) == 12
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
    assert frame["topics"].astype(str).str.contains(r"[、—]|AI|翻译").any()
    assert not frame["followers"].astype(str).str.contains(r"\{").any()