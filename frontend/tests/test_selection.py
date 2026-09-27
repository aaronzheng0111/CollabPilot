"""T09 verify cases 9–11. Fixture verdicts; no DeepSeek."""

from __future__ import annotations

from test_evidence_panel import judged_session, markup, open_session, table_frame
from collabpilot.bootstrap import create_application
from collabpilot.campaign.workbench import skip_caption
from components.main_table import SAVE_BUTTON
from components.pending_decisions import EMPTY_TEXT


def test_selection_column_defaults_and_locked_rows_unselectable() -> None:
    session_id = judged_session()
    at = open_session(session_id)

    frame = table_frame(session_id)
    assert "选中" in frame.columns
    fits = frame[frame["decision"] == "合适"]
    pending = frame[frame["decision"] == "待确认"]
    unfit = frame[frame["decision"] == "不合适"]
    assert fits["选中"].all()
    assert fits["can_select"].all()
    assert not pending["选中"].any()
    assert pending["can_select"].all()
    assert not unfit["选中"].any()
    assert not unfit["can_select"].any()
    locked = frame[frame["creator_id"] == "creator_011"]
    assert not locked["can_select"].any()
    labels = [button.label for button in at.button]
    assert SAVE_BUTTON in labels
    assert at.button[labels.index(SAVE_BUTTON)].proto.type == "secondary"


def test_save_button_queues_pending_row_and_saved_column_after_approve() -> None:
    session_id = judged_session()
    at = open_session(session_id)

    save = next(button for button in at.button if button.label == SAVE_BUTTON)
    save.click().run()
    assert not at.exception

    body = markup(at)
    assert "保存" in body and "位到活动" in body
    names = "\n".join(item.value for item in at.markdown)
    assert "保存 3 位到活动" in names
    campaign = create_application().campaign(session_id)
    assert campaign.pending_decision == "save_selection"
    assert set(campaign.pending_payload["creator_ids"]) == {
        "creator_001",
        "creator_002",
        "creator_003",
    }

    approve = next(button for button in at.button if button.label == "批准")
    approve.click().run()
    assert not at.exception
    assert EMPTY_TEXT in "\n".join(item.value for item in at.caption)
    frame = table_frame(session_id)
    assert "saved" in frame.columns
    assert frame.loc[frame["creator_id"] == "creator_001", "saved"].item()
    stored = create_application().campaign(session_id)
    assert stored.stage == "SELECTED"
    assert stored.saved_creator_ids == ["creator_001", "creator_002", "creator_003"]


def test_skip_counts_caption_after_saved_and_excluded() -> None:
    session_id = judged_session()
    application = create_application()
    campaign = application.campaign(session_id)
    application.save_campaign(
        campaign.model_copy(
            update={
                "saved_creator_ids": ["creator_001"],
                "excluded_creator_ids": ["creator_003"],
                "skip_counts": {"already_saved": 1, "excluded": 1, "topic_rejected": 2},
            }
        )
    )

    at = open_session(session_id)
    captions = "\n".join(item.value for item in at.caption)
    assert "已在名单中 1 位" in captions
    assert "已排除 1 位" in captions
    assert "此前判定不符 2 位" in captions
    assert "均未重复推荐" in captions
    assert skip_caption(application.campaign(session_id))
