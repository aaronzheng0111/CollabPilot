from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, delete, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from collabpilot.domain.models import Message, ProjectSummary, StoredMessage

DEFAULT_PROJECT_TITLE = "新项目"
TITLE_MAX_LEN = 40


class Base(DeclarativeBase):
    pass


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(120), default=DEFAULT_PROJECT_TITLE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MessageRow(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    turn_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionMetadataRow(Base):
    """Per-session JSON blob. Holds the campaign record until T09 gives it tables."""

    __tablename__ = "session_metadata"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id"), primary_key=True
    )
    data: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def truncate_title(text: str, max_len: int = TITLE_MAX_LEN) -> str:
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return DEFAULT_PROJECT_TITLE
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1] + "…"


class SQLiteSessionStore:
    def __init__(self, database_url: str, project_root: Path):
        if database_url.startswith("sqlite:///"):
            relative = database_url.removeprefix("sqlite:///")
            db_path = Path(relative)
            if not db_path.is_absolute():
                db_path = project_root / db_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self._migrate_session_title()

    def _migrate_session_title(self) -> None:
        with self.engine.begin() as conn:
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(sessions)"))}
            if "title" not in cols:
                conn.execute(
                    text(
                        "ALTER TABLE sessions ADD COLUMN title "
                        f"VARCHAR(120) DEFAULT '{DEFAULT_PROJECT_TITLE}'"
                    )
                )

    def create_session(self, title: str | None = None) -> UUID:
        session_id = uuid4()
        now = datetime.now(UTC)
        with Session(self.engine) as db:
            db.add(
                SessionRow(
                    id=str(session_id),
                    title=truncate_title(title) if title else DEFAULT_PROJECT_TITLE,
                    created_at=now,
                    updated_at=now,
                )
            )
            db.commit()
        return session_id

    def ensure_session(self, session_id: UUID | None) -> UUID:
        if session_id is None:
            return self.create_session()
        with Session(self.engine) as db:
            exists = db.get(SessionRow, str(session_id))
            if exists is None:
                now = datetime.now(UTC)
                db.add(
                    SessionRow(
                        id=str(session_id),
                        title=DEFAULT_PROJECT_TITLE,
                        created_at=now,
                        updated_at=now,
                    )
                )
                db.commit()
        return session_id

    def list_projects(self) -> list[ProjectSummary]:
        with Session(self.engine) as db:
            rows = list(
                db.scalars(select(SessionRow).order_by(SessionRow.updated_at.desc()))
            )
        return [
            ProjectSummary(
                session_id=UUID(row.id),
                title=row.title or DEFAULT_PROJECT_TITLE,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    def get_project(self, session_id: UUID) -> ProjectSummary | None:
        with Session(self.engine) as db:
            row = db.get(SessionRow, str(session_id))
            if row is None:
                return None
            return ProjectSummary(
                session_id=UUID(row.id),
                title=row.title or DEFAULT_PROJECT_TITLE,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    def set_title(self, session_id: UUID, title: str) -> bool:
        """Rename a project. Empty / whitespace-only titles are rejected."""
        cleaned = " ".join(title.strip().split())
        if not cleaned:
            return False
        with Session(self.engine) as db:
            row = db.get(SessionRow, str(session_id))
            if row is None:
                return False
            row.title = truncate_title(cleaned)
            row.updated_at = datetime.now(UTC)
            db.commit()
        return True

    def maybe_set_title_from_prompt(self, session_id: UUID, prompt: str) -> None:
        """Name an untitled project from the first user message."""
        with Session(self.engine) as db:
            row = db.get(SessionRow, str(session_id))
            if row is None:
                return
            if row.title and row.title != DEFAULT_PROJECT_TITLE:
                return
            row.title = truncate_title(prompt)
            row.updated_at = datetime.now(UTC)
            db.commit()

    def add_message(self, session_id: UUID, turn_id: UUID, message: Message) -> StoredMessage:
        now = datetime.now(UTC)
        message_id = uuid4()
        with Session(self.engine) as db:
            db.add(
                MessageRow(
                    id=str(message_id),
                    session_id=str(session_id),
                    turn_id=str(turn_id),
                    role=message.role,
                    content=message.content,
                    name=message.name,
                    tool_call_id=message.tool_call_id,
                    created_at=now,
                )
            )
            session = db.get(SessionRow, str(session_id))
            if session:
                session.updated_at = now
            db.commit()
        return StoredMessage(
            id=message_id,
            session_id=session_id,
            turn_id=turn_id,
            message=message,
            created_at=now,
        )

    def get_metadata(self, session_id: UUID) -> dict[str, Any]:
        with Session(self.engine) as db:
            row = db.get(SessionMetadataRow, str(session_id))
            return json.loads(row.data) if row else {}

    def set_metadata(self, session_id: UUID, data: dict[str, Any]) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as db:
            row = db.get(SessionMetadataRow, str(session_id))
            if row is None:
                row = SessionMetadataRow(session_id=str(session_id))
                db.add(row)
            row.data = json.dumps(data, ensure_ascii=False)
            row.updated_at = now
            db.commit()

    def list_messages(self, session_id: UUID, limit: int = 50) -> list[Message]:
        return [entry.message for entry in self.list_history(session_id, limit=limit)]

    def list_history(self, session_id: UUID, limit: int = 200) -> list[StoredMessage]:
        with Session(self.engine) as db:
            rows = list(
                db.scalars(
                    select(MessageRow)
                    .where(MessageRow.session_id == str(session_id))
                    .order_by(MessageRow.created_at.desc())
                    .limit(limit)
                )
            )
        rows.reverse()
        return [
            StoredMessage(
                id=UUID(row.id),
                session_id=UUID(row.session_id),
                turn_id=UUID(row.turn_id),
                message=Message(
                    role=row.role,  # type: ignore[arg-type]
                    content=row.content,
                    name=row.name,
                    tool_call_id=row.tool_call_id,
                ),
                created_at=row.created_at,
            )
            for row in rows
        ]

    def delete_turn(self, session_id: UUID, turn_id: UUID) -> int:
        """Remove one user turn and its assistant / tool replies. Returns rows deleted."""
        with Session(self.engine) as db:
            result = db.execute(
                delete(MessageRow).where(
                    MessageRow.session_id == str(session_id),
                    MessageRow.turn_id == str(turn_id),
                )
            )
            session = db.get(SessionRow, str(session_id))
            if session:
                session.updated_at = datetime.now(UTC)
            db.commit()
            return int(result.rowcount or 0)

    def delete_message(self, session_id: UUID, message_id: UUID) -> int:
        """Remove one stored message. Deleting an assistant also removes the
        tool rows from the same turn (they render inside that bubble)."""
        with Session(self.engine) as db:
            row = db.get(MessageRow, str(message_id))
            if row is None or row.session_id != str(session_id):
                return 0
            deleted = 0
            if row.role == "assistant":
                tools = db.execute(
                    delete(MessageRow).where(
                        MessageRow.session_id == str(session_id),
                        MessageRow.turn_id == row.turn_id,
                        MessageRow.role == "tool",
                    )
                )
                deleted += int(tools.rowcount or 0)
            db.delete(row)
            deleted += 1
            session = db.get(SessionRow, str(session_id))
            if session:
                session.updated_at = datetime.now(UTC)
            db.commit()
            return deleted

    def delete_session_rows(self, session_id: UUID) -> None:
        """Delete messages + metadata + session. Campaign tables cleared separately."""
        sid = str(session_id)
        with Session(self.engine) as db:
            db.execute(delete(MessageRow).where(MessageRow.session_id == sid))
            db.execute(
                delete(SessionMetadataRow).where(SessionMetadataRow.session_id == sid)
            )
            db.execute(delete(SessionRow).where(SessionRow.id == sid))
            db.commit()
