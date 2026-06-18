import pytest
from jose import jwt

from shared.authz import DocRole, GlobalRole
from shared.config import settings
from auth.service import AuthService


class TestTokenPayload:
    """JWT payload 必须携带 global_role，可选携带 doc_role。"""

    def test_access_token_contains_global_role(self):
        token = AuthService.create_access_token("u1", GlobalRole.PERSONAL.value)
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "u1"
        assert payload["global_role"] == GlobalRole.PERSONAL.value
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_refresh_token_contains_global_role(self):
        token = AuthService.create_refresh_token("u1", GlobalRole.TEAM_ADMIN.value)
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "u1"
        assert payload["global_role"] == GlobalRole.TEAM_ADMIN.value
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_create_tokens_returns_both_tokens(self):
        tokens = AuthService.create_tokens("u1", GlobalRole.OPS.value)
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    def test_token_with_doc_role_carries_doc_role(self):
        token = AuthService.create_token_with_doc_role("u1", GlobalRole.PERSONAL.value, DocRole.EDITOR.value)
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["global_role"] == GlobalRole.PERSONAL.value
        assert payload["doc_role"] == DocRole.EDITOR.value


class TestRegister:
    """注册默认全局角色与个人用户创建特权账号限制。"""

    @pytest.mark.asyncio
    async def test_register_defaults_to_personal(self, client):
        resp = await client.post("/api/auth/register", json={
            "display_name": "新用户",
            "email": "new@example.com",
            "password": "test123",
            "role": "editor",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["display_name"] == "新用户"
        assert data["email"] == "new@example.com"
        assert data["global_role"] == GlobalRole.PERSONAL.value
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_register_privileged_role_rejected_for_anonymous(self, client):
        resp = await client.post("/api/auth/register", json={
            "display_name": "管理员",
            "email": "admin@example.com",
            "password": "test123",
            "role": "owner",
            "global_role": GlobalRole.TEAM_ADMIN.value,
        })
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_register_privileged_role_allowed_for_team_admin(self, client, team_admin_headers):
        resp = await client.post("/api/auth/register", json={
            "display_name": "新运维",
            "email": "new-ops@example.com",
            "password": "test123",
            "role": "owner",
            "global_role": GlobalRole.OPS.value,
        }, headers=team_admin_headers)
        assert resp.status_code == 201
        assert resp.json()["global_role"] == GlobalRole.OPS.value


class TestLogin:
    """登录返回双令牌及用户信息。"""

    @pytest.mark.asyncio
    async def test_login_returns_tokens_with_global_role(self, client):
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
        assert "refresh_token" in data
        assert data["user"]["email"] == "login@example.com"
        assert data["user"]["global_role"] == GlobalRole.PERSONAL.value

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
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


class TestMe:
    """/me 返回 global_role 与可选 doc_role。"""

    @pytest.mark.asyncio
    async def test_me_returns_global_role(self, client, auth_headers):
        resp = await client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["global_role"] == GlobalRole.PERSONAL.value
        assert data["doc_role"] is None

    @pytest.mark.asyncio
    async def test_me_with_doc_id_returns_doc_role(self, client, auth_headers):
        # 创建文档并添加当前用户为 owner
        doc_resp = await client.post("/api/documents", json={
            "title": "测试文档",
            "anchor_statement": "anchor",
            "anchor_audience": "all",
            "anchor_argument": "arg",
        }, headers=auth_headers)
        doc_id = doc_resp.json()["doc_id"]

        me_resp = await client.get("/api/auth/me", headers=auth_headers)
        user_id = me_resp.json()["user_id"]

        await client.post(f"/api/auth/docs/{doc_id}/members", json={
            "user_id": user_id,
            "role": "owner",
        }, headers=auth_headers)

        me_resp = await client.get(f"/api/auth/me?doc_id={doc_id}", headers=auth_headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["doc_role"] == "owner"


class TestProtectedEndpoints:
    """无令牌或无效令牌无法访问受保护端点。"""

    @pytest.mark.asyncio
    async def test_me_without_token(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_token_missing_global_role(self, client):
        token = jwt.encode({"sub": "fake"}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
