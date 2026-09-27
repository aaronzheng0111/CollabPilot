from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from collabpilot.campaign.goal import Campaign, ParsedGoal


# (label, field) in display order. `needs_user_approval` is shown with 触达人数.
ROWS: list[tuple[str, str]] = [
    ("品牌", "brand"),
    ("产品", "product"),
    ("受众", "target_audience"),
    ("平台", "platforms"),
    ("人数", "target_count"),
    ("触达人数", "outreach_count"),
    ("发送前审核", "needs_user_approval"),
    ("筛选标准", "inclusion_criteria"),
    ("排除条件", "exclusion_criteria"),
]


def _text(value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "—"
    return "—" if value is None else str(value)


def goal_card_html(goal: ParsedGoal, model_name: str | None) -> str:
    assumptions = {item.field: item for item in goal.assumptions}
    rows: list[str] = []
    for label, field in ROWS:
        value = escape(_text(getattr(goal, field)))
        assumed = assumptions.get(field)
        tag = ""
        if assumed is not None:
            tag = (
                '<span class="cp-pill cp-pill-assumed">假设</span>'
                f'<span class="cp-reason">{escape(assumed.reason)}</span>'
            )
        rows.append(
            f'<div class="cp-goal-row"><span class="cp-goal-label">{label}</span>'
            f'<span class="cp-goal-value">{value}{tag}</span></div>'
        )
    header = (
        '<div class="cp-goal-header"><h3>合作目标</h3>'
        '<span class="cp-pill cp-pill-llm">[LLM]</span>'
        f'<span class="cp-pill"><code>{escape(model_name or "unknown")}</code></span></div>'
    )
    return f'<div class="cp-goal-card">{header}{"".join(rows)}</div>'


def render_goal_card(campaign: Campaign | None, target: Any = st) -> None:
    if campaign is None or campaign.parsed_goal is None or campaign.goal_status != "PARSED":
        return
    target.markdown(
        goal_card_html(campaign.parsed_goal, campaign.goal_model_name),
        unsafe_allow_html=True,
    )
