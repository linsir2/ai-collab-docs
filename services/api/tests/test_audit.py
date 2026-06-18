"""审计模块完整测试 — 覆盖日志列表与 CSV 导出端点。"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from audit.models import OperationLog
from auth.models import DocumentPermission, UserCreate
from auth.service import AuthService
from document.models import Document


# ============================================================
# 公共 fixture
# ============================================================

@pytest.fixture(autouse=True)
def _clear_rate_limit_buckets():
    """每个测试前后清空限流桶，避免跨测试干扰。"""
    from shared.middleware import (
        _authenticated_buckets,
        _login_buckets,
        _unauthenticated_buckets,
        _ws_buckets,
    )

    _login_buckets.clear()
    _unauthenticated_buckets.clear()
    _authenticated_buckets.clear()
    _ws_buckets.clear()
    yield
    _login_buckets.clear()
    _unauthenticated_buckets.clear()
    _authenticated_buckets.clear()
    _ws_buckets.clear()


@pytest_asyncio.fixture
async def ops_headers(client, db_session):
    """创建 ops 全局角色用户并返回认证 headers。"""
    service = AuthService(db_session)
    await service.create_user(
        UserCreate(
            display_name="Ops User",
            email="ops@example.com",
            password="test123",
            role="owner",
            global_role="ops",
        ),
        requester_global_role="team_admin",
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "ops@example.com", "password": "test123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 辅助函数
# ============================================================

async def _get_user_id(client, headers):
    """通过 /api/auth/me 获取当前用户 user_id。"""
    resp = await client.get("/api/auth/me", headers=headers)
    return resp.json()["user_id"]


async def _create_doc_with_logs(
    db_session,
    owner_id,
    num_logs=3,
    action="create_document",
    doc_id=None,
    log_user_id=None,
    add_permission=True,
):
    """创建文档（含可选权限）和审计日志，提交后返回 doc_id。

    Parameters
    ----------
    owner_id : str  — 文档所有者（也是权限持有者）
    num_logs : int  — 生成的审计日志条数
    action   : str  — 审计动作
    doc_id   : str  — 指定 doc_id（为 None 则自动生成）
    log_user_id : str — 审计日志中的 user_id（默认同 owner_id）
    add_permission : bool — 是否为 owner_id 创建 DocumentPermission
    """
    if doc_id is None:
        doc_id = str(uuid.uuid4())

    doc = Document(
        doc_id=doc_id,
        title=f"Test Doc {doc_id[:8]}",
        state="draft",
        owner_id=owner_id,
        anchor_statement="anchor-statement",
        anchor_audience="all",
        anchor_argument="arg",
    )
    db_session.add(doc)

    if add_permission:
        perm = DocumentPermission(
            doc_id=doc_id,
            user_id=owner_id,
            effective_role="owner",
            invited_by=owner_id,
        )
        db_session.add(perm)

    log_user = log_user_id or owner_id
    base_time = datetime.now(timezone.utc)
    for i in range(num_logs):
        log = OperationLog(
            op_id=str(uuid.uuid4()),
            user_id=log_user,
            action=action,
            target_type="document",
            target_id=doc_id,
            doc_id=doc_id,
            before_state="" if i == 0 else "draft",
            after_state="draft" if i == 0 else "review",
            timestamp=base_time + timedelta(seconds=i),
        )
        db_session.add(log)

    await db_session.commit()
    return doc_id


# ============================================================
# TestListLogs
# ============================================================

class TestListLogs:
    """GET /api/audit/logs — 审计日志列表端点。"""

    @pytest.mark.asyncio
    async def test_list_logs_as_ops(self, client, ops_headers, db_session):
        """ops 用户可查看所有日志。"""
        await _create_doc_with_logs(db_session, "user-1", num_logs=2)
        await _create_doc_with_logs(db_session, "user-2", num_logs=3)

        resp = await client.get("/api/audit/logs", headers=ops_headers)
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 5

    @pytest.mark.asyncio
    async def test_list_logs_as_personal(self, client, auth_headers, db_session):
        """personal 用户只能查看参与文档的日志。"""
        user_id = await _get_user_id(client, auth_headers)

        # personal 用户参与的文档
        doc_id_member = await _create_doc_with_logs(db_session, user_id, num_logs=2)
        # personal 用户未参与的文档
        await _create_doc_with_logs(db_session, "other-user", num_logs=3, add_permission=True)

        resp = await client.get("/api/audit/logs", headers=auth_headers)
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 2
        for log in logs:
            assert log["doc_id"] == doc_id_member

    @pytest.mark.asyncio
    async def test_list_logs_filter_by_doc_id(self, client, ops_headers, db_session):
        """按 doc_id 过滤。"""
        doc_id_1 = await _create_doc_with_logs(db_session, "user-1", num_logs=2)
        await _create_doc_with_logs(db_session, "user-2", num_logs=3)

        resp = await client.get(
            f"/api/audit/logs?doc_id={doc_id_1}", headers=ops_headers
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 2
        for log in logs:
            assert log["doc_id"] == doc_id_1

    @pytest.mark.asyncio
    async def test_list_logs_filter_by_action(self, client, ops_headers, db_session):
        """按 action 过滤。"""
        await _create_doc_with_logs(
            db_session, "user-1", num_logs=2, action="create_document"
        )
        await _create_doc_with_logs(
            db_session, "user-2", num_logs=3, action="state_transition"
        )

        resp = await client.get(
            "/api/audit/logs?action=create_document", headers=ops_headers
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 2
        for log in logs:
            assert log["action"] == "create_document"

    @pytest.mark.asyncio
    async def test_list_logs_filter_by_user_id(self, client, ops_headers, db_session):
        """按 user_id 过滤。"""
        await _create_doc_with_logs(
            db_session, "user-1", num_logs=2, log_user_id="actor-a"
        )
        await _create_doc_with_logs(
            db_session, "user-2", num_logs=3, log_user_id="actor-b"
        )

        resp = await client.get(
            "/api/audit/logs?user_id=actor-a", headers=ops_headers
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 2
        for log in logs:
            assert log["user_id"] == "actor-a"

    @pytest.mark.asyncio
    async def test_list_logs_pagination(self, client, ops_headers, db_session):
        """分页测试（limit + offset）。"""
        await _create_doc_with_logs(db_session, "user-1", num_logs=5)

        # 第一页
        resp = await client.get(
            "/api/audit/logs?limit=2&offset=0", headers=ops_headers
        )
        assert resp.status_code == 200
        page1 = resp.json()
        assert len(page1) == 2

        # 第二页
        resp = await client.get(
            "/api/audit/logs?limit=2&offset=2", headers=ops_headers
        )
        assert resp.status_code == 200
        page2 = resp.json()
        assert len(page2) == 2

        # 第三页（只剩 1 条）
        resp = await client.get(
            "/api/audit/logs?limit=2&offset=4", headers=ops_headers
        )
        assert resp.status_code == 200
        page3 = resp.json()
        assert len(page3) == 1

        # 无重叠
        all_op_ids = {log["op_id"] for log in page1 + page2 + page3}
        assert len(all_op_ids) == 5

    @pytest.mark.asyncio
    async def test_list_logs_without_auth(self, client):
        """无认证返回 401。"""
        resp = await client.get("/api/audit/logs")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_logs_personal_no_access(self, client, auth_headers, db_session):
        """personal 用户不能查看未参与文档的日志（返回空列表）。"""
        doc_id_other = await _create_doc_with_logs(
            db_session, "other-user", num_logs=3
        )

        resp = await client.get(
            f"/api/audit/logs?doc_id={doc_id_other}", headers=auth_headers
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) == 0


# ============================================================
# TestExportLogs
# ============================================================

class TestExportLogs:
    """GET /api/audit/logs/export — 审计日志 CSV 导出端点。"""

    @pytest.mark.asyncio
    async def test_export_logs_success(self, client, auth_headers, db_session):
        """成功导出 CSV。"""
        user_id = await _get_user_id(client, auth_headers)
        doc_id = await _create_doc_with_logs(db_session, user_id, num_logs=3)

        resp = await client.get(
            f"/api/audit/logs/export?doc_id={doc_id}", headers=auth_headers
        )
        assert resp.status_code == 200
        lines = resp.text.strip().splitlines()
        # 表头 + 3 条数据行
        assert len(lines) == 4

    @pytest.mark.asyncio
    async def test_export_logs_as_ops(self, client, ops_headers, db_session):
        """ops 用户可导出任意文档。"""
        doc_id = await _create_doc_with_logs(db_session, "some-user", num_logs=2)

        resp = await client.get(
            f"/api/audit/logs/export?doc_id={doc_id}", headers=ops_headers
        )
        assert resp.status_code == 200
        lines = resp.text.strip().splitlines()
        # 表头 + 2 条数据行
        assert len(lines) == 3

    @pytest.mark.asyncio
    async def test_export_logs_personal_no_access(self, client, auth_headers, db_session):
        """personal 用户不能导出未参与文档的日志返回 403。"""
        doc_id_other = await _create_doc_with_logs(
            db_session, "other-user", num_logs=2
        )

        resp = await client.get(
            f"/api/audit/logs/export?doc_id={doc_id_other}", headers=auth_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_export_logs_format(self, client, ops_headers, db_session):
        """验证 CSV 格式包含表头。"""
        doc_id = await _create_doc_with_logs(db_session, "some-user", num_logs=1)

        resp = await client.get(
            f"/api/audit/logs/export?doc_id={doc_id}", headers=ops_headers
        )
        assert resp.status_code == 200
        lines = resp.text.strip().splitlines()
        header = lines[0]
        assert "op_id" in header
        assert "user_id" in header
        assert "action" in header
        assert "target_type" in header
        assert "target_id" in header
        assert "doc_id" in header
        assert "before_state" in header
        assert "after_state" in header
        assert "timestamp" in header
