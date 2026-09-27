"""T08 verify cases 7–8. Fixture verdicts; no DeepSeek."""

from __future__ import annotations

from test_evidence_panel import judged_session, markup, open_session, table_frame

from components.pending_list import LIST_TITLE


def test_main_table_audience_unknown_row_is_pending_with_badge() -> None:
    session_id = judged_session()
    at = open_session(session_id)

    frame = table_frame(session_id)
    row = frame[frame["creator_id"] == "creator_020"].iloc[0]
    assert row["decision"] == "待确认"
    assert row["audience"] == "受众未知"
    assert "[RULE]" in row["source"]
    assert at.button


def test_pending_list_is_separate_and_states_reason() -> None:
    session_id = judged_session()
    at = open_session(session_id)

    html = markup(at)
    assert f"<h4>{LIST_TITLE}</h4>" in html
    assert "creator_020" in html
    assert "受众未知" in html
    assert "相关内容只有 1 条" in html
    assert "cp-pending-list" in html
    frame = table_frame(session_id)
    assert "合适" in set(frame["decision"])
    assert list(frame["decision"][:3]) == ["合适", "合适", "合适"]
