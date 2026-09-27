"""T10 verify case 10: DeepSeek drafts for creator_001–003.

Not part of the unit run. `cd backend && uv run pytest -m eval -s tests/eval/test_drafts_eval.py`.
Prints the three bodies so they can be copied into verify.md.
"""

from __future__ import annotations

import json

import pytest

from collabpilot.campaign import mock_store
from collabpilot.campaign.channels import CHANNEL_LABELS
from collabpilot.campaign.drafts import quote_found, validate_drafts
from collabpilot.campaign.goal import Campaign, ParsedGoal, validate_parsed_goal


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
IDS = ["creator_001", "creator_002", "creator_003"]
CHANNELS = {
    "creator_001": "tiktok_dm",
    "creator_002": "instagram_dm",
    "creator_003": "email",
}


@pytest.mark.eval
async def test_drafts_for_001_to_003_pass_validation(eval_application) -> None:
    application = eval_application
    session_id = application.store.create_session()
    goal = validate_parsed_goal(SAMPLE_GOAL)
    assert isinstance(goal, ParsedGoal)
    campaign = Campaign(
        campaign_id=session_id,
        goal_status="PARSED",
        parsed_goal=goal,
        stage="SELECTED",
        saved_creator_ids=list(IDS),
        confirmed_channels=dict(CHANNELS),
    )
    application.save_campaign(campaign)
    provider = application.providers.get(application.settings.model.default_provider)
    batch = await application.generate_drafts(
        campaign,
        provider,
        application.settings.model.default_model,
        creator_ids=IDS,
    )
    print("\n=== raw drafts ===")
    print(json.dumps([item.model_dump() for item in batch.accepted], ensure_ascii=False, indent=1))
    print("=== error ===", batch.error_code, "model_called", batch.model_called)
    assert batch.ok, batch.error_code
    assert batch.model_name == "deepseek-chat"
    creators = mock_store.load()
    bodies = [item.body for item in batch.accepted]
    posts = [item.cited_post_id for item in batch.accepted]
    assert len(set(bodies)) == 3
    assert len(set(posts)) == 3
    from collabpilot.campaign.channels import pick_channel

    for item in batch.accepted:
        creator = creators[item.creator_id]
        assert item.cited_post_id in creator.post_ids()
        post = next(p for p in creator.posts() if p["post_id"] == item.cited_post_id)
        assert quote_found(item.body, post)
        assert item.channel == pick_channel(creator)
        assert CHANNEL_LABELS[item.channel] in item.body
        assert item.data_origin == "real_model_output"
    again = validate_drafts(
        {"drafts": [item.model_dump() for item in batch.accepted]},
        campaign,
        creators,
        model_name=batch.model_name or "deepseek-chat",
        creator_ids=IDS,
    )
    assert again.ok, again.error_code
    print("=== bodies ===")
    for item in batch.accepted:
        print(f"--- {item.creator_id} / {item.channel} / {item.cited_post_id} ---")
        print(item.body)
