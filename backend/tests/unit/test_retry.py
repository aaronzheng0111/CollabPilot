"""T07 verify cases 1–10, 14 (backend). Injected RetryStrategy; no DeepSeek."""

from __future__ import annotations

import inspect
import json
import re
from uuid import uuid4

import pytest

from collabpilot.campaign import mock_store, retry as retry_module
from collabpilot.campaign.decisions import approve_pending
from collabpilot.campaign.goal import (
    Campaign,
    ParsedGoal,
    RetryStrategy,
    SearchRound,
    StrategyChange,
    validate_parsed_goal,
)
from collabpilot.campaign.hard_filter import hard_filter
from collabpilot.campaign.retry import (
    ACCEPT_SHORT_LIST,
    ALLOWED_FIELDS,
    MAX_AUTO_RETRIES,
    MODEL_STRATEGY_REQUIRED,
    RULE_LOCKED,
    accept_fit_count,
    accept_retry_strategy,
    accept_short_list_label,
    append_search_round,
    apply_strategy_to_search,
    build_round_summary,
    drafts_empty,
    fit_count,
    parse_retry_strategy,
    qualified_lines,
    queue_accept_short_list,
    refresh_accept_short_list,
    round_from_search,
)
from collabpilot.campaign.topic_match import lock_topic_rejections
from collabpilot.campaign.verdict import validate_verdicts
from collabpilot.domain.models import Message, ModelResponse
from collabpilot.providers.base import Provider
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.apply_hard_filters import ApplyHardFiltersTool
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool


MODEL = "deepseek-chat"
ORACLE = ("expected_ai_signals", "scenario_tags", "product_relation", "confidence")
SAMPLE_GOAL = {
    "brand": None,
    "product": "AI 翻译工具",
    "target_audience": ["中文用户"],
    "platforms": [],
    "target_count": 10,
    "inclusion_criteria": ["最近持续发布相关内容"],
    "exclusion_criteria": ["已经合作过的账号"],
    "outreach_count": 3,
    "needs_user_approval": True,
}


def parsed_goal() -> ParsedGoal:
    goal = validate_parsed_goal(SAMPLE_GOAL)
    assert isinstance(goal, ParsedGoal)
    return goal


def strategy(new_window: int = 90, **overrides) -> RetryStrategy:
    payload = {
        "changes": [
            StrategyChange(field="window_days", old_value=30, new_value=new_window)
        ],
        "reason": "窗口外仍有相关内容",
        "model_name": MODEL,
        **overrides,
    }
    return RetryStrategy.model_validate(payload)


def raw_fit(creator_id: str, rank: int) -> dict:
    creator = mock_store.load()[creator_id]
    posts = sorted(creator.post_ids())
    return {
        "creator_id": creator_id,
        "decision": "fit",
        "reasons": ["持续发布"],
        "evidence_ids": posts[:2],
        "related_post_ids": posts,
        "topic_match": "match",
        "unknowns": [],
        "rank": rank,
    }


def raw_pending(creator_id: str) -> dict:
    post = sorted(mock_store.load()[creator_id].post_ids())[0]
    return {
        "creator_id": creator_id,
        "decision": "pending",
        "reasons": ["相关内容只有 1 条"],
        "evidence_ids": [post],
        "related_post_ids": [post],
        "topic_match": "unclear",
        "unknowns": [],
        "rank": None,
    }


async def searched_filtered(application, keywords: list[str] | None = None) -> Campaign:
    session_id = application.store.create_session()
    application.save_campaign(
        Campaign(campaign_id=session_id, goal_status="PARSED", parsed_goal=parsed_goal())
    )
    context = ToolContext(session_id=session_id, turn_id=uuid4())
    assert (await SearchCreatorsTool(application.campaigns).execute(
        {"keywords": keywords or ["翻译"]}, context
    )).ok
    assert (await ApplyHardFiltersTool(application.campaigns).execute({}, context)).ok
    return application.campaign(session_id)


def with_fits(campaign: Campaign, ids: list[str]) -> Campaign:
    creators = mock_store.load()
    kept = campaign.last_filter.kept_ids if campaign.last_filter else ids
    raw = [raw_fit(cid, rank) for rank, cid in enumerate(ids, 1)]
    raw += [raw_pending(cid) for cid in kept if cid not in ids]
    batch = validate_verdicts(
        {"verdicts": raw},
        {cid: creators[cid] for cid in kept if cid in creators},
        window_days=campaign.last_search.window_days if campaign.last_search else 30,
        model_name=MODEL,
    )
    assert batch.ok
    updated = campaign.model_copy(update={"verdicts": batch.accepted})
    mismatch = [v for v in batch.accepted if v.topic_match == "mismatch"]
    updated = lock_topic_rejections(updated, mismatch)
    return append_search_round(updated)


