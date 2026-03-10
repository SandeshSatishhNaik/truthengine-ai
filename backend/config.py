from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Groq AI
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Telegram
    telegram_bot_token: str = ""

    # HuggingFace (free inference API for embeddings)
    hf_api_token: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # App
    app_name: str = "TruthEngine AI"
    debug: bool = False

    # Rate limiting
    rate_limit: str = "30/minute"
    rate_limit_search: str = "20/minute"
    rate_limit_ingest: str = "10/minute"
    rate_limit_compare: str = "10/minute"

    # Crawler
    crawl_delay_seconds: float = 2.0
    max_crawl_pages: int = 5
    request_timeout: int = 15
    max_concurrent_crawls: int = 3
    crawl_max_retries: int = 3

    # Retry
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0

    # Cache TTL (seconds)
    cache_ttl_tools: int = 120
    cache_ttl_search: int = 300
    cache_ttl_embedding: int = 600

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Keep-alive: Google Sheet webhook URL (Apps Script web app)
    google_sheet_webhook_url: str = ""

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
