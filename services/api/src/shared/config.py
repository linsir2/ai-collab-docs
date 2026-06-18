import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_WEAK_JWT_SECRET = "demo-secret-change-in-production"


class Settings(BaseSettings):
    env: str = "demo"
    database_url: str = "postgresql+asyncpg://forge:forge_dev@127.0.0.1:5433/forge"
    database_url_sync: str = "postgresql://forge:forge_dev@127.0.0.1:5433/forge"
    redis_url: str = "redis://localhost:6380/0"
    jwt_secret: str = _WEAK_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    jwt_refresh_expire_days: int = 7
    llm_api_key: str = "mock-key"
    llm_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]
    yjs_server_url: str = "ws://localhost:1234"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


def validate_security_settings():
    if settings.jwt_secret == _WEAK_JWT_SECRET:
        if settings.env != "demo":
            logger.critical(
                "SECURITY WARNING: jwt_secret is using the weak default value "
                "'%s' in a non-demo environment! Set a strong JWT_SECRET env variable immediately.",
                _WEAK_JWT_SECRET,
            )
        else:
            logger.warning(
                "jwt_secret is using the demo default value. This is acceptable for local development, "
                "but MUST be changed in production by setting JWT_SECRET environment variable.",
            )
    if settings.llm_api_key == "mock-key":
        logger.info("llm_api_key is using 'mock-key' — AI proposals will run in mock/demo mode.")
