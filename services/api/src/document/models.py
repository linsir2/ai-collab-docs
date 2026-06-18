import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, default="draft")
    owner_id: Mapped[str] = mapped_column(String)
    anchor_statement: Mapped[str] = mapped_column(Text)
    anchor_audience: Mapped[str] = mapped_column(Text, default="")
    anchor_argument: Mapped[str] = mapped_column(Text, default="")
    anchor_version: Mapped[int] = mapped_column(Integer, default=1)
    anchor_history: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class BlockMeta(Base):
    __tablename__ = "block_metas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_id: Mapped[str] = mapped_column(String, index=True)
    doc_id: Mapped[str] = mapped_column(String, index=True)
    tags: Mapped[str] = mapped_column(Text, default="[]")
    claimant_id: Mapped[str] = mapped_column(String, default="")
    drift_score: Mapped[float] = mapped_column(Float, default=0.0)
    locked_by: Mapped[str] = mapped_column(String, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class DocumentCreate(BaseModel):
    title: str
    anchor_statement: str
    anchor_audience: str = ""
    anchor_argument: str = ""


class DocumentResponse(BaseModel):
    id: str
    doc_id: str
    title: str
    state: str
    owner_id: str
    anchor_statement: str
    anchor_audience: str
    anchor_argument: str
    anchor_version: int
    anchor_history: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class BlockMetaUpdate(BaseModel):
    tags: str = "[]"
    claimant_id: str = ""
    drift_score: float = 0.0
    locked_by: str = ""


class StateTransition(BaseModel):
    to_state: str
