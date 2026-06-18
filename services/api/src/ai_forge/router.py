from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_forge.llm_client import MockLLMClient
from ai_forge.models import (
    AIMemory,
    AIProposal,
    ConflictDetectRequest,
    ConflictDetectResponse,
    ForgeRequest,
    MemoryResponse,
    PoolStatusResponse,
    ProposalResponse,
)
from ai_forge.service import ForgeService
from audit.service import AuditService
from auth.deps import get_current_user
from auth.models import DocumentPermission, UserResponse
from document.models import Document
from shared.authz import can_do_in_document
from shared.database import get_db

router = APIRouter()


def _proposal_to_response(p: AIProposal) -> ProposalResponse:
    return ProposalResponse(
        proposal_id=p.proposal_id,
        block_id=p.block_id,
        doc_id=p.doc_id,
        ai_source=p.ai_source,
        ai_memory_type=p.ai_memory_type,
        new_content=p.new_content,
        rationale=p.rationale,
        anchor_alignment_score=p.anchor_alignment_score,
        diff_summary=p.diff_summary,
        status=p.status,
        created_at=p.created_at.isoformat() if p.created_at else "",
    )


def _memory_to_response(m: AIMemory) -> MemoryResponse:
    return MemoryResponse(
        id=str(m.id),
        doc_id=m.doc_id,
        user_id=m.user_id,
        ai_role=m.ai_role,
        rule=m.rule,
        memory_type=m.memory_type,
        solidified=m.solidified,
        trigger_count=m.trigger_count,
        created_at=m.created_at.isoformat() if m.created_at else "",
    )


async def _resolve_doc_role(db: AsyncSession, doc_id: str, user_id: str) -> str:
    perm_result = await db.execute(
        select(DocumentPermission).where(
            DocumentPermission.doc_id == doc_id,
            DocumentPermission.user_id == user_id,
        )
    )
    perm = perm_result.scalar_one_or_none()
    if perm is not None:
        return perm.effective_role
    doc_result = await db.execute(select(Document).where(Document.doc_id == doc_id))
    doc = doc_result.scalar_one_or_none()
    if doc is not None and doc.owner_id == user_id:
        return "owner"
    return "reader"


@router.post("/refine", response_model=ProposalResponse)
async def request_forge(
    body: ForgeRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc_role = await _resolve_doc_role(db, body.doc_id, current_user.user_id)
    if not can_do_in_document(doc_role, "use_forge"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权使用 AI Forge")

    service = ForgeService(db, audit_service=AuditService(db))
    try:
        proposal = await service.request_forge(
            doc_id=body.doc_id,
            block_id=body.block_id,
            instruction=body.instruction,
            ai_source=body.ai_source,
        )
        await db.commit()
        await db.refresh(proposal)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return _proposal_to_response(proposal)


@router.get("/proposals", response_model=list[ProposalResponse])
async def list_proposals(
    doc_id: str = Query(...),
    block_id: str | None = Query(None),
    status: str | None = Query(None),
    ai_source_type: str | None = Query(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc_role = await _resolve_doc_role(db, doc_id, current_user.user_id)
    if not can_do_in_document(doc_role, "discuss"):
        raise HTTPException(status_code=403, detail="无权查看此文档提案")

    service = ForgeService(db)
    proposals = await service.get_proposals(
        doc_id=doc_id,
        block_id=block_id,
        status=status,
        ai_source_type=ai_source_type,
    )
    return [_proposal_to_response(p) for p in proposals]


@router.put("/proposals/{prop_id}", response_model=ProposalResponse)
async def update_proposal(
    prop_id: str,
    status: str = Query(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ForgeService(db, audit_service=AuditService(db))
    proposal = await service.update_proposal_status(
        prop_id=prop_id, status=status, user_id=current_user.user_id
    )
    if not proposal:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    await db.commit()
    await db.refresh(proposal)
    return _proposal_to_response(proposal)


@router.get("/pool-status", response_model=PoolStatusResponse)
async def get_pool_status(
    doc_id: str = Query(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc_role = await _resolve_doc_role(db, doc_id, current_user.user_id)
    if not can_do_in_document(doc_role, "discuss"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此文档信息")

    service = ForgeService(db)
    status_data = await service.get_pool_status(doc_id=doc_id, user_id=current_user.user_id)
    return PoolStatusResponse(**status_data)


@router.get("/memories", response_model=list[MemoryResponse])
async def get_memories(
    doc_id: str = Query(...),
    memory_type: str = Query("public"),
    user_id: str | None = Query(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc_role = await _resolve_doc_role(db, doc_id, current_user.user_id)
    if not can_do_in_document(doc_role, "discuss"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此文档记忆")

    effective_user_id = user_id if memory_type == "private" and user_id else current_user.user_id
    service = ForgeService(db)
    memories = await service.get_memories(
        doc_id=doc_id, memory_type=memory_type, user_id=effective_user_id
    )
    return [_memory_to_response(m) for m in memories]


@router.post("/conflicts/detect", response_model=ConflictDetectResponse)
async def detect_conflicts(
    body: ConflictDetectRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc_role = await _resolve_doc_role(db, body.doc_id, current_user.user_id)
    if not can_do_in_document(doc_role, "discuss"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权执行此操作")

    service = ForgeService(db)
    proposals = await service.get_proposals(doc_id=body.doc_id)
    prop_map = {p.proposal_id: p for p in proposals}

    prop_a = prop_map.get(body.proposal_a_id)
    prop_b = prop_map.get(body.proposal_b_id)

    if not prop_a or not prop_b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both proposals not found")

    llm = MockLLMClient()
    result = llm.detect_conflict(
        proposal_a_content=prop_a.new_content,
        proposal_b_content=prop_b.new_content,
        proposal_a_rationale=prop_a.rationale,
        proposal_b_rationale=prop_b.rationale,
    )
    return ConflictDetectResponse(
        is_opposing=result["is_opposing"],
        conflict_description=result["conflict_description"],
        proposal_a_source=prop_a.ai_source,
        proposal_b_source=prop_b.ai_source,
    )
