"""T02 verify cases 1–10. Model replies are fixed fixtures; DeepSeek is never called."""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from collabpilot.campaign.goal import (
    CONFIRM_ASSUMPTIONS,
    CRITICAL_FIELDS,
    EXCLUDE_COOPERATED,
    FILTER_HEADING,
    REPHRASE_HEADING,
    FIELD_LABELS,
    ParsedGoal,
    apply_user_cooperated_preference,
    build_grill,
    extract_json_block,
    parse_grill_reply,
    pending_assumptions,
    render_clarifying_reply,
    render_parsed_reply,
    validate_grill,
    validate_parsed_goal,
)
from collabpilot.domain.models import Message, ModelResponse, ToolResult
from collabpilot.providers.base import Provider
from collabpilot.tools.base import Tool


SAMPLE_TEXT = (
    "为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。"
    "优先选择最近持续发布相关内容的人，排除已经合作过的账号。"
    "整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。"
)

# What DeepSeek is expected to return for SAMPLE_TEXT (fixture, not a live call).
SAMPLE_PAYLOAD: dict[str, Any] = {
    "brand": None,
    "product": "AI 翻译工具",
    "target_audience": ["中文用户"],
    "platforms": [],
    "target_count": 10,
    "inclusion_criteria": ["最近持续发布相关内容"],
    "exclusion_criteria": ["已经合作过的账号"],
    "outreach_count": 3,
    "needs_user_approval": True,
    "assumptions": [],
    "missing_critical": [],
    "grill": None,
}


def payload(**overrides: Any) -> dict[str, Any]:
    return {**SAMPLE_PAYLOAD, **overrides}


def reply(data: dict[str, Any] | str, prose: str = "已读取你的需求。") -> ModelResponse:
    body = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return ModelResponse(
        content=f"{prose}\n```json\n{body}\n```",
        provider="scripted",
        model="deepseek-chat",
    )


class ScriptedProvider(Provider):
    name = "scripted"

    def __init__(self, responses: list[ModelResponse]):
        self.responses = list(responses)
        self.requests: list[list[Message]] = []
        self.tool_schemas: list[list[dict]] = []

    async def complete(self, messages, model, tools, on_delta=None, temperature=None):
        self.requests.append([message.model_copy() for message in messages])
        self.tool_schemas.append(tools)
        return self.responses.pop(0)

    async def health(self, model: str) -> tuple[bool, str]:
        return True, "scripted"


class FakeSearchTool(Tool):
    name = "search_creators"
    description = "fake"
    input_schema = {"type": "object", "properties": {}}
    risk_level = "read"

    def __init__(self):
        self.calls = 0

    async def execute(self, arguments, context) -> ToolResult:
        self.calls += 1
        return ToolResult(ok=True, data=[])


@pytest.fixture
def search_tool(application) -> FakeSearchTool:
    tool = FakeSearchTool()
    application.runtime.tools._tools[tool.name] = tool
    return tool


def scripted(application, monkeypatch, *responses: ModelResponse) -> ScriptedProvider:
    provider = ScriptedProvider(list(responses))
    monkeypatch.setattr(application.providers, "get", lambda name: provider)
    return provider


def numbered_questions(text: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(r"^\d+[.、)]\s*(.+)$", text, flags=re.MULTILINE)
    ]


def names_a_missing_field(question: str, missing: list[str]) -> bool:
    return any(field in question or FIELD_LABELS[field] in question for field in missing)


# --------------------------------------------------------------------------
# Pure validation (cases 1, 2, 5, 6)
# --------------------------------------------------------------------------


def test_sample_payload_parses_counts_approval_and_exclusion() -> None:
    goal = validate_parsed_goal(SAMPLE_PAYLOAD)

    assert isinstance(goal, ParsedGoal)
    assert (goal.target_count, goal.outreach_count, goal.needs_user_approval) == (
        10,
        3,
        True,
    )
    assert "已经合作过的账号" in goal.exclusion_criteria
    assert goal.platforms == ["tiktok", "instagram"]
    assert "platforms" in goal.assumed_fields()
    assert goal.missing_critical == []


