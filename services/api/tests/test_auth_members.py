import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

import main  # noqa: F401  导入 main 以注册所有模型到 Base.metadata
import pytest

from shared.middleware import (
    _authenticated_buckets,
    _login_buckets,
    _unauthenticated_buckets,
    _ws_buckets,
)


# ============================================================
# 辅助函数
# ============================================================

@pytest.fixture(autouse=True)
def _clear_rate_limits():
    """每个测试前后清除速率限制桶，避免测试间相互影响。"""
    _login_buckets.clear()
    _unauthenticated_buckets.clear()
    _authenticated_buckets.clear()
    _ws_buckets.clear()
    yield
    _login_buckets.clear()
    _unauthenticated_buckets.clear()
    _authenticated_buckets.clear()
    _ws_buckets.clear()


async def _register_user(client, email, password="test123", role="editor"):
    """注册并登录用户，返回 (headers, user_id)。"""
    reg_resp = await client.post("/api/auth/register", json={
        "display_name": email.split("@")[0],
        "email": email,
        "password": password,
        "role": role,
    })
    assert reg_resp.status_code == 201, f"注册失败: {reg_resp.status_code} {reg_resp.text}"
    resp = await client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert resp.status_code == 200, f"登录失败: {resp.status_code} {resp.text}"
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = await client.get("/api/auth/me", headers=headers)
    user_id = me.json()["user_id"]
    return headers, user_id


async def _create_document(client, headers, title="测试文档"):
    """创建文档，返回响应数据。"""
    resp = await client.post("/api/documents", json={
        "title": title,
        "anchor_statement": "锚点声明",
        "anchor_audience": "目标读者",
        "anchor_argument": "核心论点",
    }, headers=headers)
    assert resp.status_code == 201, f"创建文档失败: {resp.status_code} {resp.text}"
    return resp.json()


async def _add_member(client, owner_headers, doc_id, user_id, role):
    """添加文档成员。"""
    resp = await client.post(f"/api/auth/docs/{doc_id}/members", json={
        "user_id": user_id,
        "role": role,
    }, headers=owner_headers)
    return resp


# ============================================================
# 添加成员
# ============================================================

class TestAddMember:
    """POST /api/auth/docs/{doc_id}/members - 添加文档成员。"""

    @pytest.mark.asyncio
    async def test_add_member_success(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        resp = await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_add_member_without_auth(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        resp = await client.post(f"/api/auth/docs/{doc['doc_id']}/members", json={
            "user_id": member_id,
            "role": "editor",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_add_member_multiple_roles(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        roles = ["editor", "reviewer", "reader", "lead_editor"]
        for i, role in enumerate(roles):
            _, member_id = await _register_user(
                client, f"member{i}@example.com", role="editor"
            )
            resp = await _add_member(client, auth_headers, doc["doc_id"], member_id, role)
            assert resp.status_code == 200, f"添加 {role} 失败: {resp.status_code} {resp.text}"

    @pytest.mark.asyncio
    async def test_add_member_updates_existing(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        # 先添加为 reader
        resp1 = await _add_member(client, auth_headers, doc["doc_id"], member_id, "reader")
        assert resp1.status_code == 200
        # 再添加为 editor（更新角色）
        resp2 = await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        assert resp2.status_code == 200
        # 验证列表中包含 editor 角色的记录
        list_resp = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        assert list_resp.status_code == 200
        members = list_resp.json()["members"]
        roles = [m["role"] for m in members if m["user_id"] == member_id]
        assert "editor" in roles

    @pytest.mark.asyncio
    async def test_add_member_returns_ok(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        resp = await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ============================================================
# 列出成员
# ============================================================

class TestListMembers:
    """GET /api/auth/docs/{doc_id}/members - 列出文档成员。"""

    @pytest.mark.asyncio
    async def test_list_members_success(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        assert resp.status_code == 200
        assert "members" in resp.json()

    @pytest.mark.asyncio
    async def test_list_members_without_auth(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.get(f"/api/auth/docs/{doc['doc_id']}/members")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_members_empty(self, client, auth_headers):
        """文档刚创建，owner 不在 members 列表中。"""
        doc = await _create_document(client, auth_headers)
        resp = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["members"] == []

    @pytest.mark.asyncio
    async def test_list_members_includes_added_members(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        resp = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        assert resp.status_code == 200
        members = resp.json()["members"]
        assert any(m["user_id"] == member_id for m in members)

    @pytest.mark.asyncio
    async def test_list_members_correct_fields(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        resp = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        assert resp.status_code == 200
        members = resp.json()["members"]
        assert len(members) >= 1
        member = members[0]
        assert "user_id" in member
        assert "display_name" in member
        assert "email" in member
        assert "role" in member
        assert "joined_at" in member
        assert "invited_by" in member

    @pytest.mark.asyncio
    async def test_list_members_invited_by_correct(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        owner_me = await client.get("/api/auth/me", headers=auth_headers)
        owner_id = owner_me.json()["user_id"]
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        resp = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        assert resp.status_code == 200
        members = resp.json()["members"]
        member = next(m for m in members if m["user_id"] == member_id)
        assert member["invited_by"] == owner_id


# ============================================================
# 成员角色场景
# ============================================================

class TestMemberRoleScenarios:
    """成员角色相关场景测试。"""

    @pytest.mark.asyncio
    async def test_add_editor_then_list(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        resp = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        assert resp.status_code == 200
        members = resp.json()["members"]
        member = next(m for m in members if m["user_id"] == member_id)
        assert member["role"] == "editor"

    @pytest.mark.asyncio
    async def test_add_reader_then_upgrade_to_editor(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        _, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        # 先添加为 reader
        await _add_member(client, auth_headers, doc["doc_id"], member_id, "reader")
        list_resp1 = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        members1 = list_resp1.json()["members"]
        roles1 = [m["role"] for m in members1 if m["user_id"] == member_id]
        assert "reader" in roles1
        # 再更新为 editor
        await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        list_resp2 = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        members2 = list_resp2.json()["members"]
        # 验证列表中包含 editor 角色的记录
        roles2 = [m["role"] for m in members2 if m["user_id"] == member_id]
        assert "editor" in roles2

    @pytest.mark.asyncio
    async def test_add_multiple_members(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        member_ids = []
        for i in range(3):
            _, member_id = await _register_user(
                client, f"member{i}@example.com", role="editor"
            )
            await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
            member_ids.append(member_id)
        resp = await client.get(
            f"/api/auth/docs/{doc['doc_id']}/members", headers=auth_headers
        )
        assert resp.status_code == 200
        members = resp.json()["members"]
        member_user_ids = {m["user_id"] for m in members}
        for mid in member_ids:
            assert mid in member_user_ids

    @pytest.mark.asyncio
    async def test_member_can_access_document(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        member_headers, member_id = await _register_user(
            client, "member@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], member_id, "editor")
        resp = await client.get(f"/api/documents/{doc['doc_id']}", headers=member_headers)
        assert resp.status_code == 200
        assert resp.json()["doc_id"] == doc["doc_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