# --------------------------------------------------------------------------
# Cases 1, 6
# --------------------------------------------------------------------------


async def test_first_round_insufficient_shows_qualified_and_gap(application) -> None:
    campaign = with_fits(await searched_filtered(application), ["creator_001", "creator_002"])

    lines = qualified_lines(campaign)
    assert fit_count(campaign) < 10
    assert lines == ["合格 2/10", "缺口 8"]
    round1 = campaign.search_rounds[0]
    assert round1.index == 1 and round1.data_origin == "mock_seed"
    assert round1.window_days == 30 and round1.fit_count == 2 and round1.gap == 8


def test_auto_retry_budget_is_zero_for_demo_shortfall() -> None:
    assert MAX_AUTO_RETRIES == 0
    source = inspect.getsource(retry_module)
    assert not re.search(r"window_days\s*=\s*90", source)
    assert "ALLOWED_FIELDS" in source
    assert "MAX_AUTO_RETRIES = 0" in source


# --------------------------------------------------------------------------
# Cases 2, 7, 8
# --------------------------------------------------------------------------


def test_missing_strategy_is_model_strategy_required_and_does_not_change_window() -> None:
    round1 = SearchRound(
        index=1,
        keywords=["翻译"],
        window_days=30,
        min_followers=None,
        fit_count=6,
        gap=4,
        data_origin="mock_seed",
    )
    outcome = accept_retry_strategy(round1, None)

    assert not outcome.ok and outcome.error_code == MODEL_STRATEGY_REQUIRED
    assert outcome.params is None
    assert round1.window_days == 30


def test_locked_fields_return_rule_locked() -> None:
    round1 = SearchRound(
        index=1, keywords=["翻译"], window_days=30, min_followers=None,
        fit_count=6, gap=4, data_origin="mock_seed",
    )
    raw = {
        "changes": [{"field": "include_own_brand", "old_value": False, "new_value": True}],
        "reason": "把已合作的人加回来",
    }
    parsed = parse_retry_strategy(raw, MODEL)
    assert parsed.error_code == RULE_LOCKED

    raw2 = {
        "changes": [{"field": "include_keyword_mismatch", "old_value": False, "new_value": True}],
        "reason": "放宽主题",
        "include_keyword_mismatch": True,
    }
    assert parse_retry_strategy(raw2, MODEL).error_code == RULE_LOCKED
    assert accept_retry_strategy(
        round1,
        RetryStrategy(
            changes=[StrategyChange(field="include_own_brand", old_value=False, new_value=True)],
            reason="x",
            model_name=MODEL,
        ),
    ).error_code == RULE_LOCKED


def test_valid_strategy_returns_params_with_old_new_reason() -> None:
    round1 = SearchRound(
        index=1, keywords=["翻译"], window_days=30, min_followers=None,
        fit_count=6, gap=4, data_origin="mock_seed",
    )
    accepted = accept_retry_strategy(round1, strategy())
    assert accepted.ok
    assert accepted.params["window_days"] == 90
    assert accepted.params["keywords"] == ["翻译"]
    assert accepted.strategy.model_name == MODEL
    assert accepted.strategy.data_origin == "real_model_output"
    assert accepted.strategy.reason
    change = accepted.strategy.changes[0]
    assert (change.field, change.old_value, change.new_value) == ("window_days", 30, 90)


def test_keyword_json_string_and_numeric_strings_are_coerced() -> None:
    round1 = SearchRound(
        index=1, keywords=["翻译"], window_days=30, min_followers=None,
        fit_count=6, gap=4, data_origin="mock_seed",
    )
    accepted = accept_retry_strategy(
        round1,
        RetryStrategy(
            changes=[
                StrategyChange(field="window_days", old_value="30", new_value="90"),
                StrategyChange(field="keywords", old_value=["翻译"], new_value='["翻译", "AI"]'),
            ],
            reason="覆盖窗口外命中并补关键词",
            model_name=MODEL,
        ),
    )
    assert accepted.ok
    assert accepted.params["window_days"] == 90
    assert accepted.params["keywords"] == ["翻译", "AI"]


# --------------------------------------------------------------------------
# Case 9
# --------------------------------------------------------------------------


