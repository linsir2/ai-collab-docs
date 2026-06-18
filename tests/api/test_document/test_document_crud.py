import pytest


@pytest.mark.asyncio
async def test_create_document(client, auth_headers):
    resp = await client.post("/api/documents", json={
        "title": "测试文档",
        "anchor_statement": "构建一个高性能的分布式数据同步系统",
        "anchor_audience": "技术团队",
        "anchor_argument": "通过事件驱动架构实现实时数据同步",
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "测试文档"
    assert data["state"] == "draft"
    assert "doc_id" in data


@pytest.mark.asyncio
async def test_list_documents(client, auth_headers):
    await client.post("/api/documents", json={
        "title": "文档1",
        "anchor_statement": "描述文档1的核心目标与价值主张",
        "anchor_audience": "投资人",
        "anchor_argument": "市场数据支持的核心论点",
    }, headers=auth_headers)

    resp = await client.get("/api/documents", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_document(client, auth_headers):
    create_resp = await client.post("/api/documents", json={
        "title": "获取测试",
        "anchor_statement": "描述获取测试文档的核心目标与价值主张",
        "anchor_audience": "测试用户",
        "anchor_argument": "核心理由和论据支撑",
    }, headers=auth_headers)
    doc_id = create_resp.json()["doc_id"]

    resp = await client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "获取测试"


@pytest.mark.asyncio
async def test_state_transition_draft_to_discussion(client, auth_headers):
    create_resp = await client.post("/api/documents", json={
        "title": "状态转换测试",
        "anchor_statement": "用来描述文档状态转换的测试目标和愿景",
        "anchor_audience": "测试团队",
        "anchor_argument": "验证状态机核心功能",
    }, headers=auth_headers)
    doc_id = create_resp.json()["doc_id"]

    resp = await client.post(f"/api/documents/{doc_id}/transition", json={
        "to_state": "discussion",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["state"] == "discussion"
