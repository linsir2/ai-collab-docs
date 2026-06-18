from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.authz import GlobalRole, can_do_in_document
from shared.config import settings
from shared.database import get_db
from .models import DocumentPermission, User, UserResponse

security = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证令牌")

    token = credentials.credentials
    try:
        payload = _decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")

    user_id = payload.get("sub")
    global_role = payload.get("global_role")
    if user_id is None or global_role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        global_role=user.global_role,
    )


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserResponse | None:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(*allowed_roles: str):
    allowed = {str(role) for role in allowed_roles}

    async def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.global_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return current_user

    return role_checker


def get_current_doc_role(doc_id_param: str):
    async def doc_role_extractor(
        request: Request,
        current_user: UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> str | None:
        doc_id = request.path_params.get(doc_id_param)
        if doc_id is None:
            return None
        perm = await db.execute(
            select(DocumentPermission).where(
                DocumentPermission.doc_id == doc_id,
                DocumentPermission.user_id == current_user.user_id,
            )
        )
        return perm.scalar_one_or_none().effective_role if perm else None

    return doc_role_extractor


def require_doc_permission(doc_id_path_param: str = "doc_id", action: str = ""):
    async def permission_checker(
        request: Request,
        current_user: UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        doc_id = request.path_params.get(doc_id_path_param)
        if doc_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少文档标识",
            )

        perm_result = await db.execute(
            select(DocumentPermission).where(
                DocumentPermission.doc_id == doc_id,
                DocumentPermission.user_id == current_user.user_id,
            )
        )
        perm = perm_result.scalar_one_or_none()

        if perm is not None:
            doc_role = perm.effective_role
        else:
            from document.models import Document as _Document

            doc_result = await db.execute(select(_Document).where(_Document.doc_id == doc_id))
            doc = doc_result.scalar_one_or_none()
            if doc is not None and doc.owner_id == current_user.user_id:
                doc_role = "owner"
            else:
                doc_role = "reader"

        if not can_do_in_document(doc_role, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权执行此文档操作",
            )

        return {"user": current_user, "doc_role": doc_role, "doc_id": doc_id}

    return permission_checker
