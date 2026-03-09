"""Tests for metrics collection and background scheduler."""

import time
from unittest.mock import patch, MagicMock

import pytest

from backend.metrics import MetricsCollector, _Counter, _Gauge, _Histogram


# ── Counter ──────────────────────────────────────────────────────────


class TestCounter:
    def test_initial_value_is_zero(self):
        c = _Counter()
        assert c.value == 0

    def test_inc_default(self):
        c = _Counter()
        c.inc()
        assert c.value == 1

    def test_inc_amount(self):
        c = _Counter()
        c.inc(5)
        assert c.value == 5

    def test_reset(self):
        c = _Counter()
        c.inc(10)
        c.reset()
        assert c.value == 0


# ── Gauge ────────────────────────────────────────────────────────────


class TestGauge:
    def test_initial_value_is_zero(self):
        g = _Gauge()
        assert g.value == 0.0

    def test_set(self):
        g = _Gauge()
        g.set(42.5)
        assert g.value == 42.5

    def test_inc(self):
        g = _Gauge()
        g.inc()
        g.inc(3)
        assert g.value == 4.0

    def test_dec(self):
        g = _Gauge()
        g.set(10)
        g.dec(3)
        assert g.value == 7.0


# ── Histogram ────────────────────────────────────────────────────────


class TestHistogram:
    def test_empty_summary(self):
        h = _Histogram()
        s = h.summary  # property, not method
        assert s["count"] == 0
        assert s["avg"] == 0

    def test_observe_updates_stats(self):
        h = _Histogram()
        h.observe(1.0)
        h.observe(3.0)
        h.observe(2.0)
        s = h.summary
        assert s["count"] == 3
        assert s["min"] == 1.0
        assert s["max"] == 3.0
        assert s["avg"] == 2.0
        assert s["total"] == 6.0


# ── MetricsCollector ─────────────────────────────────────────────────


class TestMetricsCollector:
    def test_snapshot_returns_dict(self):
        m = MetricsCollector()
        snap = m.snapshot()
        assert isinstance(snap, dict)
        assert "requests" in snap
        assert "uptime_seconds" in snap

    def test_requests_total_increments(self):
        m = MetricsCollector()
        m.requests_total.inc()
        m.requests_total.inc()
        assert m.snapshot()["requests"]["total"] == 2

    def test_request_latency_records(self):
        m = MetricsCollector()
        m.request_latency.observe(0.5)
        m.request_latency.observe(1.5)
        snap = m.snapshot()
        lat = snap["requests"]["latency"]
        assert lat["count"] == 2
        assert lat["avg"] == 1.0

    def test_by_method_defaultdict(self):
        m = MetricsCollector()
        m.requests_by_method["GET"].inc()
        m.requests_by_method["GET"].inc()
        m.requests_by_method["POST"].inc()
        snap = m.snapshot()
        assert snap["requests"]["by_method"]["GET"] == 2
        assert snap["requests"]["by_method"]["POST"] == 1

    def test_by_status_defaultdict(self):
        m = MetricsCollector()
        m.requests_by_status[200].inc(5)
        m.requests_by_status[404].inc()
        snap = m.snapshot()
        assert snap["requests"]["by_status"]["200"] == 5
        assert snap["requests"]["by_status"]["404"] == 1

    def test_agent_metrics(self):
        m = MetricsCollector()
        m.agent_calls["extraction"].inc()
        m.agent_errors["extraction"].inc()
        m.agent_latency["extraction"].observe(2.0)
        snap = m.snapshot()
        assert snap["agents"]["extraction"]["calls"] == 1
        assert snap["agents"]["extraction"]["errors"] == 1
        assert snap["agents"]["extraction"]["latency"]["count"] == 1

    def test_cache_metrics(self):
        m = MetricsCollector()
        m.cache_hits.inc(10)
        m.cache_misses.inc(3)
        snap = m.snapshot()
        assert snap["cache"]["hits"] == 10
        assert snap["cache"]["misses"] == 3

    def test_crawl_metrics(self):
        m = MetricsCollector()
        m.crawl_requests.inc(5)
        m.crawl_failures.inc()
        m.pages_crawled.inc(4)
        snap = m.snapshot()
        assert snap["crawler"]["requests"] == 5
        assert snap["crawler"]["failures"] == 1
        assert snap["crawler"]["pages_crawled"] == 4

    def test_ingestion_metrics(self):
        m = MetricsCollector()
        m.ingestions_started.inc(3)
        m.ingestions_completed.inc(2)
        m.ingestions_failed.inc()
        snap = m.snapshot()
        assert snap["ingestion"]["started"] == 3
        assert snap["ingestion"]["completed"] == 2
        assert snap["ingestion"]["failed"] == 1

    def test_uptime_is_positive(self):
        m = MetricsCollector()
        time.sleep(0.15)
        assert m.snapshot()["uptime_seconds"] > 0

    def test_cache_hit_rate(self):
        m = MetricsCollector()
        m.cache_hits.inc(3)
        m.cache_misses.inc(1)
        snap = m.snapshot()
        assert snap["cache"]["hit_rate"] == 0.75


