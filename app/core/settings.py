from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Ride Booking"
    app_env: Literal["local", "development", "staging", "production", "test"] = "local"
    app_debug: bool = False
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    server_host: str = "0.0.0.0"
    server_port: int = 8000

    backend_cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ]
    )

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ride_booking"
    postgres_user: str = "ride_booking"
    postgres_password: str = "change-me"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800
    database_echo: bool = False

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_ssl: bool = False

    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    jwt_secret_key: str = "change-this-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    ai_default_provider: Literal["openai", "claude"] = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection_faqs: str = "ride_booking_faqs"

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        scheme = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{scheme}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
