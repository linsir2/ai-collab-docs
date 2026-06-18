import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.contracts import (
    ApprovalAction,
    ArbitrationResolution,
    ConflictType,
    DocumentState,
    LLMConflictDetectRequest,
    ProposalStatus,
)


class ApprovalService:
    def __init__(self, db: AsyncSession, audit_service=None):
        self.db = db
        self.audit_service = audit_service

    async def _log_operation(self, user_id: str, action: str, target_type: str, target_id: str, doc_id: str,
                              before_state: str = "", after_state: str = ""):
        if self.audit_service:
            await self.audit_service.log_operation(
                user_id=user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                doc_id=doc_id,
                before_state=before_state,
                after_state=after_state,
            )

    async def _get_document_state(self, doc_id: str) -> str:
        result = await self.db.execute(text("SELECT state FROM documents WHERE doc_id = :doc_id"), {"doc_id": doc_id})
        row = result.fetchone()
        if row is None:
            raise ValueError(f"Document {doc_id} not found")
        return row[0]

    async def _get_proposals_by_block(self, doc_id: str, block_id: str) -> list[dict]:
        result = await self.db.execute(
            text("SELECT * FROM ai_proposals WHERE doc_id = :doc_id AND block_id = :block_id AND status = :status"),
            {"doc_id": doc_id, "block_id": block_id, "status": ProposalStatus.PENDING.value},
        )
        rows = result.fetchall()
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]

    async def _update_proposal_status(self, prop_id: str, status: ProposalStatus):
        await self.db.execute(
            text("UPDATE ai_proposals SET status = :status WHERE proposal_id = :prop_id"),
            {"status": status.value, "prop_id": prop_id},
        )

    async def start_review(self, doc_id: str, user_id: str):
        from approval.models import ReviewSession, Snapshot

        current_state = await self._get_document_state(doc_id)
        if current_state not in (DocumentState.DISCUSSION.value, DocumentState.REVIEW.value):
            raise ValueError(
                f"Cannot start review: document is in '{current_state}' state. "
                f"Must be in DISCUSSION or REVIEW state."
            )

        snap_id = str(uuid4())
        session_id = str(uuid4())

        snapshot = Snapshot(
            snap_id=snap_id,
            doc_id=doc_id,
            state=current_state,
            created_by=user_id,
        )
        self.db.add(snapshot)

        session = ReviewSession(
            session_id=session_id,
            doc_id=doc_id,
            snapshot_id=snap_id,
            status="active",
        )
        self.db.add(session)

        await self.db.flush()

        await self._log_operation(
            user_id=user_id,
            action="start_review",
            target_type="review_session",
            target_id=session_id,
            doc_id=doc_id,
            before_state=current_state,
            after_state=current_state,
        )

        return session

    async def approve_proposal(self, prop_id: str, action: ApprovalAction, user_id: str) -> dict:
        result = await self.db.execute(
            text("SELECT * FROM ai_proposals WHERE proposal_id = :prop_id"), {"prop_id": prop_id}
        )
        row = result.fetchone()
        if row is None:
            raise ValueError(f"Proposal {prop_id} not found")

        columns = result.keys()
        proposal = dict(zip(columns, row))

        if action == ApprovalAction.MERGE_ALL:
            new_status = ProposalStatus.ACCEPTED
        elif action in (ApprovalAction.REJECT_ANNOTATE, ApprovalAction.MANUAL_EDIT):
            new_status = ProposalStatus.REJECTED
        else:
            raise ValueError(f"Unknown approval action: {action}")

        await self._update_proposal_status(prop_id, new_status)
        await self.db.flush()

        await self._log_operation(
            user_id=user_id,
            action="approve_proposal",
            target_type="proposal",
            target_id=prop_id,
            doc_id=proposal["doc_id"],
            before_state=proposal["status"],
            after_state=new_status.value,
        )

        return {"prop_id": prop_id, "status": new_status.value, "action": action.value}

    async def detect_conflicts(self, doc_id: str, block_id: str) -> list:
        from ai_forge.llm_client import llm_client
        from approval.models import Arbitration

        proposals = await self._get_proposals_by_block(doc_id, block_id)
        if len(proposals) < 2:
            return []

        arbitrations = []
        for i in range(len(proposals)):
            for j in range(i + 1, len(proposals)):
                prop_a = proposals[i]
                prop_b = proposals[j]

                if prop_a["ai_source"] == prop_b["ai_source"]:
                    continue

                request = LLMConflictDetectRequest(
                    anchor=None,
                    proposal_a=prop_a.get("new_content", ""),
                    proposal_a_rationale=prop_a.get("rationale", ""),
                    proposal_b=prop_b.get("new_content", ""),
                    proposal_b_rationale=prop_b.get("rationale", ""),
                )
                response = llm_client.detect_conflict(request)

                if response.is_opposing:
                    conflict_type = ConflictType.PURE_DOC_AI.value
                    if "personal_ai" in prop_a["ai_source"] or "personal_ai" in prop_b["ai_source"]:
                        conflict_type = ConflictType.MIXED.value

                    arbitration = await self.create_arbitration(
                        doc_id=doc_id,
                        block_id=block_id,
                        conflict_type=conflict_type,
                        proposals=[prop_a["proposal_id"], prop_b["proposal_id"]],
                        ai_sources=[prop_a["ai_source"], prop_b["ai_source"]],
                        claimant_id=prop_a.get("claimant_id", "") or prop_b.get("claimant_id", ""),
                    )
                    arbitrations.append(arbitration)

        await self._log_operation(
            user_id="system",
            action="detect_conflicts",
            target_type="block",
            target_id=block_id,
            doc_id=doc_id,
            after_state=f"Found {len(arbitrations)} conflict(s)",
        )

        return arbitrations

    async def create_arbitration(self, doc_id: str, block_id: str, conflict_type: str,
                                  proposals: list[str], ai_sources: list[str], claimant_id: str = ""):
        from approval.models import Arbitration

        arb_id = str(uuid4())
        arbitration = Arbitration(
            arb_id=arb_id,
            doc_id=doc_id,
            block_id=block_id,
            conflict_type=conflict_type,
            proposals_json=json.dumps(proposals),
            ai_sources_json=json.dumps(ai_sources),
            claimant_id=claimant_id,
        )
        self.db.add(arbitration)
        await self.db.flush()

        await self._log_operation(
            user_id="system",
            action="create_arbitration",
            target_type="arbitration",
            target_id=arb_id,
            doc_id=doc_id,
            after_state=f"conflict_type={conflict_type}",
        )

        return arbitration

    async def get_arbitrations(self, doc_id: str, status_filter: str | None = None):
        from approval.models import Arbitration

        query = select(Arbitration).where(Arbitration.doc_id == doc_id)
        result = await self.db.execute(query)
        arbitrations = list(result.scalars().all())

        if status_filter == "pending":
            arbitrations = [a for a in arbitrations if a.resolution is None]
        elif status_filter == "resolved":
            arbitrations = [a for a in arbitrations if a.resolution is not None]

        return arbitrations

    async def resolve_arbitration(self, arb_id: str, resolution: str, decider_id: str, decider_reason: str):
        from approval.models import Arbitration

        result = await self.db.execute(select(Arbitration).where(Arbitration.arb_id == arb_id))
        arbitration = result.scalar_one_or_none()
        if arbitration is None:
            raise ValueError(f"Arbitration {arb_id} not found")

        proposals = json.loads(arbitration.proposals_json)

        if resolution == ArbitrationResolution.PROPOSAL_A.value and len(proposals) >= 1:
            await self._update_proposal_status(proposals[0], ProposalStatus.ACCEPTED)
            if len(proposals) >= 2:
                await self._update_proposal_status(proposals[1], ProposalStatus.REJECTED)
        elif resolution == ArbitrationResolution.PROPOSAL_B.value and len(proposals) >= 2:
            await self._update_proposal_status(proposals[0], ProposalStatus.REJECTED)
            await self._update_proposal_status(proposals[1], ProposalStatus.ACCEPTED)
        elif resolution == ArbitrationResolution.DECLINED.value:
            for p in proposals:
                await self._update_proposal_status(p, ProposalStatus.REJECTED)

        arbitration.resolution = resolution
        arbitration.decider_id = decider_id
        arbitration.decider_reason = decider_reason
        arbitration.resolved_at = datetime.utcnow()

        await self.db.flush()

        await self._log_operation(
            user_id=decider_id,
            action="resolve_arbitration",
            target_type="arbitration",
            target_id=arb_id,
            doc_id=arbitration.doc_id,
            before_state="pending",
            after_state=f"resolved={resolution}",
        )

        return arbitration

    async def complete_review(self, doc_id: str, user_id: str) -> dict:
        from approval.models import ReviewSession

        result = await self.db.execute(
            select(ReviewSession).where(
                ReviewSession.doc_id == doc_id,
                ReviewSession.status == "active",
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError(f"No active review session found for document {doc_id}")

        result = await self.db.execute(
            text("SELECT COUNT(*) FROM ai_proposals WHERE doc_id = :doc_id AND status = :status"),
            {"doc_id": doc_id, "status": ProposalStatus.PENDING.value},
        )
        pending_count = result.scalar_one()

        result = await self.db.execute(
            text("SELECT COUNT(*) FROM arbitrations WHERE doc_id = :doc_id AND resolution IS NULL"),
            {"doc_id": doc_id},
        )
        unresolved_arbitrations = result.scalar_one()

        if pending_count > 0 or unresolved_arbitrations > 0:
            return {
                "completed": False,
                "pending_proposals": pending_count,
                "unresolved_arbitrations": unresolved_arbitrations,
                "message": "Review cannot be completed: there are still pending proposals or unresolved arbitrations.",
            }

        session.status = "completed"
        await self.db.flush()

        await self._log_operation(
            user_id=user_id,
            action="complete_review",
            target_type="review_session",
            target_id=session.session_id,
            doc_id=doc_id,
            before_state="active",
            after_state="completed",
        )

        return {
            "completed": True,
            "session_id": session.session_id,
            "pending_proposals": 0,
            "unresolved_arbitrations": 0,
        }

    async def get_review_session(self, doc_id: str):
        from approval.models import ReviewSession

        result = await self.db.execute(
            select(ReviewSession).where(ReviewSession.doc_id == doc_id).order_by(ReviewSession.created_at.desc())
        )
        return result.scalar_one_or_none()
