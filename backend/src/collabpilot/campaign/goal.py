"""ParsedGoal schema, critical-field table and clarifying-reply helpers (T02).

Everything here is pure: no model calls, no storage. The application layer
extracts the fenced JSON block from the model reply, runs
``validate_parsed_goal`` and renders the reply with the helpers below.
"""

from __future__ import annotations

import json
import re
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError, model_validator

from collabpilot.campaign.hard_filter import KeptCreator, RemovedCreator
from collabpilot.campaign.verdict import RejectedVerdict, Verdict


Platform = Literal["tiktok", "instagram"]
GoalStatus = Literal["CREATED", "PARSING", "CLARIFYING", "PARSED"]
GOAL_ORIGIN = "real_model_output"
CONFIRM_ASSUMPTIONS = "confirm_assumptions"
MAX_GRILL_ROUNDS = 3


class Assumption(BaseModel):
    field: str
    value: Any
    reason: str


class ParsedGoal(BaseModel):
    brand: str | None
    product: str | None
    target_audience: list[str]
    platforms: list[Platform]
    target_count: Annotated[int, Field(ge=1)] | None
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]
    outreach_count: Annotated[int, Field(ge=1)] | None
    needs_user_approval: bool | None
    assumptions: list[Assumption] = Field(default_factory=list)
    missing_critical: list[str] = Field(default_factory=list)

    def assumed_fields(self) -> set[str]:
        return {item.field for item in self.assumptions}


class FilterSuggestion(BaseModel):
    field: str
    operator: str
    example: str


class Grill(BaseModel):
    questions: list[str] = Field(min_length=2)
    filter_suggestion: FilterSuggestion | None = None
    rephrase: str | None = None

    @model_validator(mode="after")
    def _needs_suggestion_or_rephrase(self) -> Grill:
        if self.filter_suggestion is None and not (self.rephrase or "").strip():
            raise ValueError("filter_suggestion or rephrase is required")
        return self


# Search / evaluation stage. Kept apart from goal_status so a PARSED goal can
# be searched again (T07) without the search tools being disabled.
CampaignStage = Literal[
    "CREATED",
    "SEARCHING",
    "EVALUATING",
    "INSUFFICIENT",
    "RETRYING",
    "CANDIDATES_READY",
    "USER_REVIEW",
    "SELECTED",
    "DRAFTING",
    "DRAFT_REVIEW",
    "FOLLOW_UP",
]


class TopicLock(BaseModel):
    """Application-layer lock after a validated mismatch judgment (T06)."""

    creator_id: str
    mismatch_topic: str | None = None
    quote: str | None = None
    quoted_post_id: str | None = None
    rule: bool = True
    data_origin: Literal["rule"] = "rule"


class StrategyChange(BaseModel):
    field: str
    old_value: Any
    new_value: Any


class RetryStrategy(BaseModel):
    changes: list[StrategyChange] = Field(min_length=1, max_length=3)
    reason: str
    data_origin: Literal["real_model_output"] = "real_model_output"
    model_name: str


class SearchRound(BaseModel):
    """One search+judgment round. Round 1 is the T03 tool call (mock_seed)."""

    index: int = Field(ge=1, le=2)
    keywords: list[str]
    window_days: int
    min_followers: int | None
    fit_count: int
    gap: int
    strategy_reason: str | None = None
    data_origin: Literal["mock_seed", "real_model_output"]
    model_name: str | None = None


class CreatorRef(BaseModel):
    creator_id: str
    display_name: str
    platforms: list[Platform]


class SearchRecord(BaseModel):
    """Last successful `search_creators` call (T03). T07 uses it as round 1."""

    keywords: list[str]
    window_days: int
    min_followers: int | None
    platforms: list[Platform]
    creators: list[CreatorRef]
    outside_window_hits: int = 0

    @property
    def creator_ids(self) -> list[str]:
        return [item.creator_id for item in self.creators]


class FilterRecord(BaseModel):
    """Last successful `apply_hard_filters` call (T04)."""

    kept: list[KeptCreator]
    removed: list[RemovedCreator]

    @property
    def kept_ids(self) -> list[str]:
        return [item.creator_id for item in self.kept]


