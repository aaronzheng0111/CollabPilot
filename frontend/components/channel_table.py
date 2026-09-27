from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from collabpilot.campaign.channels import NO_CHANNEL_TEXT


PANEL_TITLE = "沟通渠道"
CONFIRM_BUTTON = "确认渠道"
SEND_LABELS = ("发送", "私信", "发邮件")
ConfirmChannel = Callable[[str, str], None]


def render_channel_table(
    rows: list[dict[str, Any]] | None,
    on_confirm: ConfirmChannel | None = None,
    target: Any = st,
) -> None:
    """Secondary「沟通渠道」table. Unknown values are the string「未知」.
    Confirm only queues a pending decision; nothing is sent."""
    if not rows:
        return
    target.markdown(f"#### {PANEL_TITLE}")
    for index, row in enumerate(rows):
        cols = target.columns([2, 2, 1, 2, 2, 2], vertical_alignment="center")
        cols[0].markdown(f"`{row['creator_id']}` {row['display_name']}")
        cols[1].write(row["preferred_label"])
        cols[2].write("可私信" if row["dm_available"] else "不可私信")
        cols[3].write(row["email_display"])
        cols[4].write(row["consent_label"])
        cols[5].markdown(row.get("source") or "[MOCK]")
        if not row.get("can_confirm"):
            target.caption(NO_CHANNEL_TEXT)
            continue
        if on_confirm is None:
            continue
        options = row.get("available_labels") or {}
        keys = list(options)
        if not keys:
            target.caption(NO_CHANNEL_TEXT)
            continue
        chosen = target.selectbox(
            "渠道",
            keys,
            format_func=lambda key, labels=options: labels.get(key, key),
            key=f"channel-{row['creator_id']}-{row['platform']}-{index}",
            label_visibility="collapsed",
        )
        if target.button(
            CONFIRM_BUTTON,
            type="secondary",
            key=f"confirm-channel-{row['creator_id']}-{row['platform']}-{index}",
        ):
            on_confirm(row["creator_id"], str(chosen))
