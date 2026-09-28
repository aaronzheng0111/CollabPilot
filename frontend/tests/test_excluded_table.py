"""T04 verify cases 7–8. Backend runs with the mock provider; no DeepSeek."""

from __future__ import annotations

import asyncio
from uuid import UUID

from conftest import FRONTEND, main_layout_columns
from streamlit.testing.v1 import AppTest

from collabpilot.bootstrap import create_application
from components.excluded_table import excluded_title

APP = str(FRONTEND / "app.py")
SAMPLE_TEXT = (
    "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
    "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
    "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。"
)


def filtered_session() -> UUID:
    application = create_application()
    first = asyncio.run(application.chat(SAMPLE_TEXT))
    asyncio.run(application.chat("开始搜索", session_id=first.session_id))
    campaign = application.campaign(first.session_id)
    assert campaign.last_filter is not None
    # The mock provider also runs the T05 judgment; roll back to "filter only".
    application.save_campaign(campaign.model_copy(update={"verdicts": None}))
    return first.session_id


def open_session(session_id: UUID) -> AppTest:
    at = AppTest.from_file(APP)
    at.query_params["session"] = str(session_id)
    at.run()
    assert not at.exception
    return at


def test_main_table_rows_equal_kept_with_filter_column() -> None:
    from collabpilot.campaign.workbench import CATALOG_PAGE_SIZE

    session_id = filtered_session()
    campaign = create_application().campaign(session_id)
    kept = list(campaign.last_filter.kept_ids)

    at = open_session(session_id)

    left, _right = main_layout_columns(at)
    frame = left.dataframe[0].value
    assert list(frame["creator_id"]) == kept[:CATALOG_PAGE_SIZE]
    assert (frame["filter"] == "kept").all()
    assert (frame["source"] == "[MOCK] [RULE]").all()
    # Paginate through every kept id — none dropped, exclusions stay out.
    seen: set[str] = set(frame["creator_id"].astype(str))
    while True:
        nxt = [b for b in at.button if b.label == "下一页" and not b.disabled]
        if not nxt:
            break
        nxt[0].click().run()
        assert not at.exception
        left, _ = main_layout_columns(at)
        seen.update(left.dataframe[0].value["creator_id"].astype(str))
    assert seen == set(kept)
    assert not seen & {"creator_016", "creator_017", "creator_018", "creator_019"}


def test_excluded_table_is_collapsed_with_reason_brand_date_and_rule() -> None:
    session_id = filtered_session()

    at = open_session(session_id)

    expander = next(item for item in at.expander if item.label == excluded_title(4))
    assert expander.proto.expanded is False
    frame = expander.dataframe[0].value
    assert set(frame["creator_id"]) == {"creator_016", "creator_017", "creator_018", "creator_019"}
    assert set(frame["reason"]) == {"已合作本品牌"}
    assert set(frame["brand_name"]) == {"LinguaGo AI 翻译"}
    assert set(frame["content_published_at"]) == {"2026-06-08"}
    assert (frame["source"] == "[RULE]").all()
    assert set(frame.columns) >= {"display_name"}


def test_no_excluded_table_before_filter() -> None:
    application = create_application()
    result = asyncio.run(application.chat(SAMPLE_TEXT))

    at = open_session(result.session_id)

    assert not [item for item in at.expander if item.label.startswith("已排除")]
