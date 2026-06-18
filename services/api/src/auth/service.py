import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from shared.authz import GlobalRole
from shared.config import settings
from .models import DocumentPermission, User, UserCreate

PRIVILEGED_GLOBAL_ROLES = {GlobalRole.TEAM_ADMIN.value, GlobalRole.OPS.value}


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(payload: dict) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self, data: UserCreate, requester_global_role: str | None = None
    ) -> User:
        global_role = data.global_role or GlobalRole.PERSONAL.value
        if global_role in PRIVILEGED_GLOBAL_ROLES:
            if requester_global_role not in PRIVILEGED_GLOBAL_ROLES:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权创建该全局角色账号",
                )
        user = User(
            user_id=str(uuid.uuid4()),
            display_name=data.display_name,
            email=data.email,
            hashed_password=await asyncio.to_thread(_hash_password, data.password),
            role=data.role,
            global_role=global_role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        # Run bcrypt verification in a thread to avoid blocking the async event loop
        is_valid = await asyncio.to_thread(_verify_password, password, user.hashed_password)
        if not is_valid:
            return None
        return user

    @staticmethod
    def _token_payload(user_id: str, global_role: str, extra: dict | None = None) -> dict:
        extra = extra or {}
        return {
            "sub": user_id,
            "global_role": global_role,
            **extra,
        }

    @staticmethod
    def create_access_token(user_id: str, global_role: str, extra: dict | None = None) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        payload = AuthService._token_payload(user_id, global_role, extra)
        payload["exp"] = expire
        payload["type"] = "access"
        return _create_token(payload)

    @staticmethod
    def create_refresh_token(user_id: str, global_role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
        payload = AuthService._token_payload(user_id, global_role)
        payload["exp"] = expire
        payload["type"] = "refresh"
        return _create_token(payload)

    @classmethod
    def create_tokens(cls, user_id: str, global_role: str, extra: dict | None = None) -> dict:
        return {
            "access_token": cls.create_access_token(user_id, global_role, extra),
            "refresh_token": cls.create_refresh_token(user_id, global_role),
        }

    @staticmethod
    def create_token_with_doc_role(user_id: str, global_role: str, doc_role: str) -> str:
        return AuthService.create_access_token(
            user_id,
            global_role,
            extra={"doc_role": doc_role},
        )

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_document_permission(self, doc_id: str, user_id: str) -> DocumentPermission | None:
        result = await self.db.execute(
            select(DocumentPermission).where(
                DocumentPermission.doc_id == doc_id,
                DocumentPermission.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def set_document_permission(
        self, doc_id: str, user_id: str, effective_role: str, invited_by: str
    ) -> DocumentPermission:
        perm = DocumentPermission(
            doc_id=doc_id,
            user_id=user_id,
            effective_role=effective_role,
            invited_by=invited_by,
        )
        self.db.add(perm)
        await self.db.commit()
        await self.db.refresh(perm)
        return perm

    async def get_document_permissions(self, doc_id: str) -> list[DocumentPermission]:
        result = await self.db.execute(select(DocumentPermission).where(DocumentPermission.doc_id == doc_id))
        return list(result.scalars().all())

    async def list_document_members(self, doc_id: str) -> list[dict]:
        result = await self.db.execute(
            select(User, DocumentPermission)
            .join(DocumentPermission, User.user_id == DocumentPermission.user_id)
            .where(DocumentPermission.doc_id == doc_id)
        )
        members = []
        for user, perm in result.all():
            members.append(
                {
                    "user_id": user.user_id,
                    "display_name": user.display_name,
                    "email": user.email,
                    "role": perm.effective_role,
                    "joined_at": perm.joined_at.isoformat() if perm.joined_at else "",
                    "invited_by": perm.invited_by,
                }
            )
        return members