def test_missing_brand_becomes_linguago_assumption() -> None:
    goal = validate_parsed_goal(payload(brand=None))

    assert isinstance(goal, ParsedGoal)
    assert goal.brand == "LinguaGo AI 翻译"
    brand = next(item for item in goal.assumptions if item.field == "brand")
    assert brand.value == "LinguaGo AI 翻译" and brand.reason


def test_missing_platforms_is_assumed_not_asked() -> None:
    goal = validate_parsed_goal(payload(platforms=[]))

    assert isinstance(goal, ParsedGoal)
    assert "platforms" not in goal.missing_critical
    assert goal.platforms == ["tiktok", "instagram"]
    assert "platforms" in goal.assumed_fields()


def test_model_missing_critical_is_recomputed_not_trusted() -> None:
    goal = validate_parsed_goal(payload(missing_critical=["platforms", "brand"]))

    assert isinstance(goal, ParsedGoal)
    assert goal.missing_critical == []


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({k: v for k, v in SAMPLE_PAYLOAD.items() if k != "target_count"}, ["target_count"]),
        (payload(target_count="ten"), ["target_count"]),
        (payload(platforms=["weibo"]), ["platforms"]),
        (payload(needs_user_approval="maybe"), ["needs_user_approval"]),
        ([1, 2], sorted(k for k in SAMPLE_PAYLOAD if k not in ("assumptions", "missing_critical", "grill"))),
    ],
)
def test_invalid_payload_returns_failed_field_names(data, expected) -> None:
    assert validate_parsed_goal(data) == expected


def test_extract_json_block_reports_unparseable_fence() -> None:
    block = extract_json_block("看这里：\n```json\n{not json\n```")
    assert block is not None and block.data is None
    assert extract_json_block("没有代码块") is None
    good = extract_json_block("```json\n{\"a\": 1}\n```")
    assert good is not None and good.data == {"a": 1}


def test_critical_field_table_has_exactly_two_entries() -> None:
    assert list(CRITICAL_FIELDS) == [
        "target_count",
        EXCLUDE_COOPERATED,
    ]
    goal = validate_parsed_goal(
        payload(target_count=None, outreach_count=None, needs_user_approval=None, exclusion_criteria=[])
    )
    assert isinstance(goal, ParsedGoal)
    assert goal.missing_critical == list(CRITICAL_FIELDS)
    assert "outreach_count" not in goal.missing_critical
    assert "needs_user_approval" not in goal.missing_critical
    assert goal.needs_user_approval is True


def test_missing_outreach_count_does_not_block_parsed() -> None:
    goal = validate_parsed_goal(payload(outreach_count=None))
    assert isinstance(goal, ParsedGoal)
    assert goal.missing_critical == []
    assert goal.outreach_count is None


def test_needs_user_approval_defaults_silently_without_asking() -> None:
    goal = validate_parsed_goal(payload(needs_user_approval=None))
    assert isinstance(goal, ParsedGoal)
    assert goal.needs_user_approval is True
    assert goal.missing_critical == []
    assert "needs_user_approval" not in goal.assumed_fields()

    incomplete = validate_parsed_goal(payload(target_count=None, needs_user_approval=None))
    assert isinstance(incomplete, ParsedGoal)
    grill = build_grill(incomplete)
    assert all("needs_user_approval" not in q and "是否需要你审核" not in q for q in grill.questions)
    text = render_clarifying_reply("", incomplete, grill)
    assert "草稿发送前是否需要你审核" not in text
    assert "needs_user_approval" not in text


# --------------------------------------------------------------------------
# Grill helpers (cases 7, 8)
# --------------------------------------------------------------------------


