"""T05 verify cases 1–11. Handwritten Verdict fixtures + mock_store; no DeepSeek."""

from __future__ import annotations

import inspect
import json
import re
from typing import Any
from uuid import uuid4

import pytest

from collabpilot.application import needs_evaluation
from collabpilot.campaign import mock_store, verdict as verdict_module
from collabpilot.campaign.goal import Campaign, ParsedGoal, validate_parsed_goal
from collabpilot.campaign.retry import fit_count
from collabpilot.campaign.verdict import (
    CANDIDATES_HEADING,
    ModelUnavailable,
    candidate_payload,
    render_campaign_prompt,
    render_candidates_message,
    sort_verdicts,
    validate_verdicts,
)
from collabpilot.campaign.workbench import evidence_view, main_table_rows
from collabpilot.domain.errors import ProviderError
from collabpilot.domain.models import Message, ModelResponse, ToolCall
from collabpilot.providers.base import Provider
from collabpilot.settings import PROJECT_ROOT
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.apply_hard_filters import ApplyHardFiltersTool
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool


ORACLE_WORDS = ("expected_ai_signals", "scenario_tags", "product_relation", "confidence")
MODEL = "deepseek-chat"
WINDOW = 30
PROMPT_PATH = PROJECT_ROOT / "config/prompts/campaign.md"


def creators() -> dict[str, mock_store.MergedCreator]:
    return mock_store.load()


def candidates(*ids: str) -> dict[str, mock_store.MergedCreator]:
    return {creator_id: creators()[creator_id] for creator_id in ids}


def first_post(creator_id: str) -> str:
    creator = creators()[creator_id]
    account = creator.tiktok or creator.instagram
    return account["recent_posts"][0]["post_id"]


def all_posts(creator_id: str) -> list[str]:
    return sorted(creators()[creator_id].post_ids())


def raw_fit(creator_id: str, rank: int | None = 1, **overrides: Any) -> dict[str, Any]:
    posts = all_posts(creator_id)
    return {
        "creator_id": creator_id,
        "decision": "fit",
        "reasons": ["持续发布本品使用内容"],
        "evidence_ids": posts[:2],
        "related_post_ids": posts,
        "topic_match": "match",
        "mismatch_topic": None,
        "quote": None,
        "unknowns": [],
        "rank": rank,
        **overrides,
    }


def raw_other(creator_id: str, decision: str = "pending", **overrides: Any) -> dict[str, Any]:
    post = first_post(creator_id) if creator_id in creators() else "tt_video_999_1"
    return {
        "creator_id": creator_id,
        "decision": decision,
        "reasons": ["相关内容只有 1 条"],
        "evidence_ids": [post],
        "related_post_ids": [post],
        "topic_match": "unclear",
        "unknowns": [],
        "rank": None,
        **overrides,
    }


def validate(items: list[dict[str, Any]], pool: dict | None = None):
    pool = pool or candidates(*[item["creator_id"] for item in items])
    return validate_verdicts({"verdicts": items}, pool, window_days=WINDOW, model_name=MODEL)


# --------------------------------------------------------------------------
# Cases 1, 5, 6, 7, 10: validation
# --------------------------------------------------------------------------


def test_unknown_evidence_id_rejects_only_that_verdict() -> None:
    batch = validate(
        [
            raw_fit("creator_001", rank=1),
            raw_fit("creator_002", rank=2, evidence_ids=["tt_video_999_1"]),
            raw_other("creator_003", evidence_ids=[first_post("creator_001")]),  # someone else's post
        ]
    )

    assert batch.ok
    assert [v.creator_id for v in batch.accepted] == ["creator_001"]
    assert [(r.creator_id, r.error_code) for r in batch.rejected] == [
        ("creator_002", "evidence_not_found"),
        ("creator_003", "evidence_not_found"),
    ]
    assert "tt_video_999_1" in batch.rejected[0].detail


def test_evidence_ids_may_point_at_product_usage_evidence() -> None:
    evidence_id = next(iter(creators()["creator_001"].evidence_ids()))
    batch = validate([raw_fit("creator_001", evidence_ids=[evidence_id])])

    assert batch.ok and batch.accepted[0].evidence_ids == [evidence_id]


