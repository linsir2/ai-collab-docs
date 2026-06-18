"""WebSocket 协作模块和 Presence 端点的完整 pytest 集成测试。

覆盖范围：
- Presence 端点 (GET /api/collab/{doc_id}/presence)
- _ws_authenticate 函数单元测试
- ws_gateway 函数单元测试
- WebSocket 消息权限矩阵集成测试
"""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import main  # noqa: F401  导入 main 以注册所有模型到 Base.metadata
from auth.service import AuthService
from collab.router import _ws_authenticate
from collab.ws_gateway import rooms, ws_gateway, ws_user_roles, ws_users
from contracts.contracts import WSMessageType
from shared.middleware import _ws_buckets


# ============================================================
# 辅助 fixtures 和函数
# ============================================================

@pytest.fixture(autouse=True)
def _cleanup_ws_state():
    """每个测试前后清理 WebSocket 全局状态，避免测试间相互影响。"""
    rooms.clear()
    ws_users.clear()
    ws_user_roles.clear()
    _ws_buckets.clear()
    yield
    rooms.clear()
    ws_users.clear()
    ws_user_roles.clear()
    _ws_buckets.clear()


class _MockAsyncSession:
    """模拟 async_sessionmaker，在 async with 上下文中返回指定的 mock_db。"""

    def __init__(self, mock_db):
        self.mock_db = mock_db

    def __call__(self):
        return self

    async def __aenter__(self):
        return self.mock_db

    async def __aexit__(self, *args):
        return None


def _make_mock_websocket(messages=None):
    """创建模拟 WebSocket。

    Args:
        messages: 要接收的消息列表（JSON 字符串）。接收完毕后抛出 RuntimeError 模拟断开。
                  若为 None 或空列表，则立即断开。
    """
    ws = AsyncMock()
    msg_list = list(messages) if messages else []
    side_effect = msg_list + [RuntimeError("disconnect")]
    ws.receive_text = AsyncMock(side_effect=side_effect)
    return ws


def _make_mock_user(doc_role="owner", user_id="test-user-001"):
    """创建模拟用户信息。"""
    return {
        "user_id": user_id,
        "display_name": "Test User",
        "global_role": "personal",
        "doc_role": doc_role,
    }


async def _run_gateway_with_message(doc_role, msg_type, doc_id="test-doc"):
    """使用指定角色和消息类型运行 ws_gateway，返回结果。

    Returns:
        dict: {accepted, closed, messages, websocket}
    """
    websocket = _make_mock_websocket([
        json.dumps({"type": msg_type, "payload": {"event": "test"}}),
    ])
    current_user = _make_mock_user(doc_role=doc_role)
    await ws_gateway(websocket, doc_id, current_user)

    sent_messages = [c.args[0] for c in websocket.send_json.call_args_list]
    error_messages = [m for m in sent_messages if m.get("type") == "ERROR"]
    was_closed_with_4003 = any(
        c.kwargs.get("code") == 4003 for c in websocket.close.call_args_list
    )

    return {
        "accepted": len(error_messages) == 0,
        "closed": was_closed_with_4003,
        "messages": sent_messages,
        "websocket": websocket,
    }


# ============================================================
# 1. Presence 端点测试
# ============================================================

