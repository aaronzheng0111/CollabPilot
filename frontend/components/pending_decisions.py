from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from collabpilot.campaign.decisions import decision_label
from collabpilot.campaign.drafts import pending_review_drafts, review_draft_label
from collabpilot.campaign.follow_up import note_row_label, waiting_user_follow_ups
from collabpilot.campaign.goal import Campaign


EMPTY_TEXT = "目前没有需要你决定的事项"
REJECT_DRAFT_BUTTON = "退回"
Decide = Callable[[str, bool], None]
ReviewDraft = Callable[[str, bool], None]
NoteFollowUp = Callable[[str, bool], None]


def render_pending_decisions(
    campaign: Campaign | None,
    on_decide: Decide,
    on_review_draft: ReviewDraft | None = None,
    on_note_follow_up: NoteFollowUp | None = None,
) -> None:
    """One row per pending decision: label, 批准 (primary/coral), 拒绝 (secondary).

    After drafts are saved, each pending_review draft is also a row with 批准 / 退回.
    After a follow-up is saved, each waiting_user item is a row with 批准 / 拒绝.
    """
    st.markdown("#### 待你决定")
    pending = campaign.pending_decision if campaign else None
    review_rows = pending_review_drafts(campaign) if campaign and on_review_draft else []
    note_rows = waiting_user_follow_ups(campaign) if campaign and on_note_follow_up else []
    if not pending and not review_rows and not note_rows:
        st.caption(EMPTY_TEXT)
        return
    if pending:
        label, approve, reject = st.columns([3, 1, 1], vertical_alignment="center")
        label.write(decision_label(campaign))
        approve.button(
            "批准",
            key=f"approve-{pending}",
            type="primary",
            on_click=on_decide,
            args=(pending, True),
            width="stretch",
        )
        reject.button(
            "拒绝",
            key=f"reject-{pending}",
            type="secondary",
            on_click=on_decide,
            args=(pending, False),
            width="stretch",
        )
    for draft in review_rows:
        label, approve, reject = st.columns([3, 1, 1], vertical_alignment="center")
        label.write(review_draft_label(campaign, draft))
        approve.button(
            "批准",
            key=f"approve-draft-{draft.id}",
            type="primary",
            on_click=on_review_draft,
            args=(draft.id, True),
            width="stretch",
        )
        reject.button(
            REJECT_DRAFT_BUTTON,
            key=f"reject-draft-{draft.id}",
            type="secondary",
            on_click=on_review_draft,
            args=(draft.id, False),
            width="stretch",
        )
    for item in note_rows:
        label, approve, reject = st.columns([3, 1, 1], vertical_alignment="center")
        label.write(note_row_label(campaign, item))
        approve.button(
            "批准",
            key=f"approve-note-{item.id}",
            type="primary",
            on_click=on_note_follow_up,
            args=(item.id, True),
            width="stretch",
        )
        reject.button(
            "拒绝",
            key=f"reject-note-{item.id}",
            type="secondary",
            on_click=on_note_follow_up,
            args=(item.id, False),
            width="stretch",
        )
