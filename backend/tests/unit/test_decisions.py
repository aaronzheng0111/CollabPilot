from uuid import uuid4

from collabpilot.campaign.decisions import (
    DECISION_LABELS,
    approve_pending,
    registered_decisions,
)
from collabpilot.campaign.goal import (
    CONFIRM_ASSUMPTIONS,
    EXCLUDE_COOPERATED,
    Campaign,
    ParsedGoal,
    validate_parsed_goal,
)


def clarifying_campaign(pending: str | None = CONFIRM_ASSUMPTIONS) -> Campaign:
    goal = validate_parsed_goal(
        {
            "brand": None,
            "product": None,
            "target_audience": [],
            "platforms": [],
            "target_count": None,
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "outreach_count": 3,
            "needs_user_approval": None,
            "assumptions": [],
            "missing_critical": [],
        }
    )
    assert isinstance(goal, ParsedGoal)
    return Campaign(
        campaign_id=uuid4(),
        goal_status="CLARIFYING",
        parsed_goal=goal,
        goal_origin="real_model_output",
        goal_model_name="deepseek-chat",
        grill_rounds=3,
        pending_decision=pending,
    )


def test_confirm_assumptions_is_registered_and_labelled() -> None:
    assert CONFIRM_ASSUMPTIONS in registered_decisions()
    assert DECISION_LABELS[CONFIRM_ASSUMPTIONS] == "确认以上假设"


def test_unapproved_returns_approval_required_and_changes_nothing() -> None:
    campaign = clarifying_campaign()

    result = approve_pending(campaign, CONFIRM_ASSUMPTIONS, user_approved=False)

    assert result.status == "approval_required" and not result.ok
    assert result.campaign == campaign
    assert result.campaign.pending_decision == CONFIRM_ASSUMPTIONS


def test_unknown_or_not_pending_decisions_are_rejected() -> None:
    assert approve_pending(clarifying_campaign(), "not_a_real_decision", True).status == (
        "unknown_decision"
    )
    assert approve_pending(clarifying_campaign(pending=None), CONFIRM_ASSUMPTIONS, True).status == (
        "not_pending"
    )


def test_approved_confirm_assumptions_fills_fallbacks_and_parses() -> None:
    result = approve_pending(clarifying_campaign(), CONFIRM_ASSUMPTIONS, user_approved=True)
    campaign = result.campaign
    goal = campaign.parsed_goal

    assert result.ok and result.status == "applied"
    assert campaign.goal_status == "PARSED"
    assert campaign.pending_decision is None
    assert goal is not None and goal.missing_critical == []
    assert (goal.target_count, goal.outreach_count, goal.needs_user_approval) == (10, 3, True)
    assert any("合作" in item for item in goal.exclusion_criteria)
    assumed = goal.assumed_fields()
    assert {"target_count", EXCLUDE_COOPERATED, "brand"} <= assumed
    assert "needs_user_approval" not in assumed
    # clarifying_campaign already had outreach_count=3; confirm must not invent one.
    assert "outreach_count" not in assumed
    assert "deepseek-chat" in result.display


def test_confirm_without_outreach_leaves_it_optional() -> None:
    goal = validate_parsed_goal(
        {
            "brand": None,
            "product": None,
            "target_audience": [],
            "platforms": [],
            "target_count": None,
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "outreach_count": None,
            "needs_user_approval": None,
            "assumptions": [],
            "missing_critical": [],
        }
    )
    assert isinstance(goal, ParsedGoal)
    campaign = Campaign(
        campaign_id=uuid4(),
        goal_status="CLARIFYING",
        parsed_goal=goal,
        grill_rounds=3,
        pending_decision=CONFIRM_ASSUMPTIONS,
    )
    result = approve_pending(campaign, CONFIRM_ASSUMPTIONS, True)
    filled = result.campaign.parsed_goal
    assert filled is not None
    assert filled.target_count == 10
    assert filled.outreach_count is None
    assert "outreach_count" not in filled.assumed_fields()
    assert "为其中多少位" not in result.display


def test_confirm_without_any_parsed_goal_builds_one_from_defaults() -> None:
    campaign = Campaign(
        campaign_id=uuid4(),
        goal_status="CLARIFYING",
        grill_rounds=3,
        pending_decision=CONFIRM_ASSUMPTIONS,
    )

    result = approve_pending(campaign, CONFIRM_ASSUMPTIONS, True)

    assert result.campaign.goal_status == "PARSED"
    assert result.campaign.parsed_goal is not None
    assert result.campaign.parsed_goal.brand == "LinguaGo AI 翻译"
    assert result.campaign.goal_origin is None
