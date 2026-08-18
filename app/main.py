from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.database import SessionLocal

settings = get_settings()
configure_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield
    finally:
        await app.state.redis.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    if settings.backend_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.backend_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    register_exception_handlers(app)

    @app.get("/health", tags=["System"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    @app.get("/ready", tags=["System"])
    async def readiness_check() -> dict[str, Any]:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

        redis: Redis = app.state.redis
        await redis.ping()

        return {
            "status": "ready",
            "database": "ok",
            "redis": "ok",
        }

    return app


app = create_app()