class TestPresenceEndpoint:
    """GET /api/collab/{doc_id}/presence — 获取文档在线用户。"""

    @pytest.mark.asyncio
    async def test_get_presence_empty(self, client):
        """无在线用户时返回空列表。"""
        resp = await client.get("/api/collab/test-doc/presence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["online_users"] == []
        assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_get_presence_returns_doc_id(self, client):
        """返回正确的 doc_id。"""
        resp = await client.get("/api/collab/my-doc-123/presence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["doc_id"] == "my-doc-123"

    @pytest.mark.asyncio
    async def test_get_presence_format(self, client):
        """验证返回格式包含 doc_id, online_users, count。"""
        resp = await client.get("/api/collab/format-test-doc/presence")
        assert resp.status_code == 200
        data = resp.json()
        assert "doc_id" in data
        assert "online_users" in data
        assert "count" in data
        assert isinstance(data["online_users"], list)
        assert isinstance(data["count"], int)


# ============================================================
# 2. _ws_authenticate 函数单元测试
# ============================================================

class TestWSAuthenticate:
    """_ws_authenticate 函数 — WebSocket 连接认证。"""

    @pytest.mark.asyncio
    async def test_ws_authenticate_valid_token(self):
        """有效 token 返回用户信息。"""
        token = AuthService.create_access_token(
            "user-001", "personal", extra={"display_name": "Alice"}
        )
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("collab.router.async_session", _MockAsyncSession(mock_db)):
            result = await _ws_authenticate(token, "doc-1")

        assert result["user_id"] == "user-001"
        assert result["display_name"] == "Alice"
        assert result["global_role"] == "personal"
        assert "doc_role" in result

    @pytest.mark.asyncio
    async def test_ws_authenticate_invalid_token(self):
        """无效 token 抛出 401。"""
        with pytest.raises(HTTPException) as exc_info:
            await _ws_authenticate("invalid.token.here", "doc-1")
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_ws_authenticate_missing_token(self):
        """空 token 抛出 401。"""
        with pytest.raises(HTTPException) as exc_info:
            await _ws_authenticate("", "doc-1")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_ws_authenticate_resolves_doc_role(self):
        """验证 doc_role 被正确解析。"""
        token = AuthService.create_access_token("user-002", "personal")

        with patch("collab.router._resolve_doc_role", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.return_value = "editor"
            result = await _ws_authenticate(token, "doc-1")

        assert result["doc_role"] == "editor"
        mock_resolve.assert_called_once_with("doc-1", "user-002")

    @pytest.mark.asyncio
    async def test_ws_authenticate_owner_role(self):
        """文档 owner 的 doc_role 为 'owner'。"""
        token = AuthService.create_access_token("owner-001", "personal")
        mock_db = AsyncMock()

        # 无权限记录，但文档 owner_id == user_id
        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = None
        mock_doc = MagicMock()
        mock_doc.owner_id = "owner-001"
        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = mock_doc
        mock_db.execute = AsyncMock(side_effect=[perm_result, doc_result])

        with patch("collab.router.async_session", _MockAsyncSession(mock_db)):
            result = await _ws_authenticate(token, "doc-1")

        assert result["doc_role"] == "owner"

    @pytest.mark.asyncio
    async def test_ws_authenticate_member_role(self):
        """文档成员的 doc_role 为其 effective_role。"""
        token = AuthService.create_access_token("member-001", "personal")
        mock_db = AsyncMock()

        # 有权限记录，effective_role = "editor"
        mock_perm = MagicMock()
        mock_perm.effective_role = "editor"
        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = mock_perm
        mock_db.execute = AsyncMock(return_value=perm_result)

        with patch("collab.router.async_session", _MockAsyncSession(mock_db)):
            result = await _ws_authenticate(token, "doc-1")

        assert result["doc_role"] == "editor"

    @pytest.mark.asyncio
    async def test_ws_authenticate_non_member_default_reader(self):
        """非成员默认 'reader'。"""
        token = AuthService.create_access_token("stranger-001", "personal")
        mock_db = AsyncMock()

        # 无权限记录，文档 owner_id != user_id
        perm_result = MagicMock()
        perm_result.scalar_one_or_none.return_value = None
        mock_doc = MagicMock()
        mock_doc.owner_id = "someone-else"
        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = mock_doc
        mock_db.execute = AsyncMock(side_effect=[perm_result, doc_result])

        with patch("collab.router.async_session", _MockAsyncSession(mock_db)):
            result = await _ws_authenticate(token, "doc-1")

        assert result["doc_role"] == "reader"


# ============================================================
# 3. ws_gateway 函数单元测试
# ============================================================

class TestWSGateway:
    """ws_gateway 函数 — WebSocket 消息网关。"""

    @pytest.mark.asyncio
    async def test_ws_gateway_broadcasts_user_joined(self):
        """连接时广播 user_joined 消息给房间内其他用户。"""
        # 设置已存在的其他用户
        other_ws = AsyncMock()
        rooms["doc-1"] = {other_ws}
        ws_users[id(other_ws)] = "other-user"

        websocket = _make_mock_websocket(messages=[])  # 立即断开
        current_user = _make_mock_user(user_id="new-user")

        await ws_gateway(websocket, "doc-1", current_user)

        # other_ws 应该收到 user_joined 消息
        other_calls = [c.args[0] for c in other_ws.send_json.call_args_list]
        join_msgs = [
            m for m in other_calls
            if m.get("payload", {}).get("event") == "user_joined"
        ]
        assert len(join_msgs) == 1
        assert join_msgs[0]["payload"]["user_id"] == "new-user"
        assert join_msgs[0]["type"] == WSMessageType.STATE_CHANGE.value

    @pytest.mark.asyncio
    async def test_ws_gateway_handles_ping(self):
        """PING 消息回复 PONG。"""
        websocket = _make_mock_websocket([
            json.dumps({"type": "ping"}),
        ])
        current_user = _make_mock_user()

        await ws_gateway(websocket, "doc-1", current_user)

        # 应该收到 PONG 响应
        sent = [c.args[0] for c in websocket.send_json.call_args_list]
        pong_msgs = [m for m in sent if m.get("type") == "pong"]
        assert len(pong_msgs) == 1
        assert pong_msgs[0]["doc_id"] == "doc-1"
        assert pong_msgs[0]["sender_id"] == "test-user-001"

    @pytest.mark.asyncio
    async def test_ws_gateway_broadcasts_message(self):
        """广播消息给房间内其他用户。"""
        other_ws = AsyncMock()
        rooms["doc-1"] = {other_ws}
        ws_users[id(other_ws)] = "other-user"

        websocket = _make_mock_websocket([
            json.dumps({"type": "state_change", "payload": {"event": "test-broadcast"}}),
        ])
        current_user = _make_mock_user(doc_role="owner", user_id="broadcaster")

        await ws_gateway(websocket, "doc-1", current_user)

        # other_ws 应该收到广播消息
        other_calls = [c.args[0] for c in other_ws.send_json.call_args_list]
        broadcast_msgs = [
            m for m in other_calls
            if m.get("payload", {}).get("event") == "test-broadcast"
        ]
        assert len(broadcast_msgs) == 1
        assert broadcast_msgs[0]["sender_id"] == "broadcaster"

    @pytest.mark.asyncio
    async def test_ws_gateway_rejects_unauthorized_message(self):
        """无权限消息被拒绝。"""
        websocket = _make_mock_websocket([
            json.dumps({"type": "state_change"}),
        ])
        current_user = _make_mock_user(doc_role="editor", user_id="editor-1")

        await ws_gateway(websocket, "doc-1", current_user)

        # 应该收到 ERROR 消息
        sent = [c.args[0] for c in websocket.send_json.call_args_list]
        error_msgs = [m for m in sent if m.get("type") == "ERROR"]
        assert len(error_msgs) == 1
        assert error_msgs[0]["payload"]["event"] == "unauthorized_message"

        # 应该被关闭，code=4003
        close_calls = websocket.close.call_args_list
        assert any(c.kwargs.get("code") == 4003 for c in close_calls)

    @pytest.mark.asyncio
    async def test_ws_gateway_rate_limits(self):
        """超过 60 msg/min 被限流。"""
        # 发送 70 条 PING 消息
        messages = [json.dumps({"type": "ping"}) for _ in range(70)]
        websocket = _make_mock_websocket(messages)
        current_user = _make_mock_user()

        await ws_gateway(websocket, "doc-1", current_user)

        sent = [c.args[0] for c in websocket.send_json.call_args_list]
        pong_msgs = [m for m in sent if m.get("type") == "pong"]
        rate_limited_msgs = [
            m for m in sent
            if m.get("type") == "ERROR" and m.get("payload", {}).get("event") == "rate_limited"
        ]

        # 前 60 条通过，后 10 条被限流
        assert len(pong_msgs) == 60
        assert len(rate_limited_msgs) == 10

    @pytest.mark.asyncio
    async def test_ws_gateway_cleans_up_on_disconnect(self):
        """断开时清理资源并广播 user_left。"""
        other_ws = AsyncMock()
        rooms["doc-1"] = {other_ws}
        ws_users[id(other_ws)] = "other-user"

        websocket = _make_mock_websocket(messages=[])  # 立即断开
        current_user = _make_mock_user(user_id="leaving-user")

        await ws_gateway(websocket, "doc-1", current_user)

        # websocket 应从 rooms 中移除
        assert websocket not in rooms.get("doc-1", set())

        # 应从 ws_users 和 ws_user_roles 中移除
        assert id(websocket) not in ws_users
        assert id(websocket) not in ws_user_roles

        # other_ws 应收到 user_left 消息
        other_calls = [c.args[0] for c in other_ws.send_json.call_args_list]
        left_msgs = [
            m for m in other_calls
            if m.get("payload", {}).get("event") == "user_left"
        ]
        assert len(left_msgs) == 1
        assert left_msgs[0]["payload"]["user_id"] == "leaving-user"


# ============================================================
# 4. WebSocket 消息权限矩阵集成测试
# ============================================================

class TestWSMessagePermissions:
    """WebSocket 消息发送权限矩阵 — 通过 ws_gateway 验证。"""

    @pytest.mark.asyncio
    async def test_editor_can_send_proposal_created(self):
        """editor 可发送 PROPOSAL_CREATED。"""
        result = await _run_gateway_with_message("editor", "proposal_created")
        assert result["accepted"] is True
        assert result["closed"] is False

    @pytest.mark.asyncio
    async def test_editor_cannot_send_state_change(self):
        """editor 不可发送 STATE_CHANGE。"""
        result = await _run_gateway_with_message("editor", "state_change")
        assert result["accepted"] is False
        assert result["closed"] is True

    @pytest.mark.asyncio
    async def test_reader_cannot_send_state_change(self):
        """reader 不可发送 STATE_CHANGE。"""
        result = await _run_gateway_with_message("reader", "state_change")
        assert result["accepted"] is False
        assert result["closed"] is True

    @pytest.mark.asyncio
    async def test_reader_cannot_send_proposal_created(self):
        """reader 不可发送 PROPOSAL_CREATED。"""
        result = await _run_gateway_with_message("reader", "proposal_created")
        assert result["accepted"] is False
        assert result["closed"] is True

    @pytest.mark.asyncio
    async def test_reviewer_can_send_conflict_detected(self):
        """reviewer 可发送 CONFLICT_DETECTED。"""
        result = await _run_gateway_with_message("reviewer", "conflict_detected")
        assert result["accepted"] is True
        assert result["closed"] is False

    @pytest.mark.asyncio
    async def test_case_insensitive_message_type(self):
        """消息类型大小写不敏感。"""
        # 大写 STATE_CHANGE 被 editor 拒绝
        result_upper = await _run_gateway_with_message("editor", "STATE_CHANGE")
        assert result_upper["accepted"] is False

        # 小写 state_change 被 editor 拒绝（行为一致）
        result_lower = await _run_gateway_with_message("editor", "state_change")
        assert result_lower["accepted"] is False

        # 混合大小写 State_Change 被 editor 拒绝（行为一致）
        result_mixed = await _run_gateway_with_message("editor", "State_Change")
        assert result_mixed["accepted"] is False

        # 小写 proposal_created 被 editor 接受（与大写行为一致）
        result_lower_ok = await _run_gateway_with_message("editor", "proposal_created")
        assert result_lower_ok["accepted"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
