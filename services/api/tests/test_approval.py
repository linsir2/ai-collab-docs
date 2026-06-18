"""审批/审查模块集成测试。

覆盖端点（前缀 /api/review）：
- POST /{doc_id}/start - 启动审查
- GET /{doc_id}/session - 获取审查会话
- PUT /proposals/{prop_id}/approve - 审批提案
- GET /{doc_id}/arbitrations - 列出仲裁
- POST /arbitrations/{arb_id}/resolve - 解决仲裁
- POST /{doc_id}/complete - 完成审查
"""

import pytest

# 导入所有模型，确保 Base.metadata 在 setup_database 创建表之前已注册全部表
import main  # noqa: F401
from approval.service import ApprovalService
from audit.service import AuditService
from contracts.contracts import (
    ApprovalAction,
    ArbitrationResolution,
    ConflictType,
    DocumentState,
    ProposalStatus,
)
from shared.middleware import (
    _authenticated_buckets,
    _login_buckets,
    _unauthenticated_buckets,
    _ws_buckets,
)


@pytest.fixture(autouse=True)
def _clear_rate_limit_buckets():
    """每个测试前后清空限流桶，避免跨测试累积触发限流（30 次/分钟登录限制）。"""
    _unauthenticated_buckets.clear()
    _authenticated_buckets.clear()
    _login_buckets.clear()
    _ws_buckets.clear()
    yield
    _unauthenticated_buckets.clear()
    _authenticated_buckets.clear()
    _login_buckets.clear()
    _ws_buckets.clear()


# ============================================================
# 辅助函数
# ============================================================


async def _create_document(client, headers, title="测试文档", anchor="测试锚点声明"):
    """创建文档并返回 doc_id。"""
    resp = await client.post(
        "/api/documents",
        json={
            "title": title,
            "anchor_statement": anchor,
            "anchor_audience": "测试团队",
            "anchor_argument": "测试论点",
        },
        headers=headers,
    )
    return resp.json()["doc_id"]


async def _transition_document(client, headers, doc_id, to_state):
    """流转文档状态。"""
    return await client.post(
        f"/api/documents/{doc_id}/transition",
        json={"to_state": to_state},
        headers=headers,
    )


async def _create_proposal(
    client,
    headers,
    doc_id,
    block_id="block_001",
    instruction="优化安全相关表述",
    ai_source="doc_ai:TechReviewer",
):
    """创建 AI 提案并返回 proposal_id。"""
    resp = await client.post(
        "/api/forge/refine",
        json={
            "doc_id": doc_id,
            "block_id": block_id,
            "instruction": instruction,
            "ai_source": ai_source,
        },
        headers=headers,
    )
    return resp.json()["proposal_id"]


async def _get_user_id(client, headers):
    """获取当前登录用户的 user_id。"""
    me = await client.get("/api/auth/me", headers=headers)
    return me.json()["user_id"]


async def _start_review(client, headers, doc_id):
    """启动审查并返回响应。"""
    user_id = await _get_user_id(client, headers)
    return await client.post(
        f"/api/review/{doc_id}/start",
        json={"user_id": user_id},
        headers=headers,
    )


async def _register_user(client, email, password="test123", role="editor"):
    """注册用户并返回 (user_id, headers)。"""
    resp = await client.post(
        "/api/auth/register",
        json={
            "display_name": email.split("@")[0],
            "email": email,
            "password": password,
            "role": role,
        },
    )
    user_id = resp.json()["user_id"]
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


async def _add_doc_member(client, owner_headers, doc_id, user_id, role):
    """添加文档成员。"""
    return await client.post(
        f"/api/auth/docs/{doc_id}/members",
        json={"user_id": user_id, "role": role},
        headers=owner_headers,
    )


async def _create_user_with_doc_role(client, owner_headers, doc_id, email, role):
    """注册用户、添加为文档成员、登录，返回 (user_id, headers)。"""
    user_id, headers = await _register_user(client, email, role=role)
    await _add_doc_member(client, owner_headers, doc_id, user_id, role)
    return user_id, headers


async def _create_arbitration(
    db_session,
    doc_id,
    block_id,
    proposal_ids,
    ai_sources,
    conflict_type=ConflictType.PURE_DOC_AI.value,
    claimant_id="",
):
    """通过 ApprovalService 直接创建仲裁记录并提交。"""
    service = ApprovalService(db_session, audit_service=AuditService(db_session))
    arbitration = await service.create_arbitration(
        doc_id=doc_id,
        block_id=block_id,
        conflict_type=conflict_type,
        proposals=proposal_ids,
        ai_sources=ai_sources,
        claimant_id=claimant_id,
    )
    await db_session.commit()
    return arbitration


