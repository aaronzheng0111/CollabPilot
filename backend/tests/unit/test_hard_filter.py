"""T04 verify cases 1–6. Rules only; no model."""

from __future__ import annotations

import inspect
import json
from uuid import uuid4

import pytest

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import Campaign, ParsedGoal, should_exclude_own_brand, validate_parsed_goal
from collabpilot.campaign.hard_filter import REASON_LABELS, hard_filter
from collabpilot.campaign.workbench import excluded_rows, main_table_rows
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.apply_hard_filters import ApplyHardFiltersTool
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool


SAMPLE_TEXT = (
    "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
    "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
    "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。"
)


def parsed_goal(platforms: list[str] | None = None) -> ParsedGoal:
    goal = validate_parsed_goal(
        {
            "brand": None,
            "product": "AI 翻译工具",
            "target_audience": ["中文用户"],
            "platforms": platforms or [],
            "target_count": 10,
            "inclusion_criteria": [],
            "exclusion_criteria": ["已经合作过的账号"],
            "outreach_count": 3,
            "needs_user_approval": True,
        }
    )
    assert isinstance(goal, ParsedGoal)
    return goal


@pytest.fixture
def searched(application):
    """PARSED campaign with a 30-day「翻译」search already recorded."""

    async def make(platforms: list[str] | None = None) -> ToolContext:
        session_id = application.store.create_session()
        application.save_campaign(
            Campaign(campaign_id=session_id, goal_status="PARSED", parsed_goal=parsed_goal(platforms))
        )
        context = ToolContext(session_id=session_id, turn_id=uuid4())
        result = await SearchCreatorsTool(application.campaigns).execute(
            {"keywords": ["翻译"]}, context
        )
        assert result.ok
        return context

    return make


# --------------------------------------------------------------------------
# Cases 1–4, 6: pure function
# --------------------------------------------------------------------------


def test_own_brand_cooperation_removes_every_platform_of_the_creator() -> None:
    creators = mock_store.load()
    kept, removed = hard_filter([creators["creator_016"], creators["creator_001"]], ["tiktok", "instagram"])

    assert [item.creator_id for item in kept] == ["creator_001"]
    assert [(item.creator_id, item.reason) for item in removed] == [("creator_016", "own_brand_cooperated")]
    assert removed[0].evidence is not None
    assert removed[0].evidence.brand_name == "LinguaGo AI 翻译"
    assert removed[0].evidence.content_published_at == "2026-06-08"
    assert removed[0].evidence.cooperation_id
    assert all(item.creator_id != "creator_016" for item in kept)


def test_mock_data_own_brand_set_is_exactly_016_to_019_without_reading_tags() -> None:
    creators = list(mock_store.load().values())
    oracle = mock_store.load_oracle()

    _, removed = hard_filter(creators, ["tiktok", "instagram"])
    own_brand = {item.creator_id for item in removed if item.reason == "own_brand_cooperated"}

    assert own_brand == {"creator_016", "creator_017", "creator_018", "creator_019"}
    assert own_brand == {cid for cid, answer in oracle.items() if "own_brand_cooperated" in answer["scenario_tags"]}
    source = inspect.getsource(inspect.getmodule(hard_filter))
    assert "is_current_brand" in source and "scenario_tags" not in source


def test_instagram_only_creator_is_platform_mismatch_when_target_is_tiktok() -> None:
    creators = mock_store.load()
    nina = creators["creator_014"]
    assert nina.platforms == ["instagram"]

    kept, removed = hard_filter([nina], ["tiktok"])

    assert kept == []
    assert [(item.creator_id, item.reason, item.evidence) for item in removed] == [
        ("creator_014", "platform_mismatch", None)
    ]
    assert REASON_LABELS[removed[0].reason] == "平台不在目标内"


def test_cross_platform_uncooperated_creator_keeps_both_accounts() -> None:
    creators = mock_store.load()

    kept, removed = hard_filter([creators["creator_001"]], ["tiktok", "instagram"])

    assert removed == []
    assert kept[0].platforms == ["tiktok", "instagram"]
    assert len(kept[0].account_ids) == 2


def test_own_brand_is_checked_before_platform_and_only_first_reason_recorded() -> None:
    creators = mock_store.load()
    # creator_018 is instagram-only AND cooperated with the brand.
    _, removed = hard_filter([creators["creator_018"]], ["tiktok"])

    assert [item.reason for item in removed] == ["own_brand_cooperated"]


def test_allow_recontact_keeps_own_brand_collaborators() -> None:
    creators = mock_store.load()
    ids = ["creator_016", "creator_017", "creator_018", "creator_019", "creator_001"]
    kept, removed = hard_filter(
        [creators[cid] for cid in ids],
        ["tiktok", "instagram"],
        exclude_own_brand=False,
    )

    assert {item.creator_id for item in kept} == set(ids)
    assert all(item.reason != "own_brand_cooperated" for item in removed)


def test_default_goal_excludes_own_brand_via_should_exclude() -> None:
    assert should_exclude_own_brand(parsed_goal()) is True
    allow = validate_parsed_goal(
        {
            "brand": None,
            "product": "AI 翻译工具",
            "target_audience": ["中文用户"],
            "platforms": [],
            "target_count": 10,
            "inclusion_criteria": ["可以再次联系已合作过的账号"],
            "exclusion_criteria": [],
            "outreach_count": 3,
            "needs_user_approval": True,
        }
    )
    assert isinstance(allow, ParsedGoal)
    assert should_exclude_own_brand(allow) is False