def test_fit_without_evidence_or_related_posts_is_evidence_required() -> None:
    no_evidence = validate([raw_fit("creator_001", evidence_ids=[])])
    no_related = validate([raw_fit("creator_001", related_post_ids=[])])

    for batch in (no_evidence, no_related):
        assert batch.ok and batch.accepted == []
        assert batch.rejected[0].error_code == "evidence_required"


def test_three_fits_need_ranks_one_two_three() -> None:
    batch = validate(
        [raw_fit(cid, rank=rank) for cid, rank in zip(("creator_001", "creator_002", "creator_003"), (1, 2, 3))]
    )

    assert batch.ok
    assert sorted(v.rank for v in batch.accepted) == [1, 2, 3]
    assert len({v.rank for v in batch.accepted}) == 3


@pytest.mark.parametrize("ranks", [(1, 1, 2), (0, 1, 2), (1, 2, None), (1, 3, 4), (2, 3, 4)])
def test_bad_fit_ranks_drop_the_whole_batch(ranks) -> None:
    batch = validate(
        [raw_fit(cid, rank=rank) for cid, rank in zip(("creator_001", "creator_002", "creator_003"), ranks)]
        + [raw_other("creator_024")]
    )

    assert batch.error_code == "rank_invalid" and not batch.ok
    assert batch.accepted == []


@pytest.mark.parametrize("decision", ["unfit", "pending"])
def test_non_fit_rank_must_be_null(decision) -> None:
    good = validate([raw_other("creator_024", decision=decision, rank=None)])
    bad = validate([raw_other("creator_024", decision=decision, rank=1)])

    assert good.ok and good.accepted[0].rank is None
    assert bad.error_code == "rank_invalid" and bad.accepted == []


def test_fit_related_posts_must_belong_to_the_creator_and_drive_recency() -> None:
    posts = all_posts("creator_001")
    foreign = validate([raw_fit("creator_001", related_post_ids=[first_post("creator_002")])])
    assert foreign.rejected[0].error_code == "evidence_not_found"

    batch = validate([raw_fit("creator_001", related_post_ids=posts)])
    verdict = batch.accepted[0]
    ages = [post["age_days"] for post in creators()["creator_001"].posts()]

    assert verdict.recency is not None
    assert verdict.recency.recent_related_count == sum(1 for age in ages if age <= WINDOW) == 6
    assert verdict.recency.latest_related_age_days == min(ages)

    late = validate([raw_fit("creator_007", related_post_ids=all_posts("creator_007"))])
    assert late.accepted[0].recency.recent_related_count == 0
    assert late.accepted[0].recency.latest_related_age_days >= 40


def test_schema_and_unknown_creator_are_rejected_individually() -> None:
    batch = validate(
        [
            raw_fit("creator_001"),
            {"creator_id": "creator_002", "decision": "maybe", "reasons": []},
            raw_other("creator_999"),
        ],
        pool=candidates("creator_001", "creator_002"),
    )

    assert batch.ok and [v.creator_id for v in batch.accepted] == ["creator_001"]
    assert [(r.creator_id, r.error_code) for r in batch.rejected] == [
        ("creator_002", "schema_invalid"),
        ("creator_999", "not_in_candidates"),
    ]
    assert validate_verdicts("nonsense", {}, window_days=WINDOW, model_name=MODEL).error_code == "verdicts_invalid"
    assert validate_verdicts({"verdicts": []}, {}, window_days=WINDOW, model_name=MODEL).ok


# --------------------------------------------------------------------------
# Cases 3, 4: unknowns + provenance
# --------------------------------------------------------------------------


def test_unknown_gpm_is_added_to_unknowns_and_payload_has_no_number() -> None:
    creator = creators()["creator_020"]
    assert all(account["metrics"]["gpm_origin"] == "unknown" for _, account in creator.accounts())

    batch = validate([raw_other("creator_020", unknowns=[])])
    payload = candidate_payload(creator)

    assert "gpm" in batch.accepted[0].unknowns and "audience" in batch.accepted[0].unknowns
    assert all(account["gpm"] is None and account["gpm_origin"] == "unknown" for account in payload["accounts"])
    known = validate([raw_fit("creator_001")])
    assert "gpm" not in known.accepted[0].unknowns