def test_template_grill_names_every_missing_field_without_rephrase_block() -> None:
    goal = validate_parsed_goal(
        payload(target_count=None, needs_user_approval=None, exclusion_criteria=[])
    )
    assert isinstance(goal, ParsedGoal)

    text = render_clarifying_reply("", goal, build_grill(goal))
    questions = numbered_questions(text)

    assert len(questions) >= 2
    assert all(names_a_missing_field(q, goal.missing_critical) for q in questions)
    assert FILTER_HEADING in text
    assert REPHRASE_HEADING not in text
    assert "为其中多少位准备邀请草稿" not in text
    assert "outreach_count" not in text
    assert "草稿发送前是否需要你审核" not in text
    assert "needs_user_approval" not in text
    assert "发送前让我审核" not in text
    assert "勾选创作者后生成邀请草稿" not in text
    parsed = parse_grill_reply(text)
    assert parsed is not None and parsed.filter_suggestion is not None
    assert parsed.rephrase is None


def test_parsed_reply_does_not_contain_rephrase_heading() -> None:
    goal = validate_parsed_goal(SAMPLE_PAYLOAD)
    assert isinstance(goal, ParsedGoal)
    prose = (
        "已读取你的需求。\n\n### 换一种说法\n"
        "> 为「LinguaGo AI 翻译」的「AI 翻译工具」（面向中文用户），"
        "在 tiktok、instagram 找 10 位持续发布相关内容的创作者，"
        "排除已经合作过的账号。勾选创作者后生成邀请草稿，发送前让我审核。"
    )
    text = render_parsed_reply(prose, goal, "deepseek-chat")
    assert REPHRASE_HEADING not in text
    assert "### 换一种说法" not in text
    assert "合作目标已解析" in text
    # Stripped rephrase body must not leak into the chat reply.
    assert "勾选创作者后生成邀请草稿" not in text


def test_model_grill_rephrase_is_dropped_from_clarifying_reply() -> None:
    goal = validate_parsed_goal(
        payload(target_count=None, needs_user_approval=None, exclusion_criteria=[])
    )
    assert isinstance(goal, ParsedGoal)
    model_grill = {
        "questions": [
            "要找多少位？（target_count）",
            "是否排除已合作？（exclude_cooperated）",
        ],
        "filter_suggestion": {
            "field": "followers",
            "operator": ">=",
            "example": "10000",
        },
        "rephrase": (
            "为「LinguaGo AI 翻译」找 10 位，排除已经合作过的账号，发送前让我审核。"
        ),
    }
    grill = build_grill(goal, validate_grill(model_grill, goal))
    assert grill.rephrase is None
    text = render_clarifying_reply("补充一下。", goal, grill)
    assert REPHRASE_HEADING not in text
    assert "排除已经合作过的账号" not in text
    assert "发送前让我审核" not in text
    assert FILTER_HEADING in text


def test_single_missing_field_second_question_confirms_an_assumption() -> None:
    goal = validate_parsed_goal(payload(target_count=None))
    assert isinstance(goal, ParsedGoal)
    assert goal.missing_critical == ["target_count"]

    grill = build_grill(goal)

    assert len(grill.questions) == 2
    assert "target_count" in grill.questions[0]
    assert "brand" in grill.questions[1]
    assert all(
        "outreach_count" not in q
        and "邀请草稿" not in q
        and "needs_user_approval" not in q
        and "是否需要你审核" not in q
        for q in grill.questions
    )


