"""Read-only loader for ``data/mock`` (T03).

``load()`` is the only runtime entry point. It strips the oracle fields that
exist for tests and evaluation, merges the two platform files by
``creator_id`` and converts post timestamps to ``age_days`` relative to the
JSON ``meta.generated_at`` so demos are repeatable.

``load_oracle()`` returns the stripped answers and is only for ``backend/tests``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from collabpilot.settings import PROJECT_ROOT


Platform = Literal["tiktok", "instagram"]
PLATFORMS: tuple[Platform, ...] = ("tiktok", "instagram")
MOCK_DIR = PROJECT_ROOT.parent / "data" / "mock"
FILES: dict[Platform, str] = {
    "tiktok": "tiktok_creators.json",
    "instagram": "instagram_creators.json",
}
MOCK_ORIGIN = "mock_seed"

# Test answers. Removed from every object before anything leaves this module.
ORACLE_ACCOUNT_FIELDS = ("scenario_tags", "expected_ai_signals")
ORACLE_NESTED_FIELDS = ("product_relation", "confidence")
ORACLE_FIELDS = (*ORACLE_ACCOUNT_FIELDS, *ORACLE_NESTED_FIELDS)


class MergedCreator(BaseModel):
    creator_id: str
    display_name: str
    platforms: list[Platform]
    tiktok: dict[str, Any] | None = None
    instagram: dict[str, Any] | None = None

    def account(self, platform: str) -> dict[str, Any] | None:
        return self.tiktok if platform == "tiktok" else self.instagram

    def accounts(self) -> list[tuple[Platform, dict[str, Any]]]:
        return [
            (platform, account)
            for platform in PLATFORMS
            if (account := self.account(platform)) is not None
        ]

    def posts(self) -> list[dict[str, Any]]:
        return [post for _, account in self.accounts() for post in account["recent_posts"]]

    def post_ids(self) -> set[str]:
        return {post["post_id"] for post in self.posts()}

    def evidence_ids(self) -> set[str]:
        return {
            item["evidence_id"]
            for _, account in self.accounts()
            for item in account.get("product_usage_evidence", [])
        }


class BrandInfo(BaseModel):
    name: str
    product: str
    key_features: list[str] = []
    exclusion_rules: list[str] = []
    target_audience: list[str] = []
    target_gpm: float | None = None


# ---------------------------------------------------------------------------
# Field helpers (the two files use different key names)
# ---------------------------------------------------------------------------


def post_id(post: dict[str, Any]) -> str:
    return str(post.get("video_id") or post.get("id") or "")


def post_text(post: dict[str, Any]) -> str:
    return str(post.get("title") or post.get("caption") or "")


def follower_count(account: dict[str, Any]) -> int | None:
    profile = account.get("profile", {})
    value = profile.get("follower_count", profile.get("followers_count"))
    return int(value) if value is not None else None


def account_id(account: dict[str, Any]) -> str:
    return f"{account['platform']}:{account['handle']}"


def bio(account: dict[str, Any]) -> str:
    profile = account.get("profile", {})
    return str(profile.get("signature") or profile.get("biography") or "")


def gpm(account: dict[str, Any]) -> float | None:
    metrics = account.get("metrics", {})
    if metrics.get("gpm_origin") == "unknown":
        return None
    value = metrics.get("video_gpm", metrics.get("gpm_30d"))
    return float(value) if value is not None else None


def _post_time(post: dict[str, Any]) -> datetime | None:
    if post.get("create_time") is not None:
        return datetime.fromtimestamp(int(post["create_time"]), UTC)
    if post.get("timestamp"):
        return datetime.fromisoformat(str(post["timestamp"]).replace("Z", "+00:00"))
    return None


def _strip_oracle(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_oracle(item)
            for key, item in value.items()
            if key not in ORACLE_FIELDS
        }
    if isinstance(value, list):
        return [_strip_oracle(item) for item in value]
    return value


def _read(mock_dir: Path, platform: Platform) -> dict[str, Any]:
    return json.loads((mock_dir / FILES[platform]).read_text(encoding="utf-8"))


def _normalize_account(account: dict[str, Any], generated_at: datetime) -> dict[str, Any]:
    clean = _strip_oracle(account)
    posts = []
    for post in clean.get("recent_posts", []):
        published = _post_time(post)
        posts.append(
            {
                **post,
                "post_id": post_id(post),
                "age_days": (generated_at - published).days if published else None,
            }
        )
    clean["recent_posts"] = posts
    clean.setdefault("data_origin", MOCK_ORIGIN)
    return clean


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@lru_cache(maxsize=4)
def generated_at(mock_dir: Path = MOCK_DIR) -> datetime:
    raw = _read(mock_dir, "tiktok")["meta"]["generated_at"]
    return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))


@lru_cache(maxsize=4)
def load(mock_dir: Path = MOCK_DIR) -> dict[str, MergedCreator]:
    """creator_id → MergedCreator with oracle fields removed and age_days added."""
    base = generated_at(mock_dir)
    merged: dict[str, MergedCreator] = {}
    for platform in PLATFORMS:
        for raw in _read(mock_dir, platform)["creators"]:
            account = _normalize_account(raw, base)
            existing = merged.get(raw["creator_id"])
            if existing is None:
                merged[raw["creator_id"]] = MergedCreator(
                    creator_id=raw["creator_id"],
                    display_name=raw["display_name"],
                    platforms=[platform],
                    **{platform: account},
                )
            else:
                setattr(existing, platform, account)
                existing.platforms.append(platform)
    return dict(sorted(merged.items()))


@lru_cache(maxsize=4)
def load_brand(mock_dir: Path = MOCK_DIR) -> BrandInfo:
    return BrandInfo.model_validate(_read(mock_dir, "tiktok")["brand"])


def load_oracle(mock_dir: Path = MOCK_DIR) -> dict[str, dict[str, Any]]:
    """Test answers by creator_id. Call only from ``backend/tests``."""
    oracle: dict[str, dict[str, Any]] = {}
    for platform in PLATFORMS:
        for raw in _read(mock_dir, platform)["creators"]:
            entry = oracle.setdefault(
                raw["creator_id"], {"scenario_tags": [], "expected_ai_signals": {}}
            )
            for tag in raw.get("scenario_tags", []):
                if tag not in entry["scenario_tags"]:
                    entry["scenario_tags"].append(tag)
            entry["expected_ai_signals"].update(raw.get("expected_ai_signals") or {})
    return oracle
