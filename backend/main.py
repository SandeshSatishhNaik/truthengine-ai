"""TruthEngine AI - FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from loguru import logger

from backend.config import get_settings
from backend.logging_config import setup_logging
from backend.middleware import limiter, RequestLoggingMiddleware
from backend.cache import tools_cache, search_cache, embedding_cache
from backend.metrics import metrics
from backend.scheduler import setup_scheduler
from backend.routers import health, ingestion, search, tools, comparison


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(debug=settings.debug)
    logger.info("Starting TruthEngine AI")
    logger.info(f"Debug mode: {settings.debug}")

    # Start background scheduler
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown scheduler and flush caches
    scheduler.shutdown(wait=False)
    tools_cache.clear()
    search_cache.clear()
    embedding_cache.clear()
    logger.info("Shutting down TruthEngine AI")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Autonomous AI knowledge engine for AI tool intelligence.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Request logging & global error handling (outermost — runs first)
    app.add_middleware(RequestLoggingMiddleware)

    # CORS
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(ingestion.router, prefix="/api/v1", tags=["Ingestion"])
    app.include_router(search.router, prefix="/api/v1", tags=["Search"])
    app.include_router(tools.router, prefix="/api/v1", tags=["Tools"])
    app.include_router(comparison.router, prefix="/api/v1", tags=["Comparison"])

    return app


app = create_app()