class Campaign(BaseModel):
    campaign_id: UUID
    goal_status: GoalStatus = "CREATED"
    parsed_goal: ParsedGoal | None = None
    goal_origin: Literal["real_model_output"] | None = None
    goal_model_name: str | None = None
    grill_rounds: int = 0
    pending_decision: str | None = None
    stage: CampaignStage = "CREATED"
    last_search: SearchRecord | None = None
    last_filter: FilterRecord | None = None
    # T05: validated model verdicts for `last_filter.kept`. None until the
    # judgment step has run; the filter tool resets it on every new round.
    verdicts: list[Verdict] | None = None
    verdict_rejected: list[RejectedVerdict] = Field(default_factory=list)
    verdict_model_name: str | None = None
    verdict_error: str | None = None
    # T06: mismatch creators stay out of later rounds and the final list.
    topic_rejected_ids: list[str] = Field(default_factory=list)
    topic_locks: list[TopicLock] = Field(default_factory=list)
    # T07: rounds, model retry strategy, auto-retry budget.
    search_rounds: list[SearchRound] = Field(default_factory=list)
    retry_strategy: RetryStrategy | None = None
    auto_retries: int = 0
    retry_error: str | None = None
    drafts: list[dict[str, Any]] = Field(default_factory=list)
    draft_error: str | None = None
    follow_ups: list[dict[str, Any]] = Field(default_factory=list)
    follow_error: str | None = None
    # T09: persisted selection. campaign_id stays stable for the same fingerprint.
    goal_fingerprint: str | None = None
    saved_creator_ids: list[str] = Field(default_factory=list)
    excluded_creator_ids: list[str] = Field(default_factory=list)
    accepted_from_pending: list[str] = Field(default_factory=list)
    pending_payload: dict[str, Any] | None = None
    skip_counts: dict[str, int] = Field(default_factory=dict)
    confirmed_channels: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Field tables
# ---------------------------------------------------------------------------

EXCLUDE_COOPERATED = "exclude_cooperated"

# Only these two decide CLARIFYING vs PARSED. Order is the order questions
# are asked in. ``outreach_count`` is optional: drafts come from table selection.
# ``needs_user_approval`` is never asked — product never sends; default True.
CRITICAL_FIELDS: dict[str, str] = {
    "target_count": "目标人数",
    EXCLUDE_COOPERATED: "是否排除已合作过的账号",
}

FIELD_LABELS: dict[str, str] = {
    "brand": "品牌",
    "product": "产品",
    "target_audience": "受众",
    "platforms": "平台",
    "inclusion_criteria": "筛选标准",
    "exclusion_criteria": "排除条件",
    "outreach_count": "触达人数",
    "needs_user_approval": "发送前审核",
    **CRITICAL_FIELDS,
}

# Non-critical fields: missing means "assume", never "ask".
DEFAULT_ASSUMPTIONS: dict[str, tuple[Any, str]] = {
    "brand": ("LinguaGo AI 翻译", "原文未提及品牌，按演示默认品牌处理"),
    "product": ("AI 翻译工具", "原文未点名产品，按默认产品处理"),
    "target_audience": (["中文用户"], "原文未描述受众，按默认受众处理"),
    "platforms": (["tiktok", "instagram"], "原文未指定平台，默认两个平台都搜"),
}

# Filled when null without recording an assumption or asking the user.
SILENT_DEFAULTS: dict[str, Any] = {
    "needs_user_approval": True,
}

# Used only when the user still has not supplied a critical field after
# MAX_GRILL_ROUNDS and approves `confirm_assumptions`.
CRITICAL_FALLBACKS: dict[str, tuple[Any, str]] = {
    "target_count": (10, "追问 3 轮仍未给出目标人数，按 10 位处理"),
    EXCLUDE_COOPERATED: ("已经合作过的账号", "未说明是否排除已合作账号，默认排除"),
}

COOPERATED_MARKERS = ("合作", "cooperat", "collab", "partner")
# Explicit allow-recontact settles exclude_cooperated without adding an exclude rule.
ALLOW_RECONTACT_MARKERS = (
    "可以再次联系",
    "可以再次取得联系",
    "再次取得联系",
    "不排除已合作",
    "不排除已经合作",
    "不排除已联系",
    "允许再次联系",
    "可以和已经联系",
    "可以和已联系",
    "可以和已合作",
    "可以和已经合作",
    "可以联系已合作",
    "可以联系已经合作",
    "可以联系已联系",
)
ALLOW_RECONTACT_CRITERION = "可以再次联系已合作过的账号"

REQUIRED_KEYS: frozenset[str] = frozenset(
    set(ParsedGoal.model_fields) - {"assumptions", "missing_critical"}
)

DEFAULT_FILTER = FilterSuggestion(
    field="follower_count", operator=">=", example="10000"
)

CLARIFYING_TABLE_TEXT = "需求未完成，表格暂无筛选结果"


def mentions_cooperated(criteria: list[str]) -> bool:
    return any(
        marker in item.lower() for item in criteria for marker in COOPERATED_MARKERS
    )


