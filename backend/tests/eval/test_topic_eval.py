"""T06 verify case 6: DeepSeek topic mismatch on 011–015 vs 001–006.

Not part of the unit run. `cd backend && uv run pytest -m eval -s`.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import (
    Campaign,
    CreatorRef,
    FilterRecord,
    ParsedGoal,
    SearchRecord,
    validate_parsed_goal,
)
from collabpilot.campaign.hard_filter import KeptCreator
from collabpilot.campaign.topic_match import lock_topic_rejections, validate_topic_verdicts


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
FIT_CONTROL = {f"creator_{index:03d}" for index in range(1, 7)}
KEYWORD_MISMATCH = {f"creator_{index:03d}" for index in range(11, 16)}


def _kept(creator_id: str) -> KeptCreator:
    creator = mock_store.load()[creator_id]
    return KeptCreator(
        creator_id=creator.creator_id,
        display_name=creator.display_name,
        platforms=creator.platforms,
        account_ids=[
            f"{platform}:{account['handle']}" for platform, account in creator.accounts()
        ],
    )


@pytest.mark.eval
async def test_keyword_mismatch_creators_are_unfit(eval_application) -> None:
    application = eval_application
    session_id = application.store.create_session()
    goal = validate_parsed_goal(SAMPLE_GOAL)
    assert isinstance(goal, ParsedGoal)
    ids = sorted(FIT_CONTROL | KEYWORD_MISMATCH)
    application.save_campaign(
        Campaign(
            campaign_id=session_id,
            goal_status="PARSED",
            parsed_goal=goal,
            stage="EVALUATING",
            last_search=SearchRecord(
                keywords=["翻译", "AI", "英语", "留学"],
                window_days=30,
                min_followers=None,
                platforms=["tiktok", "instagram"],
                creators=[
                    CreatorRef(
                        creator_id=cid,
                        display_name=mock_store.load()[cid].display_name,
                        platforms=mock_store.load()[cid].platforms,
                    )
                    for cid in ids
                ],
            ),
            last_filter=FilterRecord(kept=[_kept(cid) for cid in ids], removed=[]),
        )
    )
    campaign = application.campaign(session_id)
    provider = application.providers.get(application.settings.model.default_provider)
    batch, model_name, _skipped = await application.evaluate_candidates(
        campaign, provider, application.settings.model.default_model
    )

    print("\n=== raw topic verdicts ===")
    print(json.dumps([v.model_dump() for v in batch.accepted], ensure_ascii=False, indent=1))
    print("=== rejected ===", [r.model_dump() for r in batch.rejected])
    assert batch.ok, batch.error_code

    creators = mock_store.load()
    topic = validate_topic_verdicts(batch.accepted, {cid: creators[cid] for cid in ids})
    locked = lock_topic_rejections(
        campaign.model_copy(update={"verdicts": topic.accepted}), topic.accepted
    )
    decisions = {v.creator_id: v for v in topic.accepted}
    oracle = mock_store.load_oracle()
    mismatches: list[str] = []
    for creator_id in ids:
        verdict = decisions.get(creator_id)
        tags = oracle[creator_id]["scenario_tags"]
        if verdict is None:
            mismatches.append(f"{creator_id}: no accepted verdict (tags={tags})")
            continue
        if creator_id in KEYWORD_MISMATCH:
            if verdict.topic_match != "mismatch" or verdict.decision != "unfit":
                mismatches.append(
                    f"{creator_id}: expected mismatch+unfit, got "
                    f"{verdict.topic_match}/{verdict.decision} — {verdict.reasons}"
                )
        if creator_id in FIT_CONTROL and verdict.topic_match == "mismatch":
            mismatches.append(
                f"{creator_id}: control marked mismatch — {verdict.mismatch_topic} {verdict.reasons}"
            )
    print("=== mismatches ===")
    for line in mismatches:
        print(line)
    print(
        f"model={model_name} locked={locked.topic_rejected_ids} "
        f"fit={[cid for cid, v in decisions.items() if v.decision == 'fit']}"
    )

    assert model_name == "deepseek-chat"
    assert not mismatches, mismatches
    assert set(locked.topic_rejected_ids) >= KEYWORD_MISMATCH
    assert not (FIT_CONTROL & set(locked.topic_rejected_ids))
