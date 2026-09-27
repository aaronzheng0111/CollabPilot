"""T08 verify cases 1–5. Mock-store audience + handwritten Verdicts; no DeepSeek."""

from __future__ import annotations

import inspect
from uuid import uuid4

from collabpilot.campaign import audience as audience_module
from collabpilot.campaign import mock_store
from collabpilot.campaign.audience import (
    AUDIENCE_FIELDS,
    AUDIENCE_OVERRIDE,
    UNKNOWN,
    apply_audience_overrides,
    audience_of,
    audience_view,
    enforce_audience_unknown,
    fit_creators,
    pending_creators,
)
from collabpilot.campaign.goal import Campaign
from collabpilot.campaign.hard_filter import RULE_LABEL
from collabpilot.campaign.verdict import validate_verdicts


MODEL = "deepseek-chat"
UNKNOWN_IDS = [f"creator_{i:03d}" for i in range(20, 24)]


def posts(creator_id: str) -> list[str]:
    return sorted(mock_store.load()[creator_id].post_ids())


def raw_fit(creator_id: str, rank: int) -> dict:
    ids = posts(creator_id)
    return {
        "creator_id": creator_id,
        "decision": "fit",
        "reasons": ["持续发布本品使用内容"],
        "evidence_ids": ids[:2],
        "related_post_ids": ids,
        "topic_match": "match",
        "unknowns": [],
        "rank": rank,
    }


def test_audience_view_unknown_fields_are_the_string_unknown() -> None:
    view = audience_view(
        {
            "status": "unknown",
            "age_range": None,
            "gender": 0,
            "regions": [],
            "interests": "不限",
            "note": "平台未公开受众画像，数据缺失",
        }
    )
    for field in AUDIENCE_FIELDS:
        assert view[field] == UNKNOWN
        assert view[field] not in (None, 0, [], "", "不限")
    assert view["source"] == "[MOCK]"
    assert view["override_source"] == RULE_LABEL
    assert view["note"] == "平台未公开受众画像，数据缺失"

    live = audience_view(audience_of(mock_store.load()["creator_020"]))
    for field in AUDIENCE_FIELDS:
        assert live[field] == UNKNOWN


def test_fit_with_unknown_audience_becomes_pending_with_override() -> None:
    creators = mock_store.load()
    creator = creators["creator_020"]
    batch = validate_verdicts(
        {"verdicts": [raw_fit("creator_001", 1), raw_fit("creator_020", 2)]},
        {"creator_001": creators["creator_001"], "creator_020": creator},
        window_days=30,
        model_name=MODEL,
    )
    assert batch.ok
    original = next(item for item in batch.accepted if item.creator_id == "creator_020")
    assert original.decision == "fit"
    assert "audience" in original.unknowns

    updated = enforce_audience_unknown(original, audience_of(creator))
    assert updated.decision == "pending"
    assert "audience" in updated.unknowns
    assert updated.rule_override == AUDIENCE_OVERRIDE
    assert updated.rank is None

    kept = enforce_audience_unknown(
        next(item for item in batch.accepted if item.creator_id == "creator_001"),
        audience_of(creators["creator_001"]),
    )
    assert kept.decision == "fit" and kept.rule_override is None


def test_020_to_023_are_not_in_fit_creators_and_overridden_are_pending() -> None:
    creators = mock_store.load()
    ids = UNKNOWN_IDS + ["creator_001"]
    batch = validate_verdicts(
        {"verdicts": [raw_fit(cid, rank) for rank, cid in enumerate(ids, 1)]},
        {cid: creators[cid] for cid in ids},
        window_days=30,
        model_name=MODEL,
    )
    assert batch.ok
    accepted = apply_audience_overrides(batch.accepted, {cid: creators[cid] for cid in ids})
    campaign = Campaign(campaign_id=uuid4(), verdicts=accepted)

    assert set(fit_creators(campaign)) == {"creator_001"}
    pending = {item["creator_id"]: item for item in pending_creators(campaign)}
    for cid in UNKNOWN_IDS:
        assert cid not in fit_creators(campaign)
        row = pending[cid]
        assert row["rule_override"] == AUDIENCE_OVERRIDE
        assert row["pending_reason"] == "受众未知"
        assert row["source"] == RULE_LABEL
        assert row["decision"] == "待确认"


def test_verdict_summary_names_audience_unknown_and_fit_gap() -> None:
    from collabpilot.application import render_verdict_summary
    from collabpilot.campaign.goal import ParsedGoal

    creators = mock_store.load()
    ids = ["creator_001", "creator_020"]
    batch = validate_verdicts(
        {"verdicts": [raw_fit(cid, rank) for rank, cid in enumerate(ids, 1)]},
        {cid: creators[cid] for cid in ids},
        window_days=30,
        model_name=MODEL,
    )
    accepted = apply_audience_overrides(batch.accepted, {cid: creators[cid] for cid in ids})
    campaign = Campaign(
        campaign_id=uuid4(),
        goal_status="PARSED",
        parsed_goal=ParsedGoal(
            brand="LinguaGo",
            product="AI 翻译",
            target_audience=["中文用户"],
            platforms=["tiktok"],
            target_count=10,
            inclusion_criteria=[],
            exclusion_criteria=[],
            outreach_count=None,
            needs_user_approval=True,
        ),
        verdicts=accepted,
        verdict_model_name=MODEL,
    )
    text = render_verdict_summary(campaign)
    assert "受众未知" in text and "待确认未计入合格" in text
    assert "合格 1/10" in text
    assert "creator_020" not in text
    assert "creator_020" not in fit_creators(campaign)
    assert "接受当前短名单" in text or "生成草稿" in text
    assert "主题不符与受众未知不计入合格" in text


def test_audience_source_labels_are_mock_and_rule() -> None:
    view = audience_view(audience_of(mock_store.load()["creator_020"]))
    assert view["source"] == "[MOCK]"
    assert view["override_source"] == RULE_LABEL


def test_module_does_not_infer_audience_from_nickname_or_language() -> None:
    source = inspect.getsource(audience_module)
    assert "nickname" not in source
    assert "signature" not in source
    assert "display_name" not in source
    assert "infer" not in source.lower()
