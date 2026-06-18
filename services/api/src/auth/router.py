from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from .deps import get_current_user, get_optional_current_user
from .models import DocumentPermission, MemberAdd, TokenResponse, User, UserCreate, UserLogin, UserResponse
from .service import AuthService

router = APIRouter()


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        global_role=user.global_role,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse | None = Depends(get_optional_current_user),
):
    requester_global_role = current_user.global_role if current_user else None
    service = AuthService(db)
    user = await service.create_user(data, requester_global_role=requester_global_role)
    return _user_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await AuthService.authenticate_user(db, data.email, data.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    tokens = AuthService.create_tokens(user.user_id, user.global_role)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        user=_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    doc_id: str | None = Query(None),
):
    response = _user_response(current_user)
    if doc_id:
        result = await db.execute(
            select(DocumentPermission).where(
                DocumentPermission.doc_id == doc_id,
                DocumentPermission.user_id == current_user.user_id,
            )
        )
        perm = result.scalar_one_or_none()
        if perm:
            response.doc_role = perm.effective_role
        else:
            from document.models import Document

            doc_result = await db.execute(select(Document).where(Document.doc_id == doc_id))
            doc = doc_result.scalar_one_or_none()
            if doc is not None and doc.owner_id == current_user.user_id:
                response.doc_role = "owner"
    return response


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
