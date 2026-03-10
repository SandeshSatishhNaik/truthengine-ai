"""TruthEngine AI - FastAPI Application."""

import os
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
from backend.routers import health, ingestion, search, tools, comparison, telegram


async def _setup_telegram_bot(app: FastAPI, settings):
    """Initialize Telegram bot in webhook mode for production."""
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled")
        app.state.tg_app = None
        return

    external_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if not external_url:
        logger.info("Not on Render — Telegram bot webhook skipped (use polling locally)")
        app.state.tg_app = None
        return

    from telegram.ext import Application, CommandHandler
    from tgbot.bot import (
        start_command, help_command, save_command,
        search_command, compare_command, list_command,
    )

    tg_app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .updater(None)  # No updater — we handle HTTP via FastAPI
        .build()
    )

    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CommandHandler("help", help_command))
    tg_app.add_handler(CommandHandler("save", save_command))
    tg_app.add_handler(CommandHandler("search", search_command))
    tg_app.add_handler(CommandHandler("compare", compare_command))
    tg_app.add_handler(CommandHandler("list", list_command))

    await tg_app.initialize()
    await tg_app.start()

    # Register webhook with Telegram
    webhook_url = f"{external_url}/api/v1/telegram/webhook"
    await tg_app.bot.set_webhook(url=webhook_url)
    logger.info(f"Telegram bot webhook set: {webhook_url}")

    app.state.tg_app = tg_app


async def _shutdown_telegram_bot(app: FastAPI):
    """Gracefully stop Telegram bot."""
    tg_app = getattr(app.state, "tg_app", None)
    if tg_app is not None:
        await tg_app.bot.delete_webhook()
        await tg_app.stop()
        await tg_app.shutdown()
        logger.info("Telegram bot stopped")


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

    # Start Telegram bot (webhook mode)
    await _setup_telegram_bot(app, settings)

    yield

    # Shutdown Telegram bot
    await _shutdown_telegram_bot(app)

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
    app.include_router(telegram.router, prefix="/api/v1", tags=["Telegram"])

    return app


app = create_app()
