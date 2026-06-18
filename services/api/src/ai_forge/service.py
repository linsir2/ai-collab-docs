import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ai_forge.llm_client import MockLLMClient
from ai_forge.models import AIMemory, AIProposal


class ForgeService:
    PUBLIC_LIMIT = 800
    PRIVATE_PER_DOC_LIMIT = 400
    GLOBAL_PRIVATE_LIMIT = 1200

    def __init__(self, db: AsyncSession, audit_service=None):
        self.db = db
        self.audit_service = audit_service
        self.llm = MockLLMClient()

    async def request_forge(
        self,
        doc_id: str,
        block_id: str,
        instruction: str,
        ai_source: str,
    ) -> AIProposal:
        if ai_source.startswith("personal_ai"):
            ai_memory_type = "private"
            ai_role = ai_source.split(":", 1)[1] if ":" in ai_source else ai_source
        else:
            ai_memory_type = "public"
            ai_role = ai_source.split(":", 1)[1] if ":" in ai_source else ai_source

        pool_count = await self._get_pool_count(doc_id, ai_memory_type)
        if ai_memory_type == "public" and pool_count >= self.PUBLIC_LIMIT:
            raise ValueError(f"Public proposal pool limit ({self.PUBLIC_LIMIT}) exceeded for doc {doc_id}")
        if ai_memory_type == "private":
            if pool_count >= self.PRIVATE_PER_DOC_LIMIT:
                raise ValueError(f"Private proposal pool limit ({self.PRIVATE_PER_DOC_LIMIT}) exceeded for doc {doc_id}")
            global_private = await self._get_global_private_count()
            if global_private >= self.GLOBAL_PRIVATE_LIMIT:
                raise ValueError(f"Global private proposal limit ({self.GLOBAL_PRIVATE_LIMIT}) exceeded")

        result = self.llm.forge(
            anchor_statement="",
            block_content="",
            block_context="",
            ai_role=ai_role,
            ai_source=ai_source,
            instruction=instruction,
        )

        proposal = AIProposal(
            proposal_id=str(uuid.uuid4()),
            block_id=block_id,
            doc_id=doc_id,
            ai_source=ai_source,
            ai_memory_type=ai_memory_type,
            old_content="",
            new_content=result["new_content"],
            rationale=result["rationale"],
            anchor_alignment_score=result["anchor_alignment_score"],
            diff_summary=result["diff_summary"],
            status="pending",
        )
        self.db.add(proposal)
        await self.db.flush()

        if self.audit_service:
            await self.audit_service.log_operation(
                user_id="system",
                action="forge_proposal",
                target_type="proposal",
                target_id=proposal.proposal_id,
                doc_id=doc_id,
                after_state=proposal.new_content[:500],
            )

        return proposal

    async def get_proposals(
        self,
        doc_id: str,
        block_id: str | None = None,
        status: str | None = None,
        ai_source_type: str | None = None,
        user_id: str | None = None,
    ) -> list[AIProposal]:
        stmt = select(AIProposal).where(AIProposal.doc_id == doc_id)
        if block_id:
            stmt = stmt.where(AIProposal.block_id == block_id)
        if status:
            stmt = stmt.where(AIProposal.status == status)
        if ai_source_type == "personal":
            stmt = stmt.where(AIProposal.ai_memory_type == "private")
        elif ai_source_type == "doc":
            stmt = stmt.where(AIProposal.ai_memory_type == "public")
        stmt = stmt.order_by(AIProposal.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_proposal_status(self, prop_id: str, status: str, user_id: str) -> AIProposal | None:
        stmt = update(AIProposal).where(AIProposal.proposal_id == prop_id).values(status=status).returning(AIProposal)
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            await self.db.flush()
            if self.audit_service:
                await self.audit_service.log_operation(
                    user_id=user_id,
                    action="update_proposal_status",
                    target_type="proposal",
                    target_id=prop_id,
                    doc_id=row.doc_id,
                    before_state=row.status,
                    after_state=status,
                )
        return row

    async def get_pool_status(self, doc_id: str, user_id: str) -> dict:
        public_count = await self._get_pool_count(doc_id, "public")
        private_count = await self._get_pool_count(doc_id, "private")
        global_private_count = await self._get_global_private_count()
        return {
            "doc_id": doc_id,
            "public_count": public_count,
            "private_count": private_count,
            "public_limit": self.PUBLIC_LIMIT,
            "private_limit": self.PRIVATE_PER_DOC_LIMIT,
            "global_private_count": global_private_count,
            "global_private_limit": self.GLOBAL_PRIVATE_LIMIT,
        }

    async def get_memories(
        self, doc_id: str, memory_type: str, user_id: str | None = None
    ) -> list[AIMemory]:
        stmt = select(AIMemory).where(
            AIMemory.doc_id == doc_id,
            AIMemory.memory_type == memory_type,
        )
        if user_id:
            stmt = stmt.where(AIMemory.user_id == user_id)
        stmt = stmt.order_by(AIMemory.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_memory(
        self,
        doc_id: str,
        user_id: str,
        ai_role: str,
        rule: str,
        memory_type: str,
        trigger_count: int = 0,
        solidified: bool = False,
    ) -> AIMemory:
        stmt = select(AIMemory).where(
            AIMemory.doc_id == doc_id,
            AIMemory.user_id == user_id,
            AIMemory.ai_role == ai_role,
        )
        result = await self.db.execute(stmt)
        memory = result.scalar_one_or_none()

        if memory:
            memory.rule = rule
            memory.trigger_count = trigger_count
            memory.solidified = solidified or (trigger_count >= 3)
            memory.memory_type = memory_type
        else:
            memory = AIMemory(
                doc_id=doc_id,
                user_id=user_id,
                ai_role=ai_role,
                rule=rule,
                memory_type=memory_type,
                trigger_count=trigger_count,
                solidified=solidified or (trigger_count >= 3),
            )
            self.db.add(memory)

        await self.db.flush()
        return memory

    async def _get_pool_count(self, doc_id: str, memory_type: str) -> int:
        stmt = select(func.count()).where(
            AIProposal.doc_id == doc_id,
            AIProposal.ai_memory_type == memory_type,
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _get_global_private_count(self) -> int:
        stmt = select(func.count()).where(AIProposal.ai_memory_type == "private")
        result = await self.db.execute(stmt)
        return result.scalar() or 0
