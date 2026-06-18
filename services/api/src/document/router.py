from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.deps import get_current_user
from auth.models import UserResponse
from contracts.contracts import DocumentState, UserRole
from shared.database import get_db
from state_engine.engine import state_engine
from .models import BlockMetaUpdate, DocumentCreate, DocumentResponse, StateTransition
from .service import DocumentService

router = APIRouter()


def _doc_to_response(doc) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        doc_id=doc.doc_id,
        title=doc.title,
        state=doc.state,
        owner_id=doc.owner_id,
        anchor_statement=doc.anchor_statement,
        anchor_audience=doc.anchor_audience,
        anchor_argument=doc.anchor_argument,
        anchor_version=doc.anchor_version,
        anchor_history=doc.anchor_history,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
        updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
    )


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.create_document(current_user.user_id, data)
    return _doc_to_response(doc)


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    docs = await service.list_documents()
    return [_doc_to_response(d) for d in docs]


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return _doc_to_response(doc)


@router.put("/documents/{doc_id}/blocks/{block_id}/meta")
async def update_block_meta(
    doc_id: str,
    block_id: str,
    data: BlockMetaUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    try:
        meta = await service.update_block_meta(block_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {
        "block_id": meta.block_id,
        "doc_id": meta.doc_id,
        "tags": meta.tags,
        "claimant_id": meta.claimant_id,
        "drift_score": meta.drift_score,
        "locked_by": meta.locked_by,
        "sort_order": meta.sort_order,
    }


@router.post("/documents/{doc_id}/blocks/{block_id}/claim")
async def claim_block(
    doc_id: str,
    block_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    try:
        meta = await service.claim_block(block_id, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {
        "block_id": meta.block_id,
        "claimant_id": meta.claimant_id,
    }


@router.post("/documents/{doc_id}/transition", response_model=DocumentResponse)
async def transition_document(
    doc_id: str,
    data: StateTransition,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    if not state_engine.guard_transition(
        DocumentState(doc.state),
        DocumentState(data.to_state),
        UserRole(current_user.role),
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权执行此状态转换")

    doc = await service.update_document_state(doc_id, data.to_state)
    return _doc_to_response(doc)


@router.get("/documents/{doc_id}/blocks")
async def list_block_metas(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    metas = await service.get_block_metas(doc_id)
    return [
        {
            "block_id": m.block_id,
            "doc_id": m.doc_id,
            "tags": m.tags,
            "claimant_id": m.claimant_id,
            "drift_score": m.drift_score,
            "locked_by": m.locked_by,
            "sort_order": m.sort_order,
        }
        for m in metas
    ]
