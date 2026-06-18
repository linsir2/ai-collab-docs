from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.contracts import UserRole
from shared.config import settings
from shared.database import get_db
from .models import UserResponse
from .service import AuthService

ROLE_HIERARCHY = {
    UserRole.READER: 0,
    UserRole.REVIEWER: 1,
    UserRole.EDITOR: 2,
    UserRole.LEAD_EDITOR: 3,
    UserRole.OWNER: 4,
}

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")

    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
    )


def require_role(min_role: str):
    async def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        current_level = ROLE_HIERARCHY.get(UserRole(current_user.role), -1)
        required_level = ROLE_HIERARCHY.get(UserRole(min_role), -1)
        if current_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {min_role} 或更高权限",
            )
        return current_user

    return role_checker
