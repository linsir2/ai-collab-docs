"""限流中间件测试 — 覆盖登录、未认证、已认证及 WebSocket 限流。"""

import pytest

from shared.middleware import (
    _ws_buckets,
    cleanup_ws_rate_limit,
    try_acquire_ws_message,
)


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


# ============================================================
# TestRateLimitLogin
# ============================================================

class TestRateLimitLogin:
    """登录端点 /api/auth/login — 30 req/min per IP。"""

    @pytest.mark.asyncio
    async def test_login_rate_limit_enforced(self, client):
        """连续 30 次登录后第 31 次返回 429。"""
        login_payload = {"email": "nobody@example.com", "password": "wrong"}

        for i in range(30):
            resp = await client.post("/api/auth/login", json=login_payload)
            # 前 30 次不应被限流（401 表示凭据错误，但请求到达了端点）
            assert resp.status_code != 429, f"第 {i + 1} 次请求不应被限流"

        resp = await client.post("/api/auth/login", json=login_payload)
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_login_rate_limit_retry_after_header(self, client):
        """429 响应包含 Retry-After header。"""
        login_payload = {"email": "nobody@example.com", "password": "wrong"}

        for _ in range(30):
            await client.post("/api/auth/login", json=login_payload)

        resp = await client.post("/api/auth/login", json=login_payload)
        assert resp.status_code == 429
        assert "retry-after" in {k.lower() for k in resp.headers.keys()}
        assert resp.headers["retry-after"] == "60"


# ============================================================
# TestRateLimitUnauthenticated
# ============================================================

class TestRateLimitUnauthenticated:
    """其他未认证端点 — 60 req/min per IP。"""

    @pytest.mark.asyncio
    async def test_unauthenticated_rate_limit(self, client):
        """未认证端点超过 60/min 返回 429。"""
        for i in range(60):
            resp = await client.get("/health")
            assert resp.status_code != 429, f"第 {i + 1} 次请求不应被限流"

        resp = await client.get("/health")
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_unauthenticated_rate_limit_headers(self, client):
        """响应包含 X-RateLimit-Limit 和 X-RateLimit-Remaining headers。"""
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert "x-ratelimit-limit" in {k.lower() for k in resp.headers.keys()}
        assert "x-ratelimit-remaining" in {k.lower() for k in resp.headers.keys()}
        assert resp.headers["x-ratelimit-limit"] == "60"
        assert resp.headers["x-ratelimit-remaining"] == "59"


# ============================================================
# TestRateLimitAuthenticated
# ============================================================

class TestRateLimitAuthenticated:
    """已认证端点 — 200 req/min per user。"""

    @pytest.mark.asyncio
    async def test_authenticated_rate_limit_headers(self, client, auth_headers):
        """已认证请求包含限流 headers。"""
        resp = await client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert "x-ratelimit-limit" in {k.lower() for k in resp.headers.keys()}
        assert "x-ratelimit-remaining" in {k.lower() for k in resp.headers.keys()}
        assert resp.headers["x-ratelimit-limit"] == "200"
        assert resp.headers["x-ratelimit-remaining"] == "199"

    @pytest.mark.asyncio
    async def test_authenticated_rate_limit_not_triggered(self, client, auth_headers):
        """正常使用不会触发限流。"""
        for i in range(10):
            resp = await client.get("/api/auth/me", headers=auth_headers)
            assert resp.status_code == 200, f"第 {i + 1} 次请求不应被限流"


# ============================================================
# TestWSRateLimit
# ============================================================

class TestWSRateLimit:
    """WebSocket 消息限流 — 60 msg/min per connection（单元测试，直接调用函数）。"""

    def test_ws_rate_limit_allows_under_limit(self):
        """60 条消息内允许。"""
        ws_id = 10001
        for i in range(60):
            assert try_acquire_ws_message(ws_id) is True, f"第 {i + 1} 条消息应被允许"

    def test_ws_rate_limit_blocks_over_limit(self):
        """超过 60 条后返回 False。"""
        ws_id = 10002
        for _ in range(60):
            assert try_acquire_ws_message(ws_id) is True

        assert try_acquire_ws_message(ws_id) is False

    def test_ws_rate_limit_cleanup(self):
        """cleanup_ws_rate_limit 清理桶。"""
        ws_id = 10003
        # 消耗部分配额
        for _ in range(30):
            assert try_acquire_ws_message(ws_id) is True

        # 清理
        cleanup_ws_rate_limit(ws_id)
        assert ws_id not in _ws_buckets

        # 清理后配额重置
        assert try_acquire_ws_message(ws_id) is True
