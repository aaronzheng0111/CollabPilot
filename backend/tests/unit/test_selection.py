"""T09 verify cases 1–4, 6, 8. Mock provider / in-process store; no DeepSeek."""

from __future__ import annotations

from uuid import uuid4

from collabpilot.campaign.goal import Campaign, CreatorRef, FilterRecord, ParsedGoal, SearchRecord
from collabpilot.campaign.hard_filter import KeptCreator
from collabpilot.campaign.selection import (
    ALREADY_SAVED,
    SAVE_SELECTION,
    SkipCounts,
    fingerprint_goal,
    recommend,
)
from collabpilot.campaign.verdict import Verdict
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.exclude_creator import ExcludeCreatorTool
from collabpilot.tools.builtin.save_campaign_selection import SaveCampaignSelectionTool
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool


def pending_verdict(creator_id: str) -> Verdict:
    return Verdict(
        creator_id=creator_id,
        decision="pending",
        reasons=["受众未知"],
        evidence_ids=[f"{creator_id}_post"],
        related_post_ids=[],
        topic_match="unclear",
        rank=None,
        model_name="deepseek-chat",
    )


def fit_verdict(creator_id: str, rank: int) -> Verdict:
    return Verdict(
        creator_id=creator_id,
        decision="fit",
        reasons=["持续发布"],
        evidence_ids=[f"{creator_id}_post"],
        related_post_ids=[],
        topic_match="match",
        rank=rank,
        model_name="deepseek-chat",
    )


def seeded_campaign(**updates) -> Campaign:
    kept = [
        KeptCreator(
            creator_id="creator_001",
            display_name="A",
            platforms=["tiktok"],
            account_ids=["tiktok:a"],
        ),
        KeptCreator(
            creator_id="creator_002",
            display_name="B",
            platforms=["tiktok"],
            account_ids=["tiktok:b"],
        ),
        KeptCreator(
            creator_id="creator_020",
            display_name="P",
            platforms=["tiktok"],
            account_ids=["tiktok:p"],
        ),
    ]
    campaign = Campaign(
        campaign_id=uuid4(),
        goal_status="PARSED",
        stage="CANDIDATES_READY",
        parsed_goal=ParsedGoal(
            brand="LinguaGo AI 翻译",
            product="AI 翻译工具",
            target_audience=["中文用户"],
            platforms=["tiktok", "instagram"],
            target_count=10,
            inclusion_criteria=["最近持续发布相关内容"],
            exclusion_criteria=["已经合作过的账号"],
            outreach_count=3,
            needs_user_approval=True,
        ),
        last_search=SearchRecord(
            keywords=["翻译"],
            window_days=30,
            min_followers=None,
            platforms=["tiktok", "instagram"],
            creators=[
                CreatorRef(creator_id=item.creator_id, display_name=item.display_name, platforms=item.platforms)
                for item in kept
            ],
        ),
        last_filter=FilterRecord(kept=kept, removed=[]),
        verdicts=[
            fit_verdict("creator_001", 1),
            fit_verdict("creator_002", 2),
            pending_verdict("creator_020"),
        ],
    )
    return campaign.model_copy(update=updates)


def test_fingerprint_is_stable_for_normalized_goal() -> None:
    goal = ParsedGoal(
        brand=" LinguaGo AI 翻译 ",
        product="AI 翻译工具",
        target_audience=["中文用户"],
        platforms=["instagram", "tiktok"],
        target_count=10,
        inclusion_criteria=["B", "A"],
        exclusion_criteria=["已经合作过的账号"],
        outreach_count=3,
        needs_user_approval=True,
    )
    twin = goal.model_copy(
        update={
            "brand": "linguago ai 翻译",
            "platforms": ["tiktok", "instagram"],
            "inclusion_criteria": ["a", "b"],
        }
    )
    assert fingerprint_goal(goal) == fingerprint_goal(twin)
    different = goal.model_copy(update={"target_count": 8})
    assert fingerprint_goal(goal) != fingerprint_goal(different)


def test_recommend_drops_saved_excluded_and_topic_rejected() -> None:
    campaign = Campaign(
        campaign_id=uuid4(),
        saved_creator_ids=["creator_001"],
        excluded_creator_ids=["creator_003"],
        topic_rejected_ids=["creator_011"],
    )
    kept, counts = recommend(
        ["creator_001", "creator_002", "creator_003", "creator_011", "creator_004"],
        campaign,
    )
    assert kept == ["creator_002", "creator_004"]
    assert counts == SkipCounts(already_saved=1, excluded=1, topic_rejected=1)
    assert "均未重复推荐" in (counts.note() or "")
    assert "已在名单中 1 位" in (counts.note() or "")


