import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class User(Base):
    """User account model.

    The `role` column is legacy / default and is kept for backwards compatibility.
    `global_role` is the source of truth for account-wide permissions.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="editor")
    global_role: Mapped[str] = mapped_column(String, nullable=False, default="personal")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class DocumentPermission(Base):
    """Document-local permission for a user on a specific document.

    `effective_role` represents the user's role within the scope of a single
    document and is independent of the user's account `global_role`.
    """

    __tablename__ = "document_permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    effective_role: Mapped[str] = mapped_column(String)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    invited_by: Mapped[str] = mapped_column(String, default="")


class UserCreate(BaseModel):
    display_name: str
    email: str
    password: str
    role: str = "editor"
    global_role: str = "personal"


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    display_name: str
    email: str
    role: str
    global_role: str
    doc_role: str | None = None

    model_config = {"from_attributes": True}


class MemberAdd(BaseModel):
    user_id: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
