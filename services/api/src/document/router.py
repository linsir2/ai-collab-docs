from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.deps import get_current_user, require_doc_permission
from auth.models import DocumentPermission, UserResponse
from shared.database import get_db
from .models import BlockMetaUpdate, Document, DocumentCreate, DocumentResponse, StateTransition
from .service import DocumentService

router = APIRouter()


def _doc_to_response(doc: Document) -> DocumentResponse:
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
    _ctx: dict = Depends(require_doc_permission("doc_id", "discuss")),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return _doc_to_response(doc)


@router.get("/documents/{doc_id}/me")
async def get_document_my_role(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
        doc_result = await db.execute(select(Document).where(Document.doc_id == doc_id))
        doc = doc_result.scalar_one_or_none()
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
        if doc.owner_id == current_user.user_id:
            doc_role = "owner"
        else:
            doc_role = "reader"
    return {"doc_id": doc_id, "user_id": current_user.user_id, "doc_role": doc_role}


@router.put("/documents/{doc_id}/blocks/{block_id}/meta")
async def update_block_meta(
    doc_id: str,
    block_id: str,
    data: BlockMetaUpdate,
    _ctx: dict = Depends(require_doc_permission("doc_id", "discuss")),
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
    _ctx: dict = Depends(require_doc_permission("doc_id", "claim_paragraph")),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
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
    _ctx: dict = Depends(require_doc_permission("doc_id", "state_transition")),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    doc = await service.update_document_state(doc_id, data.to_state)
    return _doc_to_response(doc)


@router.post("/documents/{doc_id}/archive")
async def archive_document(
    doc_id: str,
    _ctx: dict = Depends(require_doc_permission("doc_id", "archive")),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    doc = await service.update_document_state(doc_id, "archived")
    return {"status": "ok", "doc_id": doc_id}


@router.get("/documents/{doc_id}/blocks")
async def list_block_metas(
    doc_id: str,
    _ctx: dict = Depends(require_doc_permission("doc_id", "discuss")),
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