def test_accepted_verdicts_carry_real_model_output_and_model_name() -> None:
    batch = validate([raw_fit("creator_001")])

    verdict = batch.accepted[0]
    assert verdict.data_origin == "real_model_output" and verdict.model_name == MODEL
    assert json.loads(verdict.model_dump_json())["model_name"] == MODEL


# --------------------------------------------------------------------------
# Case 8: ordering
# --------------------------------------------------------------------------


def test_sort_is_fit_rank_then_pending_then_unfit() -> None:
    batch = validate(
        [
            raw_other("creator_011", decision="unfit"),
            raw_fit("creator_002", rank=2),
            raw_other("creator_024"),
            raw_fit("creator_001", rank=1),
            raw_other("creator_025"),
            raw_fit("creator_003", rank=3),
        ]
    )

    ordered = sort_verdicts(batch.accepted)

    assert [(v.creator_id, v.decision) for v in ordered] == [
        ("creator_001", "fit"),
        ("creator_002", "fit"),
        ("creator_003", "fit"),
        ("creator_024", "pending"),
        ("creator_025", "pending"),
        ("creator_011", "unfit"),
    ]
    source = inspect.getsource(sort_verdicts)
    assert not re.search(r"follower|gpm|keyword|score", source)


# --------------------------------------------------------------------------
# Cases 2, 9: prompt
# --------------------------------------------------------------------------


def rendered_prompt() -> str:
    return render_campaign_prompt(
        PROMPT_PATH.read_text(encoding="utf-8"),
        brand=mock_store.load_brand(),
        goal_brand=mock_store.load_brand().name,
        goal_product=mock_store.load_brand().product,
        target_audience=["中文用户"],
        inclusion_criteria=["最近持续发布相关内容"],
        exclusion_criteria=["已经合作过的账号"],
        target_count=10,
        window_days=WINDOW,
    )


def test_prompt_does_not_substitute_a_catalog_brand() -> None:
    prompt = render_campaign_prompt(
        PROMPT_PATH.read_text(encoding="utf-8"),
        brand=mock_store.load_brand(),
        goal_brand=None,
        goal_product="美妆",
        target_audience=[],
        inclusion_criteria=[],
        exclusion_criteria=[],
        target_count=10,
        window_days=WINDOW,
    )
    catalog = mock_store.load_brand()
    assert catalog.name not in prompt
    assert "美妆" in prompt
    assert "未指定" in prompt


def test_prompt_and_candidates_have_no_oracle_fields() -> None:
    prompt = rendered_prompt()
    message = render_candidates_message(list(candidates("creator_001", "creator_020").values()))

    for word in ORACLE_WORDS:
        assert word not in PROMPT_PATH.read_text(encoding="utf-8")
        assert word not in prompt and word not in message
    assert "expected_decision_hint" not in message
    assert "{" not in prompt.split("输出格式")[0], "all placeholders filled"


def test_prompt_states_recency_priority_exclusion_rules_and_age_days() -> None:
    prompt = rendered_prompt()
    brand = mock_store.load_brand()
    message = render_candidates_message([creators()["creator_001"]])

    assert "优先最近持续发布相关内容" in prompt
    for rule in brand.exclusion_rules:
        assert rule in prompt
    assert "已经合作过的账号" in prompt and "中英日韩互译" in prompt
    assert "窗口：30 天" in prompt
    payload = json.loads(re.search(r"```json\n(.*?)\n```", message, re.DOTALL).group(1))
    posts = [post for account in payload[0]["accounts"] for post in account["posts"]]
    assert posts and all(isinstance(post["age_days"], int) for post in posts)
    assert message.startswith(CANDIDATES_HEADING)


# --------------------------------------------------------------------------
# Case 11 + application flow (cases 4, 8 persisted)
# --------------------------------------------------------------------------

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


