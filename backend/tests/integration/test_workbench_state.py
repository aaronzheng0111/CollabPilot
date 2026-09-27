"""T11 verify case 1: get_workbench_state is a complete read-only snapshot."""

from __future__ import annotations

from uuid import uuid4

from collabpilot.campaign.goal import Campaign
from collabpilot.campaign.workbench import WorkbenchState


REQUIRED = (
    "goal_status",
    "parsed_goal",
    "pending_decision",
    "pending_decisions",
    "main_rows",
    "search_rounds",
    "verdicts",
    "excluded_rows",
    "pending_rows",
    "channel_rows",
    "draft_rows",
    "follow_up_rows",
)


def test_get_workbench_state_returns_all_fields_and_does_not_write(application) -> None:
    session_id = application.store.create_session()
    campaign = Campaign(
        campaign_id=session_id,
        goal_status="PARSED",
        stage="SELECTED",
        saved_creator_ids=["creator_001"],
        pending_decision="accept_short_list",
    )
    application.save_campaign(campaign)
    before = application.campaign(session_id).model_dump(mode="json")

    state = application.get_workbench_state(session_id)
    assert isinstance(state, WorkbenchState)
    dumped = state.model_dump(mode="json")
    for field in REQUIRED:
        assert field in dumped
    assert dumped["goal_status"] == "PARSED"
    assert dumped["pending_decision"] == "accept_short_list"
    assert dumped["pending_decisions"]
    assert dumped["clarifying"] is False

    after = application.campaign(session_id).model_dump(mode="json")
    assert after == before

    empty = application.get_workbench_state(None)
    assert len(empty.main_rows) == 12
    assert empty.search_caption == "示例达人"
    assert empty.campaign is None
    assert {"display_name", "platforms", "followers"} <= set(empty.main_rows[0])
    assert {"category", "topics", "audience_summary", "contact", "last_post"} <= set(
        empty.main_rows[0]
    )
    assert "decision" not in empty.main_rows[0] and "rank" not in empty.main_rows[0]
    # unused uuid still does not create a row beyond ensure
    ghost = application.get_workbench_state(uuid4())
    assert ghost.goal_status == "CREATED"
    assert len(ghost.main_rows) == 12
    assert ghost.search_caption == "示例达人"