def allows_recontact(texts: list[str] | str) -> bool:
    """True when the user (or model criteria) explicitly allow contacting past collaborators."""
    if isinstance(texts, str):
        blob = texts
    else:
        blob = "\n".join(texts)
    return any(marker in blob for marker in ALLOW_RECONTACT_MARKERS)


def excludes_cooperated(criteria: list[str]) -> bool:
    """True when exclusion_criteria names past collaborators and is not an allow-recontact line."""
    return any(
        mentions_cooperated([item]) and not allows_recontact(item)
        for item in criteria
    )


def cooperated_preference_settled(goal: ParsedGoal) -> bool:
    """Settled by exclude-past OR explicit allow-recontact; default exclude only if neither."""
    if allows_recontact(goal.inclusion_criteria + goal.exclusion_criteria):
        return True
    return excludes_cooperated(goal.exclusion_criteria)


def should_exclude_own_brand(goal: ParsedGoal) -> bool:
    """Hard filter drops past collaborators unless the goal explicitly allows recontact."""
    return not allows_recontact(goal.inclusion_criteria + goal.exclusion_criteria)


def apply_user_cooperated_preference(goal: ParsedGoal, user_text: str) -> ParsedGoal:
    """If the user's own words allow recontact, record it and drop a conflicting exclude."""
    if not allows_recontact(user_text):
        return goal
    inclusion = list(goal.inclusion_criteria)
    if not allows_recontact(inclusion + goal.exclusion_criteria):
        inclusion.append(ALLOW_RECONTACT_CRITERION)
    exclusion = [
        item
        for item in goal.exclusion_criteria
        if not (mentions_cooperated([item]) and not allows_recontact(item))
    ]
    updated = goal.model_copy(
        update={"inclusion_criteria": inclusion, "exclusion_criteria": exclusion}
    )
    return updated.model_copy(
        update={"missing_critical": compute_missing_critical(updated)}
    )


def compute_missing_critical(goal: ParsedGoal) -> list[str]:
    missing: list[str] = []
    if goal.target_count is None:
        missing.append("target_count")
    if not cooperated_preference_settled(goal):
        missing.append(EXCLUDE_COOPERATED)
    return missing


def _is_blank(value: Any) -> bool:
    return value is None or value == [] or value == ""


def apply_default_assumptions(goal: ParsedGoal) -> ParsedGoal:
    """Fill non-critical blanks with defaults and record them as assumptions.

    ``needs_user_approval`` is filled silently (never asked, never listed under
    待你确认的假设): the product never sends outreach.
    """
    updates: dict[str, Any] = {}
    assumptions = list(goal.assumptions)
    assumed = goal.assumed_fields()
    for field, value in SILENT_DEFAULTS.items():
        if getattr(goal, field) is None:
            updates[field] = value
    for field, (value, reason) in DEFAULT_ASSUMPTIONS.items():
        if not _is_blank(getattr(goal, field)):
            continue
        updates[field] = value
        if field not in assumed:
            assumptions.append(Assumption(field=field, value=value, reason=reason))
    updates["assumptions"] = assumptions
    filled = goal.model_copy(update=updates)
    return filled.model_copy(update={"missing_critical": compute_missing_critical(filled)})


def validate_parsed_goal(obj: Any) -> ParsedGoal | list[str]:
    """Return a ParsedGoal, or the names of the fields that failed validation.

    ``missing_critical`` is always recomputed here; whatever the model wrote
    into that key is ignored so non-critical fields can never block parsing.
    """
    if not isinstance(obj, dict):
        return sorted(REQUIRED_KEYS)
    payload = {key: value for key, value in obj.items() if key != "grill"}
    missing_keys = sorted(REQUIRED_KEYS - payload.keys())
    if missing_keys:
        return missing_keys
    payload.pop("missing_critical", None)
    try:
        goal = ParsedGoal.model_validate(payload)
    except ValidationError as exc:
        failed = {str(error["loc"][0]) for error in exc.errors() if error["loc"]}
        return sorted(failed) or sorted(REQUIRED_KEYS)
    return apply_default_assumptions(goal)


