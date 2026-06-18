import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class AIProposal(Base):
    __tablename__ = "ai_proposals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proposal_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    block_id: Mapped[str] = mapped_column(String(128), nullable=False)
    doc_id: Mapped[str] = mapped_column(String(128), nullable=False)
    ai_source: Mapped[str] = mapped_column(String(256), nullable=False)
    ai_memory_type: Mapped[str] = mapped_column(String(16), nullable=False, default="public")
    old_content: Mapped[str] = mapped_column(Text, default="")
    new_content: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    anchor_alignment_score: Mapped[float] = mapped_column(Float, default=0.0)
    diff_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")

    __table_args__ = (
        Index("ix_ai_proposals_doc_id", "doc_id"),
        Index("ix_ai_proposals_block_id", "block_id"),
        Index("ix_ai_proposals_status", "status"),
        Index("ix_ai_proposals_ai_source", "ai_source"),
    )


class AIMemory(Base):
    __tablename__ = "ai_memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    doc_id: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    ai_role: Mapped[str] = mapped_column(String(128), nullable=False)
    rule: Mapped[str] = mapped_column(Text, default="")
    memory_type: Mapped[str] = mapped_column(String(16), nullable=False, default="public")
    solidified: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_ai_memories_doc_id", "doc_id"),
        Index("ix_ai_memories_user_id", "user_id"),
        Index("ix_ai_memories_memory_type", "memory_type"),
    )


class ForgeRequest(BaseModel):
    block_id: str
    doc_id: str
    instruction: str = ""
    ai_source: str = ""


class ProposalResponse(BaseModel):
    proposal_id: str
    block_id: str
    doc_id: str
    ai_source: str
    ai_memory_type: str
    old_hint: str = ""
    new_content: str
    rationale: str
    anchor_alignment_score: float = 0.0
    diff_summary: str = ""
    status: str = "pending"
    created_at: str = ""

    model_config = {"from_attributes": True}


class PoolStatusResponse(BaseModel):
    doc_id: str
    public_count: int
    private_count: int
    public_limit: int = 800
    private_limit: int = 400
    global_private_count: int = 0
    global_private_limit: int = 1200


class MemoryResponse(BaseModel):
    id: str
    doc_id: str
    user_id: str
    ai_role: str
    rule: str
    memory_type: str
    solidified: bool
    trigger_count: int
    created_at: str

    model_config = {"from_attributes": True}


class ConflictDetectRequest(BaseModel):
    doc_id: str = ""
    proposal_a_id: str
    proposal_b_id: str


class ConflictDetectResponse(BaseModel):
    is_opposing: bool
    conflict_description: str
    proposal_a_source: str = ""
    proposal_b_source: str = ""
