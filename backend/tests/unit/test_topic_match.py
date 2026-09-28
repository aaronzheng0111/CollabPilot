"""T06 verify cases 1–5, 7. Handwritten Verdict fixtures; no DeepSeek."""

from __future__ import annotations

import inspect
import json
import re
from uuid import uuid4

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import Campaign, FilterRecord, ParsedGoal, validate_parsed_goal
from collabpilot.campaign.hard_filter import RULE_LABEL, KeptCreator
from collabpilot.campaign.topic_match import (
    LOCKED_TEXT,
    QUOTE_NOT_FOUND,
    TOPIC_CONFLICT,
    drop_locked_ids,
    fit_creator_ids,
    ids_excluded_from_judgment,
    lock_topic_rejections,
    skipped_locked_note,
    topic_badge,
    validate_topic_verdicts,
)
from collabpilot.campaign.verdict import candidate_payload, render_campaign_prompt, validate_verdicts
from collabpilot.campaign.workbench import evidence_view, main_table_rows
from collabpilot.domain.models import ModelResponse
from collabpilot.settings import PROJECT_ROOT
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.apply_hard_filters import ApplyHardFiltersTool
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool


MODEL = "deepseek-chat"
WINDOW = 30
PROMPT_PATH = PROJECT_ROOT / "config" / "prompts" / "campaign.md"
SRC = PROJECT_ROOT / "src"
QUOTE_011 = "5分钟通勤妆完整步骤"


def creators() -> dict[str, mock_store.MergedCreator]:
    return mock_store.load()


def posts(creator_id: str) -> list[str]:
    return sorted(creators()[creator_id].post_ids())


def first_post(creator_id: str) -> str:
    return posts(creator_id)[0]


def raw_mismatch(creator_id: str = "creator_011", **overrides):
    post = first_post(creator_id)
    payload = {
        "creator_id": creator_id,
        "decision": "unfit",
        "reasons": ["帖子主题与本品无关"],
        "evidence_ids": [post],
        "related_post_ids": [],
        "topic_match": "mismatch",
        "mismatch_topic": "美妆",
        "quote": QUOTE_011,
        "unknowns": [],
        "rank": None,
    }
    payload.update(overrides)
    return payload


def raw_fit(creator_id: str, rank: int = 1, **overrides):
    ids = posts(creator_id)
    payload = {
        "creator_id": creator_id,
        "decision": "fit",
        "reasons": ["持续发布本品使用内容"],
        "evidence_ids": ids[:2],
        "related_post_ids": ids,
        "topic_match": "match",
        "mismatch_topic": None,
        "quote": None,
        "unknowns": [],
        "rank": rank,
    }
    payload.update(overrides)
    return payload


def as_verdicts(items: list[dict], pool: dict | None = None):
    pool = pool or {item["creator_id"]: creators()[item["creator_id"]] for item in items}
    batch = validate_verdicts({"verdicts": items}, pool, window_days=WINDOW, model_name=MODEL)
    assert batch.ok, batch.error_code
    return batch.accepted, pool


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


# --------------------------------------------------------------------------
# Cases 1, 2: topic_conflict / quote_not_found
# --------------------------------------------------------------------------


def test_mismatch_plus_fit_is_topic_conflict_and_not_saved() -> None:
    accepted, pool = as_verdicts(
        [raw_fit("creator_001"), raw_mismatch(decision="fit", rank=2, related_post_ids=posts("creator_011"))]
    )
    topic = validate_topic_verdicts(accepted, pool)

    assert [v.creator_id for v in topic.accepted] == ["creator_001"]
    assert [(r.creator_id, r.error_code) for r in topic.rejected] == [
        ("creator_011", TOPIC_CONFLICT)
    ]


def test_unclear_fit_is_topic_conflict() -> None:
    accepted, pool = as_verdicts([raw_fit("creator_001", topic_match="unclear")])
    topic = validate_topic_verdicts(accepted, pool)

    assert topic.accepted == []
    assert topic.rejected[0].error_code == TOPIC_CONFLICT


def test_mismatch_missing_topic_evidence_or_quote_is_quote_not_found() -> None:
    cases = [
        raw_mismatch(mismatch_topic=""),
        raw_mismatch(mismatch_topic=None),
        raw_mismatch(quote="这段话完全不是帖子原文"),
        raw_mismatch(quote="高" * 81, mismatch_topic="美妆"),
        raw_mismatch(evidence_ids=["ev_tt_011_1"], quote=QUOTE_011),
        raw_mismatch(quote=""),
    ]
    for item in cases:
        accepted, pool = as_verdicts([item])
        topic = validate_topic_verdicts(accepted, pool)
        assert topic.accepted == []
        assert topic.rejected[0].error_code == QUOTE_NOT_FOUND, item


def test_valid_mismatch_quote_must_be_post_substring() -> None:
    accepted, pool = as_verdicts([raw_mismatch()])
    topic = validate_topic_verdicts(accepted, pool)

    assert [v.creator_id for v in topic.accepted] == ["creator_011"]
    assert topic.rejected == []