def apply_confirm_assumptions(goal: ParsedGoal | None) -> ParsedGoal:
    """Fill the still-missing critical fields from CRITICAL_FALLBACKS."""
    if goal is None:
        goal = apply_default_assumptions(
            ParsedGoal(
                brand=None,
                product=None,
                target_audience=[],
                platforms=[],
                target_count=None,
                inclusion_criteria=[],
                exclusion_criteria=[],
                outreach_count=None,
                needs_user_approval=None,
            )
        )
    updates: dict[str, Any] = {}
    assumptions = list(goal.assumptions)
    for field in compute_missing_critical(goal):
        value, reason = CRITICAL_FALLBACKS[field]
        if field == EXCLUDE_COOPERATED:
            updates["exclusion_criteria"] = [*goal.exclusion_criteria, value]
        else:
            updates[field] = value
        assumptions.append(Assumption(field=field, value=value, reason=reason))
    updates["assumptions"] = assumptions
    filled = goal.model_copy(update=updates)
    return filled.model_copy(update={"missing_critical": compute_missing_critical(filled)})


def pending_assumptions(goal: ParsedGoal) -> list[Assumption]:
    """Assumptions the user would be confirming: recorded ones + critical fallbacks."""
    extra = [
        Assumption(field=field, value=value, reason=reason)
        for field, (value, reason) in CRITICAL_FALLBACKS.items()
        if field in goal.missing_critical
    ]
    return [*goal.assumptions, *extra]


# ---------------------------------------------------------------------------
# JSON block extraction
# ---------------------------------------------------------------------------

FENCE = re.compile(r"```(?:json|JSON)?[ \t]*\r?\n(.*?)```", re.DOTALL)


class JsonBlock(BaseModel):
    raw: str
    data: dict[str, Any] | None = None  # None when the block is not a JSON object


def extract_json_block(text: str) -> JsonBlock | None:
    """Return the first fenced block that parses as an object, else the first fence."""
    first: JsonBlock | None = None
    for match in FENCE.finditer(text or ""):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            return JsonBlock(raw=raw, data=data)
        if first is None:
            first = JsonBlock(raw=raw, data=None)
    return first