def test_tool_schema_has_no_relax_parameter_preference_comes_from_goal() -> None:
    parameters = inspect.signature(hard_filter).parameters
    assert list(parameters) == ["merged", "platforms", "exclude_own_brand"]
    assert parameters["exclude_own_brand"].default is True
    schema = ApplyHardFiltersTool.input_schema["properties"]
    assert list(schema) == ["creator_ids"]
    assert "relax" not in ApplyHardFiltersTool.description.lower()
    assert "exclude_own_brand" not in schema


# --------------------------------------------------------------------------
# Case 5 + tool contract
# --------------------------------------------------------------------------


async def test_tool_marks_rule_and_records_last_filter(application, searched) -> None:
    context = await searched()
    tool = ApplyHardFiltersTool(application.campaigns)

    result = await tool.execute({}, context)
    campaign = application.campaign(context.session_id)

    assert result.ok and result.display.startswith("[RULE]")
    assert result.data["data_origin"] == "rule" != "real_model_output"
    assert campaign.stage == "EVALUATING"
    assert campaign.last_filter is not None
    assert campaign.last_filter.kept_ids == [item["creator_id"] for item in result.data["kept"]]
    removed_ids = {item.creator_id for item in campaign.last_filter.removed}
    assert removed_ids == {"creator_016", "creator_017", "creator_018", "creator_019"}
    assert set(campaign.last_filter.kept_ids) | removed_ids == set(campaign.last_search.creator_ids)
    assert all(item.evidence and item.evidence.brand_name for item in campaign.last_filter.removed)


async def test_tool_rejects_ids_outside_the_search_and_requires_search(application, searched) -> None:
    context = await searched()
    tool = ApplyHardFiltersTool(application.campaigns)

    bad = await tool.execute({"creator_ids": ["creator_001", "creator_007"]}, context)
    assert bad.ok is False and bad.error_code == "not_in_search"
    assert bad.data == {"not_in_search": ["creator_007"]}
    assert application.campaign(context.session_id).last_filter is None

    fresh = application.store.create_session()
    application.save_campaign(Campaign(campaign_id=fresh, goal_status="PARSED", parsed_goal=parsed_goal()))
    missing = await tool.execute({}, ToolContext(session_id=fresh, turn_id=uuid4()))
    assert missing.ok is False and missing.error_code == "search_required"


async def test_tool_uses_goal_platforms_for_mismatch(application, searched) -> None:
    context = await searched(platforms=["tiktok"])

    result = await ApplyHardFiltersTool(application.campaigns).execute({}, context)

    reasons = {item["creator_id"]: item["reason"] for item in result.data["removed"]}
    # creator_022 is instagram-only and matched the search.
    assert reasons["creator_022"] == "platform_mismatch"
    assert reasons["creator_018"] == "own_brand_cooperated"
    assert all(item["platforms"] == ["tiktok"] for item in result.data["kept"])


async def test_workbench_rows_switch_to_kept_and_excluded(application, searched) -> None:
    context = await searched()
    await ApplyHardFiltersTool(application.campaigns).execute({}, context)
    campaign = application.campaign(context.session_id)

    rows = main_table_rows(campaign)
    assert [row["creator_id"] for row in rows] == campaign.last_filter.kept_ids
    assert all(row["filter"] == "kept" and "[RULE]" in row["source"] for row in rows)
    excluded = excluded_rows(campaign)
    assert len(excluded) == 4
    assert excluded[0]["reason"] == "已合作本品牌" and excluded[0]["source"] == "[RULE]"
    assert excluded[0]["brand_name"] == "LinguaGo AI 翻译" and excluded[0]["content_published_at"] == "2026-06-08"


async def test_tool_keeps_own_brand_when_goal_allows_recontact(application, searched) -> None:
    context = await searched()
    campaign = application.campaign(context.session_id)
    goal = campaign.parsed_goal.model_copy(
        update={
            "inclusion_criteria": ["可以再次联系已合作过的账号"],
            "exclusion_criteria": [],
        }
    )
    application.save_campaign(campaign.model_copy(update={"parsed_goal": goal}))

    result = await ApplyHardFiltersTool(application.campaigns).execute({}, context)
    stored = application.campaign(context.session_id)

    assert result.ok
    removed_reasons = {item["reason"] for item in result.data["removed"]}
    assert "own_brand_cooperated" not in removed_reasons
    assert {"creator_016", "creator_017", "creator_018", "creator_019"} <= set(
        stored.last_filter.kept_ids
    )
    assert all(item.reason != "own_brand_cooperated" for item in stored.last_filter.removed)


async def test_tool_excludes_own_brand_on_default_goal(application, searched) -> None:
    context = await searched()
    result = await ApplyHardFiltersTool(application.campaigns).execute({}, context)
    removed_ids = {item["creator_id"] for item in result.data["removed"]}
    assert removed_ids == {"creator_016", "creator_017", "creator_018", "creator_019"}


async def test_mock_provider_chains_search_then_filter(application) -> None:
    first = await application.chat(SAMPLE_TEXT, provider_name="mock")
    second = await application.chat("开始搜索", session_id=first.session_id, provider_name="mock")
    campaign = application.campaign(first.session_id)

    assert second.tool_calls == 2
    assert campaign.stage in ("EVALUATING", "INSUFFICIENT", "CANDIDATES_READY") and campaign.last_filter is not None
    tool_names = [message.name for message in application.history(first.session_id) if message.role == "tool"]
    assert tool_names == ["search_creators", "apply_hard_filters"]
    filter_msg = next(
        message
        for message in application.history(first.session_id)
        if message.role == "tool" and message.name == "apply_hard_filters"
    )
    assert "[RULE]" in filter_msg.content or '"data_origin": "rule"' in filter_msg.content.replace(" ", "")
    payload = json.loads(filter_msg.content)
    assert payload["data"]["data_origin"] == "rule"
