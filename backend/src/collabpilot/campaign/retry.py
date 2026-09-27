"""Insufficient-fit retry: model proposes a strategy, the app only validates (T07).

Round-1 search parameters come from the T03 tool call (``data_origin=mock_seed``).
A second search is created only after ``accept_retry_strategy`` succeeds. There
is no hard-coded window or follower threshold in this module.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError

from collabpilot.campaign.goal import (
    Campaign,
    RetryStrategy,
    SearchRound,
)
from collabpilot.campaign.hard_filter import RULE_LABEL
from collabpilot.campaign.selection import recommend
from collabpilot.campaign.topic_match import fit_creator_ids
from collabpilot.campaign.verdict import LLM_LABEL
from collabpilot.tools.builtin.search_creators import run_search


ALLOWED_FIELDS = ("window_days", "min_followers", "keywords")
LOCKED_FIELDS = frozenset({"include_own_brand", "include_keyword_mismatch"})
MODEL_STRATEGY_REQUIRED = "model_strategy_required"
RULE_LOCKED = "rule_locked"
STRATEGY_INVALID = "strategy_invalid"
ACCEPT_SHORT_LIST = "accept_short_list"
# Demo needs the first-round shortfall (合格 n/10, n<10) visible. Auto-retry
# would widen the window and pad toward the target; keep budget at 0.
MAX_AUTO_RETRIES = 0
RETRY_ORIGIN = "real_model_output"
RETRY_HEADING = "【再搜策略】"
RETRY_STEP = "retry_strategy"

STAGE_LABELS: dict[str, str] = {
    "CREATED": "未开始",
    "SEARCHING": "搜索中",
    "EVALUATING": "匹配判断中",
    "INSUFFICIENT": "人数不足",
    "RETRYING": "正在再搜",
    "CANDIDATES_READY": "候选已就绪",
    "USER_REVIEW": "待你确认名单",
    "SELECTED": "已保存名单",
    "DRAFTING": "正在写草稿",
    "DRAFT_REVIEW": "草稿待审核",
    "FOLLOW_UP": "待记下跟进",
}


class NotSelected(BaseModel):
    own_brand_cooperated: int
    topic_mismatch: int
    pending: int
    unfit: int


class RoundSummary(BaseModel):
    round: SearchRound
    not_selected: NotSelected
    outside_window_hits: int


class StrategyOutcome(BaseModel):
    params: dict[str, Any] | None = None
    error_code: str | None = None
    detail: str = ""
    strategy: RetryStrategy | None = None

    @property
    def ok(self) -> bool:
        return self.error_code is None and self.params is not None


def target_count(campaign: Campaign) -> int:
    goal = campaign.parsed_goal
    return int(goal.target_count) if goal is not None and goal.target_count else 0


def fit_count(campaign: Campaign) -> int:
    return len(fit_creator_ids(campaign))


def best_round_fit_count(campaign: Campaign) -> int:
    if not campaign.search_rounds:
        return 0
    return max(item.fit_count for item in campaign.search_rounds)


def accept_fit_count(campaign: Campaign) -> int:
    """Qualified count for the accept card — same source as chat/progress.

    Prefer live fit verdicts. If those are empty but an earlier search round
    recorded fits (stale wipe / reset), use that count so the card is not 0.
    When verdicts are missing entirely, fall back to pending_payload then rounds.
    """
    n = fit_count(campaign)
    if n > 0:
        return n
    best = best_round_fit_count(campaign)
    if best > 0:
        return best
    if campaign.verdicts is not None:
        return 0
    payload = campaign.pending_payload or {}
    stored = payload.get("fit_count")
    if isinstance(stored, int) and stored >= 0:
        return stored
    return 0


def gap_count(campaign: Campaign) -> int:
    return max(target_count(campaign) - fit_count(campaign), 0)


def is_insufficient(campaign: Campaign) -> bool:
    target = target_count(campaign)
    return target > 0 and fit_count(campaign) < target


def qualified_lines(campaign: Campaign) -> list[str]:
    n = fit_count(campaign)
    target = target_count(campaign)
    return [f"合格 {n}/{target}", f"缺口 {max(target - n, 0)}"]


def accept_short_list_label(campaign: Campaign) -> str:
    n = accept_fit_count(campaign)
    target = target_count(campaign)
    if target == 0 and campaign.search_rounds:
        last = campaign.search_rounds[-1]
        target = last.fit_count + last.gap
    return f"当前合格 {n} 位，少于目标 {target} 位，是否接受"


def accept_short_list_payload(campaign: Campaign) -> dict[str, int]:
    return {
        "fit_count": accept_fit_count(campaign),
        "target": target_count(campaign),
    }


def queue_accept_short_list(campaign: Campaign) -> Campaign:
    """Set pending accept from the current fit count. Skip a bogus n=0 card when
    there is no judgment and no prior round fits."""
    n = accept_fit_count(campaign)
    if n == 0 and campaign.verdicts is None and best_round_fit_count(campaign) == 0:
        return campaign
    return campaign.model_copy(
        update={
            "stage": "CANDIDATES_READY",
            "pending_decision": ACCEPT_SHORT_LIST,
            "pending_payload": {"fit_count": n, "target": target_count(campaign)},
            "retry_error": None,
        }
    )


def refresh_accept_short_list(campaign: Campaign) -> Campaign:
    """After a newer search/judgment, replace a stale accept card (e.g. n=0 → 5)."""
    if campaign.pending_decision != ACCEPT_SHORT_LIST:
        return campaign
    if campaign.verdicts is None:
        return campaign
    n = fit_count(campaign)
    target = target_count(campaign)
    if target > 0 and n >= target:
        return campaign.model_copy(
            update={"pending_decision": None, "pending_payload": None, "stage": "CANDIDATES_READY"}
        )
    if n == 0 and best_round_fit_count(campaign) == 0:
        return campaign.model_copy(
            update={
                "pending_payload": {"fit_count": 0, "target": target},
            }
        )
    return queue_accept_short_list(campaign)


def round_from_search(campaign: Campaign, *, index: int, strategy: RetryStrategy | None = None) -> SearchRound:
    assert campaign.last_search is not None
    search = campaign.last_search
    n = fit_count(campaign)
    target = target_count(campaign)
    if index == 1:
        origin = "mock_seed"
        reason = None
        model_name = None
    else:
        origin = RETRY_ORIGIN
        reason = strategy.reason if strategy else None
        model_name = strategy.model_name if strategy else campaign.verdict_model_name
    return SearchRound(
        index=index,
        keywords=list(search.keywords),
        window_days=search.window_days,
        min_followers=search.min_followers,
        fit_count=n,
        gap=max(target - n, 0),
        strategy_reason=reason,
        data_origin=origin,
        model_name=model_name,
    )


def append_search_round(campaign: Campaign, *, strategy: RetryStrategy | None = None) -> Campaign:
    index = len(campaign.search_rounds) + 1
    if campaign.last_search is None:
        return campaign
    if index > 2:
        # Third+ judgment: refresh the latest round counts from live fits.
        if not campaign.search_rounds:
            return campaign
        last = round_from_search(
            campaign, index=campaign.search_rounds[-1].index, strategy=strategy
        )
        last = last.model_copy(
            update={
                "strategy_reason": campaign.search_rounds[-1].strategy_reason,
                "data_origin": campaign.search_rounds[-1].data_origin,
                "model_name": campaign.search_rounds[-1].model_name,
            }
        )
        return campaign.model_copy(
            update={"search_rounds": [*campaign.search_rounds[:-1], last]}
        )
    return campaign.model_copy(
        update={"search_rounds": [*campaign.search_rounds, round_from_search(campaign, index=index, strategy=strategy)]}
    )


def build_round_summary(campaign: Campaign) -> RoundSummary:
    """Payload sent to the model. Counts only; no oracle fields."""
    round1 = campaign.search_rounds[0] if campaign.search_rounds else round_from_search(
        campaign, index=1
    )
    verdicts = campaign.verdicts or []
    own_brand = 0
    if campaign.last_filter is not None:
        own_brand = sum(
            1 for item in campaign.last_filter.removed if item.reason == "own_brand_cooperated"
        )
    return RoundSummary(
        round=round1,
        not_selected=NotSelected(
            own_brand_cooperated=own_brand,
            topic_mismatch=len(campaign.topic_rejected_ids),
            pending=sum(1 for item in verdicts if item.decision == "pending"),
            unfit=sum(1 for item in verdicts if item.decision == "unfit"),
        ),
        outside_window_hits=(
            campaign.last_search.outside_window_hits if campaign.last_search else 0
        ),
    )


def _contains_locked_field(value: Any) -> bool:
    if isinstance(value, dict):
        if LOCKED_FIELDS & set(value):
            return True
        if value.get("field") in LOCKED_FIELDS:
            return True
        return any(_contains_locked_field(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_locked_field(item) for item in value)
    return False


def _coerce_change(field: str, value: Any) -> Any:
    """JSON numbers/lists sometimes arrive as strings; never iterate a string as keywords."""
    if field == "window_days":
        return int(value)
    if field == "min_followers":
        if value is None or value == "null":
            return None
        return int(value)
    if field == "keywords":
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                value = parsed
            else:
                value = [value]
        if not isinstance(value, list):
            value = [value]
        return [str(item) for item in value if str(item).strip()]
    return value


def _round_value(round1: SearchRound, field: str) -> Any:
    return getattr(round1, field)


def accept_retry_strategy(round1: SearchRound, strategy: RetryStrategy | None) -> StrategyOutcome:
    """Validate a model strategy. Never invents a window or follower floor."""
    if strategy is None:
        return StrategyOutcome(error_code=MODEL_STRATEGY_REQUIRED)
    if not (strategy.reason or "").strip():
        return StrategyOutcome(error_code=STRATEGY_INVALID, detail="reason 不能为空")
    params: dict[str, Any] = {
        "keywords": list(round1.keywords),
        "window_days": round1.window_days,
        "min_followers": round1.min_followers,
    }
    seen: set[str] = set()
    for change in strategy.changes:
        if change.field in LOCKED_FIELDS:
            return StrategyOutcome(error_code=RULE_LOCKED, detail=change.field)
        if change.field not in ALLOWED_FIELDS:
            return StrategyOutcome(error_code=STRATEGY_INVALID, detail=change.field)
        if change.field in seen:
            return StrategyOutcome(error_code=STRATEGY_INVALID, detail=f"重复字段 {change.field}")
        seen.add(change.field)
        current = _round_value(round1, change.field)
        new_value = _coerce_change(change.field, change.new_value)
        if new_value == current:
            return StrategyOutcome(
                error_code=STRATEGY_INVALID, detail=f"{change.field} 新值与首轮相同"
            )
        params[change.field] = new_value
    return StrategyOutcome(params=params, strategy=strategy)


def parse_retry_strategy(raw: Any, model_name: str) -> StrategyOutcome:
    if raw is None:
        return StrategyOutcome(error_code=MODEL_STRATEGY_REQUIRED)
    if _contains_locked_field(raw):
        return StrategyOutcome(error_code=RULE_LOCKED)
    payload = raw
    if isinstance(raw, dict) and "changes" not in raw and isinstance(raw.get("strategy"), dict):
        payload = raw["strategy"]
    if not isinstance(payload, dict):
        return StrategyOutcome(error_code=STRATEGY_INVALID, detail="strategy 不是对象")
    try:
        data = dict(payload)
        data["model_name"] = model_name
        data["data_origin"] = RETRY_ORIGIN
        strategy = RetryStrategy.model_validate(data)
    except (ValidationError, TypeError, ValueError) as exc:
        return StrategyOutcome(error_code=STRATEGY_INVALID, detail=str(exc))
    return StrategyOutcome(strategy=strategy, params={})


def render_retry_message(summary: RoundSummary) -> str:
    payload = summary.model_dump()
    return (
        f"{RETRY_HEADING}首轮结果如下，请提出一轮再搜策略。\n"
        "```json\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n```\n"
        "只允许改 window_days、min_followers、keywords（1 到 3 项，新值必须与首轮不同），"
        "并写非空 reason。禁止修改或放开 include_own_brand / include_keyword_mismatch。"
        "请只回复一个 ```json 代码块：{\"changes\": [...], \"reason\": \"...\"}。"
    )


def render_strategy_reply(strategy: RetryStrategy) -> str:
    lines = [
        f"再搜策略 {LLM_LABEL} {strategy.model_name}：{strategy.reason}"
    ]
    for change in strategy.changes:
        lines.append(
            f"- {change.field}：{change.old_value} → {change.new_value}（{strategy.reason}）"
        )
    return "\n".join(lines)


def render_strategy_failure(error_code: str) -> str:
    if error_code == MODEL_STRATEGY_REQUIRED:
        return (
            f"未获得模型再搜策略（{error_code}），不创建第 2 轮搜索，"
            "也没有改写时间窗口。"
        )
    if error_code == RULE_LOCKED:
        return f"{RULE_LABEL} 再搜策略试图放开已合作或主题不符排除（{error_code}），未搜索。"
    return f"再搜策略未通过校验（{error_code}），未搜索。"


def list_has_locked_or_own_brand(campaign: Campaign) -> tuple[int, int]:
    """How many locked / own-brand creators leaked into the current kept list."""
    kept = set(campaign.last_filter.kept_ids) if campaign.last_filter else set()
    locked = len(set(campaign.topic_rejected_ids) & kept)
    own_brand = 0
    if campaign.last_filter is not None:
        own_brand = sum(
            1
            for item in campaign.last_filter.removed
            if item.reason == "own_brand_cooperated" and item.creator_id in kept
        )
    return own_brand, locked


def apply_strategy_to_search(campaign: Campaign, params: dict[str, Any], creators: dict) -> Any:
    """Pure second-round search using validated params. No default window."""
    from collabpilot.campaign import mock_store
    from collabpilot.campaign.mock_store import PLATFORMS

    platforms = list(campaign.last_search.platforms) if campaign.last_search else list(PLATFORMS)
    result = run_search(
        creators,
        platforms=platforms,
        keywords=list(params["keywords"]),
        window_days=int(params["window_days"]),
        min_followers=params["min_followers"],
        limit=50,
        generated_at=mock_store.generated_at().isoformat(),
    )
    kept_ids, _skips = recommend(
        [item.creator_id for item in result.creators], campaign
    )
    kept = set(kept_ids)
    return result.model_copy(
        update={
            "creators": [item for item in result.creators if item.creator_id in kept],
            "accounts": [item for item in result.accounts if item.creator_id in kept],
        }
    )


def drafts_empty(campaign: Campaign) -> bool:
    return not campaign.drafts
