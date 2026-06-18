from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from approval.models import ArbitrationResponse, ArbitrationResolveRequest, ReviewSessionResponse
from approval.service import ApprovalService
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
async def start_review(doc_id: str, body: StartReviewRequest, db: AsyncSession = Depends(get_db)):
    service = ApprovalService(db)
    try:
        session = await service.start_review(doc_id, body.user_id)
        await db.commit()
        return ReviewSessionResponse.model_validate(session)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{doc_id}/session", response_model=ReviewSessionResponse | None)
async def get_review_session(doc_id: str, db: AsyncSession = Depends(get_db)):
    service = ApprovalService(db)
    session = await service.get_review_session(doc_id)
    if session is None:
        return None
    return ReviewSessionResponse.model_validate(session)


@router.put("/proposals/{prop_id}/approve")
async def approve_proposal(prop_id: str, body: ApproveRequest, db: AsyncSession = Depends(get_db)):
    service = ApprovalService(db)
    try:
        result = await service.approve_proposal(prop_id, body.action, body.user_id)
        await db.commit()
        return result
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{doc_id}/arbitrations", response_model=list[ArbitrationResponse])
async def list_arbitrations(doc_id: str, status: str | None = None, db: AsyncSession = Depends(get_db)):
    service = ApprovalService(db)
    arbitrations = await service.get_arbitrations(doc_id, status_filter=status)
    return [ArbitrationResponse.model_validate(a) for a in arbitrations]


@router.post("/arbitrations/{arb_id}/resolve", response_model=ArbitrationResponse)
async def resolve_arbitration(arb_id: str, body: ArbitrationResolveRequest, db: AsyncSession = Depends(get_db)):
    service = ApprovalService(db)
    try:
        arbitration = await service.resolve_arbitration(
            arb_id, body.resolution, body.decider_id, body.decider_reason
        )
        await db.commit()
        return ArbitrationResponse.model_validate(arbitration)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{doc_id}/complete")
async def complete_review(doc_id: str, body: CompleteReviewRequest, db: AsyncSession = Depends(get_db)):
    service = ApprovalService(db)
    try:
        result = await service.complete_review(doc_id, body.user_id)
        await db.commit()
        return result
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