async def test_unapproved_save_returns_approval_required(application) -> None:
    session_id = application.store.create_session()
    application.save_campaign(Campaign(campaign_id=session_id, saved_creator_ids=["creator_009"]))
    tool = SaveCampaignSelectionTool(application.campaigns)
    context = ToolContext(session_id=session_id, turn_id=uuid4())

    result = await tool.execute({"creator_ids": ["creator_001", "creator_002"]}, context)

    assert result.ok is False and result.error_code == "approval_required"
    stored = application.campaign(session_id)
    assert stored.saved_creator_ids == ["creator_009"]
    assert stored.pending_decision == SAVE_SELECTION


async def test_approved_save_writes_ids_and_selected_stage(application) -> None:
    session_id = application.store.create_session()
    application.save_campaign(seeded_campaign(campaign_id=session_id))
    tool = SaveCampaignSelectionTool(application.campaigns)
    context = ToolContext(session_id=session_id, turn_id=uuid4(), user_approved=True)

    result = await tool.execute({"creator_ids": ["creator_001", "creator_002"]}, context)

    assert result.ok
    stored = application.campaign(session_id)
    assert stored.saved_creator_ids == ["creator_001", "creator_002"]
    assert stored.stage == "SELECTED"


async def test_duplicate_save_keeps_one_and_mentions_already(application) -> None:
    session_id = application.store.create_session()
    application.save_campaign(
        seeded_campaign(campaign_id=session_id, saved_creator_ids=["creator_001"])
    )
    tool = SaveCampaignSelectionTool(application.campaigns)
    context = ToolContext(session_id=session_id, turn_id=uuid4(), user_approved=True)

    result = await tool.execute({"creator_ids": ["creator_001"]}, context)

    assert result.ok
    stored = application.campaign(session_id)
    assert stored.saved_creator_ids == ["creator_001"]
    assert ALREADY_SAVED in result.display


async def test_unapproved_exclude_rejected_then_approved_moves(application) -> None:
    session_id = application.store.create_session()
    application.save_campaign(
        seeded_campaign(
            campaign_id=session_id,
            saved_creator_ids=["creator_001", "creator_002"],
        )
    )
    tool = ExcludeCreatorTool(application.campaigns)
    denied = await tool.execute(
        {"creator_id": "creator_001"},
        ToolContext(session_id=session_id, turn_id=uuid4()),
    )
    assert denied.error_code == "approval_required"
    assert application.campaign(session_id).saved_creator_ids == ["creator_001", "creator_002"]
    assert application.campaign(session_id).excluded_creator_ids == []

    result = application.approve_pending(session_id, "exclude_creator", True)
    assert result.ok
    stored = application.campaign(session_id)
    assert "creator_001" not in stored.saved_creator_ids
    assert stored.excluded_creator_ids == ["creator_001"]


async def test_pending_accepted_stays_pending(application) -> None:
    session_id = application.store.create_session()
    application.save_campaign(seeded_campaign(campaign_id=session_id))
    tool = SaveCampaignSelectionTool(application.campaigns)
    result = await tool.execute(
        {"creator_ids": ["creator_020"]},
        ToolContext(session_id=session_id, turn_id=uuid4(), user_approved=True),
    )
    assert result.ok
    stored = application.campaign(session_id)
    assert stored.saved_creator_ids == ["creator_020"]
    assert "creator_020" in stored.accepted_from_pending
    verdict = next(item for item in stored.verdicts or [] if item.creator_id == "creator_020")
    assert verdict.decision == "pending"


async def test_search_skips_excluded(application) -> None:
    session_id = application.store.create_session()
    from collabpilot.campaign.goal import validate_parsed_goal

    goal = validate_parsed_goal(
        {
            "brand": None,
            "product": "AI 翻译工具",
            "target_audience": ["中文用户"],
            "platforms": [],
            "target_count": 10,
            "inclusion_criteria": [],
            "exclusion_criteria": ["已经合作过的账号"],
            "outreach_count": 3,
            "needs_user_approval": True,
        }
    )
    assert isinstance(goal, ParsedGoal)
    application.save_campaign(
        Campaign(
            campaign_id=session_id,
            goal_status="PARSED",
            parsed_goal=goal,
            excluded_creator_ids=["creator_003"],
        )
    )
    result = await SearchCreatorsTool(application.campaigns).execute(
        {"keywords": ["翻译"]},
        ToolContext(session_id=session_id, turn_id=uuid4()),
    )
    assert result.ok
    ids = [item["creator_id"] for item in result.data["creators"]]
    assert "creator_003" not in ids
    stored = application.campaign(session_id)
    assert stored.skip_counts.get("excluded", 0) >= 1
