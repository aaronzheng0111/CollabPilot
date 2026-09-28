"""T03 verify cases 1, 2, 4, 5, 9 (loader side)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from collabpilot.campaign import mock_store
from collabpilot.campaign.mock_store import MOCK_DIR, ORACLE_FIELDS, MergedCreator
from collabpilot.settings import PROJECT_ROOT


def raw_ids(platform: str) -> list[str]:
    data = json.loads((MOCK_DIR / mock_store.FILES[platform]).read_text(encoding="utf-8"))
    return [item["creator_id"] for item in data["creators"]]


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


def test_reads_repo_data_mock_not_backend_data() -> None:
    assert MOCK_DIR == PROJECT_ROOT.parent / "data" / "mock"
    assert MOCK_DIR.is_dir() and not str(MOCK_DIR).startswith(str(PROJECT_ROOT / "data"))


def test_merges_both_files_by_creator_id() -> None:
    creators = mock_store.load()
    tiktok, instagram = set(raw_ids("tiktok")), set(raw_ids("instagram"))

    assert set(creators) == tiktok | instagram
    assert len(creators) == 40
    cross = [item for item in creators.values() if len(item.platforms) == 2]
    assert len(cross) == len(tiktok & instagram) == 10
    amy = creators["creator_001"]
    assert amy.platforms == ["tiktok", "instagram"]
    assert amy.tiktok is not None and amy.instagram is not None
    assert amy.tiktok["display_name"] == amy.instagram["display_name"] == amy.display_name


def test_single_platform_creator_has_null_other_side() -> None:
    creators = mock_store.load()
    tiktok_only = next(cid for cid in raw_ids("tiktok") if cid not in raw_ids("instagram"))
    instagram_only = next(cid for cid in raw_ids("instagram") if cid not in raw_ids("tiktok"))

    assert creators[tiktok_only].instagram is None and creators[tiktok_only].platforms == ["tiktok"]
    assert creators[instagram_only].tiktok is None and creators[instagram_only].platforms == ["instagram"]


def test_oracle_fields_are_removed_everywhere() -> None:
    dumped = [item.model_dump() for item in mock_store.load().values()]
    keys = walk_keys(dumped)

    assert not keys & set(ORACLE_FIELDS)
    # The evidence rows survive, only their two answer keys are gone.
    evidence = dumped[0]["tiktok"]["product_usage_evidence"][0]
    assert {"evidence_id", "evidence_text", "source_post_id"} <= set(evidence)
    accounts = [account for item in dumped for account in (item["tiktok"], item["instagram"]) if account]
    assert all(account["data_origin"] == "mock_seed" for account in accounts)


def test_posts_get_age_days_relative_to_generated_at_not_now() -> None:
    creators = mock_store.load()
    assert mock_store.generated_at().isoformat() == "2026-09-26T00:00:00+00:00"
    for post in creators["creator_001"].posts():
        assert post["post_id"] and isinstance(post["age_days"], int)
        assert 0 <= post["age_days"] <= 14
    late = [post["age_days"] for post in creators["creator_007"].posts()]
    assert min(late) >= 40 and max(late) <= 73


def test_oracle_is_only_readable_through_load_oracle() -> None:
    oracle = mock_store.load_oracle()

    assert set(oracle) == set(mock_store.load())
    assert "first_round_pass" in oracle["creator_001"]["scenario_tags"]
    assert oracle["creator_001"]["expected_ai_signals"]
    assert isinstance(mock_store.load()["creator_001"], MergedCreator)


def test_backend_src_only_names_oracle_fields_in_the_strip_list() -> None:
    pattern = re.compile(r"scenario_tags|expected_ai_signals|product_relation")
    offenders = [
        path.relative_to(PROJECT_ROOT)
        for path in (PROJECT_ROOT / "src").rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == [Path("src/collabpilot/campaign/mock_store.py")]
