"""AI Forge 模块完整集成测试。

覆盖端点：
- POST /api/forge/refine
- GET /api/forge/proposals
- PUT /api/forge/proposals/{prop_id}
- GET /api/forge/pool-status
- GET /api/forge/memories
- POST /api/forge/conflicts/detect
"""

import uuid

import pytest

# 导入所有模型以确保 Base.metadata 在 setup_database fixture 之前完成注册
from ai_forge.models import AIMemory, AIProposal  # noqa: F401
from approval.models import Arbitration, ReviewSession, Snapshot  # noqa: F401
from audit.models import OperationLog  # noqa: F401
from auth.models import DocumentPermission, User  # noqa: F401
from document.models import BlockMeta, Document  # noqa: F401

# ============================================================
# Helper Functions
# ============================================================


async def _create_doc(client, headers, title="测试文档"):
    """创建文档并返回 doc_id。"""
    resp = await client.post("/api/documents", json={
        "title": title,
        "anchor_statement": "测试锚点声明",
        "anchor_audience": "测试受众",
        "anchor_argument": "测试论点",
    }, headers=headers)
    return resp.json()["doc_id"]


async def _get_user_id(client, headers):
    """获取当前登录用户的 user_id。"""
    resp = await client.get("/api/auth/me", headers=headers)
    return resp.json()["user_id"]


