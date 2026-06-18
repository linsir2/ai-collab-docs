import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    op_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(128), nullable=False)
    doc_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    before_state: Mapped[str] = mapped_column(Text, default="")
    after_state: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_operation_logs_doc_id", "doc_id"),
        Index("ix_operation_logs_user_id", "user_id"),
        Index("ix_operation_logs_action", "action"),
        Index("ix_operation_logs_timestamp", "timestamp"),
    )


class OperationLogResponse(BaseModel):
    op_id: str
    user_id: str
    action: str
    target_type: str
    target_id: str
    doc_id: str
    before_state: str = ""
    after_state: str = ""
    timestamp: str

    model_config = {"from_attributes": True}
