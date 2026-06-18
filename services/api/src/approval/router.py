from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from approval.models import ArbitrationResponse, ArbitrationResolveRequest, ReviewSessionResponse
from approval.service import ApprovalService
from audit.service import AuditService
from auth.deps import get_current_user, require_doc_permission
from auth.models import UserResponse
from contracts.contracts import ApprovalAction
from shared.database import get_db

router = APIRouter()


class ApproveRequest(BaseModel):
    action: ApprovalAction
    user_id: str


class StartReviewRequest(BaseModel):
    user_id: str


class CompleteReviewRequest(BaseModel):
    user_id: str


@router.post("/{doc_id}/start", response_model=ReviewSessionResponse)
async def start_review(
    doc_id: str,
    body: StartReviewRequest,
    _ctx: dict = Depends(require_doc_permission("doc_id", "start_review")),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ApprovalService(db, audit_service=AuditService(db))
    try:
        session = await service.start_review(doc_id, current_user.user_id)
        await db.commit()
        return ReviewSessionResponse.model_validate(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{doc_id}/session", response_model=ReviewSessionResponse | None)
async def get_review_session(
    doc_id: str,
    _ctx: dict = Depends(require_doc_permission("doc_id", "discuss")),
    db: AsyncSession = Depends(get_db),
):
    service = ApprovalService(db, audit_service=AuditService(db))
    session = await service.get_review_session(doc_id)
    if session is None:
        return None
    return ReviewSessionResponse.model_validate(session)


@router.put("/proposals/{prop_id}/approve")
async def approve_proposal(
    prop_id: str,
    body: ApproveRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ApprovalService(db, audit_service=AuditService(db))
    try:
        result = await service.approve_proposal(prop_id, body.action, current_user.user_id)
        await db.commit()
        return result
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{doc_id}/arbitrations", response_model=list[ArbitrationResponse])
async def list_arbitrations(
    doc_id: str,
    status_filter: str | None = None,
    _ctx: dict = Depends(require_doc_permission("doc_id", "discuss")),
    db: AsyncSession = Depends(get_db),
):
    service = ApprovalService(db, audit_service=AuditService(db))
    arbitrations = await service.get_arbitrations(doc_id, status_filter=status_filter)
    return [ArbitrationResponse.model_validate(a) for a in arbitrations]


@router.post("/arbitrations/{arb_id}/resolve", response_model=ArbitrationResponse)
async def resolve_arbitration(
    arb_id: str,
    body: ArbitrationResolveRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from approval.models import Arbitration
    from auth.models import DocumentPermission
    from shared.authz import can_do_in_document
    from sqlalchemy import select

    stmt = select(Arbitration).where(Arbitration.arb_id == arb_id)
    result = await db.execute(stmt)
    arbitration = result.scalar_one_or_none()
    if not arbitration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="仲裁不存在")

    doc_id = arbitration.doc_id
    doc_role_result = await db.execute(
        select(DocumentPermission).where(
            DocumentPermission.doc_id == doc_id,
            DocumentPermission.user_id == current_user.user_id,
        )
    )
    perm = doc_role_result.scalar_one_or_none()
    doc_role = perm.effective_role if perm else "reader"
    if not can_do_in_document(doc_role, "resolve_arbitration"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权裁决仲裁")

    service = ApprovalService(db, audit_service=AuditService(db))
    try:
        arbitration = await service.resolve_arbitration(
            arb_id, body.resolution, current_user.user_id, body.decider_reason
        )
        await db.commit()
        return ArbitrationResponse.model_validate(arbitration)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{doc_id}/complete")
async def complete_review(
    doc_id: str,
    body: CompleteReviewRequest,
    _ctx: dict = Depends(require_doc_permission("doc_id", "resolve_arbitration")),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ApprovalService(db, audit_service=AuditService(db))
    try:
        result = await service.complete_review(doc_id, current_user.user_id)
        await db.commit()
        return result
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
