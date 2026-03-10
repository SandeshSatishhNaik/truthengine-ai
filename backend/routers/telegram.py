"""Telegram bot webhook endpoint for production (Render)."""

import json

from fastapi import APIRouter, Request, Response
from loguru import logger
from telegram import Update

router = APIRouter(tags=["Telegram"])


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Receive Telegram updates via webhook."""
    tg_app = request.app.state.tg_app
    if tg_app is None:
        return Response(status_code=200)

    try:
        body = await request.json()
        update = Update.de_json(body, tg_app.bot)
        await tg_app.process_update(update)
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")

    return Response(status_code=200)
