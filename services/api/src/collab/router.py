from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from collab.ws_gateway import rooms, ws_gateway, ws_users
from shared.config import settings

router = APIRouter()

try:
    from jose import jwt
    from jose.exceptions import JWTError
except ImportError:
    jwt = None
    JWTError = Exception


async def get_current_user_ws(websocket: WebSocket, token: str = Query(...)):
    if jwt is None:
        return {"user_id": "anonymous", "display_name": "Anonymous"}
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub", "anonymous")
        display_name = payload.get("display_name", user_id)
        return {"user_id": user_id, "display_name": display_name}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.websocket("/ws/{doc_id}")
async def ws_endpoint(websocket: WebSocket, doc_id: str, token: str = Query(...)):
    try:
        if jwt is not None:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id = payload.get("sub", "anonymous")
            display_name = payload.get("display_name", user_id)
            current_user = {"user_id": user_id, "display_name": display_name}
        else:
            current_user = {"user_id": "anonymous", "display_name": "Anonymous"}
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await ws_gateway(websocket, doc_id, current_user)


@router.get("/{doc_id}/presence")
async def get_presence(doc_id: str):
    room = rooms.get(doc_id, set())
    user_ids: list[str] = []
    for ws in room:
        uid = ws_users.get(id(ws), "")
        if uid:
            user_ids.append(uid)
    return {"doc_id": doc_id, "online_users": list(set(user_ids)), "count": len(set(user_ids))}
