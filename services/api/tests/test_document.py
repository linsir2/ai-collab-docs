import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

import main  # noqa: F401  导入 main 以注册所有模型到 Base.metadata
import pytest

from document.service import DocumentService
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
    return resp.json()


async def _add_member(client, owner_headers, doc_id, user_id, role):
    """添加文档成员。"""
    resp = await client.post(f"/api/auth/docs/{doc_id}/members", json={
        "user_id": user_id,
        "role": role,
    }, headers=owner_headers)
    return resp


# ============================================================
# 文档创建
# ============================================================

class TestDocumentCreate:
    """POST /api/documents — 创建文档。"""

    @pytest.mark.asyncio
    async def test_create_document_success(self, client, auth_headers):
        resp = await client.post("/api/documents", json={
            "title": "测试文档",
            "anchor_statement": "锚点声明",
            "anchor_audience": "目标读者",
            "anchor_argument": "核心论点",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["doc_id"]
        assert data["title"] == "测试文档"
        assert data["state"] == "draft"
        assert data["owner_id"]
        assert data["anchor_statement"] == "锚点声明"
        assert data["anchor_audience"] == "目标读者"
        assert data["anchor_argument"] == "核心论点"
        assert data["anchor_version"] == 1
        assert data["anchor_history"] == "[]"
        assert data["id"]
        assert data["created_at"]
        assert data["updated_at"]

    @pytest.mark.asyncio
    async def test_create_document_without_auth(self, client):
        resp = await client.post("/api/documents", json={
            "title": "测试文档",
            "anchor_statement": "锚点声明",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_document_owner_is_current_user(self, client, auth_headers):
        me = await client.get("/api/auth/me", headers=auth_headers)
        user_id = me.json()["user_id"]
        resp = await client.post("/api/documents", json={
            "title": "测试文档",
            "anchor_statement": "锚点声明",
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["owner_id"] == user_id


# ============================================================
# 文档列表
# ============================================================

class TestDocumentList:
    """GET /api/documents — 列出文档。"""

    @pytest.mark.asyncio
    async def test_list_documents_success(self, client, auth_headers):
        await _create_document(client, auth_headers)
        resp = await client.get("/api/documents", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_list_documents_without_auth(self, client):
        resp = await client.get("/api/documents")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_documents_returns_all(self, client, auth_headers):
        for i in range(3):
            await _create_document(client, auth_headers, title=f"文档{i}")
        resp = await client.get("/api/documents", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 3


# ============================================================
# 获取单个文档
# ============================================================

class TestDocumentGet:
    """GET /api/documents/{doc_id} — 获取单个文档。"""

    @pytest.mark.asyncio
    async def test_get_document_success(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.get(f"/api/documents/{doc['doc_id']}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["doc_id"] == doc["doc_id"]
        assert data["title"] == "测试文档"
        assert data["state"] == "draft"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, client, auth_headers):
        resp = await client.get("/api/documents/non-existent-id", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_without_auth(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.get(f"/api/documents/{doc['doc_id']}")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_document_as_reader(self, client, auth_headers):
        """reader 角色拥有 discuss 权限，可以获取文档。"""
        doc = await _create_document(client, auth_headers)
        reader_headers, reader_id = await _register_user(
            client, "reader@example.com", role="reader"
        )
        await _add_member(client, auth_headers, doc["doc_id"], reader_id, "reader")
        resp = await client.get(f"/api/documents/{doc['doc_id']}", headers=reader_headers)
        assert resp.status_code == 200
        assert resp.json()["doc_id"] == doc["doc_id"]


# ============================================================
# 获取用户在文档中的角色
# ============================================================

class TestDocumentMyRole:
    """GET /api/documents/{doc_id}/me — 获取用户在文档中的角色。"""

    @pytest.mark.asyncio
    async def test_get_my_role_as_owner(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.get(f"/api/documents/{doc['doc_id']}/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["doc_role"] == "owner"
        assert data["doc_id"] == doc["doc_id"]

    @pytest.mark.asyncio
    async def test_get_my_role_as_editor(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        editor_headers, editor_id = await _register_user(
            client, "editor@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], editor_id, "editor")
        resp = await client.get(f"/api/documents/{doc['doc_id']}/me", headers=editor_headers)
        assert resp.status_code == 200
        assert resp.json()["doc_role"] == "editor"

    @pytest.mark.asyncio
    async def test_get_my_role_as_reader(self, client, auth_headers):
        """未被添加为成员的用户默认返回 reader。"""
        doc = await _create_document(client, auth_headers)
        other_headers, _ = await _register_user(
            client, "other@example.com", role="editor"
        )
        resp = await client.get(f"/api/documents/{doc['doc_id']}/me", headers=other_headers)
        assert resp.status_code == 200
        assert resp.json()["doc_role"] == "reader"

    @pytest.mark.asyncio
    async def test_get_my_role_document_not_found(self, client, auth_headers):
        resp = await client.get("/api/documents/non-existent-id/me", headers=auth_headers)
        assert resp.status_code == 404


# ============================================================
# 块元数据
# ============================================================

class TestBlockMeta:
    """PUT /api/documents/{doc_id}/blocks/{block_id}/meta
       GET /api/documents/{doc_id}/blocks — 块元数据操作。"""

    @pytest.mark.asyncio
    async def test_update_block_meta_success(self, client, auth_headers, db_session):
        doc = await _create_document(client, auth_headers)
        service = DocumentService(db_session)
        await service.create_block_meta(doc["doc_id"], "block-1", 0)
        resp = await client.put(
            f"/api/documents/{doc['doc_id']}/blocks/block-1/meta",
            json={
                "tags": '["locked"]',
                "claimant_id": "u1",
                "drift_score": 0.5,
                "locked_by": "u1",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["block_id"] == "block-1"
        assert data["doc_id"] == doc["doc_id"]
        assert data["tags"] == '["locked"]'
        assert data["claimant_id"] == "u1"
        assert data["drift_score"] == 0.5
        assert data["locked_by"] == "u1"

    @pytest.mark.asyncio
    async def test_update_block_meta_not_found(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.put(
            f"/api/documents/{doc['doc_id']}/blocks/non-existent/meta",
            json={"tags": "[]"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_block_meta_without_discuss_permission(self, client, auth_headers):
        """discuss 权限对所有角色开放，无认证时返回 401。"""
        doc = await _create_document(client, auth_headers)
        resp = await client.put(
            f"/api/documents/{doc['doc_id']}/blocks/block-1/meta",
            json={"tags": "[]"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_block_metas(self, client, auth_headers, db_session):
        doc = await _create_document(client, auth_headers)
        service = DocumentService(db_session)
        await service.create_block_meta(doc["doc_id"], "block-1", 1)
        await service.create_block_meta(doc["doc_id"], "block-2", 0)
        resp = await client.get(f"/api/documents/{doc['doc_id']}/blocks", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # 按 sort_order 排序：block-2 (0) 在前，block-1 (1) 在后
        assert data[0]["block_id"] == "block-2"
        assert data[1]["block_id"] == "block-1"

    @pytest.mark.asyncio
    async def test_list_block_metas_empty(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.get(f"/api/documents/{doc['doc_id']}/blocks", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []


# ============================================================
# 块认领
# ============================================================

class TestBlockClaim:
    """POST /api/documents/{doc_id}/blocks/{block_id}/claim — 认领块。"""

    @pytest.mark.asyncio
    async def test_claim_block_success(self, client, auth_headers, db_session):
        doc = await _create_document(client, auth_headers)
        service = DocumentService(db_session)
        await service.create_block_meta(doc["doc_id"], "block-1", 0)
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/blocks/block-1/claim",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["block_id"] == "block-1"
        assert data["claimant_id"]

    @pytest.mark.asyncio
    async def test_claim_block_not_found(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/blocks/non-existent/claim",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_claim_block_by_reader(self, client, auth_headers, db_session):
        """reader 不在 claim_paragraph 权限中，返回 403。"""
        doc = await _create_document(client, auth_headers)
        service = DocumentService(db_session)
        await service.create_block_meta(doc["doc_id"], "block-1", 0)
        reader_headers, reader_id = await _register_user(
            client, "reader@example.com", role="reader"
        )
        await _add_member(client, auth_headers, doc["doc_id"], reader_id, "reader")
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/blocks/block-1/claim",
            headers=reader_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_claim_block_by_editor(self, client, auth_headers, db_session):
        """editor 在 claim_paragraph 权限中，可以认领。"""
        doc = await _create_document(client, auth_headers)
        service = DocumentService(db_session)
        await service.create_block_meta(doc["doc_id"], "block-1", 0)
        editor_headers, editor_id = await _register_user(
            client, "editor@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], editor_id, "editor")
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/blocks/block-1/claim",
            headers=editor_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["claimant_id"] == editor_id


# ============================================================
# 状态流转
# ============================================================

class TestStateTransition:
    """POST /api/documents/{doc_id}/transition — 状态流转。"""

    @pytest.mark.asyncio
    async def test_transition_document_success(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/transition",
            json={"to_state": "discussion"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "discussion"

    @pytest.mark.asyncio
    async def test_transition_by_editor(self, client, auth_headers):
        """editor 不在 state_transition 权限中，返回 403。"""
        doc = await _create_document(client, auth_headers)
        editor_headers, editor_id = await _register_user(
            client, "editor@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], editor_id, "editor")
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/transition",
            json={"to_state": "discussion"},
            headers=editor_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_transition_by_reader(self, client, auth_headers):
        """reader 不在 state_transition 权限中，返回 403。"""
        doc = await _create_document(client, auth_headers)
        reader_headers, reader_id = await _register_user(
            client, "reader@example.com", role="reader"
        )
        await _add_member(client, auth_headers, doc["doc_id"], reader_id, "reader")
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/transition",
            json={"to_state": "discussion"},
            headers=reader_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_transition_document_not_found(self, client, auth_headers):
        """不存在的文档：权限检查先于存在性检查，reader 无 state_transition 权限，返回 403。"""
        resp = await client.post(
            "/api/documents/non-existent-id/transition",
            json={"to_state": "discussion"},
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ============================================================
# 归档
# ============================================================

class TestArchive:
    """POST /api/documents/{doc_id}/archive — 归档文档。"""

    @pytest.mark.asyncio
    async def test_archive_document_success(self, client, auth_headers):
        doc = await _create_document(client, auth_headers)
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/archive",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["doc_id"] == doc["doc_id"]

    @pytest.mark.asyncio
    async def test_archive_by_editor(self, client, auth_headers):
        """editor 不在 archive 权限中，返回 403。"""
        doc = await _create_document(client, auth_headers)
        editor_headers, editor_id = await _register_user(
            client, "editor@example.com", role="editor"
        )
        await _add_member(client, auth_headers, doc["doc_id"], editor_id, "editor")
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/archive",
            headers=editor_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_archive_by_reader(self, client, auth_headers):
        """reader 不在 archive 权限中，返回 403。"""
        doc = await _create_document(client, auth_headers)
        reader_headers, reader_id = await _register_user(
            client, "reader@example.com", role="reader"
        )
        await _add_member(client, auth_headers, doc["doc_id"], reader_id, "reader")
        resp = await client.post(
            f"/api/documents/{doc['doc_id']}/archive",
            headers=reader_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_archive_document_not_found(self, client, auth_headers):
        """不存在的文档：权限检查先于存在性检查，reader 无 archive 权限，返回 403。"""
        resp = await client.post(
            "/api/documents/non-existent-id/archive",
            headers=auth_headers,
        )
        assert resp.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
