"""T03 verify cases 1–3, 5–8 (tool side). Mock provider only; no DeepSeek."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from collabpilot.campaign import mock_store
from collabpilot.campaign.goal import Campaign, ParsedGoal, validate_parsed_goal
from collabpilot.campaign.store import CampaignStore
from collabpilot.domain.models import ToolResult
from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.get_creator import GetCreatorTool, fit_result
from collabpilot.tools.builtin.search_creators import SearchCreatorsTool, run_search


ORACLE_KEYS = {"scenario_tags", "expected_ai_signals", "product_relation", "confidence"}


def walk_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(key)
            keys |= walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            keys |= walk_keys(item)
    return keys
SAMPLE_TEXT = (
    "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
    "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
    "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。"
)


def parsed_goal() -> ParsedGoal:
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
    return goal


@pytest.fixture
def campaigns(application) -> CampaignStore:
    return application.campaigns


@pytest.fixture
def parsed_session(application) -> ToolContext:
    session_id = application.store.create_session()
    application.save_campaign(
        Campaign(campaign_id=session_id, goal_status="PARSED", parsed_goal=parsed_goal())
    )
    return ToolContext(session_id=session_id, turn_id=uuid4())


def search(campaigns: CampaignStore) -> SearchCreatorsTool:
    return SearchCreatorsTool(campaigns)


def pure_search(**overrides):
    params = {
        "platforms": ["tiktok", "instagram"],
        "keywords": ["翻译"],
        "window_days": 30,
        "min_followers": None,
        "limit": 50,
        "generated_at": "2026-09-26T00:00:00+00:00",
    }
    return run_search(mock_store.load(), **{**params, **overrides})


# --------------------------------------------------------------------------
# Cases 1, 2, 5, 7, 8: pure search
# --------------------------------------------------------------------------


def test_results_come_from_both_files_and_are_mock() -> None:
    result = pure_search()

    assert {hit.platform for hit in result.accounts} == {"tiktok", "instagram"}
    assert result.meta.is_mock is True and result.meta.data_origin == "mock_seed"
    assert all(hit.account_id.startswith(f"{hit.platform}:") for hit in result.accounts)


def test_cross_platform_creator_is_one_row_with_two_platforms() -> None:
    result = pure_search()

    rows = [item for item in result.creators if item.creator_id == "creator_001"]
    assert len(rows) == 1
    assert rows[0].platforms == ["tiktok", "instagram"]
    assert len(rows[0].account_ids) == 2
    assert len({item.creator_id for item in result.creators}) == len(result.creators)


def test_window_30_excludes_007_009_and_counts_them_outside() -> None:
    narrow = pure_search(window_days=30)
    wide = pure_search(window_days=90)
    late = {"creator_007", "creator_008", "creator_009"}

    assert not late & {item.creator_id for item in narrow.creators}
    assert narrow.meta.outside_window_hits >= 3
    assert late <= {item.creator_id for item in wide.creators}
    assert wide.meta.outside_window_hits < narrow.meta.outside_window_hits


def test_min_followers_drops_only_the_account_below_threshold() -> None:
    result = pure_search(min_followers=100_000)
    creators = mock_store.load()

    assert result.accounts
    assert all(hit.follower_count is not None and hit.follower_count >= 100_000 for hit in result.accounts)
    # creator_003: tiktok 12k (dropped), instagram 198k (kept).
    cora = next(item for item in result.creators if item.creator_id == "creator_003")
    assert cora.platforms == ["instagram"]
    assert mock_store.follower_count(creators["creator_003"].tiktok) < 100_000


def test_keyword_match_is_case_insensitive_substring_and_needs_window_post() -> None:
    by_name = pure_search(keywords=["amy"])
    assert "creator_001" in {item.creator_id for item in by_name.creators}
    none = pure_search(keywords=["不存在的关键词zzz"])
    assert none.creators == [] and none.meta.outside_window_hits == 0
    only_tiktok = pure_search(platforms=["tiktok"])
    assert {hit.platform for hit in only_tiktok.accounts} == {"tiktok"}


def test_search_payload_has_no_oracle_keys() -> None:
    assert not walk_keys(pure_search().model_dump()) & ORACLE_KEYS


# --------------------------------------------------------------------------
# Cases 3, 4, 5, 6: tools against the campaign store
# --------------------------------------------------------------------------


async def test_search_requires_parsed_goal(campaigns, application) -> None:
    session_id = application.store.create_session()
    application.save_campaign(Campaign(campaign_id=session_id, goal_status="CLARIFYING"))

    result = await search(campaigns).execute(
        {"keywords": ["翻译"]}, ToolContext(session_id=session_id, turn_id=uuid4())
    )

    assert result.ok is False and result.error_code == "goal_not_ready"
    assert result.data is None
    assert campaigns.get(session_id).last_search is None


async def test_search_records_last_search_and_defaults(campaigns, parsed_session) -> None:
    tool = search(campaigns)
    result = await tool.execute({"keywords": ["翻译"]}, parsed_session)
    campaign = campaigns.get(parsed_session.session_id)

    assert result.ok and result.data["meta"]["is_mock"] is True
    assert "[MOCK]" in result.display
    assert (tool.default("window_days"), tool.default("min_followers"), tool.default("limit")) == (30, None, 50)
    assert result.data["meta"]["window_days"] == 30 and result.data["meta"]["min_followers"] is None
    assert campaign.stage == "SEARCHING"
    assert campaign.last_search is not None
    assert campaign.last_search.keywords == ["翻译"] and campaign.last_search.window_days == 30
    assert campaign.last_search.creator_ids == [item["creator_id"] for item in result.data["creators"]]
    assert campaign.last_search.creators[0].display_name


async def test_get_creator_returns_both_sides_with_same_display_name(campaigns, parsed_session) -> None:
    tool = GetCreatorTool(campaigns, max_result_chars=12000)

    result = await tool.execute({"creator_id": "creator_001"}, parsed_session)

    assert result.ok
    data = result.data
    assert set(data) >= {"tiktok", "instagram", "creator_id", "display_name"}
    assert data["tiktok"]["display_name"] == data["instagram"]["display_name"] == data["display_name"]
    assert data["data_origin"] == "mock_seed" and data["truncated"] is False
    for account in (data["tiktok"], data["instagram"]):
        assert {
            "recent_posts", "cooperation_history", "audience", "metrics", "contact", "product_usage_evidence"
        } <= set(account)
        assert all("age_days" in post for post in account["recent_posts"])
    assert not walk_keys(data) & ORACLE_KEYS
    assert len(result.model_dump_json()) <= 12000


async def test_get_creator_single_platform_and_not_found(campaigns, parsed_session) -> None:
    tool = GetCreatorTool(campaigns, max_result_chars=12000)

    single = await tool.execute({"creator_id": "creator_011"}, parsed_session)
    missing = await tool.execute({"creator_id": "creator_999"}, parsed_session)

    assert single.ok and single.data["instagram"] is None and single.data["tiktok"] is not None
    assert single.data["platforms"] == ["tiktok"]
    assert missing.ok is False and missing.error_code == "not_found"

    by_name = await tool.execute({"name": "周可儿"}, parsed_session)
    assert by_name.ok and by_name.data["creator_id"] == "creator_104"
    assert by_name.data["display_name"] == "周可儿"

    by_id_field = await tool.execute({"creator_id": "周可儿"}, parsed_session)
    assert by_id_field.ok and by_id_field.data["creator_id"] == "creator_104"


async def test_get_creator_is_truncated_to_limit_keeping_id(campaigns, parsed_session) -> None:
    tool = GetCreatorTool(campaigns, max_result_chars=2500)

    result = await tool.execute({"creator_id": "creator_001"}, parsed_session)

    assert result.ok and len(result.model_dump_json()) <= 2500
    assert result.data["creator_id"] == "creator_001" and result.data["truncated"] is True


def test_fit_result_drops_noise_before_posts() -> None:
    creator = mock_store.load()["creator_001"].model_copy(deep=True)
    from collabpilot.tools.builtin.get_creator import creator_payload

    full = ToolResult(ok=True, data=creator_payload(creator))
    trimmed = fit_result(full, 5500)

    assert trimmed.data["truncated"] is True
    assert len(trimmed.model_dump_json()) <= 5500
    assert trimmed.data["tiktok"]["recent_posts"], "posts survive the first trims"
    assert "music_info" not in trimmed.data["tiktok"]["recent_posts"][0]


async def test_mock_provider_turn_searches_and_fills_the_campaign(application) -> None:
    first = await application.chat(SAMPLE_TEXT, provider_name="mock")
    assert first.goal_status == "PARSED"

    second = await application.chat("开始搜索", session_id=first.session_id, provider_name="mock")
    campaign = application.campaign(first.session_id)

    assert second.tool_calls >= 1
    assert campaign.stage in ("SEARCHING", "EVALUATING", "INSUFFICIENT", "CANDIDATES_READY") and campaign.last_search is not None
    assert campaign.goal_status == "PARSED"
    assert len(campaign.last_search.creators) >= 20
    stored = application.history(first.session_id)
    tool_message = next(message for message in stored if message.role == "tool")
    payload = json.loads(tool_message.content)
    assert payload["ok"] and payload["data"]["meta"]["is_mock"] is True
    assert payload["data"]["meta"]["data_origin"] == "mock_seed"


BEAUTY_CAMERA_IDS = {
    "creator_101",
    "creator_102",
    "creator_103",
    "creator_104",
    "creator_105",
    "creator_106",
}


def test_beauty_camera_keywords_return_six_with_mismatch_and_unknown_audience() -> None:
    creators = mock_store.load()
    generated = mock_store.generated_at().isoformat()
    for keyword in ("美妆", "AI美颜相机"):
        result = run_search(
            creators,
            platforms=["tiktok", "instagram"],
            keywords=[keyword],
            window_days=30,
            min_followers=None,
            limit=50,
            generated_at=generated,
        )
        assert {item.creator_id for item in result.creators} == BEAUTY_CAMERA_IDS

    mismatch = creators["creator_106"].tiktok
    posts = " ".join(post["title"] for post in mismatch["recent_posts"])
    assert mismatch["content_topics"] == ["AI测评", "效率工具", "编程助手"]
    assert "AI美颜相机" in posts and "美妆" in posts
    assert "不拍妆" in posts or "不搭" in posts
    assert creators["creator_101"].tiktok["audience"]["status"] == "known"
    assert creators["creator_104"].tiktok["audience"]["status"] == "unknown"
    assert creators["creator_105"].tiktok["audience"]["status"] == "unknown"