async def test_round_summary_has_counts_outside_window_and_no_oracle(application) -> None:
    campaign = with_fits(await searched_filtered(application), ["creator_001"])
    campaign = campaign.model_copy(update={"topic_rejected_ids": ["creator_011"]})
    summary = build_round_summary(campaign)
    dumped = json.dumps(summary.model_dump(), ensure_ascii=False)

    assert summary.round.window_days == 30
    assert summary.round.keywords == ["翻译"]
    assert summary.round.fit_count == 1
    assert summary.round.gap == 9
    assert summary.outside_window_hits >= 3
    assert summary.not_selected.own_brand_cooperated >= 1
    assert summary.not_selected.topic_mismatch == 1
    assert summary.not_selected.pending >= 1
    for word in ORACLE:
        assert word not in dumped
    assert set(ALLOWED_FIELDS) == {"window_days", "min_followers", "keywords"}


# --------------------------------------------------------------------------
# Cases 3, 10
# --------------------------------------------------------------------------


async def test_injected_window_90_adds_007_009_excludes_011_019(application) -> None:
    campaign = await searched_filtered(application)
    locked = [f"creator_{i:03d}" for i in range(11, 16)]
    campaign = campaign.model_copy(update={"topic_rejected_ids": locked})
    round1 = round_from_search(campaign, index=1)
    outcome = accept_retry_strategy(round1, strategy())
    assert outcome.ok and outcome.params is not None

    result = apply_strategy_to_search(campaign, outcome.params, mock_store.load())
    ids = {item.creator_id for item in result.creators}
    kept, removed = hard_filter(
        [mock_store.load()[cid] for cid in ids],
        ["tiktok", "instagram"],
    )
    kept_ids = {item.creator_id for item in kept}

    assert {"creator_007", "creator_008", "creator_009"} <= kept_ids
    assert not {f"creator_{i:03d}" for i in range(11, 20)} & kept_ids
    assert all(item.reason != "own_brand_cooperated" or item.creator_id not in kept_ids for item in removed)
    assert not (set(locked) & kept_ids)


# --------------------------------------------------------------------------
# Cases 4, 5
# --------------------------------------------------------------------------


async def test_still_short_sets_accept_short_list_and_reject_does_not_promote(application) -> None:
    campaign = with_fits(await searched_filtered(application), ["creator_001"])
    campaign = campaign.model_copy(
        update={
            "stage": "CANDIDATES_READY",
            "pending_decision": ACCEPT_SHORT_LIST,
            "auto_retries": 1,
        }
    )
    before = [v.model_dump() for v in campaign.verdicts or []]
    assert drafts_empty(campaign)

    refused = approve_pending(campaign, ACCEPT_SHORT_LIST, user_approved=False)
    assert refused.status == "approval_required"
    assert [v.model_dump() for v in refused.campaign.verdicts or []] == before
    assert not any(
        original["decision"] != "fit" and updated.decision == "fit"
        for original, updated in zip(before, refused.campaign.verdicts or [], strict=True)
    )

    accepted = approve_pending(campaign, ACCEPT_SHORT_LIST, user_approved=True)
    assert accepted.ok
    assert accepted.campaign.pending_decision is None
    assert accepted.campaign.stage == "CANDIDATES_READY"
    assert drafts_empty(accepted.campaign)


class Scripted(Provider):
    name = "scripted"

    def __init__(self, responses: list[ModelResponse]):
        self.responses = list(responses)
        self.requests: list[list[Message]] = []

    async def complete(self, messages, model, tools, on_delta=None, temperature=None):
        self.requests.append(messages)
        return self.responses.pop(0)

    async def health(self, model: str) -> tuple[bool, str]:
        return True, "ok"


