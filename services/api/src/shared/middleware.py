import re
import time
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_UNAUTHENTICATED_PATHS = ("/api/auth/refresh", "/health", "/docs", "/openapi.json", "/redoc")
_LOGIN_PATH = "/api/auth/login"

_LOGIN_RATE_LIMIT_PER_MINUTE = 30
_UNAUTHENTICATED_RATE_LIMIT_PER_MINUTE = 60
_AUTHENTICATED_RATE_LIMIT_PER_MINUTE = 200
_WS_MESSAGE_RATE_LIMIT_PER_MINUTE = 60

_unauthenticated_buckets: dict[str, tuple[float, int]] = {}
_authenticated_buckets: dict[str, tuple[float, int]] = {}
_login_buckets: dict[str, tuple[float, int]] = {}
_ws_buckets: dict[int, tuple[float, int]] = {}

_token_re = re.compile(r"^Bearer\s+(\S+)$", re.IGNORECASE)


def _try_acquire(buckets: dict, key, limit: int, now: float, window_seconds: float = 60.0) -> tuple[bool, int]:
    bucket_start, count = buckets.get(key, (now, 0))
    if now - bucket_start > window_seconds:
        buckets[key] = (now, 1)
        return True, limit - 1
    if count >= limit:
        return False, 0
    buckets[key] = (bucket_start, count + 1)
    return True, limit - count - 1


def _prune_old_buckets(now: float, window_seconds: float = 60.0) -> None:
    for d in (_unauthenticated_buckets, _authenticated_buckets, _login_buckets, _ws_buckets):
        stale = [k for k, (t, _) in d.items() if now - t > window_seconds]
        for k in stale:
            del d[k]


def _extract_user_id(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    m = _token_re.match(auth)
    if not m:
        return None
    token = m.group(1)
    try:
        import base64
        import json

        payload_b64 = token.split(".")[1]
        padding = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
        return payload.get("sub") or payload.get("user_id")
    except Exception:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        now = time.monotonic()
        _prune_old_buckets(now)

        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Login endpoint gets its own stricter rate limit to prevent brute-force
        # without blocking legitimate users from other unauthenticated endpoints.
        if path == _LOGIN_PATH:
            key = f"{client_ip}:login"
            allowed, remaining = _try_acquire(_login_buckets, key, _LOGIN_RATE_LIMIT_PER_MINUTE, now)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many login attempts. Rate limit: 30/min per IP."},
                    headers={"Retry-After": "60"},
                )
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(_LOGIN_RATE_LIMIT_PER_MINUTE)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        if path in _UNAUTHENTICATED_PATHS or path.startswith(("/docs", "/openapi.json", "/redoc")):
            key = f"{client_ip}:unauth"
            allowed, remaining = _try_acquire(_unauthenticated_buckets, key, _UNAUTHENTICATED_RATE_LIMIT_PER_MINUTE, now)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Rate limit: 60/min for unauthenticated endpoints."},
                    headers={"Retry-After": "60"},
                )
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(_UNAUTHENTICATED_RATE_LIMIT_PER_MINUTE)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        user_id = _extract_user_id(request)
        if not user_id:
            key = f"{client_ip}:unauth"
            allowed, remaining = _try_acquire(_unauthenticated_buckets, key, _UNAUTHENTICATED_RATE_LIMIT_PER_MINUTE, now)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Rate limit: 60/min for unauthenticated endpoints."},
                    headers={"Retry-After": "60"},
                )
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(_UNAUTHENTICATED_RATE_LIMIT_PER_MINUTE)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        key = user_id
        allowed, remaining = _try_acquire(_authenticated_buckets, key, _AUTHENTICATED_RATE_LIMIT_PER_MINUTE, now)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Rate limit: 200/min per user."},
                headers={"Retry-After": "60"},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(_AUTHENTICATED_RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def try_acquire_ws_message(ws_id: int) -> bool:
    now = time.monotonic()
    _prune_old_buckets(now)
    allowed, _ = _try_acquire(_ws_buckets, ws_id, _WS_MESSAGE_RATE_LIMIT_PER_MINUTE, now)
    return allowed


def cleanup_ws_rate_limit(ws_id: int) -> None:
    _ws_buckets.pop(ws_id, None)
