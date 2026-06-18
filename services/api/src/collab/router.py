from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from collab.ws_gateway import ws_gateway
from shared.config import settings
from shared.database import async_session

try:
    from jose import jwt
    from jose.exceptions import JWTError
except ImportError:
    jwt = None
    JWTError = Exception

router = APIRouter()


async def _resolve_doc_role(doc_id: str, user_id: str) -> str:
    """查询用户在指定文档中的有效角色。

    优先查 document_permissions；若无记录且用户为文档所有者，则返回 "owner"；
    否则默认 "reader"。
    """
    from auth.models import DocumentPermission
    from document.models import Document

    async with async_session() as db:
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


async def _ws_authenticate(token: str, doc_id: str):
    if jwt is None:
        return {
            "user_id": "anonymous",
            "display_name": "Anonymous",
            "global_role": "personal",
            "doc_role": "reader",
        }
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    global_role = payload.get("global_role")
    if user_id is None or global_role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    doc_role = await _resolve_doc_role(doc_id, user_id)

    return {
        "user_id": user_id,
        "display_name": payload.get("display_name", user_id),
        "global_role": global_role,
        "doc_role": doc_role,
    }


@router.websocket("/ws/{doc_id}")
async def ws_endpoint(websocket: WebSocket, doc_id: str, token: str = Query(...)):
    try:
        current_user = await _ws_authenticate(token, doc_id)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await ws_gateway(websocket, doc_id, current_user)


@router.get("/{doc_id}/presence")
async def get_presence(doc_id: str):
    from collab.ws_gateway import rooms, ws_users

    room = rooms.get(doc_id, set())
    user_ids: list[str] = []
    for ws in room:
        uid = ws_users.get(id(ws), "")
        if uid:
            user_ids.append(uid)
    return {"doc_id": doc_id, "online_users": list(set(user_ids)), "count": len(set(user_ids))}