async def test_valid_strategy_runs_second_round_once_then_asks_to_accept(
    application, monkeypatch
) -> None:
    # Demo caps auto-retry at 0; exercise the still-supported second-round path.
    monkeypatch.setattr("collabpilot.application.MAX_AUTO_RETRIES", 1)
    monkeypatch.setattr(retry_module, "MAX_AUTO_RETRIES", 1)
    campaign = await searched_filtered(application)
    kept = campaign.last_filter.kept_ids
    round1 = [raw_fit("creator_001", 1)] + [raw_pending(cid) for cid in kept if cid != "creator_001"]
    strategy_json = {
        "changes": [{"field": "window_days", "old_value": 30, "new_value": 90}],
        "reason": "窗口外仍有相关帖子",
    }
    round2_ids = ["creator_001", "creator_007"]
    round2 = [raw_fit("creator_001", 1), raw_fit("creator_007", 2)]
    provider = Scripted(
        [
            ModelResponse(content="判断。", provider="scripted", model=MODEL),
            ModelResponse(
                content="```json\n" + json.dumps({"verdicts": round1}, ensure_ascii=False) + "\n```",
                provider="scripted",
                model=MODEL,
            ),
            ModelResponse(
                content="```json\n" + json.dumps(strategy_json, ensure_ascii=False) + "\n```",
                provider="scripted",
                model=MODEL,
            ),
            ModelResponse(
                content="```json\n" + json.dumps({"verdicts": round2}, ensure_ascii=False) + "\n```",
                provider="scripted",
                model=MODEL,
            ),
        ]
    )
    monkeypatch.setattr(application.providers, "get", lambda name: provider)

    result = await application.chat("请判断", session_id=campaign.campaign_id)
    stored = application.campaign(campaign.campaign_id)

    assert stored.auto_retries == 1
    assert stored.retry_strategy is not None
    assert stored.retry_strategy.model_name == MODEL
    assert "window_days" in result.content and "30" in result.content and "90" in result.content
    assert "窗口外仍有相关帖子" in result.content
    assert "[LLM]" in result.content and MODEL in result.content
    assert stored.last_search.window_days == 90
    assert {"creator_007", "creator_008", "creator_009"} <= set(stored.last_search.creator_ids)
    assert stored.pending_decision == ACCEPT_SHORT_LIST
    assert stored.stage == "CANDIDATES_READY"
    assert drafts_empty(stored)
    assert len(stored.search_rounds) == 2
    assert stored.search_rounds[1].data_origin == "real_model_output"
    own_brand, locked = (
        {item.creator_id for item in stored.last_filter.removed if item.reason == "own_brand_cooperated"},
        set(stored.topic_rejected_ids),
    )
    kept_now = set(stored.last_filter.kept_ids)
    assert not own_brand & kept_now
    assert not locked & kept_now
    # A third auto retry does not happen.
    assert stored.auto_retries == 1


async def test_first_round_shortfall_queues_accept_without_auto_retry(
    application, monkeypatch
) -> None:
    """Demo: MAX_AUTO_RETRIES=0 → show 合格 n/10 after first judgment, no pad."""
    campaign = await searched_filtered(application)
    kept = campaign.last_filter.kept_ids
    fits = [raw_fit("creator_001", 1), raw_fit("creator_002", 2)]
    others = [raw_pending(cid) for cid in kept if cid not in ("creator_001", "creator_002")]
    provider = Scripted(
        [
            ModelResponse(content="判断。", provider="scripted", model=MODEL),
            ModelResponse(
                content="```json\n"
                + json.dumps({"verdicts": fits + others}, ensure_ascii=False)
                + "\n```",
                provider="scripted",
                model=MODEL,
            ),
        ]
    )
    monkeypatch.setattr(application.providers, "get", lambda name: provider)

    result = await application.chat("请判断", session_id=campaign.campaign_id)
    stored = application.campaign(campaign.campaign_id)

    assert MAX_AUTO_RETRIES == 0
    assert "合格 2/10" in result.content
    assert "人数不足" in result.content or "接受当前短名单" in result.content
    assert "不会把主题不符或受众未知改成合适" in result.content
    assert stored.pending_decision == ACCEPT_SHORT_LIST
    assert stored.auto_retries == 0
    assert len(stored.search_rounds) == 1
    assert stored.last_search is not None and stored.last_search.window_days == 30
    assert fit_count(stored) == 2
    assert fit_count(stored) < 10
    assert drafts_empty(stored)


async def test_chat_without_strategy_does_not_open_round_two(application, monkeypatch) -> None:
    monkeypatch.setattr("collabpilot.application.MAX_AUTO_RETRIES", 1)
    monkeypatch.setattr(retry_module, "MAX_AUTO_RETRIES", 1)
    campaign = await searched_filtered(application)
    kept = campaign.last_filter.kept_ids
    fits = [raw_fit("creator_001", 1)]
    others = [raw_pending(cid) for cid in kept if cid != "creator_001"]
    provider = Scripted(
        [
            ModelResponse(content="判断。", provider="scripted", model=MODEL),
            ModelResponse(
                content="```json\n"
                + json.dumps({"verdicts": fits + others}, ensure_ascii=False)
                + "\n```",
                provider="scripted",
                model=MODEL,
            ),
            ModelResponse(content="没有策略", provider="scripted", model=MODEL),
        ]
    )
    monkeypatch.setattr(application.providers, "get", lambda name: provider)

    result = await application.chat("请判断", session_id=campaign.campaign_id)
    stored = application.campaign(campaign.campaign_id)

    assert "合格 1/10" in result.content and "缺口 9" in result.content
    assert MODEL_STRATEGY_REQUIRED in result.content
    assert stored.last_search.window_days == 30
    assert stored.auto_retries == 0
    assert len(stored.search_rounds) == 1
    assert stored.stage == "INSUFFICIENT"
    strategy_turn = provider.requests[-1]
    assert "outside_window_hits" in strategy_turn[-1].content
    for word in ORACLE:
        assert word not in strategy_turn[-1].content


