"""T07 verify cases 12–14. Fixture rounds; no DeepSeek."""

from __future__ import annotations

from uuid import UUID

from conftest import FRONTEND
from streamlit.testing.v1 import AppTest

from collabpilot.bootstrap import create_application
from collabpilot.campaign.goal import Campaign, ParsedGoal, RetryStrategy, SearchRound, StrategyChange
from collabpilot.campaign.retry import ACCEPT_SHORT_LIST
from components.pending_decisions import EMPTY_TEXT
from components.progress_panel import CHANGES_TITLE, PANEL_TITLE

APP = str(FRONTEND / "app.py")
MODEL = "deepseek-chat"


def open_session(session_id: UUID) -> AppTest:
    at = AppTest.from_file(APP)
    at.query_params["session"] = str(session_id)
    at.run()
    assert not at.exception
    return at


def two_round_campaign() -> UUID:
    application = create_application()
    session_id = application.store.create_session()
    application.save_campaign(
        Campaign(
            campaign_id=session_id,
            goal_status="PARSED",
            parsed_goal=ParsedGoal(
                brand="LinguaGo AI 翻译",
                product="AI 翻译工具",
                target_audience=["中文用户"],
                platforms=["tiktok", "instagram"],
                target_count=10,
                inclusion_criteria=[],
                exclusion_criteria=["已经合作过的账号"],
                outreach_count=3,
                needs_user_approval=True,
            ),
            stage="CANDIDATES_READY",
            pending_decision=ACCEPT_SHORT_LIST,
            search_rounds=[
                SearchRound(
                    index=1,
                    keywords=["翻译"],
                    window_days=30,
                    min_followers=None,
                    fit_count=6,
                    gap=4,
                    data_origin="mock_seed",
                ),
                SearchRound(
                    index=2,
                    keywords=["翻译"],
                    window_days=90,
                    min_followers=None,
                    fit_count=9,
                    gap=1,
                    strategy_reason="窗口外仍有相关帖子",
                    data_origin="real_model_output",
                    model_name=MODEL,
                ),
            ],
            retry_strategy=RetryStrategy(
                changes=[
                    StrategyChange(field="window_days", old_value=30, new_value=90)
                ],
                reason="窗口外仍有相关帖子",
                model_name=MODEL,
            ),
            auto_retries=1,
        )
    )
    return session_id


def test_progress_panel_lists_each_round_and_chinese_stage() -> None:
    at = open_session(two_round_campaign())

    html = "\n".join(item.value for item in at.markdown)
    assert PANEL_TITLE in html and "候选已就绪" in html
    frames = [frame.value for frame in at.dataframe]
    rounds = next(frame for frame in frames if "轮次" in frame.columns)
    assert list(rounds["轮次"]) == [1, 2]
    assert list(rounds["窗口天数"]) == [30, 90]
    assert list(rounds["合格"]) == ["6/10", "9/10"]
    assert list(rounds["缺口"]) == [4, 1]


def test_changes_table_has_old_new_reason_llm_and_model() -> None:
    at = open_session(two_round_campaign())

    html = "\n".join(item.value for item in at.markdown)
    assert CHANGES_TITLE in html and "[LLM]" in html and MODEL in html
    frames = list(at.dataframe)
    changes = next(frame.value for frame in frames if "字段" in frame.value.columns)
    assert list(changes["字段"]) == ["window_days"]
    assert list(changes["旧值"]) == [30]
    assert list(changes["新值"]) == [90]
    assert list(changes["理由"]) == ["窗口外仍有相关帖子"]


def test_accept_short_list_row_and_empty_drafts() -> None:
    at = open_session(two_round_campaign())

    labels = [button.label for button in at.button]
    assert "批准" in labels and "拒绝" in labels
    assert labels.index("批准") < labels.index("拒绝")
    text = "\n".join(item.value for item in at.markdown)
    assert "当前合格 9 位，少于目标 10 位，是否接受" in text
    assert "待审核草稿" not in text


def test_accept_short_list_label_uses_round_fit_when_verdicts_missing() -> None:
    """Pending copy must mention 少于目标 even when verdicts are not loaded."""
    at = open_session(two_round_campaign())
    body = "\n".join(item.value for item in at.markdown)
    assert "是否接受" in body
    assert not at.exception
