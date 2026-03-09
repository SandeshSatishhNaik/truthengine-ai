"""Supabase database connection."""

from __future__ import annotations
from supabase import create_client, Client
from loguru import logger

from backend.config import get_settings


_client: Client | None = None


def get_supabase_client() -> Client:
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")
    logger.info("Initializing Supabase client")
    _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client
