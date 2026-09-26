from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from collabpilot.domain.models import Message


class Base(DeclarativeBase):
    pass


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
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

    def create_session(self) -> UUID:
        session_id = uuid4()
        now = datetime.now(UTC)
        with Session(self.engine) as db:
            db.add(SessionRow(id=str(session_id), created_at=now, updated_at=now))
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
                        id=str(session_id), created_at=now, updated_at=now
                    )
                )
                db.commit()
        return session_id

    def add_message(self, session_id: UUID, turn_id: UUID, message: Message) -> None:
        now = datetime.now(UTC)
        with Session(self.engine) as db:
            db.add(
                MessageRow(
                    id=str(uuid4()),
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

    def list_messages(self, session_id: UUID, limit: int = 50) -> list[Message]:
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
            Message(
                role=row.role,  # type: ignore[arg-type]
                content=row.content,
                name=row.name,
                tool_call_id=row.tool_call_id,
            )
            for row in rows
        ]

