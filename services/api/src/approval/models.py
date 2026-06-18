from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class ReviewSession(Base):
    __tablename__ = "review_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid4()))
    doc_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    snap_id: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid4()))
    doc_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    yjs_snapshot: Mapped[str] = mapped_column(Text, default="")
    block_metas_json: Mapped[str] = mapped_column(Text, default="[]")
    anchor_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Arbitration(Base):
    __tablename__ = "arbitrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    arb_id: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid4()))
    doc_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    block_id: Mapped[str] = mapped_column(String(36), nullable=False)
    conflict_type: Mapped[str] = mapped_column(String(32), nullable=False)
    proposals_json: Mapped[str] = mapped_column(Text, default="[]")
    ai_sources_json: Mapped[str] = mapped_column(Text, default="[]")
    claimant_id: Mapped[str] = mapped_column(String(36), default="")
    resolution: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decider_id: Mapped[str] = mapped_column(String(36), default="")
    decider_reason: Mapped[str] = mapped_column(Text, default="")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReviewSessionResponse(BaseModel):
    id: str
    session_id: str
    doc_id: str
    snapshot_id: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SnapshotResponse(BaseModel):
    id: str
    snap_id: str
    doc_id: str
    state: str
    yjs_snapshot: str
    block_metas_json: str
    anchor_json: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ArbitrationResponse(BaseModel):
    id: str
    arb_id: str
    doc_id: str
    block_id: str
    conflict_type: str
    proposals_json: str
    ai_sources_json: str
    claimant_id: str
    resolution: str | None
    decider_id: str
    decider_reason: str
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArbitrationResolveRequest(BaseModel):
    resolution: str
    decider_id: str
    decider_reason: str