# --------------------------------------------------------------------------
# Cases 3, 4, 7: lock, skip later rounds, GPM does not upgrade, labels
# --------------------------------------------------------------------------


def test_lock_puts_mismatch_in_topic_rejected_ids() -> None:
    accepted, pool = as_verdicts([raw_fit("creator_001"), raw_mismatch()])
    topic = validate_topic_verdicts(accepted, pool)
    campaign = lock_topic_rejections(
        Campaign(campaign_id=uuid4(), verdicts=topic.accepted), topic.accepted
    )

    assert campaign.topic_rejected_ids == ["creator_011"]
    assert campaign.topic_locks[0].rule is True
    assert campaign.topic_locks[0].quoted_post_id == first_post("creator_011")
    assert campaign.topic_locks[0].data_origin == "rule"
    assert "creator_011" not in fit_creator_ids(campaign)
    assert fit_creator_ids(campaign) == ["creator_001"]


async def test_locked_ids_are_dropped_from_later_search_and_judgment(application) -> None:
    session_id = application.store.create_session()
    goal = validate_parsed_goal(SAMPLE_GOAL)
    assert isinstance(goal, ParsedGoal)
    accepted, _pool = as_verdicts([raw_mismatch()])
    topic = validate_topic_verdicts(accepted, { "creator_011": creators()["creator_011"] })
    campaign = lock_topic_rejections(
        Campaign(campaign_id=session_id, goal_status="PARSED", parsed_goal=goal, verdicts=topic.accepted),
        topic.accepted,
    )
    application.save_campaign(campaign)

    context = ToolContext(session_id=session_id, turn_id=uuid4())
    search = await SearchCreatorsTool(application.campaigns).execute({"keywords": ["翻译"]}, context)
    stored = application.campaign(session_id)

    assert search.ok
    assert "creator_011" not in stored.last_search.creator_ids
    assert skipped_locked_note(1) in search.display
    kept, skipped = drop_locked_ids(["creator_001", "creator_011"], stored.topic_rejected_ids)
    assert kept == ["creator_001"] and skipped == 1
    assert "creator_011" in ids_excluded_from_judgment(stored)


def test_high_gpm_mismatch_stays_out_of_fit() -> None:
    creator = creators()["creator_012"]
    gpm = mock_store.gpm(creator.tiktok or creator.instagram)
    brand = mock_store.load_brand()
    assert gpm is not None and brand.target_gpm == 20 and gpm > brand.target_gpm

    quote = mock_store.post_text(creator.posts()[0])[:20]
    accepted, pool = as_verdicts(
        [
            raw_fit("creator_001"),
            raw_mismatch(
                "creator_012",
                mismatch_topic="美妆",
                quote=quote,
                evidence_ids=[creator.posts()[0]["post_id"]],
            ),
        ]
    )
    topic = validate_topic_verdicts(accepted, pool)
    campaign = lock_topic_rejections(
        Campaign(campaign_id=uuid4(), verdicts=topic.accepted), topic.accepted
    )

    assert "creator_012" in campaign.topic_rejected_ids
    assert "creator_012" not in fit_creator_ids(campaign)
    source = inspect.getsource(fit_creator_ids) + inspect.getsource(validate_topic_verdicts)
    assert not re.search(r"target_gpm|video_gpm|gpm\s*>", source)


def test_mismatch_judgment_is_llm_lock_is_rule() -> None:
    accepted, pool = as_verdicts([raw_mismatch()])
    topic = validate_topic_verdicts(accepted, pool)
    campaign = lock_topic_rejections(
        Campaign(campaign_id=uuid4(), verdicts=topic.accepted), topic.accepted
    )
    view = evidence_view(campaign, "creator_011")
    rows = main_table_rows(
        campaign.model_copy(
            update={
                "goal_status": "PARSED",
                "last_filter": FilterRecord(
                    kept=[
                        KeptCreator(
                            creator_id="creator_011",
                            display_name="翻译剪辑君",
                            platforms=["tiktok"],
                            account_ids=["tiktok:@subtitle.cut"],
                        )
                    ],
                    removed=[],
                ),
            }
        )
    )

    assert view["judgment_source"] == "[LLM]" and view["data_origin"] == "real_model_output"
    assert view["lock_source"] == RULE_LABEL and view["locked"] is True
    assert view["lock_text"] == LOCKED_TEXT
    assert view["quoted_post_id"] == first_post("creator_011")
    assert view["quote"] == QUOTE_011
    assert view["can_restore"] is False
    assert rows[0]["decision"] == "不合适"
    assert rows[0]["topic"] == "主题不符：美妆"
    assert "[LLM]" in rows[0]["source"] and RULE_LABEL in rows[0]["source"]
    assert topic_badge(topic.accepted[0]) == "主题不符：美妆"


