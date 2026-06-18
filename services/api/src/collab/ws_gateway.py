import json
from datetime import datetime, timezone

from contracts.contracts import WSMessage, WSMessageType
from fastapi import WebSocket
from shared.authz import is_allowed_ws_message
from shared.middleware import cleanup_ws_rate_limit, try_acquire_ws_message

rooms: dict[str, set] = {}
ws_users: dict[int, str] = {}
ws_user_roles: dict[int, str] = {}


async def broadcast_to_room(doc_id: str, message: dict, exclude: WebSocket | None = None):
    room = rooms.get(doc_id, set())
    dead: list[WebSocket] = []
    for ws in room:
        if ws is exclude:
            continue
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        room.discard(ws)
        ws_users.pop(id(ws), None)
        ws_user_roles.pop(id(ws), None)


async def ws_gateway(websocket: WebSocket, doc_id: str, current_user: dict):
    await websocket.accept()

    if doc_id not in rooms:
        rooms[doc_id] = set()
    rooms[doc_id].add(websocket)
    ws_users[id(websocket)] = current_user.get("user_id", "")
    ws_user_roles[id(websocket)] = current_user.get("doc_role", "reader")

    join_msg = {
        "type": WSMessageType.STATE_CHANGE.value,
        "doc_id": doc_id,
        "payload": {
            "event": "user_joined",
            "user_id": current_user.get("user_id", ""),
            "display_name": current_user.get("display_name", ""),
        },
        "sender_id": current_user.get("user_id", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await broadcast_to_room(doc_id, join_msg, exclude=websocket)

    ws_id = id(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            if not try_acquire_ws_message(ws_id):
                throttled = {
                    "type": "ERROR",
                    "doc_id": doc_id,
                    "payload": {
                        "event": "rate_limited",
                        "reason": "Message rate limit exceeded (60/min). Slow down.",
                    },
                    "sender_id": "system",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    await websocket.send_json(throttled)
                except Exception:
                    pass
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type", "").lower()

            if msg_type == WSMessageType.PING.value:
                pong = WSMessage(
                    type=WSMessageType.PONG,
                    doc_id=doc_id,
                    sender_id=current_user.get("user_id", ""),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                await websocket.send_json(pong.__dict__)
                continue

            sender_role = ws_user_roles.get(id(websocket), "reader")
            if not is_allowed_ws_message(sender_role, msg_type):
                rejection = {
                    "type": "ERROR",
                    "doc_id": doc_id,
                    "payload": {
                        "event": "unauthorized_message",
                        "reason": "无权发送此类型消息",
                        "msg_type": msg_type,
                        "doc_role": sender_role,
                    },
                    "sender_id": "system",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    await websocket.send_json(rejection)
                    await websocket.close(code=4003, reason="Unauthorized message")
                except Exception:
                    pass
                return

            if msg_type in {
                WSMessageType.PROPOSAL_CREATED.value,
                WSMessageType.PROPOSAL_UPDATED.value,
                WSMessageType.CONFLICT_DETECTED.value,
                WSMessageType.ARBITRATION_RESOLVED.value,
                WSMessageType.STATE_CHANGE.value,
                WSMessageType.DRIFT_ALERT.value,
            }:
                outbound = {
                    **data,
                    "sender_id": current_user.get("user_id", ""),
                    "timestamp": data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                }
                await broadcast_to_room(doc_id, outbound)
    except Exception:
        pass
    finally:
        if doc_id in rooms:
            rooms[doc_id].discard(websocket)
            if not rooms[doc_id]:
                del rooms[doc_id]
        ws_users.pop(id(websocket), None)
        ws_user_roles.pop(id(websocket), None)
        cleanup_ws_rate_limit(id(websocket))

        leave_msg = {
            "type": WSMessageType.STATE_CHANGE.value,
            "doc_id": doc_id,
            "payload": {
                "event": "user_left",
                "user_id": current_user.get("user_id", ""),
                "display_name": current_user.get("display_name", ""),
            },
            "sender_id": current_user.get("user_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await broadcast_to_room(doc_id, leave_msg)