def test_model_grill_is_used_only_when_questions_name_missing_fields() -> None:
    goal = validate_parsed_goal(
        payload(target_count=None, needs_user_approval=None, exclusion_criteria=[])
    )
    assert isinstance(goal, ParsedGoal)
    assert set(goal.missing_critical) == {"target_count", EXCLUDE_COOPERATED}
    good = {
        "questions": [
            "要找多少位？（target_count）",
            "是否排除已合作？（exclude_cooperated）",
        ],
        "filter_suggestion": None,
        "rephrase": "找 10 位创作者，排除已合作。",
    }
    asks_approval = {
        "questions": [
            "要找多少位？（target_count）",
            "发送前要审核吗？（needs_user_approval）",
        ],
        "filter_suggestion": None,
        "rephrase": "找 10 位创作者，发送前让我审核。",
    }
    asks_draft_count = {
        "questions": ["要找多少位？（target_count）", "为其中多少位准备邀请草稿？（outreach_count）"],
        "filter_suggestion": None,
        "rephrase": "找 10 位。",
    }
    vague = {**good, "questions": ["能多说一点吗？", "预算多少？"]}
    no_blocks = {**good, "filter_suggestion": None, "rephrase": None}

    assert validate_grill(good, goal) is not None
    assert validate_grill(asks_approval, goal) is None
    assert validate_grill(asks_draft_count, goal) is None
    assert validate_grill(vague, goal) is None
    assert validate_grill(no_blocks, goal) is None
    assert validate_grill({"questions": ["只有一个问题（target_count）"], "rephrase": "x"}, goal) is None


# --------------------------------------------------------------------------
# Application flow (cases 1–4, 6–10)
# --------------------------------------------------------------------------


async def test_sample_text_turn_reaches_parsed_and_records_model(
    application, monkeypatch, search_tool
) -> None:
    scripted(application, monkeypatch, reply(SAMPLE_PAYLOAD))

    result = await application.chat(SAMPLE_TEXT)
    campaign = application.campaign(result.session_id)

    assert result.goal_status == campaign.goal_status == "PARSED"
    assert campaign.goal_origin == "real_model_output"
    assert campaign.goal_model_name == "deepseek-chat"
    assert campaign.parsed_goal is not None
    assert campaign.parsed_goal.target_count == 10
    assert campaign.parsed_goal.brand == "LinguaGo AI 翻译"
    assert "LinguaGo AI 翻译" in result.content and "[LLM] deepseek-chat" in result.content
    assert "```" not in result.content
    assert REPHRASE_HEADING not in result.content
    assert search_tool.calls == 0


@pytest.mark.parametrize("missing", ["target_count"])
async def test_missing_count_is_clarifying_and_never_searches(
    application, monkeypatch, search_tool, missing
) -> None:
    provider = scripted(application, monkeypatch, reply(payload(**{missing: None})))

    result = await application.chat(SAMPLE_TEXT)
    campaign = application.campaign(result.session_id)

    assert campaign.goal_status == "CLARIFYING"
    assert campaign.parsed_goal is not None
    assert campaign.parsed_goal.missing_critical == [missing]
    assert campaign.grill_rounds == 1
    assert result.tool_calls == 0 and search_tool.calls == 0
    offered = [schema["function"]["name"] for schema in provider.tool_schemas[0]]
    assert "search_creators" not in offered
    assert "草稿" not in result.content.split("###")[0].split("\n")[0]
    assert "为其中多少位准备邀请草稿" not in result.content


async def test_missing_outreach_still_parses_without_draft_count_question(
    application, monkeypatch, search_tool
) -> None:
    scripted(application, monkeypatch, reply(payload(outreach_count=None)))

    result = await application.chat(SAMPLE_TEXT)
    campaign = application.campaign(result.session_id)

    assert result.goal_status == campaign.goal_status == "PARSED"
    assert campaign.parsed_goal is not None
    assert campaign.parsed_goal.outreach_count is None
    assert campaign.parsed_goal.missing_critical == []
    assert "为其中多少位准备邀请草稿" not in result.content
    assert "草稿按勾选生成" in result.content
    assert search_tool.calls == 0


async def test_invalid_json_is_retried_once_then_not_written(
    application, monkeypatch
) -> None:
    provider = scripted(
        application,
        monkeypatch,
        reply("{not json", prose="解析如下"),
        reply({"brand": "x"}, prose="再试一次"),
    )

    result = await application.chat(SAMPLE_TEXT)
    campaign = application.campaign(result.session_id)

    assert len(provider.requests) == 2
    assert provider.requests[1][-1].role == "user"
    assert "未通过校验" in provider.requests[1][-1].content
    assert campaign.parsed_goal is None
    assert campaign.goal_status == "CLARIFYING"
    assert "target_count" in result.content and "未通过校验" in result.content


