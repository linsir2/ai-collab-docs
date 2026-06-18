from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import PlainTextResponse

from audit.models import OperationLogResponse
from audit.service import AuditService
from shared.database import get_db

router = APIRouter()


@router.get("/logs", response_model=list[OperationLogResponse])
async def list_logs(
    doc_id: str | None = Query(None),
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    logs = await service.query_logs(doc_id=doc_id, user_id=user_id, action=action, limit=limit, offset=offset)
    return [
        OperationLogResponse(
            op_id=log.op_id,
            user_id=log.user_id,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            doc_id=log.doc_id,
            before_state=log.before_state,
            after_state=log.after_state,
            timestamp=log.timestamp.isoformat() if log.timestamp else "",
        )
        for log in logs
    ]


@router.get("/logs/export", response_class=PlainTextResponse)
async def export_logs(
    doc_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    csv_data = await service.export_csv(doc_id=doc_id)
    return PlainTextResponse(content=csv_data, media_type="text/csv")
