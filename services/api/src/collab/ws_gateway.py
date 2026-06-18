import json
from datetime import datetime, timezone

from contracts.contracts import WSMessage, WSMessageType
from fastapi import WebSocket

rooms: dict[str, set] = {}
ws_users: dict[int, str] = {}


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


async def ws_gateway(websocket: WebSocket, doc_id: str, current_user: dict):
    await websocket.accept()

    if doc_id not in rooms:
        rooms[doc_id] = set()
    rooms[doc_id].add(websocket)
    ws_users[id(websocket)] = current_user.get("user_id", "")

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

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type", "")

            if msg_type == WSMessageType.PING.value:
                pong = WSMessage(
                    type=WSMessageType.PONG,
                    doc_id=doc_id,
                    sender_id=current_user.get("user_id", ""),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                await websocket.send_json(pong.__dict__)
                continue

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