async def test_invalid_then_valid_json_is_written(application, monkeypatch) -> None:
    scripted(application, monkeypatch, reply("oops"), reply(SAMPLE_PAYLOAD))

    result = await application.chat(SAMPLE_TEXT)

    assert result.goal_status == "PARSED"
    assert application.campaign(result.session_id).parsed_goal is not None


async def test_reply_without_json_block_passes_through(application, monkeypatch) -> None:
    provider = scripted(
        application,
        monkeypatch,
        ModelResponse(content="你好！", provider="scripted", model="deepseek-chat"),
    )

    result = await application.chat("你好")

    assert result.content == "你好！"
    assert len(provider.requests) == 1
    assert application.campaign(result.session_id).goal_status == "CREATED"


async def test_vague_request_with_mock_provider_gets_numbered_questions(
    application, search_tool
) -> None:
    result = await application.chat("帮我找达人", provider_name="mock")
    campaign = application.campaign(result.session_id)

    assert campaign.goal_status == "CLARIFYING"
    assert result.tool_calls == 0 and search_tool.calls == 0
    questions = numbered_questions(result.content)
    assert len(questions) >= 2
    assert campaign.parsed_goal is not None
    assert all(
        names_a_missing_field(q, campaign.parsed_goal.missing_critical) for q in questions
    )
    assert FILTER_HEADING in result.content
    assert REPHRASE_HEADING not in result.content
    assert parse_grill_reply(result.content) is not None


async def test_third_round_lists_assumptions_and_sets_pending_decision(
    application, monkeypatch, search_tool
) -> None:
    incomplete = payload(target_count=None, needs_user_approval=None, outreach_count=None)
    scripted(application, monkeypatch, *(reply(incomplete) for _ in range(3)))

    first = await application.chat("帮我找达人")
    await application.chat("还是那些", session_id=first.session_id)
    third = await application.chat("不知道", session_id=first.session_id)
    campaign = application.campaign(first.session_id)

    assert campaign.grill_rounds == 3
    assert campaign.pending_decision == CONFIRM_ASSUMPTIONS
    assert third.pending_decision == CONFIRM_ASSUMPTIONS
    assert campaign.goal_status == "CLARIFYING"
    assert "待你确认的假设" in third.content
    assert "目标人数" in third.content and "LinguaGo AI 翻译" in third.content
    assert "为其中多少位准备邀请草稿" not in third.content
    assert "触达人数" not in third.content
    assert "草稿发送前是否需要你审核" not in third.content
    assert "needs_user_approval" not in third.content
    assert "发送前是否需要你审核" not in third.content
    assert search_tool.calls == 0

    approved = application.approve_pending(first.session_id, CONFIRM_ASSUMPTIONS, True)
    campaign = application.campaign(first.session_id)
    assert approved.ok and campaign.goal_status == "PARSED"
    assert campaign.pending_decision is None
    assert campaign.parsed_goal is not None
    assert campaign.parsed_goal.target_count == 10
    assert campaign.parsed_goal.needs_user_approval is True
    # outreach_count is optional — confirm must not invent a draft count.
    assert campaign.parsed_goal.outreach_count is None
    assert "target_count" in campaign.parsed_goal.assumed_fields()
    assert "outreach_count" not in campaign.parsed_goal.assumed_fields()
    assert "needs_user_approval" not in campaign.parsed_goal.assumed_fields()


async def test_confirm_in_chat_approves_pending_without_model_call(
    application, monkeypatch
) -> None:
    incomplete = payload(target_count=None)
    provider = scripted(application, monkeypatch, *(reply(incomplete) for _ in range(3)))
    first = await application.chat("找达人")
    for _ in range(2):
        await application.chat("不知道", session_id=first.session_id)
    assert application.campaign(first.session_id).pending_decision == CONFIRM_ASSUMPTIONS

    result = await application.chat("确认", session_id=first.session_id)

    assert len(provider.requests) == 3
    assert result.goal_status == "PARSED" and result.pending_decision is None
    assert application.history(first.session_id)[-1].content == result.content


