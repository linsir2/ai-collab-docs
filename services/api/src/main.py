import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared import close_redis, settings
from shared.config import validate_security_settings
from shared.middleware import RateLimitMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_security_settings()
    logger.info("App started — env=%s, origins=%s", settings.env, settings.cors_origins)
    yield
    await close_redis()


app = FastAPI(
    title="AI文档锻造平台",
    description="ai-collab-docs — 企业级高严谨度文档人机协作锻造平台",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


def register_routers():
    from auth.router import router as auth_router
    from document.router import router as document_router
    from audit.router import router as audit_router
    from ai_forge.router import router as forge_router
    from approval.router import router as approval_router
    from collab.router import router as collab_router

    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(document_router, prefix="/api", tags=["document"])
    app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
    app.include_router(forge_router, prefix="/api/forge", tags=["forge"])
    app.include_router(approval_router, prefix="/api/review", tags=["approval"])
    app.include_router(collab_router, prefix="/api/collab", tags=["collab"])


register_routers()