# ── Scheduler ────────────────────────────────────────────────────────


class TestScheduler:
    def test_setup_scheduler_creates_scheduler(self):
        """Test that setup_scheduler creates an AsyncIOScheduler with expected jobs."""
        import backend.scheduler as sched_module
        sched_module._scheduler = None

        scheduler = sched_module.setup_scheduler()
        jobs = scheduler.get_jobs()
        job_ids = [j.id for j in jobs]

        assert "discovery" in job_ids
        assert "cache_cleanup" in job_ids
        assert "metrics_snapshot" in job_ids

        sched_module._scheduler = None

    def test_get_scheduler_returns_singleton(self):
        """Test that get_scheduler returns the same instance."""
        import backend.scheduler as sched_module
        sched_module._scheduler = None

        s1 = sched_module.get_scheduler()
        s2 = sched_module.get_scheduler()
        assert s1 is s2

        sched_module._scheduler = None

    def test_wrap_job_tracks_metrics(self):
        """Test that _wrap_job increments job metrics on success."""
        from backend.scheduler import _wrap_job
        from backend.metrics import metrics

        initial_val = metrics.jobs_executed["test_job"].value

        def dummy_func():
            pass

        wrapped = _wrap_job("test_job", dummy_func)
        wrapped()

        assert metrics.jobs_executed["test_job"].value == initial_val + 1

    def test_wrap_job_tracks_failures(self):
        """Test that _wrap_job increments failure metrics on error."""
        from backend.scheduler import _wrap_job
        from backend.metrics import metrics

        initial_failures = metrics.jobs_failed["fail_job"].value

        def failing_func():
            raise RuntimeError("boom")

        wrapped = _wrap_job("fail_job", failing_func)
        wrapped()  # should not raise, just log

        assert metrics.jobs_failed["fail_job"].value == initial_failures + 1


# ── Metrics endpoint (via TestClient) ────────────────────────────────


class TestMetricsEndpoint:
    @patch("backend.scheduler.setup_scheduler")
    @patch("backend.routers.health.get_supabase_client")
    def test_metrics_endpoint_returns_json(self, mock_db, mock_sched):
        from fastapi.testclient import TestClient

        mock_sched.return_value = MagicMock()
        mock_db.side_effect = Exception("no db")

        from backend.main import create_app
        app = create_app()
        client = TestClient(app)

        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "requests" in data
        assert "uptime_seconds" in data
        assert "cache" in data

    @patch("backend.scheduler.setup_scheduler")
    @patch("backend.routers.health.get_supabase_client")
    def test_health_includes_scheduler_and_cache(self, mock_db, mock_sched):
        from fastapi.testclient import TestClient

        mock_sched.return_value = MagicMock()
        mock_db.side_effect = Exception("no db")

        from backend.main import create_app
        app = create_app()
        client = TestClient(app)

        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "scheduler" in data["services"]
        assert "cache_entries" in data["services"]
