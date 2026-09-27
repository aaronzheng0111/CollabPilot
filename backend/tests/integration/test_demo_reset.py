"""T12 verify case 1: `agent demo reset` clears SQLite, not data/mock."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from collabpilot.campaign.goal import Campaign
from collabpilot.domain.models import Message
from collabpilot.infrastructure.campaign_store import DEMO_TABLES, reset_demo_tables
from collabpilot.interfaces.cli import app
from collabpilot.settings import PROJECT_ROOT


MOCK_DIR = PROJECT_ROOT.parent / "data" / "mock"
if not MOCK_DIR.is_dir():
    MOCK_DIR = PROJECT_ROOT / "data" / "mock"


def _mock_snapshot() -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(MOCK_DIR.glob("*.json"))}


def _row_count(engine, table: str) -> int:
    with Session(engine) as db:
        return int(db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())


def test_demo_reset_clears_tables_and_leaves_mock_untouched(application) -> None:
    session_id = application.store.create_session()
    application.store.add_message(
        session_id,
        session_id,
        Message(role="user", content="hello"),
    )
    application.save_campaign(
        Campaign(
            campaign_id=session_id,
            saved_creator_ids=["creator_001"],
            drafts=[
                {
                    "id": "draft-1",
                    "campaign_id": str(session_id),
                    "creator_id": "creator_001",
                    "body": "body",
                    "cited_post_id": "p1",
                    "channel": "email",
                    "status": "approved",
                    "data_origin": "real_model_output",
                    "model_name": "deepseek-chat",
                }
            ],
            follow_ups=[
                {
                    "id": "fu-1",
                    "campaign_id": str(session_id),
                    "creator_id": "creator_001",
                    "draft_id": "draft-1",
                    "channel": "email",
                    "next_step": "三天后邮件再问",
                    "follow_status": "waiting_user",
                    "data_origin": "real_model_output",
                    "model_name": "deepseek-chat",
                }
            ],
            confirmed_channels={"creator_001": "email"},
        )
    )
    engine = application.store.engine
    assert _row_count(engine, "sessions") >= 1
    assert _row_count(engine, "campaigns") >= 1
    assert _row_count(engine, "drafts") >= 1
    assert _row_count(engine, "follow_ups") >= 1
    before_mock = _mock_snapshot()

    reset_demo_tables(engine)

    for table in DEMO_TABLES:
        assert _row_count(engine, table) == 0, table
    assert _mock_snapshot() == before_mock


def test_cli_demo_reset_invokes_clear(application, monkeypatch) -> None:
    called = []

    def fake_reset(engine) -> None:
        called.append(engine)

    monkeypatch.setattr(
        "collabpilot.interfaces.cli.reset_demo_tables", fake_reset
    )
    monkeypatch.setattr(
        "collabpilot.interfaces.cli.create_application", lambda: application
    )
    result = CliRunner().invoke(app, ["demo", "reset"])
    assert result.exit_code == 0, result.output
    assert called
    assert "data/mock" in result.output
