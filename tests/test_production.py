"""Tests for production features: retry, cache, and middleware."""

import time
from unittest.mock import patch, MagicMock

import pytest

from backend.retry import retry, async_retry
from backend.cache import TTLCache, tools_cache, search_cache, embedding_cache


# ── Retry Decorator ────────────────────────────────────────────────────


class TestRetrySync:
    @patch("backend.retry.time.sleep")
    def test_succeeds_on_first_attempt(self, mock_sleep):
        call_count = 0

        @retry(max_attempts=3)
        def succeeds():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeeds() == "ok"
        assert call_count == 1
        mock_sleep.assert_not_called()

    @patch("backend.retry.time.sleep")
    def test_retries_on_failure_then_succeeds(self, mock_sleep):
        call_count = 0

        @retry(max_attempts=3, base_delay=1.0, retryable_exceptions=(ValueError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient")
            return "recovered"

        assert flaky() == "recovered"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("backend.retry.time.sleep")
    def test_raises_after_max_attempts(self, mock_sleep):
        @retry(max_attempts=2, base_delay=0.1, retryable_exceptions=(RuntimeError,))
        def always_fails():
            raise RuntimeError("permanent")

        with pytest.raises(RuntimeError, match="permanent"):
            always_fails()
        assert mock_sleep.call_count == 1

    @patch("backend.retry.time.sleep")
    def test_does_not_retry_non_retryable_exception(self, mock_sleep):
        @retry(max_attempts=3, retryable_exceptions=(ValueError,))
        def wrong_error():
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            wrong_error()
        mock_sleep.assert_not_called()

    @patch("backend.retry.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep):
        @retry(max_attempts=4, base_delay=1.0, backoff_factor=2.0, max_delay=10.0)
        def fails():
            raise Exception("fail")

        with pytest.raises(Exception):
            fails()

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]

    @patch("backend.retry.time.sleep")
    def test_max_delay_cap(self, mock_sleep):
        @retry(max_attempts=4, base_delay=5.0, backoff_factor=3.0, max_delay=10.0)
        def fails():
            raise Exception("fail")

        with pytest.raises(Exception):
            fails()

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert all(d <= 10.0 for d in delays)


class TestRetryAsync:
    @patch("asyncio.sleep")
    async def test_async_succeeds_first_attempt(self, mock_sleep):
        @async_retry(max_attempts=3)
        async def succeeds():
            return "ok"

        assert await succeeds() == "ok"

    @patch("asyncio.sleep")
    async def test_async_retries_then_succeeds(self, mock_sleep):
        call_count = 0

        @async_retry(max_attempts=3, base_delay=0.1, retryable_exceptions=(ValueError,))
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("transient")
            return "ok"

        assert await flaky() == "ok"
        assert call_count == 2

    @patch("asyncio.sleep")
    async def test_async_raises_after_max_attempts(self, mock_sleep):
        @async_retry(max_attempts=2, base_delay=0.1, retryable_exceptions=(RuntimeError,))
        async def always_fails():
            raise RuntimeError("permanent")

        with pytest.raises(RuntimeError, match="permanent"):
            await always_fails()


# ── TTL Cache ──────────────────────────────────────────────────────────


class TestTTLCache:
    def test_set_and_get(self):
        cache = TTLCache(default_ttl=60, max_size=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        cache = TTLCache(default_ttl=60, max_size=10)
        assert cache.get("missing") is None

    def test_ttl_expiry(self):
        cache = TTLCache(default_ttl=0.1, max_size=10)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.15)
        assert cache.get("key") is None

    def test_invalidate(self):
        cache = TTLCache(default_ttl=60, max_size=10)
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None

    def test_clear(self):
        cache = TTLCache(default_ttl=60, max_size=10)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_max_size_eviction(self):
        cache = TTLCache(default_ttl=60, max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should trigger eviction
        # At least latest entry should be present
        assert cache.get("d") == 4

    def test_custom_ttl_per_key(self):
        cache = TTLCache(default_ttl=60, max_size=10)
        cache.set("short", "value", ttl=0.1)
        cache.set("long", "value", ttl=60)
        time.sleep(0.15)
        assert cache.get("short") is None
        assert cache.get("long") == "value"


class TestCacheSingletons:
    def test_tools_cache_exists(self):
        assert tools_cache is not None
        tools_cache.set("test", "value")
        assert tools_cache.get("test") == "value"
        tools_cache.clear()

    def test_search_cache_exists(self):
        assert search_cache is not None

    def test_embedding_cache_exists(self):
        assert embedding_cache is not None


# ── Middleware ──────────────────────────────────────────────────────────


class TestRequestLoggingMiddleware:
    @pytest.fixture()
    def client(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        return TestClient(app)

    @patch("backend.routers.health.get_supabase_client")
    def test_request_id_header(self, mock_client, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock(data=[{"id": "1"}])
        )
        mock_client.return_value = mock_sb

        resp = client.get("/health")
        assert "x-request-id" in resp.headers

    def test_404_returns_json(self, client):
        resp = client.get("/nonexistent-endpoint")
        assert resp.status_code == 404
