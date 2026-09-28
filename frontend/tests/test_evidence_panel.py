"""T05 verify cases 13–14 (+ case 2 UI half). Fixture verdicts; no DeepSeek."""

from __future__ import annotations

import asyncio
from uuid import UUID

from conftest import FRONTEND
from streamlit.testing.v1 import AppTest

from collabpilot.bootstrap import create_application
from collabpilot.campaign import mock_store
from collabpilot.campaign.audience import apply_audience_overrides
from collabpilot.campaign.topic_match import lock_topic_rejections
from collabpilot.campaign.verdict import Verdict, validate_verdicts
from collabpilot.campaign.workbench import main_table_rows
from components.evidence_panel import PANEL_TITLE, SELECT_LABEL

APP = str(FRONTEND / "app.py")
MODEL = "deepseek-chat"
SAMPLE_TEXT = (
    "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
    "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
    "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。"
)


def fixture_verdicts(kept_ids: list[str]) -> list[Verdict]:
    """3 fits (ranked 2,1,3 on purpose), one unfit, the rest pending, one with
    unknown GPM (creator_020)."""
    creators = mock_store.load()
    posts = {cid: sorted(creators[cid].post_ids()) for cid in kept_ids}
    raw = []
    for cid, rank in (("creator_002", 2), ("creator_001", 1), ("creator_003", 3)):
        raw.append(
            {
                "creator_id": cid,
                "decision": "fit",
                "reasons": [f"{cid} 持续发布本品使用内容"],
                "evidence_ids": posts[cid][:2],
                "related_post_ids": posts[cid],
                "topic_match": "match",
                "unknowns": [],
                "rank": rank,
            }
        )
    extra_fit = [
        cid
        for cid in ("creator_020", "creator_021", "creator_022", "creator_023")
        if cid in kept_ids
    ]
    for offset, cid in enumerate(extra_fit, start=4):
        raw.append(
            {
                "creator_id": cid,
                "decision": "fit",
                "reasons": [f"{cid} 持续发布本品使用内容"],
                "evidence_ids": posts[cid][:2],
                "related_post_ids": posts[cid],
                "topic_match": "match",
                "unknowns": [],
                "rank": offset,
            }
        )
    raw.append(
        {
            "creator_id": "creator_011",
            "decision": "unfit",
            "reasons": ["帖子主题是美妆内容，与 AI 翻译工具无关"],
            "evidence_ids": posts["creator_011"][:1],
            "related_post_ids": [],
            "topic_match": "mismatch",
            "mismatch_topic": "美妆",
            "quote": "5分钟通勤妆完整步骤",
            "unknowns": [],
            "rank": None,
        }
    )
    skip = {"creator_001", "creator_002", "creator_003", "creator_011", *extra_fit}
    for cid in kept_ids:
        if cid in skip:
            continue
        raw.append(
            {
                "creator_id": cid,
                "decision": "pending",
                "reasons": ["相关内容只有 1 条"],
                "evidence_ids": posts[cid][:1],
                "related_post_ids": posts[cid][:1],
                "topic_match": "unclear",
                "unknowns": [],
                "rank": None,
            }
        )
    batch = validate_verdicts(
        {"verdicts": raw}, {cid: creators[cid] for cid in kept_ids}, window_days=30, model_name=MODEL
    )
    assert batch.ok and not batch.rejected
    return batch.accepted


def judged_session() -> UUID:
    application = create_application()
    first = asyncio.run(application.chat(SAMPLE_TEXT))
    asyncio.run(application.chat("开始搜索", session_id=first.session_id))
    campaign = application.campaign(first.session_id)
    assert campaign.last_filter is not None
    creators = mock_store.load()
    verdicts = apply_audience_overrides(
        fixture_verdicts(campaign.last_filter.kept_ids),
        {cid: creators[cid] for cid in campaign.last_filter.kept_ids if cid in creators},
    )
    application.save_campaign(
        lock_topic_rejections(
            campaign.model_copy(
                update={
                    "verdicts": verdicts,
                    "verdict_model_name": MODEL,
                    "verdict_error": None,
                }
            ),
            verdicts,
        )
    )
    return first.session_id


def open_session(session_id: UUID) -> AppTest:
    at = AppTest.from_file(APP)
    at.query_params["session"] = str(session_id)
    at.run()
    assert not at.exception
    return at


def table_frame(session_id: UUID):
    import pandas as pd

    campaign = create_application().campaign(session_id)
    return pd.DataFrame(main_table_rows(campaign))


def markup(at: AppTest) -> str:
    return "\n".join(item.value for item in at.markdown)


def test_main_table_shows_decision_and_rank_in_order_with_llm() -> None:
    session_id = judged_session()

    at = open_session(session_id)

    frame = table_frame(session_id)
    assert list(frame["creator_id"][:3]) == ["creator_001", "creator_002", "creator_003"]
    assert list(frame["decision"][:3]) == ["合适", "合适", "合适"]
    assert list(frame["rank"][:3]) == [1, 2, 3]
    assert frame["decision"].iloc[-1] == "不合适" and frame["creator_id"].iloc[-1] == "creator_011"
    assert set(frame["decision"][3:-1]) == {"待确认"}
    assert (frame["source"] == "[MOCK] [RULE] [LLM]").all()
    assert len(frame) == 22


def test_evidence_panel_shows_reasons_posts_age_recency_unknowns_and_model() -> None:
    session_id = judged_session()

    at = open_session(session_id)

    select = next(item for item in at.selectbox if item.label == SELECT_LABEL)
    assert select.value == "creator_001", "top rank is selected by default"
    html = markup(at)
    assert PANEL_TITLE in html and "cp-evidence" in html
    assert "creator_001 持续发布本品使用内容" in html
    assert "<code>ig_media_001_1</code>" in html and "天前" in html
    assert "出差东京第3天，靠LinguaGo实时翻译搞定地铁问路和点餐" in html
    assert "窗口内相关帖子 6 条" in html
    assert "[LLM]" in html and MODEL in html
    assert "expected_decision_hint" not in html

    select.select("creator_020").run()
    assert not at.exception
    html = markup(at)
    assert "未知：gpm" in html and "未知：audience" in html
    assert "待确认" in html
    assert "年龄" in html and "性别" in html and "地区" in html and "兴趣" in html
    assert html.count("未知") >= 4
    assert "平台未公开受众画像" in html
    assert "[MOCK]" in html and "[RULE]" in html
    assert "受众未知" in html


def test_mismatch_row_and_panel_show_quote_lock_and_no_restore() -> None:
    session_id = judged_session()

    at = open_session(session_id)

    frame = table_frame(session_id)
    mismatch = frame[frame["creator_id"] == "creator_011"].iloc[0]
    assert mismatch["decision"] == "不合适"
    assert mismatch["topic"] == "主题不符：美妆"

    select = next(item for item in at.selectbox if item.label == SELECT_LABEL)
    select.select("creator_011").run()
    assert not at.exception
    html = markup(at)
    assert "主题不符：美妆" in html
    assert "5分钟通勤妆完整步骤" in html
    assert "tt_video_011_1" in html
    assert "[LLM]" in html
    assert "已锁定，不再推荐" in html and "[RULE]" in html
    assert "加回名单" not in html


def test_no_panel_before_verdicts() -> None:
    application = create_application()
    first = asyncio.run(application.chat(SAMPLE_TEXT))

    at = open_session(first.session_id)

    assert not [item for item in at.selectbox if item.label == SELECT_LABEL]
    assert '<div class="cp-evidence">' not in markup(at)
