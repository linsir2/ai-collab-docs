import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/auth/register", json={
        "display_name": "新用户",
        "email": "new@example.com",
        "password": "test123",
        "role": "editor",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "新用户"
    assert data["email"] == "new@example.com"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/auth/register", json={
        "display_name": "登录测试",
        "email": "login@example.com",
        "password": "test123",
        "role": "owner",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "test123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_me(client, auth_headers):
    resp = await client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "display_name": "错密测试",
        "email": "wrong@example.com",
        "password": "correct",
        "role": "editor",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrong",
    })
    assert resp.status_code == 401