def test_accept_short_list_label_uses_five_fit_verdicts_not_zero() -> None:
    """Pending accept must echo live fit verdicts (5), never a stale 0."""
    fits = [
        raw_fit(f"creator_{i:03d}", i)
        for i in range(1, 6)
    ]
    creators = mock_store.load()
    batch = validate_verdicts(
        {"verdicts": fits},
        {item["creator_id"]: creators[item["creator_id"]] for item in fits},
        window_days=30,
        model_name=MODEL,
    )
    assert batch.ok
    campaign = Campaign(
        campaign_id=uuid4(),
        goal_status="PARSED",
        parsed_goal=parsed_goal(),
        stage="CANDIDATES_READY",
        pending_decision=ACCEPT_SHORT_LIST,
        pending_payload={"fit_count": 0, "target": 10},
        verdicts=batch.accepted,
        search_rounds=[
            SearchRound(
                index=1,
                keywords=["翻译"],
                window_days=30,
                min_followers=None,
                fit_count=0,
                gap=10,
                data_origin="mock_seed",
            ),
            SearchRound(
                index=2,
                keywords=["翻译"],
                window_days=90,
                min_followers=None,
                fit_count=0,
                gap=10,
                data_origin="real_model_output",
                model_name=MODEL,
            ),
        ],
        auto_retries=1,
    )
    label = accept_short_list_label(campaign)
    assert "当前合格 5 位" in label
    assert "当前合格 0 位" not in label
    assert accept_fit_count(campaign) == 5

    refreshed = refresh_accept_short_list(campaign)
    assert refreshed.pending_decision == ACCEPT_SHORT_LIST
    assert refreshed.pending_payload == {"fit_count": 5, "target": 10}
    assert "当前合格 5 位" in accept_short_list_label(refreshed)


def test_queue_accept_short_list_stores_live_fit_count() -> None:
    campaign = Campaign(
        campaign_id=uuid4(),
        goal_status="PARSED",
        parsed_goal=parsed_goal(),
        stage="CANDIDATES_READY",
        pending_decision=ACCEPT_SHORT_LIST,
        pending_payload={"fit_count": 0, "target": 10},
        search_rounds=[
            SearchRound(
                index=1,
                keywords=["翻译"],
                window_days=30,
                min_followers=None,
                fit_count=5,
                gap=5,
                data_origin="mock_seed",
            )
        ],
        auto_retries=1,
    )
    # No verdicts: fall back to round fit_count so the card is not stuck at 0.
    assert "当前合格 5 位" in accept_short_list_label(campaign)
    queued = queue_accept_short_list(campaign)
    assert queued.pending_payload == {"fit_count": 5, "target": 10}


def test_retain_prior_fits_survives_demoting_second_batch() -> None:
    from collabpilot.campaign.verdict import retain_prior_fits

    creators = mock_store.load()
    ids = [f"creator_{i:03d}" for i in range(1, 6)]
    pool = {cid: creators[cid] for cid in ids}
    prior = validate_verdicts(
        {"verdicts": [raw_fit(cid, rank) for rank, cid in enumerate(ids, 1)]},
        pool,
        window_days=30,
        model_name=MODEL,
    ).accepted
    demoted = validate_verdicts(
        {"verdicts": [raw_pending(cid) for cid in ids]},
        pool,
        window_days=30,
        model_name=MODEL,
    ).accepted
    merged = retain_prior_fits(prior, demoted, ids)
    assert sum(1 for item in merged if item.decision == "fit") == 5
    label = accept_short_list_label(
        Campaign(
            campaign_id=uuid4(),
            goal_status="PARSED",
            parsed_goal=parsed_goal(),
            pending_decision=ACCEPT_SHORT_LIST,
            verdicts=merged,
        )
    )
    assert "当前合格 5 位" in label
