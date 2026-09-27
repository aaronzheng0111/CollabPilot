"""SQLite campaigns table (T09). Replaces the session-metadata blob."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, delete, select, text
from sqlalchemy.orm import Mapped, Session, mapped_column

from collabpilot.campaign.goal import Campaign
from collabpilot.campaign.drafts import Draft
from collabpilot.campaign.follow_up import FollowUp
from collabpilot.infrastructure.session_store import Base, SQLiteSessionStore


CAMPAIGN_KEY = "campaign"


class CampaignRow(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), index=True
    )
    goal_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="CREATED")
    parsed_goal_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    pending_decision_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    saved_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    excluded_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    topic_rejected_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    accepted_from_pending_json: Mapped[str] = mapped_column(Text, default="[]")
    record_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CreatorChannelRow(Base):
    __tablename__ = "creator_channels"

    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id"), primary_key=True
    )
    creator_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    channel: Mapped[str] = mapped_column(String(32))
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DraftRow(Base):
    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id"), index=True
    )
    creator_id: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(Text)
    cited_post_id: Mapped[str] = mapped_column(String(64))
    channel: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    data_origin: Mapped[str] = mapped_column(String(32), default="real_model_output")
    model_name: Mapped[str] = mapped_column(String(64))


class FollowUpRow(Base):
    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id"), index=True
    )
    creator_id: Mapped[str] = mapped_column(String(64))
    draft_id: Mapped[str] = mapped_column(String(36), unique=True)
    channel: Mapped[str] = mapped_column(String(32))
    next_step: Mapped[str] = mapped_column(Text)
    follow_status: Mapped[str] = mapped_column(String(32))
    data_origin: Mapped[str] = mapped_column(String(32), default="real_model_output")
    model_name: Mapped[str] = mapped_column(String(64))


class CampaignStore:
    def __init__(self, sessions: SQLiteSessionStore):
        self.sessions = sessions
        self.engine = sessions.engine
        Base.metadata.create_all(self.engine)

    def get(self, session_id: UUID) -> Campaign:
        with Session(self.engine) as db:
            row = db.scalar(
                select(CampaignRow).where(CampaignRow.session_id == str(session_id))
            )
            if row is None:
                row = db.get(CampaignRow, str(session_id))
            if row is not None:
                campaign = self._from_row(row)
                channels = self._channels_for(campaign.campaign_id)
                drafts = self._drafts_for(campaign.campaign_id)
                follow_ups = self._follow_ups_for(campaign.campaign_id)
                updates: dict[str, Any] = {}
                if channels:
                    updates["confirmed_channels"] = channels
                if drafts:
                    updates["drafts"] = drafts
                if follow_ups:
                    updates["follow_ups"] = follow_ups
                return campaign.model_copy(update=updates) if updates else campaign
        migrated = self._from_metadata(session_id)
        if migrated is not None:
            self.save(migrated)
            return migrated
        return Campaign(campaign_id=session_id)

    def save(self, campaign: Campaign) -> None:
        now = datetime.now(UTC)
        record = campaign.model_dump(mode="json")
        pending = None
        if campaign.pending_decision:
            pending = json.dumps(
                {
                    "decision": campaign.pending_decision,
                    **(campaign.pending_payload or {}),
                },
                ensure_ascii=False,
            )
        parsed = (
            json.dumps(campaign.parsed_goal.model_dump(mode="json"), ensure_ascii=False)
            if campaign.parsed_goal is not None
            else None
        )
        with Session(self.engine) as db:
            row = db.get(CampaignRow, str(campaign.campaign_id))
            if row is None:
                row = db.scalar(
                    select(CampaignRow).where(
                        CampaignRow.session_id == str(campaign.campaign_id)
                    )
                )
            if row is None:
                row = CampaignRow(
                    id=str(campaign.campaign_id),
                    session_id=str(campaign.campaign_id),
                )
                db.add(row)
            row.session_id = str(campaign.campaign_id)
            row.goal_fingerprint = campaign.goal_fingerprint
            row.status = campaign.stage
            row.parsed_goal_json = parsed
            row.pending_decision_json = pending
            row.saved_ids_json = json.dumps(campaign.saved_creator_ids, ensure_ascii=False)
            row.excluded_ids_json = json.dumps(
                campaign.excluded_creator_ids, ensure_ascii=False
            )
            row.topic_rejected_ids_json = json.dumps(
                campaign.topic_rejected_ids, ensure_ascii=False
            )
            row.accepted_from_pending_json = json.dumps(
                campaign.accepted_from_pending, ensure_ascii=False
            )
            row.record_json = json.dumps(record, ensure_ascii=False)
            row.updated_at = now
            db.commit()
        self._sync_channels(campaign)
        self._sync_drafts(campaign)
        self._sync_follow_ups(campaign)

    def saved_in_other_campaigns(
        self, creator_ids: list[str], campaign_id: UUID
    ) -> list[str]:
        wanted = set(creator_ids)
        if not wanted:
            return []
        found: list[str] = []
        with Session(self.engine) as db:
            rows = list(db.scalars(select(CampaignRow)))
        for row in rows:
            if row.id == str(campaign_id):
                continue
            saved = set(json.loads(row.saved_ids_json or "[]"))
            for creator_id in creator_ids:
                if creator_id in saved and creator_id not in found:
                    found.append(creator_id)
        return found

    def _sync_channels(self, campaign: Campaign) -> None:
        now = datetime.now(UTC)
        campaign_key = str(campaign.campaign_id)
        wanted = dict(campaign.confirmed_channels)
        with Session(self.engine) as db:
            existing = list(
                db.scalars(
                    select(CreatorChannelRow).where(
                        CreatorChannelRow.campaign_id == campaign_key
                    )
                )
            )
            have = {row.creator_id: row for row in existing}
            for creator_id, row in list(have.items()):
                if creator_id not in wanted:
                    db.delete(row)
                else:
                    row.channel = wanted[creator_id]
            for creator_id, channel in wanted.items():
                if creator_id not in have:
                    db.add(
                        CreatorChannelRow(
                            campaign_id=campaign_key,
                            creator_id=creator_id,
                            channel=channel,
                            confirmed_at=now,
                        )
                    )
            db.commit()

    def _channels_for(self, campaign_id: UUID) -> dict[str, str]:
        with Session(self.engine) as db:
            rows = list(
                db.scalars(
                    select(CreatorChannelRow).where(
                        CreatorChannelRow.campaign_id == str(campaign_id)
                    )
                )
            )
        return {row.creator_id: row.channel for row in rows}

    def _sync_drafts(self, campaign: Campaign) -> None:
        campaign_key = str(campaign.campaign_id)
        wanted = {item["id"]: item for item in campaign.drafts if item.get("id")}
        with Session(self.engine) as db:
            existing = list(
                db.scalars(select(DraftRow).where(DraftRow.campaign_id == campaign_key))
            )
            have = {row.id: row for row in existing}
            for row_id, row in list(have.items()):
                if row_id not in wanted:
                    db.delete(row)
                else:
                    self._fill_draft_row(row, wanted[row_id])
            for draft_id, payload in wanted.items():
                if draft_id not in have:
                    row = DraftRow(id=draft_id, campaign_id=campaign_key)
                    self._fill_draft_row(row, payload)
                    db.add(row)
            db.commit()

    @staticmethod
    def _fill_draft_row(row: DraftRow, payload: dict[str, Any]) -> None:
        row.creator_id = str(payload.get("creator_id") or "")
        row.body = str(payload.get("body") or "")
        row.cited_post_id = str(payload.get("cited_post_id") or "")
        row.channel = str(payload.get("channel") or "")
        row.status = str(payload.get("status") or "pending_review")
        row.data_origin = str(payload.get("data_origin") or "real_model_output")
        row.model_name = str(payload.get("model_name") or "")

    def _drafts_for(self, campaign_id: UUID) -> list[dict[str, Any]]:
        with Session(self.engine) as db:
            rows = list(
                db.scalars(select(DraftRow).where(DraftRow.campaign_id == str(campaign_id)))
            )
        return [
            Draft(
                id=row.id,
                campaign_id=row.campaign_id,
                creator_id=row.creator_id,
                body=row.body,
                cited_post_id=row.cited_post_id,
                channel=row.channel,  # type: ignore[arg-type]
                status=row.status,  # type: ignore[arg-type]
                data_origin=row.data_origin,  # type: ignore[arg-type]
                model_name=row.model_name,
            ).model_dump(mode="json")
            for row in rows
        ]

    def _sync_follow_ups(self, campaign: Campaign) -> None:
        campaign_key = str(campaign.campaign_id)
        wanted = {item["id"]: item for item in campaign.follow_ups if item.get("id")}
        with Session(self.engine) as db:
            existing = list(
                db.scalars(
                    select(FollowUpRow).where(FollowUpRow.campaign_id == campaign_key)
                )
            )
            have = {row.id: row for row in existing}
            for row_id, row in list(have.items()):
                if row_id not in wanted:
                    db.delete(row)
                else:
                    self._fill_follow_up_row(row, wanted[row_id])
            for follow_id, payload in wanted.items():
                if follow_id not in have:
                    row = FollowUpRow(id=follow_id, campaign_id=campaign_key)
                    self._fill_follow_up_row(row, payload)
                    db.add(row)
            db.commit()

    @staticmethod
    def _fill_follow_up_row(row: FollowUpRow, payload: dict[str, Any]) -> None:
        row.creator_id = str(payload.get("creator_id") or "")
        row.draft_id = str(payload.get("draft_id") or "")
        row.channel = str(payload.get("channel") or "")
        row.next_step = str(payload.get("next_step") or "")
        row.follow_status = str(payload.get("follow_status") or "waiting_user")
        row.data_origin = str(payload.get("data_origin") or "real_model_output")
        row.model_name = str(payload.get("model_name") or "")

    def _follow_ups_for(self, campaign_id: UUID) -> list[dict[str, Any]]:
        with Session(self.engine) as db:
            rows = list(
                db.scalars(
                    select(FollowUpRow).where(
                        FollowUpRow.campaign_id == str(campaign_id)
                    )
                )
            )
        return [
            FollowUp(
                id=row.id,
                campaign_id=row.campaign_id,
                creator_id=row.creator_id,
                draft_id=row.draft_id,
                channel=row.channel,  # type: ignore[arg-type]
                next_step=row.next_step,
                follow_status=row.follow_status,  # type: ignore[arg-type]
                data_origin=row.data_origin,  # type: ignore[arg-type]
                model_name=row.model_name,
            ).model_dump(mode="json")
            for row in rows
        ]


    def _from_row(self, row: CampaignRow) -> Campaign:
        data = json.loads(row.record_json or "{}")
        if data:
            return Campaign.model_validate(data)
        return Campaign(
            campaign_id=UUID(row.id),
            stage=row.status,  # type: ignore[arg-type]
            goal_fingerprint=row.goal_fingerprint,
            saved_creator_ids=json.loads(row.saved_ids_json or "[]"),
            excluded_creator_ids=json.loads(row.excluded_ids_json or "[]"),
            topic_rejected_ids=json.loads(row.topic_rejected_ids_json or "[]"),
            accepted_from_pending=json.loads(row.accepted_from_pending_json or "[]"),
        )

    def _from_metadata(self, session_id: UUID) -> Campaign | None:
        blob: dict[str, Any] = self.sessions.get_metadata(session_id)
        data = blob.get(CAMPAIGN_KEY)
        if not data:
            return None
        return Campaign.model_validate(data)

    def delete_for_session(self, session_id: UUID) -> None:
        """Remove campaign rows scoped to this session (no chat/session rows)."""
        sid = str(session_id)
        with Session(self.engine) as db:
            campaign_ids = [
                row.id
                for row in db.scalars(
                    select(CampaignRow).where(CampaignRow.session_id == sid)
                )
            ]
            # Legacy rows used campaign.id == session_id without matching session_id.
            if sid not in campaign_ids and db.get(CampaignRow, sid) is not None:
                campaign_ids.append(sid)
            for cid in campaign_ids:
                db.execute(delete(FollowUpRow).where(FollowUpRow.campaign_id == cid))
                db.execute(delete(DraftRow).where(DraftRow.campaign_id == cid))
                db.execute(
                    delete(CreatorChannelRow).where(CreatorChannelRow.campaign_id == cid)
                )
                db.execute(delete(CampaignRow).where(CampaignRow.id == cid))
            db.commit()


DEMO_TABLES = (
    "follow_ups",
    "drafts",
    "creator_channels",
    "campaigns",
    "messages",
    "session_metadata",
    "sessions",
)


def reset_demo_tables(engine) -> None:
    """Delete demo rows. Does not drop tables or touch data/mock/."""
    with Session(engine) as db:
        db.execute(text("PRAGMA foreign_keys=OFF"))
        for table in DEMO_TABLES:
            db.execute(text(f"DELETE FROM {table}"))
        db.commit()
