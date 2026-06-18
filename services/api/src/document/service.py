import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BlockMeta, BlockMetaUpdate, Document, DocumentCreate


class DocumentService:
    def __init__(self, db: AsyncSession, audit_service=None):
        self.db = db
        self.audit_service = audit_service

    async def create_document(self, owner_id: str, data: DocumentCreate) -> Document:
        doc = Document(
            doc_id=str(uuid.uuid4()),
            title=data.title,
            state="draft",
            owner_id=owner_id,
            anchor_statement=data.anchor_statement,
            anchor_audience=data.anchor_audience,
            anchor_argument=data.anchor_argument,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get_document(self, doc_id: str) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.doc_id == doc_id))
        return result.scalar_one_or_none()

    async def list_documents(self, user_id: str | None = None) -> list[Document]:
        result = await self.db.execute(select(Document).order_by(Document.updated_at.desc()))
        return list(result.scalars().all())

    async def update_document_state(self, doc_id: str, new_state: str, audit_service=None) -> Document:
        doc = await self.get_document(doc_id)
        if doc is None:
            raise ValueError(f"文档 {doc_id} 不存在")
        old_state = doc.state
        doc.state = new_state
        doc.updated_at = datetime.utcnow()
        svc = audit_service or self.audit_service
        if svc:
            await svc.log(
                user_id="system",
                action="state_transition",
                target_type="document",
                target_id=doc_id,
                doc_id=doc_id,
                before_state=old_state,
                after_state=new_state,
            )
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def create_block_meta(self, doc_id: str, block_id: str, sort_order: int = 0) -> BlockMeta:
        meta = BlockMeta(
            block_id=block_id,
            doc_id=doc_id,
            sort_order=sort_order,
        )
        self.db.add(meta)
        await self.db.commit()
        await self.db.refresh(meta)
        return meta

    async def get_block_metas(self, doc_id: str) -> list[BlockMeta]:
        result = await self.db.execute(
            select(BlockMeta).where(BlockMeta.doc_id == doc_id).order_by(BlockMeta.sort_order)
        )
        return list(result.scalars().all())

    async def update_block_meta(self, block_id: str, data: BlockMetaUpdate) -> BlockMeta:
        result = await self.db.execute(select(BlockMeta).where(BlockMeta.block_id == block_id))
        meta = result.scalar_one_or_none()
        if meta is None:
            raise ValueError(f"Block {block_id} 不存在")
        meta.tags = data.tags
        meta.claimant_id = data.claimant_id
        meta.drift_score = data.drift_score
        meta.locked_by = data.locked_by
        await self.db.commit()
        await self.db.refresh(meta)
        return meta

    async def claim_block(self, block_id: str, user_id: str) -> BlockMeta:
        result = await self.db.execute(select(BlockMeta).where(BlockMeta.block_id == block_id))
        meta = result.scalar_one_or_none()
        if meta is None:
            raise ValueError(f"Block {block_id} 不存在")
        meta.claimant_id = user_id
        await self.db.commit()
        await self.db.refresh(meta)
        return meta

    async def lock_block(self, block_id: str, user_id: str) -> BlockMeta:
        result = await self.db.execute(select(BlockMeta).where(BlockMeta.block_id == block_id))
        meta = result.scalar_one_or_none()
        if meta is None:
            raise ValueError(f"Block {block_id} 不存在")
        meta.locked_by = user_id
        await self.db.commit()
        await self.db.refresh(meta)
        return meta