async def test_evaluate_skips_locked_and_does_not_rejudge(application, monkeypatch) -> None:
    from collabpilot.providers.base import Provider

    session_id = application.store.create_session()
    goal = validate_parsed_goal(SAMPLE_GOAL)
    assert isinstance(goal, ParsedGoal)
    accepted, _ = as_verdicts([raw_mismatch()])
    topic = validate_topic_verdicts(accepted, {"creator_011": creators()["creator_011"]})
    locked = lock_topic_rejections(
        Campaign(campaign_id=session_id, goal_status="PARSED", parsed_goal=goal),
        topic.accepted,
    )
    application.save_campaign(locked)
    context = ToolContext(session_id=session_id, turn_id=uuid4())
    assert (await SearchCreatorsTool(application.campaigns).execute({"keywords": ["翻译"]}, context)).ok
    assert (await ApplyHardFiltersTool(application.campaigns).execute({}, context)).ok
    stored = application.campaign(session_id)
    assert "creator_011" not in stored.last_filter.kept_ids

    class Capture(Provider):
        name = "capture"

        def __init__(self):
            self.user_text = ""

        async def complete(self, messages, model, tools, on_delta=None, temperature=None):
            self.user_text = messages[-1].content
            kept = stored.last_filter.kept_ids
            items = []
            rank = 1
            for cid in kept:
                if cid == "creator_001":
                    items.append(raw_fit(cid, rank))
                    rank += 1
                else:
                    items.append(
                        {
                            "creator_id": cid,
                            "decision": "pending",
                            "reasons": ["待确认"],
                            "evidence_ids": [first_post(cid)],
                            "related_post_ids": [first_post(cid)],
                            "topic_match": "unclear",
                            "unknowns": [],
                            "rank": None,
                        }
                    )
            import json

            return ModelResponse(
                content="```json\n" + json.dumps({"verdicts": items}, ensure_ascii=False) + "\n```",
                provider=self.name,
                model=MODEL,
            )

        async def health(self, model: str) -> tuple[bool, str]:
            return True, "ok"

    provider = Capture()
    batch, model_name, skipped = await application.evaluate_candidates(stored, provider, MODEL)
    assert batch.ok
    assert "creator_011" not in provider.user_text
    assert all(v.creator_id != "creator_011" for v in batch.accepted)
    assert "creator_011" not in fit_creator_ids(
        lock_topic_rejections(stored.model_copy(update={"verdicts": batch.accepted}), batch.accepted)
    )


# --------------------------------------------------------------------------
# Case 5: runtime source does not read oracle fields
# --------------------------------------------------------------------------


def test_runtime_source_does_not_read_keyword_mismatch_or_scenario_tags() -> None:
    hits: list[str] = []
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if path.name == "mock_store.py":
            assert "keyword_mismatch" not in text
            continue
        if "scenario_tags" in text:
            hits.append(str(path.relative_to(SRC)))
            continue
        # T07 names a locked strategy field `include_keyword_mismatch`; that is
        # not a read of the oracle tag `keyword_mismatch`.
        if re.search(r"(?<![A-Za-z_])keyword_mismatch(?![A-Za-z_])", text):
            hits.append(str(path.relative_to(SRC)))
    assert hits == []

    prompt = render_campaign_prompt(
        PROMPT_PATH.read_text(encoding="utf-8"),
        brand=mock_store.load_brand(),
        goal_brand=None,
        goal_product=None,
        target_audience=["中文用户"],
        inclusion_criteria=[],
        exclusion_criteria=["已经合作过的账号"],
        target_count=10,
        window_days=WINDOW,
    )
    assert "昵称或话题命中关键词不代表内容相关" in prompt
    payload = candidate_payload(creators()["creator_011"])
    assert "keyword_mismatch" not in json.dumps(payload, ensure_ascii=False)


def test_verdict_summary_names_topic_mismatch_and_keeps_them_out_of_fit() -> None:
    from collabpilot.application import render_verdict_summary
    from collabpilot.campaign.goal import ParsedGoal

    accepted, pool = as_verdicts(
        [raw_fit("creator_001", 1), raw_mismatch()]
    )
    topic = validate_topic_verdicts(accepted, pool)
    campaign = lock_topic_rejections(
        Campaign(
            campaign_id=uuid4(),
            goal_status="PARSED",
            parsed_goal=ParsedGoal(
                brand="LinguaGo",
                product="AI 翻译",
                target_audience=["中文用户"],
                platforms=["tiktok"],
                target_count=10,
                inclusion_criteria=[],
                exclusion_criteria=[],
                outreach_count=None,
                needs_user_approval=True,
            ),
            verdicts=topic.accepted,
            verdict_model_name=MODEL,
        ),
        topic.accepted,
    )
    text = render_verdict_summary(campaign)
    assert "主题不符" in text and ("未入名单" in text or "不计入合格" in text)
    assert "合格 1/10" in text
    assert "creator_011" not in text
    assert "creator_011" not in fit_creator_ids(campaign)
    assert "接受当前短名单" in text or "生成草稿" in text
    assert "主题不符与受众未知不计入合格" in text
