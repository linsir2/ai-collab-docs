from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from .deps import get_current_user
from .models import MemberAdd, TokenResponse, UserCreate, UserLogin, UserResponse
from .service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.create_user(data)
    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await AuthService.authenticate_user(db, data.email, data.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    token = AuthService.create_token(user)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            user_id=user.user_id,
            display_name=user.display_name,
            email=user.email,
            role=user.role,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user


@router.post("/docs/{doc_id}/members")
async def add_member(
    doc_id: str,
    data: MemberAdd,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.set_document_permission(
        doc_id=doc_id,
        user_id=data.user_id,
        effective_role=data.role,
        invited_by=current_user.user_id,
    )
    return {"status": "ok"}


@router.get("/docs/{doc_id}/members")
async def list_members(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    members = await service.list_document_members(doc_id)
    return {"members": members}
