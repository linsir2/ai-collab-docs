import pytest


@pytest.mark.asyncio
async def test_request_forge(client, auth_headers):
    create_resp = await client.post("/api/documents", json={
        "title": "AI锻造测试",
        "anchor_statement": "构建测试AI锻造功能的基线文档内容",
        "anchor_audience": "测试用户",
        "anchor_argument": "核心测试论点和依据",
    }, headers=auth_headers)
    doc_id = create_resp.json()["doc_id"]

    resp = await client.post("/api/forge/refine", json={
        "doc_id": doc_id,
        "block_id": "block_001",
        "instruction": "请优化安全相关的表述",
        "ai_source": "doc_ai:TechReviewer",
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "proposal_id" in data
    assert data["ai_memory_type"] == "public"
    assert data["ai_source"] == "doc_ai:TechReviewer"


@pytest.mark.asyncio
async def test_request_forge_private(client, auth_headers):
    create_resp = await client.post("/api/documents", json={
        "title": "私人AI测试",
        "anchor_statement": "测试私人AI锻造功能的基线描述内容",
        "anchor_audience": "测试团队",
        "anchor_argument": "验证私有AI隔离机制",
    }, headers=auth_headers)
    doc_id = create_resp.json()["doc_id"]

    resp = await client.post("/api/forge/refine", json={
        "doc_id": doc_id,
        "block_id": "block_002",
        "instruction": "请调整我的写作风格",
        "ai_source": "personal_ai:我的技术顾问",
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_memory_type"] == "private"


@pytest.mark.asyncio
async def test_get_proposals_with_source_filter(client, auth_headers):
    create_resp = await client.post("/api/documents", json={
        "title": "提案查询测试",
        "anchor_statement": "测试提案查询功能的基线文档描述",
        "anchor_audience": "测试团队",
        "anchor_argument": "验证双轨AI查询隔离",
    }, headers=auth_headers)
    doc_id = create_resp.json()["doc_id"]

    await client.post("/api/forge/refine", json={
        "doc_id": doc_id,
        "block_id": "block_001",
        "instruction": "优化",
        "ai_source": "doc_ai:TechReviewer",
    }, headers=auth_headers)
    await client.post("/api/forge/refine", json={
        "doc_id": doc_id,
        "block_id": "block_001",
        "instruction": "调整风格",
        "ai_source": "personal_ai:我的技术顾问",
    }, headers=auth_headers)

    doc_resp = await client.get(f"/api/forge/proposals?doc_id={doc_id}&ai_source_type=doc", headers=auth_headers)
    private_resp = await client.get(f"/api/forge/proposals?doc_id={doc_id}&ai_source_type=personal", headers=auth_headers)

    doc_proposals = doc_resp.json()
    private_proposals = private_resp.json()
    assert all(p["ai_memory_type"] == "public" for p in doc_proposals)
    assert all(p["ai_memory_type"] == "private" for p in private_proposals)
