"""Shared fixtures for TruthEngine AI tests."""

import os
from unittest.mock import MagicMock, patch

import pytest

# Set env vars before any settings import
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("HF_API_TOKEN", "test-hf-token")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "000000000:AAFakeToken")

from backend.cache import tools_cache, search_cache, embedding_cache
from backend.config import get_settings
from database.connection import get_supabase_client


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear lru_cache singletons and API caches between tests."""
    import database.connection as db_conn
    get_settings.cache_clear()
    db_conn._client = None
    tools_cache.clear()
    search_cache.clear()
    embedding_cache.clear()
    yield
    get_settings.cache_clear()
    db_conn._client = None
    tools_cache.clear()
    search_cache.clear()
    embedding_cache.clear()


@pytest.fixture()
def mock_supabase():
    """Provide a fully mocked Supabase client."""
    import database.connection as db_conn
    client = MagicMock()
    with patch("database.connection.create_client", return_value=client):
        db_conn._client = None
        yield client
        db_conn._client = None


@pytest.fixture()
def sample_tool():
    return {
        "id": "aaa-bbb-ccc",
        "name": "TestTool",
        "website": "https://testtool.ai",
        "category": "AI coding",
        "core_function": "AI code assistant",
        "pricing_model": "Freemium",
        "free_tier_limits": "100 requests/day",
        "community_verdict": "Great for beginners",
        "trust_score": 0.85,
        "tags": ["coding", "ai", "free"],
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture()
def sample_html():
    return """
    <html>
    <head>
        <title>TestTool - AI Code Assistant</title>
        <meta name="description" content="AI-powered code completion.">
    </head>
    <body>
        <nav><a href="/">Home</a></nav>
        <main>
            <h1>TestTool</h1>
            <p>TestTool is a powerful AI coding assistant that helps you write faster.</p>
            <p>Free tier: 100 requests per day.</p>
        </main>
        <footer>
            <a href="/pricing">Pricing</a>
            <a href="/docs">Documentation</a>
        </footer>
    </body>
    </html>
    """


@pytest.fixture()
def sample_extraction():
    return {
        "tool_name": "TestTool",
        "core_function": "AI code assistant",
        "pricing_model": "Freemium",
        "free_tier_limits": "100 requests/day",
        "community_verdict": "Great tool for devs",
        "tags": ["coding", "ai"],
    }
