import uuid
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from .models import DocumentPermission, User, UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: UserCreate) -> User:
        user = User(
            user_id=str(uuid.uuid4()),
            display_name=data.display_name,
            email=data.email,
            hashed_password=pwd_context.hash(data.password),
            role=data.role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not pwd_context.verify(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_token(user: User) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
        payload = {
            "sub": user.user_id,
            "exp": expire,
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.user_id == user_id))
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