async def test_completing_critical_fields_next_turn_becomes_parsed(
    application, search_tool
) -> None:
    first = await application.chat("帮我找达人", provider_name="mock")
    assert first.goal_status == "CLARIFYING"

    second = await application.chat(
        "找 10 位，触达 3 位，发送前我要审核，排除已合作过的账号",
        session_id=first.session_id,
        provider_name="mock",
    )
    campaign = application.campaign(first.session_id)

    assert second.goal_status == campaign.goal_status == "PARSED"
    assert campaign.parsed_goal is not None
    assert campaign.parsed_goal.missing_critical == []
    assert (campaign.parsed_goal.target_count, campaign.parsed_goal.outreach_count) == (10, 3)
    assert campaign.grill_rounds == 1
    assert search_tool.calls == 0


def test_allow_recontact_does_not_produce_exclude_confirm_assumption() -> None:
    """User allows recontact → exclude_cooperated is settled; not in 待你确认的假设."""
    goal = validate_parsed_goal(
        payload(
            exclusion_criteria=[],
            inclusion_criteria=["可以再次联系已合作过的账号"],
        )
    )
    assert isinstance(goal, ParsedGoal)
    assert EXCLUDE_COOPERATED not in goal.missing_critical
    assert EXCLUDE_COOPERATED not in {item.field for item in pending_assumptions(goal)}
    assert "已经合作过的账号" not in goal.exclusion_criteria

    # Model forgot the allow marker; user text still settles it.
    blank = validate_parsed_goal(payload(exclusion_criteria=[], inclusion_criteria=[]))
    assert isinstance(blank, ParsedGoal)
    assert EXCLUDE_COOPERATED in blank.missing_critical
    settled = apply_user_cooperated_preference(
        blank, "可以和已经联系过的用户再次取得联系"
    )
    assert EXCLUDE_COOPERATED not in settled.missing_critical
    assert EXCLUDE_COOPERATED not in {item.field for item in pending_assumptions(settled)}


async def test_user_allow_recontact_message_reaches_parsed_without_exclude_confirm(
    application, monkeypatch, search_tool
) -> None:
    # Model leaves cooperated preference blank; user's words settle allow-recontact.
    scripted(
        application,
        monkeypatch,
        reply(payload(exclusion_criteria=[], inclusion_criteria=[])),
    )
    result = await application.chat(
        "找 10 位，触达 3 位，发送前我要审核，可以和已经联系过的用户再次取得联系"
    )
    campaign = application.campaign(result.session_id)

    assert result.goal_status == campaign.goal_status == "PARSED"
    assert campaign.parsed_goal is not None
    assert EXCLUDE_COOPERATED not in campaign.parsed_goal.missing_critical
    assert EXCLUDE_COOPERATED not in {
        item.field for item in pending_assumptions(campaign.parsed_goal)
    }
    assert "已经合作过的账号" not in campaign.parsed_goal.exclusion_criteria
    assert campaign.pending_decision != CONFIRM_ASSUMPTIONS
    assert search_tool.calls == 0


async def test_disabled_search_tool_call_is_rejected_while_clarifying(
    application, monkeypatch, search_tool
) -> None:
    from collabpilot.domain.models import ToolCall

    scripted(
        application,
        monkeypatch,
        ModelResponse(
            provider="scripted",
            model="deepseek-chat",
            tool_calls=[ToolCall(id="c1", name="search_creators", arguments={})],
        ),
        reply(payload(target_count=None)),
    )

    result = await application.chat("找达人")

    assert search_tool.calls == 0
    stored = application.history(result.session_id)
    tool_message = next(message for message in stored if message.role == "tool")
    assert json.loads(tool_message.content)["error_code"] == "tool_disabled"