async def _setup_doc_in_discussion(client, headers, title="审查测试文档"):
    """创建文档并流转到 discussion 状态，返回 doc_id。"""
    doc_id = await _create_document(client, headers, title=title)
    await _transition_document(client, headers, doc_id, DocumentState.DISCUSSION.value)
    return doc_id


async def _setup_doc_with_review(client, headers, title="审查测试文档"):
    """创建文档、流转到 discussion、启动审查，返回 (doc_id, session_json)。"""
    doc_id = await _setup_doc_in_discussion(client, headers, title=title)
    review_resp = await _start_review(client, headers, doc_id)
    return doc_id, review_resp.json()


async def _get_proposal_status(client, headers, doc_id, proposal_id):
    """查询指定提案的当前状态。"""
    resp = await client.get(
        f"/api/forge/proposals?doc_id={doc_id}",
        headers=headers,
    )
    for p in resp.json():
        if p["proposal_id"] == proposal_id:
            return p["status"]
    return None


# ============================================================
# TestStartReview
# ============================================================


class TestStartReview:
    """启动审查端点测试。"""

    @pytest.mark.asyncio
    async def test_start_review_success(self, client, auth_headers):
        """文档在 discussion 状态下成功启动审查。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        resp = await _start_review(client, auth_headers, doc_id)
        assert resp.status_code == 200
        data = resp.json()
        assert data["doc_id"] == doc_id
        assert data["status"] == "active"
        assert "session_id" in data
        assert "snapshot_id" in data

    @pytest.mark.asyncio
    async def test_start_review_wrong_state(self, client, auth_headers):
        """文档在 draft 状态下启动审查返回 400。"""
        doc_id = await _create_document(client, auth_headers, title="草稿文档")
        resp = await _start_review(client, auth_headers, doc_id)
        assert resp.status_code == 400
        assert "draft" in resp.json()["detail"].lower() or "state" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_start_review_by_reader(self, client, auth_headers):
        """reader 无 start_review 权限返回 403。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        _, reader_headers = await _create_user_with_doc_role(
            client, auth_headers, doc_id, "reader@example.com", "reader"
        )
        resp = await _start_review(client, reader_headers, doc_id)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_start_review_by_editor(self, client, auth_headers):
        """editor 无 start_review 权限返回 403。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        _, editor_headers = await _create_user_with_doc_role(
            client, auth_headers, doc_id, "editor@example.com", "editor"
        )
        resp = await _start_review(client, editor_headers, doc_id)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_start_review_by_reviewer(self, client, auth_headers):
        """reviewer 有 start_review 权限可以启动。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        _, reviewer_headers = await _create_user_with_doc_role(
            client, auth_headers, doc_id, "reviewer@example.com", "reviewer"
        )
        resp = await _start_review(client, reviewer_headers, doc_id)
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_start_review_without_auth(self, client, auth_headers):
        """无认证返回 401。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        resp = await client.post(
            f"/api/review/{doc_id}/start",
            json={"user_id": "any"},
        )
        assert resp.status_code == 401


# ============================================================
# TestGetReviewSession
# ============================================================


class TestGetReviewSession:
    """获取审查会话端点测试。"""

    @pytest.mark.asyncio
    async def test_get_review_session_success(self, client, auth_headers):
        """获取审查会话。"""
        doc_id, session = await _setup_doc_with_review(client, auth_headers)
        resp = await client.get(
            f"/api/review/{doc_id}/session",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None
        assert data["doc_id"] == doc_id
        assert data["session_id"] == session["session_id"]

    @pytest.mark.asyncio
    async def test_get_review_session_none(self, client, auth_headers):
        """无审查会话时返回 null。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        resp = await client.get(
            f"/api/review/{doc_id}/session",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() is None

    @pytest.mark.asyncio
    async def test_get_review_session_without_permission(self, client, auth_headers):
        """无认证访问返回 401。

        注：discuss 权限对所有文档角色（含 reader）开放，
        因此持有有效令牌的任意文档成员均可访问；
        此处验证未认证请求被拒绝。
        """
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        resp = await client.get(f"/api/review/{doc_id}/session")
        assert resp.status_code == 401


# ============================================================
# TestApproveProposal
# ============================================================


class TestApproveProposal:
    """审批提案端点测试。"""

    @pytest.mark.asyncio
    async def test_approve_proposal_merge_all(self, client, auth_headers):
        """merge_all 操作将提案状态改为 accepted。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        prop_id = await _create_proposal(client, auth_headers, doc_id)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.put(
            f"/api/review/proposals/{prop_id}/approve",
            json={"action": ApprovalAction.MERGE_ALL.value, "user_id": user_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == ProposalStatus.ACCEPTED.value
        assert data["action"] == ApprovalAction.MERGE_ALL.value

    @pytest.mark.asyncio
    async def test_approve_proposal_reject_annotate(self, client, auth_headers):
        """reject_annotate 操作将提案状态改为 rejected。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        prop_id = await _create_proposal(client, auth_headers, doc_id)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.put(
            f"/api/review/proposals/{prop_id}/approve",
            json={"action": ApprovalAction.REJECT_ANNOTATE.value, "user_id": user_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == ProposalStatus.REJECTED.value

    @pytest.mark.asyncio
    async def test_approve_proposal_manual_edit(self, client, auth_headers):
        """manual_edit 操作将提案状态改为 rejected。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        prop_id = await _create_proposal(client, auth_headers, doc_id)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.put(
            f"/api/review/proposals/{prop_id}/approve",
            json={"action": ApprovalAction.MANUAL_EDIT.value, "user_id": user_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == ProposalStatus.REJECTED.value

    @pytest.mark.asyncio
    async def test_approve_proposal_not_found(self, client, auth_headers):
        """不存在的提案返回 400。"""
        user_id = await _get_user_id(client, auth_headers)
        resp = await client.put(
            "/api/review/proposals/non-existent-prop-id/approve",
            json={"action": ApprovalAction.MERGE_ALL.value, "user_id": user_id},
            headers=auth_headers,
        )
        assert resp.status_code == 400


# ============================================================
# TestListArbitrations
# ============================================================


class TestListArbitrations:
    """列出仲裁端点测试。"""

    @pytest.mark.asyncio
    async def test_list_arbitrations_success(self, client, auth_headers, db_session):
        """列出仲裁。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        prop_a = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_001",
            instruction="扩充安全架构描述", ai_source="doc_ai:TechReviewer",
        )
        prop_b = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_001",
            instruction="精简技术细节", ai_source="doc_ai:LegalAgent",
        )
        await _create_arbitration(
            db_session, doc_id, "block_001", [prop_a, prop_b],
            ["doc_ai:TechReviewer", "doc_ai:LegalAgent"],
        )

        resp = await client.get(
            f"/api/review/{doc_id}/arbitrations",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["doc_id"] == doc_id

    @pytest.mark.asyncio
    async def test_list_arbitrations_empty(self, client, auth_headers):
        """无仲裁时返回空列表。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        resp = await client.get(
            f"/api/review/{doc_id}/arbitrations",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_arbitrations_filter_pending(self, client, auth_headers, db_session):
        """按 pending 过滤。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        prop_a = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_001",
            ai_source="doc_ai:TechReviewer",
        )
        prop_b = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_001",
            ai_source="doc_ai:LegalAgent",
        )
        prop_c = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_002",
            ai_source="doc_ai:TechReviewer",
        )
        prop_d = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_002",
            ai_source="doc_ai:LegalAgent",
        )

        # 创建两个仲裁：一个 pending，一个已解决
        arb_pending = await _create_arbitration(
            db_session, doc_id, "block_001", [prop_a, prop_b],
            ["doc_ai:TechReviewer", "doc_ai:LegalAgent"],
        )
        arb_resolved = await _create_arbitration(
            db_session, doc_id, "block_002", [prop_c, prop_d],
            ["doc_ai:TechReviewer", "doc_ai:LegalAgent"],
        )
        # 解决第二个仲裁
        service = ApprovalService(db_session, audit_service=AuditService(db_session))
        user_id = await _get_user_id(client, auth_headers)
        await service.resolve_arbitration(
            arb_resolved.arb_id,
            ArbitrationResolution.PROPOSAL_A.value,
            user_id,
            "测试解决原因",
        )
        await db_session.commit()

        resp = await client.get(
            f"/api/review/{doc_id}/arbitrations?status_filter=pending",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["arb_id"] == arb_pending.arb_id
        assert data[0]["resolution"] is None

    @pytest.mark.asyncio
    async def test_list_arbitrations_filter_resolved(self, client, auth_headers, db_session):
        """按 resolved 过滤。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        prop_a = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_001",
            ai_source="doc_ai:TechReviewer",
        )
        prop_b = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_001",
            ai_source="doc_ai:LegalAgent",
        )
        prop_c = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_002",
            ai_source="doc_ai:TechReviewer",
        )
        prop_d = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_002",
            ai_source="doc_ai:LegalAgent",
        )

        arb_pending = await _create_arbitration(
            db_session, doc_id, "block_001", [prop_a, prop_b],
            ["doc_ai:TechReviewer", "doc_ai:LegalAgent"],
        )
        arb_resolved = await _create_arbitration(
            db_session, doc_id, "block_002", [prop_c, prop_d],
            ["doc_ai:TechReviewer", "doc_ai:LegalAgent"],
        )
        service = ApprovalService(db_session, audit_service=AuditService(db_session))
        user_id = await _get_user_id(client, auth_headers)
        await service.resolve_arbitration(
            arb_resolved.arb_id,
            ArbitrationResolution.PROPOSAL_A.value,
            user_id,
            "测试解决原因",
        )
        await db_session.commit()

        resp = await client.get(
            f"/api/review/{doc_id}/arbitrations?status_filter=resolved",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["arb_id"] == arb_resolved.arb_id
        assert data[0]["resolution"] is not None


# ============================================================
# TestResolveArbitration
# ============================================================


class TestResolveArbitration:
    """解决仲裁端点测试。"""

    async def _setup_arbitration(self, client, auth_headers, db_session):
        """创建带两个提案的仲裁记录，返回 (doc_id, arb, prop_a_id, prop_b_id)。

        注：resolve_arbitration 端点仅检查 DocumentPermission 表，
        不回退判断文档 owner，因此需要显式为 owner 添加成员记录。
        """
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        # 显式为 owner 添加文档成员记录，使其在 resolve_arbitration 权限检查中可见
        owner_id = await _get_user_id(client, auth_headers)
        await _add_doc_member(client, auth_headers, doc_id, owner_id, "owner")
        prop_a = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_001",
            instruction="扩充安全架构描述", ai_source="doc_ai:TechReviewer",
        )
        prop_b = await _create_proposal(
            client, auth_headers, doc_id, block_id="block_001",
            instruction="精简技术细节", ai_source="doc_ai:LegalAgent",
        )
        arb = await _create_arbitration(
            db_session, doc_id, "block_001", [prop_a, prop_b],
            ["doc_ai:TechReviewer", "doc_ai:LegalAgent"],
        )
        return doc_id, arb, prop_a, prop_b

    @pytest.mark.asyncio
    async def test_resolve_arbitration_proposal_a(self, client, auth_headers, db_session):
        """选择 proposal_a，A 被接受 B 被拒绝。"""
        doc_id, arb, prop_a, prop_b = await self._setup_arbitration(client, auth_headers, db_session)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.post(
            f"/api/review/arbitrations/{arb.arb_id}/resolve",
            json={
                "resolution": ArbitrationResolution.PROPOSAL_A.value,
                "decider_id": user_id,
                "decider_reason": "采纳 A 方案",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution"] == ArbitrationResolution.PROPOSAL_A.value
        assert data["decider_reason"] == "采纳 A 方案"

        status_a = await _get_proposal_status(client, auth_headers, doc_id, prop_a)
        status_b = await _get_proposal_status(client, auth_headers, doc_id, prop_b)
        assert status_a == ProposalStatus.ACCEPTED.value
        assert status_b == ProposalStatus.REJECTED.value

    @pytest.mark.asyncio
    async def test_resolve_arbitration_proposal_b(self, client, auth_headers, db_session):
        """选择 proposal_b，B 被接受 A 被拒绝。"""
        doc_id, arb, prop_a, prop_b = await self._setup_arbitration(client, auth_headers, db_session)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.post(
            f"/api/review/arbitrations/{arb.arb_id}/resolve",
            json={
                "resolution": ArbitrationResolution.PROPOSAL_B.value,
                "decider_id": user_id,
                "decider_reason": "采纳 B 方案",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["resolution"] == ArbitrationResolution.PROPOSAL_B.value

        status_a = await _get_proposal_status(client, auth_headers, doc_id, prop_a)
        status_b = await _get_proposal_status(client, auth_headers, doc_id, prop_b)
        assert status_a == ProposalStatus.REJECTED.value
        assert status_b == ProposalStatus.ACCEPTED.value

    @pytest.mark.asyncio
    async def test_resolve_arbitration_declined(self, client, auth_headers, db_session):
        """选择 declined，所有提案被拒绝。"""
        doc_id, arb, prop_a, prop_b = await self._setup_arbitration(client, auth_headers, db_session)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.post(
            f"/api/review/arbitrations/{arb.arb_id}/resolve",
            json={
                "resolution": ArbitrationResolution.DECLINED.value,
                "decider_id": user_id,
                "decider_reason": "双方都不采纳",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["resolution"] == ArbitrationResolution.DECLINED.value

        status_a = await _get_proposal_status(client, auth_headers, doc_id, prop_a)
        status_b = await _get_proposal_status(client, auth_headers, doc_id, prop_b)
        assert status_a == ProposalStatus.REJECTED.value
        assert status_b == ProposalStatus.REJECTED.value

    @pytest.mark.asyncio
    async def test_resolve_arbitration_by_editor(self, client, auth_headers, db_session):
        """lead_editor 可以解决仲裁。"""
        doc_id, arb, _, _ = await self._setup_arbitration(client, auth_headers, db_session)
        _, lead_editor_headers = await _create_user_with_doc_role(
            client, auth_headers, doc_id, "lead_editor@example.com", "lead_editor"
        )
        lead_editor_id = await _get_user_id(client, lead_editor_headers)

        resp = await client.post(
            f"/api/review/arbitrations/{arb.arb_id}/resolve",
            json={
                "resolution": ArbitrationResolution.PROPOSAL_A.value,
                "decider_id": lead_editor_id,
                "decider_reason": "主编辑裁决",
            },
            headers=lead_editor_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["resolution"] == ArbitrationResolution.PROPOSAL_A.value

    @pytest.mark.asyncio
    async def test_resolve_arbitration_by_reader(self, client, auth_headers, db_session):
        """reader 无权解决仲裁返回 403。"""
        doc_id, arb, _, _ = await self._setup_arbitration(client, auth_headers, db_session)
        _, reader_headers = await _create_user_with_doc_role(
            client, auth_headers, doc_id, "reader2@example.com", "reader"
        )
        reader_id = await _get_user_id(client, reader_headers)

        resp = await client.post(
            f"/api/review/arbitrations/{arb.arb_id}/resolve",
            json={
                "resolution": ArbitrationResolution.PROPOSAL_A.value,
                "decider_id": reader_id,
                "decider_reason": "读者尝试裁决",
            },
            headers=reader_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_resolve_arbitration_not_found(self, client, auth_headers):
        """不存在的仲裁返回 404。"""
        user_id = await _get_user_id(client, auth_headers)
        resp = await client.post(
            "/api/review/arbitrations/non-existent-arb-id/resolve",
            json={
                "resolution": ArbitrationResolution.PROPOSAL_A.value,
                "decider_id": user_id,
                "decider_reason": "测试",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ============================================================
# TestCompleteReview
# ============================================================


class TestCompleteReview:
    """完成审查端点测试。"""

    @pytest.mark.asyncio
    async def test_complete_review_success(self, client, auth_headers):
        """无 pending 提案和未解决仲裁时成功完成审查。"""
        doc_id, _ = await _setup_doc_with_review(client, auth_headers)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.post(
            f"/api/review/{doc_id}/complete",
            json={"user_id": user_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed"] is True
        assert data["pending_proposals"] == 0
        assert data["unresolved_arbitrations"] == 0

    @pytest.mark.asyncio
    async def test_complete_review_with_pending(self, client, auth_headers):
        """有 pending 提案时返回 completed=False。"""
        doc_id, _ = await _setup_doc_with_review(client, auth_headers)
        # 创建一个 pending 提案
        await _create_proposal(client, auth_headers, doc_id)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.post(
            f"/api/review/{doc_id}/complete",
            json={"user_id": user_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed"] is False
        assert data["pending_proposals"] >= 1

    @pytest.mark.asyncio
    async def test_complete_review_no_session(self, client, auth_headers):
        """无活跃审查会话返回 400。"""
        doc_id = await _setup_doc_in_discussion(client, auth_headers)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.post(
            f"/api/review/{doc_id}/complete",
            json={"user_id": user_id},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_complete_review_by_reader(self, client, auth_headers):
        """reader 无权完成审查返回 403。"""
        doc_id, _ = await _setup_doc_with_review(client, auth_headers)
        _, reader_headers = await _create_user_with_doc_role(
            client, auth_headers, doc_id, "reader3@example.com", "reader"
        )
        reader_id = await _get_user_id(client, reader_headers)

        resp = await client.post(
            f"/api/review/{doc_id}/complete",
            json={"user_id": reader_id},
            headers=reader_headers,
        )
        assert resp.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
