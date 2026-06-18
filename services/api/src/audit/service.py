import csv
import io
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audit.models import OperationLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_operation(
        self,
        user_id: str,
        action: str,
        target_type: str,
        target_id: str,
        doc_id: str,
        before_state: str = "",
        after_state: str = "",
    ) -> OperationLog:
        op = OperationLog(
            op_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            doc_id=doc_id,
            before_state=before_state,
            after_state=after_state,
        )
        self.db.add(op)
        await self.db.flush()
        return op

    async def query_logs(
        self,
        doc_id: str | None = None,
        user_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OperationLog]:
        stmt = select(OperationLog)
        if doc_id:
            stmt = stmt.where(OperationLog.doc_id == doc_id)
        if user_id:
            stmt = stmt.where(OperationLog.user_id == user_id)
        if action:
            stmt = stmt.where(OperationLog.action == action)
        stmt = stmt.order_by(OperationLog.timestamp.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def export_csv(self, doc_id: str) -> str:
        logs = await self.query_logs(doc_id=doc_id, limit=10000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["op_id", "user_id", "action", "target_type", "target_id", "doc_id", "before_state", "after_state", "timestamp"])
        for log in logs:
            writer.writerow([
                log.op_id,
                log.user_id,
                log.action,
                log.target_type,
                log.target_id,
                log.doc_id,
                log.before_state,
                log.after_state,
                log.timestamp.isoformat() if log.timestamp else "",
            ])
        return output.getvalue()
