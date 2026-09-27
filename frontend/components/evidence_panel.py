from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


PANEL_TITLE = "判断依据"
SELECT_LABEL = "查看判断依据"


def _age(age_days: int | None) -> str:
    return "发布时间未知" if age_days is None else f"{age_days} 天前"


def evidence_panel_html(view: dict[str, Any]) -> str:
    """Dark product panel (`surface-dark`): reasons, cited post text in code
    font + body-sm, recency, unknowns and the model name."""
    reasons = "".join(f"<li>{escape(reason)}</li>" for reason in view["reasons"])
    excerpts = "".join(
        '<div class="cp-evidence-item">'
        f'<code>{escape(item["id"])}</code>'
        f'<span class="cp-evidence-age">{escape(_age(item["age_days"]))}</span>'
        f'<p class="cp-evidence-text">{escape(item["text"] or "")}</p></div>'
        for item in view["excerpts"]
    ) or '<p class="cp-evidence-text">未引用帖子原文</p>'
    recency = view.get("recency") or {}
    recency_line = (
        f"窗口内相关帖子 {recency.get('recent_related_count', 0)} 条 · "
        f"最近一条 {_age(recency.get('latest_related_age_days'))}"
    )
    unknowns = "".join(
        f'<span class="cp-pill cp-pill-unknown">未知：{escape(field)}</span>'
        for field in view["unknowns"]
    ) or '<span class="cp-evidence-muted">无缺失数据</span>'
    rank = f" · rank {view['rank']}" if view.get("rank") is not None else ""
    audience = view.get("audience") or {}
    audience_block = ""
    if audience:
        cells = "".join(
            f'<div class="cp-audience-cell"><span class="cp-audience-label">{escape(label)}</span>'
            f"<span>{escape(str(audience.get(field) or '未知'))}</span></div>"
            for field, label in (
                ("age_range", "年龄"),
                ("gender", "性别"),
                ("regions", "地区"),
                ("interests", "兴趣"),
            )
        )
        note = audience.get("note") or ""
        audience_block = (
            '<div class="cp-evidence-section">受众</div>'
            f'<div class="cp-audience">{cells}</div>'
            f'<p class="cp-evidence-text">{escape(note)}'
            f'<span class="cp-pill">{escape(audience.get("source") or "[MOCK]")}</span></p>'
        )
        if view.get("rule_override") == "audience_unknown" or audience.get("unknown"):
            audience_block += (
                f'<span class="cp-pill cp-pill-mismatch">{escape(view.get("audience_badge") or "受众未知")}</span>'
                f'<span class="cp-pill cp-pill-rule">{escape(audience.get("override_source") or "[RULE]")}</span>'
            )
    quote = ""
    if view.get("topic_match") == "mismatch":
        post_id = view.get("quoted_post_id") or ""
        badge = view.get("topic_badge") or f"主题不符：{view.get('mismatch_topic') or ''}"
        quote = (
            '<div class="cp-evidence-section">主题不符</div>'
            f'<span class="cp-pill cp-pill-mismatch">{escape(badge)}</span>'
            f'<span class="cp-pill cp-pill-llm">{escape(view.get("judgment_source") or "[LLM]")}</span>'
            f'<blockquote class="cp-evidence-quote">「{escape(view.get("quote") or "")}」'
            f'<br><code>{escape(post_id)}</code></blockquote>'
        )
        if view.get("locked"):
            quote += (
                f'<p class="cp-evidence-lock">{escape(view.get("lock_text") or "已锁定，不再推荐")}'
                f'<span class="cp-pill cp-pill-rule">{escape(view.get("lock_source") or "[RULE]")}</span></p>'
            )
    return (
        '<div class="cp-evidence">'
        '<div class="cp-evidence-header">'
        f"<h3>{PANEL_TITLE} · {escape(view['display_name'])}</h3>"
        f'<span class="cp-pill cp-pill-decision">{escape(view["decision_label"])}{rank}</span>'
        f'<span class="cp-pill cp-pill-llm">[LLM]</span>'
        f'<span class="cp-pill"><code>{escape(view["model_name"])}</code></span>'
        "</div>"
        f'<ul class="cp-evidence-reasons">{reasons}</ul>'
        f'<div class="cp-evidence-section">证据</div>{excerpts}'
        f'<div class="cp-evidence-section">近期</div><p class="cp-evidence-text">{escape(recency_line)}</p>'
        f'<div class="cp-evidence-section">缺失</div><div>{unknowns}</div>'
        f"{audience_block}"
        f"{quote}"
        "</div>"
    )


def render_evidence_panel(
    options: list[tuple[str, str]],
    view_for: Any,
    target: Any = st,
) -> None:
    """`options` are (creator_id, label) in table order; the first one (top
    rank) is selected by default. `view_for(creator_id)` returns the view."""
    if not options:
        return
    ids = [creator_id for creator_id, _ in options]
    labels = dict(options)
    selected = target.selectbox(
        SELECT_LABEL, ids, format_func=lambda cid: labels[cid], key="cp-evidence-creator"
    )
    view = view_for(selected)
    if view is None:
        target.caption("该创作者没有模型判断。")
        return
    target.markdown(evidence_panel_html(view), unsafe_allow_html=True)
