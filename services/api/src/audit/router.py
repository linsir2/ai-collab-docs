from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audit.models import OperationLog, OperationLogResponse
from audit.service import AuditService
from auth.deps import get_current_user
from auth.models import DocumentPermission, UserResponse
from shared.authz import GlobalRole
from shared.database import get_db

router = APIRouter()


@router.get("/logs", response_model=list[OperationLogResponse])
async def list_logs(
    doc_id: str | None = Query(None),
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)

    if current_user.global_role == GlobalRole.OPS.value:
        logs = await service.query_logs(
            doc_id=doc_id, user_id=user_id, action=action, limit=limit, offset=offset
        )
    else:
        # team_admin 与 personal 用户：仅可见其参与文档的日志。
        # NOTE: MVP 已知限制 — team_admin 暂与 personal 用户同等过滤
        # （按文档参与范围）。更细粒度的团队级视图（覆盖团队成员拥有的
        # 全部文档、排除纯基础设施事件如 llm_degraded/memory_repair）
        # 留待后续迭代实现。
        perm_result = await db.execute(
            select(DocumentPermission.doc_id).where(
                DocumentPermission.user_id == current_user.user_id,
            )
        )
        member_doc_ids = {row for row in perm_result.scalars().all()}

        stmt = select(OperationLog)
        if doc_id:
            if doc_id not in member_doc_ids:
                return []
            stmt = stmt.where(OperationLog.doc_id == doc_id)
        else:
            if member_doc_ids:
                stmt = stmt.where(OperationLog.doc_id.in_(member_doc_ids))
            else:
                return []
        if user_id:
            stmt = stmt.where(OperationLog.user_id == user_id)
        if action:
            stmt = stmt.where(OperationLog.action == action)
        stmt = stmt.order_by(OperationLog.timestamp.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        logs = list(result.scalars().all())

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
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.global_role == GlobalRole.OPS.value:
        pass
    elif current_user.global_role == GlobalRole.TEAM_ADMIN.value:
        pass
    else:
        perm_result = await db.execute(
            select(DocumentPermission).where(
                DocumentPermission.doc_id == doc_id,
                DocumentPermission.user_id == current_user.user_id,
            )
        )
        if perm_result.scalar_one_or_none() is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权导出此文档日志")

    service = AuditService(db)
    csv_data = await service.export_csv(doc_id=doc_id)
    return PlainTextResponse(content=csv_data, media_type="text/csv")