def strip_json_blocks(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", FENCE.sub("", text or "")).strip()


# ---------------------------------------------------------------------------
# Grill (clarifying questions)
# ---------------------------------------------------------------------------

QUESTION_TEMPLATES: dict[str, str] = {
    "target_count": "需要找多少位创作者？（target_count，例如 10）",
    EXCLUDE_COOPERATED: "是否排除已经合作过的账号？（exclude_cooperated，是/否）",
}


def _names_field(question: str, fields: set[str]) -> bool:
    lowered = question.lower()
    return any(
        field.lower() in lowered or FIELD_LABELS.get(field, field) in question
        for field in fields
    )


def validate_grill(obj: Any, goal: ParsedGoal) -> Grill | None:
    """Accept the model's grill only if every question names a missing field
    (or, when one critical field is missing, an assumption)."""
    if not isinstance(obj, dict):
        return None
    try:
        grill = Grill.model_validate(obj)
    except ValidationError:
        return None
    allowed = set(goal.missing_critical)
    if len(goal.missing_critical) == 1:
        allowed |= goal.assumed_fields()
    if all(_names_field(question, allowed) for question in grill.questions):
        return grill
    return None


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "—"
    return "—" if value is None else str(value)


def build_grill(goal: ParsedGoal, model_grill: Grill | None = None) -> Grill:
    if model_grill is not None:
        # Never surface a rephrase block in chat, even if the model sent one.
        return model_grill.model_copy(
            update={
                "rephrase": None,
                "filter_suggestion": model_grill.filter_suggestion or DEFAULT_FILTER,
            }
        )
    questions = [QUESTION_TEMPLATES[field] for field in goal.missing_critical]
    if len(questions) == 1:
        first = goal.assumptions[0] if goal.assumptions else None
        if first is not None:
            label = FIELD_LABELS.get(first.field, first.field)
            questions.append(
                f"{label}按假设为「{_format_value(first.value)}」，是否正确？（{first.field}）"
            )
        else:
            questions.append("品牌按假设为「LinguaGo AI 翻译」，是否正确？（brand）")
    return Grill(
        questions=questions,
        filter_suggestion=DEFAULT_FILTER,
        rephrase=None,
    )


# ---------------------------------------------------------------------------
# Reply rendering / parsing
# ---------------------------------------------------------------------------

FILTER_HEADING = "推荐过滤"
REPHRASE_HEADING = "换一种说法"  # legacy; must never appear in rendered chat replies
ASSUMPTIONS_HEADING = "当前假设"
CONFIRM_HEADING = "待你确认的假设"
QUESTIONS_LEAD = "关键信息还不完整，补齐以下字段后才会开始搜索："

# Drop model prose that still emits the old rephrase heading/block.
_REPHRASE_SECTION = re.compile(
    rf"(?:^|\n)#{{1,3}}\s*{re.escape(REPHRASE_HEADING)}\s*\n(?:>[^\n]*(?:\n|$))*",
    flags=re.MULTILINE,
)


def strip_rephrase_section(text: str) -> str:
    cleaned = _REPHRASE_SECTION.sub("\n", text or "")
    # Also drop a bare heading if the model omitted the markdown hashes.
    cleaned = re.sub(
        rf"(?:^|\n){re.escape(REPHRASE_HEADING)}\s*(?:\n|$)",
        "\n",
        cleaned,
    )
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _render_assumptions(assumptions: list[Assumption]) -> list[str]:
    return [
        f"- {FIELD_LABELS.get(item.field, item.field)}：{_format_value(item.value)}"
        f"（{item.reason}）"
        for item in assumptions
    ]


def render_clarifying_reply(
    prose: str,
    goal: ParsedGoal,
    grill: Grill,
    *,
    ask_confirmation: bool = False,
) -> str:
    lines: list[str] = []
    prose = strip_rephrase_section(prose)
    if prose:
        lines += [prose, ""]
    lines.append(QUESTIONS_LEAD)
    lines += [f"{index}. {question}" for index, question in enumerate(grill.questions, 1)]
    if grill.filter_suggestion:
        suggestion = grill.filter_suggestion
        lines += [
            "",
            f"### {FILTER_HEADING}",
            f"- 字段 `{suggestion.field}` · 比较方式 `{suggestion.operator}` · 示例值 `{suggestion.example}`",
        ]
    # Deliberately omit 「换一种说法」: never put a rephrase heading or block in chat.
    if ask_confirmation:
        lines += ["", f"### {CONFIRM_HEADING}"]
        lines += _render_assumptions(pending_assumptions(goal))
        lines.append("")
        lines.append(
            "已追问 3 轮。请在「待你决定」中批准「确认以上假设」，或直接回复「确认」，"
            "我将按这些假设整理目标；确认前不会开始搜索。"
        )
    elif goal.assumptions:
        lines += ["", f"### {ASSUMPTIONS_HEADING}"]
        lines += _render_assumptions(goal.assumptions)
    return "\n".join(lines).strip()


def render_invalid_reply(prose: str, failed_fields: list[str]) -> str:
    fields = "、".join(f"`{field}`" for field in failed_fields)
    note = f"模型输出的目标 JSON 两次未通过校验，未写入活动。未通过的字段：{fields}。请再描述一次合作目标。"
    prose = strip_rephrase_section(prose)
    return f"{prose}\n\n{note}".strip() if prose else note


def goal_summary(goal: ParsedGoal, model_name: str) -> str:
    assumed = goal.assumed_fields()

    def cell(field: str, value: Any) -> str:
        text = _format_value(value)
        return f"{text}（假设）" if field in assumed else text

    outreach = (
        f"触达 {goal.outreach_count} · "
        if goal.outreach_count is not None
        else "草稿按勾选生成 · "
    )
    return (
        f"合作目标已解析 [LLM] {model_name}："
        f"品牌 {cell('brand', goal.brand)} · 受众 {cell('target_audience', goal.target_audience)} · "
        f"平台 {cell('platforms', goal.platforms)} · 人数 {goal.target_count} · "
        f"{outreach}发送前审核 {_format_value(goal.needs_user_approval)} · "
        f"排除 {_format_value(goal.exclusion_criteria)}"
    )


def render_parsed_reply(prose: str, goal: ParsedGoal, model_name: str) -> str:
    summary = goal_summary(goal, model_name)
    prose = strip_rephrase_section(prose)
    return f"{prose}\n\n{summary}".strip() if prose else summary


NUMBERED = re.compile(r"^\s*(\d+)[.、)]\s*(.+?)\s*$")


def parse_grill_reply(text: str) -> Grill | None:
    """Recover the Grill structure from a rendered clarifying reply."""
    questions: list[str] = []
    filter_suggestion: FilterSuggestion | None = None
    rephrase: str | None = None
    section: str | None = None
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip()
            continue
        if section is None:
            match = NUMBERED.match(stripped)
            if match:
                questions.append(match.group(2))
        elif section == FILTER_HEADING and stripped.startswith("-"):
            codes = re.findall(r"`([^`]+)`", stripped)
            if len(codes) >= 3:
                filter_suggestion = FilterSuggestion(
                    field=codes[0], operator=codes[1], example=codes[2]
                )
        elif section == REPHRASE_HEADING and stripped.startswith(">"):
            rephrase = stripped.lstrip(">").strip()
    try:
        return Grill(
            questions=questions, filter_suggestion=filter_suggestion, rephrase=rephrase
        )
    except ValidationError:
        return None
