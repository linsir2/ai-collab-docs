from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/forge"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5433/forge"
    redis_url: str = "redis://localhost:6380/0"
    jwt_secret: str = "demo-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    llm_api_key: str = "mock-key"
    llm_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]
    yjs_server_url: str = "ws://localhost:1234"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