class ScriptedProvider(Provider):
    name = "scripted"

    def __init__(self, responses: list[ModelResponse | Exception]):
        self.responses = list(responses)
        self.requests: list[list[Message]] = []

    async def complete(self, messages, model, tools, on_delta=None, temperature=None):
        self.requests.append([message.model_copy() for message in messages])
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def health(self, model: str) -> tuple[bool, str]:
        return True, "scripted"


def text(content: str) -> ModelResponse:
    return ModelResponse(content=content, provider="scripted", model=MODEL)


def verdict_reply(items: list[dict[str, Any]]) -> ModelResponse:
    return text("```json\n" + json.dumps({"verdicts": items}, ensure_ascii=False) + "\n```")


def tool_call(name: str, arguments: dict | None = None) -> ModelResponse:
    return ModelResponse(
        provider="scripted",
        model=MODEL,
        tool_calls=[ToolCall(id=f"c-{name}", name=name, arguments=arguments or {})],
    )


@pytest.fixture
def filtered(application):
    """PARSED goal + search + filter already done; verdicts still None."""

    async def make():
        session_id = application.store.create_session()
        goal = validate_parsed_goal(SAMPLE_GOAL)
        assert isinstance(goal, ParsedGoal)
        application.save_campaign(Campaign(campaign_id=session_id, goal_status="PARSED", parsed_goal=goal))
        context = ToolContext(session_id=session_id, turn_id=uuid4())
        assert (await SearchCreatorsTool(application.campaigns).execute({"keywords": ["翻译"]}, context)).ok
        assert (await ApplyHardFiltersTool(application.campaigns).execute({}, context)).ok
        campaign = application.campaign(session_id)
        assert needs_evaluation(campaign)
        return campaign

    return make


def scripted(application, monkeypatch, *responses) -> ScriptedProvider:
    provider = ScriptedProvider(list(responses))
    monkeypatch.setattr(application.providers, "get", lambda name: provider)
    return provider


async def test_provider_failure_becomes_model_unavailable_without_fallback(
    application, monkeypatch, filtered
) -> None:
    campaign = await filtered()
    provider = ScriptedProvider([ProviderError("boom")])

    with pytest.raises(ModelUnavailable) as raised:
        await application.evaluate_candidates(campaign, provider, MODEL)
    assert raised.value.code == "model_unavailable"

    events = []

    async def on_event(event):
        events.append((event.type, event.name, event.ok, event.error_code))

    scripted(application, monkeypatch, text("继续"), ProviderError("boom"))
    result = await application.chat("请判断", session_id=campaign.campaign_id, on_event=on_event)
    stored = application.campaign(campaign.campaign_id)

    assert "model_unavailable" in result.content
    assert stored.verdicts is None and stored.stage == "EVALUATING"
    assert stored.verdict_error == "model_unavailable"
    assert main_table_rows(stored) and all("decision" not in row for row in main_table_rows(stored))
    assert events[-2:] == [
        ("tool.started", "evaluate_candidates", None, None),
        ("tool.completed", "evaluate_candidates", False, "model_unavailable"),
    ]
    # No fallback list: nothing in the module orders creators by followers,
    # GPM or keyword hits.
    module_source = inspect.getsource(verdict_module)
    assert not re.search(r"sort\w*\([^)]*(follower|gpm|keyword|hit)", module_source)