async def _create_user_with_role(client, owner_headers, doc_id, email, role):
    """注册用户、登录、并以指定角色加入文档。返回 (headers, user_id)。"""
    await client.post("/api/auth/register", json={
        "display_name": f"Test {role}",
        "email": email,
        "password": "test123",
        "role": role,
    })
    resp = await client.post("/api/auth/login", json={
        "email": email,
        "password": "test123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = await client.get("/api/auth/me", headers=headers)
    user_id = me_resp.json()["user_id"]
    await client.post(f"/api/auth/docs/{doc_id}/members", json={
        "user_id": user_id,
        "role": role,
    }, headers=owner_headers)
    return headers, user_id


async def _create_proposal(client, headers, doc_id, block_id="block_001",
                           instruction="请优化安全表述",
                           ai_source="doc_ai:TechReviewer"):
    """通过 refine 端点创建提案，返回响应对象。"""
    return await client.post("/api/forge/refine", json={
        "doc_id": doc_id,
        "block_id": block_id,
        "instruction": instruction,
        "ai_source": ai_source,
    }, headers=headers)


# ============================================================
# TestForgeRefine
# ============================================================


class TestForgeRefine:
    """POST /api/forge/refine 端点测试。"""

    @pytest.mark.asyncio
    async def test_forge_refine_success_public(self, client, auth_headers):
        """使用 doc_ai:TechReviewer 成功创建公开提案。"""
        doc_id = await _create_doc(client, auth_headers, "公开AI锻造测试")
        resp = await _create_proposal(client, auth_headers, doc_id,
                                     instruction="请优化安全表述",
                                     ai_source="doc_ai:TechReviewer")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_memory_type"] == "public"
        assert data["ai_source"] == "doc_ai:TechReviewer"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_forge_refine_success_private(self, client, auth_headers):
        """使用 personal_ai:我的技术顾问 成功创建私有提案。"""
        doc_id = await _create_doc(client, auth_headers, "私有AI锻造测试")
        resp = await _create_proposal(client, auth_headers, doc_id,
                                     instruction="请调整技术方案",
                                     ai_source="personal_ai:我的技术顾问")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_memory_type"] == "private"
        assert data["ai_source"] == "personal_ai:我的技术顾问"

    @pytest.mark.asyncio
    async def test_forge_refine_without_auth(self, client, auth_headers):
        """无认证返回 401。"""
        doc_id = await _create_doc(client, auth_headers, "无认证测试")
        resp = await client.post("/api/forge/refine", json={
            "doc_id": doc_id,
            "block_id": "block_001",
            "instruction": "请优化",
            "ai_source": "doc_ai:TechReviewer",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_forge_refine_by_reader(self, client, auth_headers):
        """reader 无 use_forge 权限返回 403。"""
        doc_id = await _create_doc(client, auth_headers, "Reader权限测试")
        reader_headers, _ = await _create_user_with_role(
            client, auth_headers, doc_id, "reader@example.com", "reader"
        )
        resp = await _create_proposal(client, reader_headers, doc_id)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_forge_refine_by_reviewer(self, client, auth_headers):
        """reviewer 无 use_forge 权限返回 403。"""
        doc_id = await _create_doc(client, auth_headers, "Reviewer权限测试")
        reviewer_headers, _ = await _create_user_with_role(
            client, auth_headers, doc_id, "reviewer@example.com", "reviewer"
        )
        resp = await _create_proposal(client, reviewer_headers, doc_id)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_forge_refine_by_editor(self, client, auth_headers):
        """editor 可以使用 forge。"""
        doc_id = await _create_doc(client, auth_headers, "Editor权限测试")
        editor_headers, _ = await _create_user_with_role(
            client, auth_headers, doc_id, "editor@example.com", "editor"
        )
        resp = await _create_proposal(client, editor_headers, doc_id)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_memory_type"] == "public"

    @pytest.mark.asyncio
    async def test_forge_refine_returns_correct_fields(self, client, auth_headers):
        """验证返回的 proposal 包含所有必要字段。"""
        doc_id = await _create_doc(client, auth_headers, "字段验证测试")
        resp = await _create_proposal(client, auth_headers, doc_id,
                                     instruction="请优化安全表述",
                                     ai_source="doc_ai:TechReviewer")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["proposal_id"], str)
        assert len(data["proposal_id"]) > 0
        assert data["block_id"] == "block_001"
        assert data["doc_id"] == doc_id
        assert data["ai_source"] == "doc_ai:TechReviewer"
        assert data["ai_memory_type"] == "public"
        assert isinstance(data["new_content"], str)
        assert len(data["new_content"]) > 0
        assert isinstance(data["rationale"], str)
        assert len(data["rationale"]) > 0
        assert isinstance(data["anchor_alignment_score"], (int, float))
        assert 0 <= data["anchor_alignment_score"] <= 1
        assert isinstance(data["diff_summary"], str)
        assert len(data["diff_summary"]) > 0
        assert data["status"] == "pending"
        assert isinstance(data["created_at"], str)
        assert len(data["created_at"]) > 0


# ============================================================
# TestForgeProposals
# ============================================================


class TestForgeProposals:
    """GET /api/forge/proposals 与 PUT /api/forge/proposals/{prop_id} 测试。"""

    @pytest.mark.asyncio
    async def test_list_proposals_success(self, client, auth_headers):
        """列出提案。"""
        doc_id = await _create_doc(client, auth_headers, "提案列表测试")
        await _create_proposal(client, auth_headers, doc_id)
        resp = await client.get(
            f"/api/forge/proposals?doc_id={doc_id}", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["doc_id"] == doc_id

    @pytest.mark.asyncio
    async def test_list_proposals_empty(self, client, auth_headers):
        """无提案时返回空列表。"""
        doc_id = await _create_doc(client, auth_headers, "空提案测试")
        resp = await client.get(
            f"/api/forge/proposals?doc_id={doc_id}", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_proposals_filter_by_block_id(self, client, auth_headers):
        """按 block_id 过滤提案。"""
        doc_id = await _create_doc(client, auth_headers, "Block过滤测试")
        await _create_proposal(client, auth_headers, doc_id, block_id="block_a")
        await _create_proposal(client, auth_headers, doc_id, block_id="block_b")
        resp = await client.get(
            f"/api/forge/proposals?doc_id={doc_id}&block_id=block_a",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["block_id"] == "block_a"

    @pytest.mark.asyncio
    async def test_list_proposals_filter_by_status(self, client, auth_headers):
        """按 status 过滤提案。"""
        doc_id = await _create_doc(client, auth_headers, "状态过滤测试")
        resp1 = await _create_proposal(client, auth_headers, doc_id, block_id="block_a")
        await _create_proposal(client, auth_headers, doc_id, block_id="block_b")
        prop_id = resp1.json()["proposal_id"]

        await client.put(
            f"/api/forge/proposals/{prop_id}?status=accepted",
            headers=auth_headers,
        )

        resp = await client.get(
            f"/api/forge/proposals?doc_id={doc_id}&status=accepted",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "accepted"

        resp = await client.get(
            f"/api/forge/proposals?doc_id={doc_id}&status=pending",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_proposals_without_discuss_permission(self, client, auth_headers):
        """无 discuss 权限返回 403。"""
        doc_id = await _create_doc(client, auth_headers, "无discuss权限测试")
        blocked_headers, _ = await _create_user_with_role(
            client, auth_headers, doc_id, "blocked@example.com", "blocked"
        )
        resp = await client.get(
            f"/api/forge/proposals?doc_id={doc_id}", headers=blocked_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_proposal_status_success(self, client, auth_headers):
        """更新提案状态为 accepted。"""
        doc_id = await _create_doc(client, auth_headers, "更新提案状态测试")
        resp = await _create_proposal(client, auth_headers, doc_id)
        prop_id = resp.json()["proposal_id"]

        update_resp = await client.put(
            f"/api/forge/proposals/{prop_id}?status=accepted",
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["status"] == "accepted"
        assert data["proposal_id"] == prop_id

    @pytest.mark.asyncio
    async def test_update_proposal_status_to_rejected(self, client, auth_headers):
        """更新提案状态为 rejected。"""
        doc_id = await _create_doc(client, auth_headers, "拒绝提案测试")
        resp = await _create_proposal(client, auth_headers, doc_id)
        prop_id = resp.json()["proposal_id"]

        update_resp = await client.put(
            f"/api/forge/proposals/{prop_id}?status=rejected",
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["status"] == "rejected"
        assert data["proposal_id"] == prop_id


# ============================================================
# TestPoolStatus
# ============================================================


class TestPoolStatus:
    """GET /api/forge/pool-status 端点测试。"""

    @pytest.mark.asyncio
    async def test_get_pool_status_success(self, client, auth_headers):
        """获取池状态。"""
        doc_id = await _create_doc(client, auth_headers, "池状态测试")
        resp = await client.get(
            f"/api/forge/pool-status?doc_id={doc_id}", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["doc_id"] == doc_id
        assert "public_count" in data
        assert "private_count" in data
        assert "public_limit" in data
        assert "private_limit" in data
        assert "global_private_count" in data
        assert "global_private_limit" in data

    @pytest.mark.asyncio
    async def test_get_pool_status_counts_correct(self, client, auth_headers):
        """验证计数正确（创建提案后计数增加）。"""
        doc_id = await _create_doc(client, auth_headers, "池计数测试")

        resp = await client.get(
            f"/api/forge/pool-status?doc_id={doc_id}", headers=auth_headers
        )
        assert resp.json()["public_count"] == 0
        assert resp.json()["private_count"] == 0

        await _create_proposal(client, auth_headers, doc_id,
                              instruction="请优化安全表述",
                              ai_source="doc_ai:TechReviewer")
        resp = await client.get(
            f"/api/forge/pool-status?doc_id={doc_id}", headers=auth_headers
        )
        assert resp.json()["public_count"] == 1
        assert resp.json()["private_count"] == 0

        await _create_proposal(client, auth_headers, doc_id,
                              instruction="请调整技术方案",
                              ai_source="personal_ai:我的技术顾问")
        resp = await client.get(
            f"/api/forge/pool-status?doc_id={doc_id}", headers=auth_headers
        )
        assert resp.json()["public_count"] == 1
        assert resp.json()["private_count"] == 1

    @pytest.mark.asyncio
    async def test_get_pool_status_without_permission(self, client, auth_headers):
        """无 discuss 权限返回 403。"""
        doc_id = await _create_doc(client, auth_headers, "池状态权限测试")
        blocked_headers, _ = await _create_user_with_role(
            client, auth_headers, doc_id, "blocked@example.com", "blocked"
        )
        resp = await client.get(
            f"/api/forge/pool-status?doc_id={doc_id}", headers=blocked_headers
        )
        assert resp.status_code == 403


# ============================================================
# TestMemories
# ============================================================


class TestMemories:
    """GET /api/forge/memories 端点测试。"""

    @pytest.mark.asyncio
    async def test_get_memories_public(self, client, auth_headers, db_session):
        """获取公开记忆。"""
        doc_id = await _create_doc(client, auth_headers, "公开记忆测试")
        user_id = await _get_user_id(client, auth_headers)

        memory = AIMemory(
            doc_id=doc_id,
            user_id=user_id,
            ai_role="TechReviewer",
            rule="安全相关内容需要包含加密和权限控制描述",
            memory_type="public",
            solidified=False,
            trigger_count=0,
        )
        db_session.add(memory)
        await db_session.commit()

        resp = await client.get(
            f"/api/forge/memories?doc_id={doc_id}&memory_type=public",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["doc_id"] == doc_id
        assert data[0]["ai_role"] == "TechReviewer"
        assert data[0]["memory_type"] == "public"

    @pytest.mark.asyncio
    async def test_get_memories_private(self, client, auth_headers, db_session):
        """获取私有记忆。"""
        doc_id = await _create_doc(client, auth_headers, "私有记忆测试")
        user_id = await _get_user_id(client, auth_headers)

        memory = AIMemory(
            doc_id=doc_id,
            user_id=user_id,
            ai_role="我的技术顾问",
            rule="用户偏好事件驱动架构",
            memory_type="private",
            solidified=False,
            trigger_count=0,
        )
        db_session.add(memory)
        await db_session.commit()

        resp = await client.get(
            f"/api/forge/memories?doc_id={doc_id}&memory_type=private",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["doc_id"] == doc_id
        assert data[0]["memory_type"] == "private"
        assert data[0]["ai_role"] == "我的技术顾问"

    @pytest.mark.asyncio
    async def test_get_memories_empty(self, client, auth_headers):
        """无记忆时返回空列表。"""
        doc_id = await _create_doc(client, auth_headers, "空记忆测试")
        resp = await client.get(
            f"/api/forge/memories?doc_id={doc_id}&memory_type=public",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []


# ============================================================
# TestConflictDetect
# ============================================================


class TestConflictDetect:
    """POST /api/forge/conflicts/detect 端点测试。"""

    @pytest.mark.asyncio
    async def test_detect_conflict_success(self, client, auth_headers, db_session):
        """检测两个提案的冲突。"""
        doc_id = await _create_doc(client, auth_headers, "冲突检测测试")

        prop_a = AIProposal(
            proposal_id=str(uuid.uuid4()),
            block_id="block_a",
            doc_id=doc_id,
            ai_source="doc_ai:TechReviewer",
            ai_memory_type="public",
            new_content="需要补充更多安全细节来完善文档",
            rationale="需要补充更多细节来完善文档",
            anchor_alignment_score=0.85,
            diff_summary="+10/-2",
            status="pending",
        )
        prop_b = AIProposal(
            proposal_id=str(uuid.uuid4()),
            block_id="block_b",
            doc_id=doc_id,
            ai_source="doc_ai:LegalAgent",
            ai_memory_type="public",
            new_content="建议精简技术细节以提高可读性",
            rationale="建议精简内容以提高可读性",
            anchor_alignment_score=0.75,
            diff_summary="-5/+2",
            status="pending",
        )
        db_session.add(prop_a)
        db_session.add(prop_b)
        await db_session.commit()

        resp = await client.post("/api/forge/conflicts/detect", json={
            "doc_id": doc_id,
            "proposal_a_id": prop_a.proposal_id,
            "proposal_b_id": prop_b.proposal_id,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_opposing"] is True
        assert len(data["conflict_description"]) > 0
        assert data["proposal_a_source"] == "doc_ai:TechReviewer"
        assert data["proposal_b_source"] == "doc_ai:LegalAgent"

    @pytest.mark.asyncio
    async def test_detect_conflict_not_found(self, client, auth_headers):
        """提案不存在返回 404。"""
        doc_id = await _create_doc(client, auth_headers, "冲突404测试")
        resp = await client.post("/api/forge/conflicts/detect", json={
            "doc_id": doc_id,
            "proposal_a_id": "nonexistent_proposal_a",
            "proposal_b_id": "nonexistent_proposal_b",
        }, headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_detect_conflict_without_permission(self, client, auth_headers):
        """无 discuss 权限返回 403。"""
        doc_id = await _create_doc(client, auth_headers, "冲突权限测试")
        blocked_headers, _ = await _create_user_with_role(
            client, auth_headers, doc_id, "blocked@example.com", "blocked"
        )
        resp = await client.post("/api/forge/conflicts/detect", json={
            "doc_id": doc_id,
            "proposal_a_id": "any_proposal_a",
            "proposal_b_id": "any_proposal_b",
        }, headers=blocked_headers)
        assert resp.status_code == 403
