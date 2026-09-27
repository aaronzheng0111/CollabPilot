"""T05 verify case 12: DeepSeek judgment on the first round (window 30).

Not part of the unit run. `cd backend && uv run pytest -m eval -s`.
Prints every mismatch against `load_oracle()` plus the raw model output so
the numbers can be copied into `documents/T05-fit-judgment/verify.md`.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import Campaign, ParsedGoal, validate_parsed_goal
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.apply_hard_filters import ApplyHardFiltersTool
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool


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
FIRST_ROUND_FIT = {f"creator_{index:03d}" for index in range(1, 7)}
KEYWORD_MISMATCH = {f"creator_{index:03d}" for index in range(11, 16)}


@pytest.mark.eval
async def test_first_round_judgment_matches_oracle(eval_application) -> None:
    application = eval_application
    session_id = application.store.create_session()
    goal = validate_parsed_goal(SAMPLE_GOAL)
    assert isinstance(goal, ParsedGoal)
    application.save_campaign(Campaign(campaign_id=session_id, goal_status="PARSED", parsed_goal=goal))
    context = ToolContext(session_id=session_id, turn_id=uuid4())
    assert (await SearchCreatorsTool(application.campaigns).execute({"keywords": ["翻译"]}, context)).ok
    assert (await ApplyHardFiltersTool(application.campaigns).execute({}, context)).ok
    campaign = application.campaign(session_id)

    provider = application.providers.get(application.settings.model.default_provider)
    batch, model_name, _skipped = await application.evaluate_candidates(
        campaign, provider, application.settings.model.default_model
    )

    print("\n=== raw verdicts ===")
    print(json.dumps([v.model_dump() for v in batch.accepted], ensure_ascii=False, indent=1))
    print("=== rejected ===", [r.model_dump() for r in batch.rejected])
    assert batch.ok, batch.error_code

    oracle = mock_store.load_oracle()
    decisions = {v.creator_id: v for v in batch.accepted}
    candidates = set(campaign.last_filter.kept_ids)
    mismatches: list[str] = []
    for creator_id in sorted(candidates):
        verdict = decisions.get(creator_id)
        tags = oracle[creator_id]["scenario_tags"]
        if verdict is None:
            mismatches.append(f"{creator_id}: no verdict (tags={tags})")
            continue
        if creator_id in FIRST_ROUND_FIT and verdict.decision != "fit":
            mismatches.append(f"{creator_id}: expected fit, got {verdict.decision} — {verdict.reasons}")
        if creator_id in KEYWORD_MISMATCH and verdict.decision == "fit":
            mismatches.append(f"{creator_id}: expected not fit, got fit — {verdict.reasons}")
    print("=== mismatches ===")
    for line in mismatches:
        print(line)
    print(f"model={model_name} fit={sorted(cid for cid, v in decisions.items() if v.decision == 'fit')}")

    assert model_name == "deepseek-chat"
    assert all(decisions[cid].decision == "fit" for cid in FIRST_ROUND_FIT & candidates), mismatches
    assert not any(decisions[cid].decision == "fit" for cid in KEYWORD_MISMATCH & candidates), mismatches
