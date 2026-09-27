"""T09 verify cases 5 and 7: campaigns table survives restart; same-goal reuse."""

from __future__ import annotations

from uuid import uuid4

from collabpilot.campaign.goal import Campaign, ParsedGoal, validate_parsed_goal
from collabpilot.campaign.selection import fingerprint_goal
from collabpilot.campaign.store import CampaignStore
from collabpilot.infrastructure.session_store import SQLiteSessionStore
from collabpilot.tools.base import ToolContext
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


def test_campaign_lists_survive_reopen(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'agent.db'}"
    first = SQLiteSessionStore(database_url, tmp_path)
    campaigns = CampaignStore(first)
    session_id = first.create_session()
    campaigns.save(
        Campaign(
            campaign_id=session_id,
            saved_creator_ids=["creator_001", "creator_002"],
            excluded_creator_ids=["creator_003"],
            topic_rejected_ids=["creator_011"],
            stage="SELECTED",
        )
    )

    reopened = CampaignStore(SQLiteSessionStore(database_url, tmp_path))
    loaded = reopened.get(session_id)
    assert loaded.campaign_id == session_id
    assert loaded.saved_creator_ids == ["creator_001", "creator_002"]
    assert loaded.excluded_creator_ids == ["creator_003"]
    assert loaded.topic_rejected_ids == ["creator_011"]
    assert loaded.stage == "SELECTED"


async def test_same_goal_reuses_campaign_id_and_skips_three_classes(application) -> None:
    session_id = application.store.create_session()
    goal = validate_parsed_goal(SAMPLE_GOAL)
    assert isinstance(goal, ParsedGoal)
    fingerprint = fingerprint_goal(goal)
    application.save_campaign(
        Campaign(
            campaign_id=session_id,
            goal_status="PARSED",
            parsed_goal=goal,
            goal_fingerprint=fingerprint,
            saved_creator_ids=["creator_001"],
            excluded_creator_ids=["creator_003"],
            topic_rejected_ids=["creator_011"],
        )
    )
    first = await application.chat(
        "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
        "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
        "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。",
        session_id=session_id,
        provider_name="mock",
    )
    stored = application.campaign(session_id)
    assert first.session_id == session_id
    assert stored.campaign_id == session_id
    assert stored.goal_fingerprint == fingerprint

    result = await SearchCreatorsTool(application.campaigns).execute(
        {"keywords": ["翻译"]},
        ToolContext(session_id=session_id, turn_id=uuid4()),
    )
    assert result.ok
    ids = {item["creator_id"] for item in result.data["creators"]}
    assert not {"creator_001", "creator_003", "creator_011"} & ids
    display = result.display
    assert "已在名单中" in display and "已排除" in display and "此前判定不符" in display
    counts = result.data["skip_counts"]
    assert counts["already_saved"] >= 1
    assert counts["excluded"] >= 1
    assert counts["topic_rejected"] >= 1


async def test_metadata_campaign_migrates_into_table(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'agent.db'}"
    sessions = SQLiteSessionStore(database_url, tmp_path)
    session_id = sessions.create_session()
    sessions.set_metadata(
        session_id,
        {
            "campaign": Campaign(
                campaign_id=session_id,
                saved_creator_ids=["creator_002"],
                excluded_creator_ids=["creator_010"],
                topic_rejected_ids=["creator_012"],
            ).model_dump(mode="json")
        },
    )
    store = CampaignStore(sessions)
    loaded = store.get(session_id)
    assert loaded.saved_creator_ids == ["creator_002"]
    fresh = CampaignStore(SQLiteSessionStore(database_url, tmp_path)).get(session_id)
    assert fresh.saved_creator_ids == ["creator_002"]
    assert fresh.excluded_creator_ids == ["creator_010"]
    assert fresh.topic_rejected_ids == ["creator_012"]