async def test_chat_turn_searches_filters_and_persists_validated_verdicts(
    application, monkeypatch, filtered
) -> None:
    campaign = await filtered()
    kept = campaign.last_filter.kept_ids
    fits = [raw_fit("creator_001", 1), raw_fit("creator_002", 2), raw_fit("creator_003", 3)]
    others = [raw_other(cid) for cid in kept if cid not in ("creator_001", "creator_002", "creator_003", "creator_011")]
    bad = raw_other("creator_011", decision="unfit", evidence_ids=["nope"])
    provider = scripted(
        application, monkeypatch, text("已过滤，开始判断。"), verdict_reply(fits + others + [bad])
    )

    result = await application.chat("请判断", session_id=campaign.campaign_id)
    stored = application.campaign(campaign.campaign_id)

    assert len(provider.requests) == 2
    judgment = provider.requests[1]
    assert judgment[0].role == "system" and "优先最近持续发布相关内容" in judgment[0].content
    assert judgment[1].content.startswith(CANDIDATES_HEADING)
    assert stored.verdicts is not None and len(stored.verdicts) == len(kept) - 1
    assert stored.verdict_model_name == MODEL and stored.verdict_error is None
    assert [(v.creator_id, v.rank) for v in stored.verdicts[:3]] == [
        ("creator_001", 1),
        ("creator_002", 2),
        ("creator_003", 3),
    ]
    assert all(v.data_origin == "real_model_output" and v.model_name == MODEL for v in stored.verdicts)
    assert [(r.creator_id, r.error_code) for r in stored.verdict_rejected] == [("creator_011", "evidence_not_found")]
    assert "[LLM] deepseek-chat" in result.content and "合格 3/10" in result.content
    assert "应用层拒绝了 1 条判断" in result.content
    assert "creator_001" not in result.content
    assert "合适（按 rank）" not in result.content
    assert stored.pending_decision == "accept_short_list"
    assert "接受当前短名单" in result.content or "人数不足" in result.content
    # Do not pad: unfit / missing verdict for 011 stays out of fit count.
    assert fit_count(stored) == 3
    assert fit_count(stored) < 10

    rows = main_table_rows(stored)
    assert [row["creator_id"] for row in rows[:3]] == ["creator_001", "creator_002", "creator_003"]
    assert [row["decision"] for row in rows[:3]] == ["合适", "合适", "合适"]
    assert [row["rank"] for row in rows[:3]] == [1, 2, 3]
    assert rows[3]["decision"] == "待确认" and rows[-1] == {**rows[-1], "creator_id": "creator_011", "decision": "—"}
    assert all("[LLM]" in row["source"] for row in rows[:-1])

    view = evidence_view(stored, "creator_001")
    assert view["reasons"] == ["持续发布本品使用内容"]
    assert len(view["excerpts"]) == 2
    assert all(isinstance(item["age_days"], int) and item["text"] for item in view["excerpts"])
    assert view["recency"]["recent_related_count"] == 6 and view["model_name"] == MODEL
    assert evidence_view(stored, "creator_011") is None


async def test_invalid_batch_is_retried_once_then_left_empty(application, monkeypatch, filtered) -> None:
    campaign = await filtered()
    provider = scripted(
        application,
        monkeypatch,
        text("开始判断。"),
        verdict_reply([raw_fit("creator_001", 2)]),  # rank_invalid
        text("我不会输出 JSON"),
    )

    result = await application.chat("请判断", session_id=campaign.campaign_id)
    stored = application.campaign(campaign.campaign_id)

    assert len(provider.requests) == 3
    assert "rank_invalid" in provider.requests[2][-1].content
    assert stored.verdicts is None and stored.verdict_error == "verdicts_invalid"
    assert "verdicts_invalid" in result.content


async def test_evaluation_only_runs_once_per_filter(application, monkeypatch, filtered) -> None:
    campaign = await filtered()
    provider = scripted(
        application,
        monkeypatch,
        text("开始判断。"),
        verdict_reply([raw_fit("creator_001", 1)]),
        text("好的"),
    )

    await application.chat("请判断", session_id=campaign.campaign_id)
    await application.chat("谢谢", session_id=campaign.campaign_id)

    assert len(provider.requests) == 3
    assert not needs_evaluation(application.campaign(campaign.campaign_id))


async def test_mock_provider_runs_full_chain_with_pending_verdicts(application) -> None:
    sample = (
        "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
        "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
        "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。"
    )
    first = await application.chat(sample, provider_name="mock", model="collabpilot-mock")
    second = await application.chat(
        "开始搜索", session_id=first.session_id, provider_name="mock", model="collabpilot-mock"
    )
    stored = application.campaign(first.session_id)

    assert stored.verdicts is not None and len(stored.verdicts) == len(stored.last_filter.kept)
    assert all(v.decision == "pending" and v.rank is None for v in stored.verdicts)
    assert stored.verdict_model_name == "collabpilot-mock"
    assert "合格 0/10" in second.content
    assert "creator_001" not in second.content
