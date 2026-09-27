"""Channel UI is read-only now; confirm-before-drafts is gone."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

from collabpilot.bootstrap import create_application
from collabpilot.campaign.channels import pick_channel
from collabpilot.campaign.workbench import main_table_rows
from components.channel_table import CONFIRM_BUTTON, PANEL_TITLE, SEND_LABELS
from test_evidence_panel import judged_session, markup, open_session


def selected_session():
    session_id = judged_session()
    application = create_application()
    campaign = application.campaign(session_id)
    application.save_campaign(
        campaign.model_copy(
            update={
                "stage": "SELECTED",
                "saved_creator_ids": ["creator_001", "creator_002"],
            }
        )
    )
    return session_id


def test_channel_confirm_ui_removed_from_workbench() -> None:
    at = open_session(selected_session())
    html = markup(at)
    assert PANEL_TITLE not in html
    assert CONFIRM_BUTTON not in [button.label for button in at.button]


def test_main_table_shows_auto_channel_without_confirm() -> None:
    session_id = selected_session()
    rows = main_table_rows(create_application().campaign(session_id))
    assert any(row.get("channel") for row in rows)
    amy = next(row for row in rows if row["creator_id"] == "creator_001")
    from collabpilot.campaign import mock_store
    from collabpilot.campaign.channels import CHANNEL_LABELS

    expected = CHANNEL_LABELS[pick_channel(mock_store.load()["creator_001"])]
    assert amy["channel"] == expected


def _unknown_channel_page() -> None:
    from components.channel_table import render_channel_table

    render_channel_table(
        [
            {
                "creator_id": "creator_ghost",
                "display_name": "无渠道",
                "platform": "tiktok",
                "preferred_label": "未知",
                "dm_available": False,
                "email_display": "未知",
                "consent_label": "未知",
                "source": "[MOCK]",
                "can_confirm": False,
                "available_channels": [],
                "available_labels": {},
            }
        ]
    )


def test_unknown_channel_row_has_no_confirm_button() -> None:
    from collabpilot.campaign.channels import NO_CHANNEL_TEXT

    at = AppTest.from_function(_unknown_channel_page).run()
    assert not at.exception
    html = "\n".join(item.value for item in at.markdown)
    captions = "\n".join(item.value for item in at.caption)
    assert NO_CHANNEL_TEXT in captions or NO_CHANNEL_TEXT in html
    assert CONFIRM_BUTTON not in [button.label for button in at.button]


def test_channel_area_has_no_send_buttons() -> None:
    at = open_session(selected_session())
    labels = [button.label for button in at.button if button.key != "cp-chat-send"]
    for forbidden in SEND_LABELS:
        assert forbidden not in labels
        assert not any(label == forbidden for label in labels)
