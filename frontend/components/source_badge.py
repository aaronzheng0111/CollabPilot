from __future__ import annotations


MOCK = "[MOCK]"
RULE = "[RULE]"
LLM = "[LLM]"
MOCK_SEND = "[MOCK-SEND]"

ORIGIN_BADGES = {
    "mock_seed": MOCK,
    "mock_api_response": MOCK,
    "real_model_output": LLM,
}

LEGEND_ITEMS = (
    (MOCK, "模拟数据", "cp-pill-mock"),
    (RULE, "应用层规则", "cp-pill-rule"),
    (LLM, "DeepSeek 实时输出", "cp-pill-llm"),
    (MOCK_SEND, "不会发送", "cp-pill-mock-send"),
)


def source_badge(origin: str | None, *, rule: bool = False) -> str:
    if rule:
        return RULE
    return ORIGIN_BADGES.get(origin or "", MOCK if not origin else origin)


def source_badge_html(
    origin: str | None,
    *,
    rule: bool = False,
    model_name: str | None = None,
) -> str:
    label = source_badge(origin, rule=rule)
    css = {
        MOCK: "cp-pill-mock",
        RULE: "cp-pill-rule",
        LLM: "cp-pill-llm",
        MOCK_SEND: "cp-pill-mock-send",
    }.get(label, "cp-pill-mock")
    extra = (
        f' <span class="cp-pill"><code>{model_name}</code></span>'
        if label == LLM and model_name
        else ""
    )
    return f'<span class="cp-pill {css}">{label}</span>{extra}'


def legend_html() -> str:
    """Explanatory strip for demos/docs. Not rendered in the live app."""
    pills = "".join(
        f'<span class="cp-pill {css}">{label}</span> {meaning}'
        for label, meaning, css in LEGEND_ITEMS
    )
    return f'<p class="cp-legend">{pills}</p>'
