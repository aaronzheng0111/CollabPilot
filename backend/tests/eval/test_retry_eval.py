"""T07 verify case 11: DeepSeek retry strategy then a second search.

Not part of the unit run. `cd backend && uv run pytest -m eval -s`.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from collabpilot.campaign.goal import Campaign, ParsedGoal, validate_parsed_goal
from collabpilot.campaign.retry import fit_count
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


@pytest.mark.eval
async def test_retry_strategy_raises_second_round_fit(eval_application, monkeypatch) -> None:
    # Production demo caps auto-retry at 0; eval still exercises the second-round path.
    monkeypatch.setattr("collabpilot.application.MAX_AUTO_RETRIES", 1)
    monkeypatch.setattr("collabpilot.campaign.retry.MAX_AUTO_RETRIES", 1)
    application = eval_application
    session_id = application.store.create_session()
    goal = validate_parsed_goal(SAMPLE_GOAL)
    assert isinstance(goal, ParsedGoal)
    application.save_campaign(
        Campaign(campaign_id=session_id, goal_status="PARSED", parsed_goal=goal)
    )
    context = ToolContext(session_id=session_id, turn_id=uuid4())
    assert (await SearchCreatorsTool(application.campaigns).execute({"keywords": ["翻译"]}, context)).ok
    assert (await ApplyHardFiltersTool(application.campaigns).execute({}, context)).ok
    campaign = application.campaign(session_id)
    provider = application.providers.get(application.settings.model.default_provider)
    model = application.settings.model.default_model

    campaign, summary = await application._evaluate_candidates(
        campaign, provider, model, session_id, uuid4(), None
    )
    round1 = fit_count(campaign)
    print("\n=== round 1 ===")
    print(summary)
    print("fit", round1, "ids", [v.creator_id for v in campaign.verdicts or [] if v.decision == "fit"])

    campaign, extra = await application._maybe_search_retry(
        campaign, provider, model, session_id, uuid4(), None
    )
    round2 = fit_count(campaign)
    print("=== retry ===")
    print(extra)
    print("strategy", campaign.retry_strategy.model_dump() if campaign.retry_strategy else None)
    print("fit", round2, "ids", [v.creator_id for v in campaign.verdicts or [] if v.decision == "fit"])
    print("rounds", json.dumps([item.model_dump() for item in campaign.search_rounds], ensure_ascii=False))

    assert campaign.retry_error is None
    assert campaign.retry_strategy is not None
    assert campaign.retry_strategy.model_name == "deepseek-chat"
    assert campaign.auto_retries == 1
    assert round2 > round1
    assert campaign.last_search is not None
