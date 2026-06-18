import pytest


@pytest.mark.asyncio
async def test_detect_and_resolve_arbitration(client, auth_headers):
    create_resp = await client.post("/api/documents", json={
        "title": "仲裁测试文档",
        "anchor_statement": "构建测试冲突仲裁完整流程的基线文档",
        "anchor_audience": "测试团队",
        "anchor_argument": "验证仲裁台核心功能闭环",
    }, headers=auth_headers)
    doc_id = create_resp.json()["doc_id"]

    await client.post("/api/forge/refine", json={
        "doc_id": doc_id,
        "block_id": "block_003",
        "instruction": "扩充安全架构描述",
        "ai_source": "doc_ai:TechReviewer",
    }, headers=auth_headers)

    await client.post("/api/forge/refine", json={
        "doc_id": doc_id,
        "block_id": "block_003",
        "instruction": "精简技术细节",
        "ai_source": "doc_ai:LegalAgent",
    }, headers=auth_headers)

    detect_resp = await client.post("/api/forge/conflicts/detect", json={
        "doc_id": doc_id,
        "block_id": "block_003",
    }, headers=auth_headers)
    assert detect_resp.status_code == 200

    arb_resp = await client.get(f"/api/review/{doc_id}/arbitrations", headers=auth_headers)
    assert arb_resp.status_code == 200
    arbitrations = arb_resp.json()
    assert len(arbitrations) > 0

    arb_id = arbitrations[0]["arb_id"]
    resolve_resp = await client.post(f"/api/review/arbitrations/{arb_id}/resolve", json={
        "resolution": "adopt_a",
        "decider_id": "usr_001",
        "decider_reason": "安全架构是合规基础，应优先采纳TechReviewer的扩充建议。",
    }, headers=auth_headers)

    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["resolution"] == "adopt_a"
    assert resolve_resp.json()["decider_reason"] != ""
