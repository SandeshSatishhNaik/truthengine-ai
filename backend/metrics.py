"""Lightweight in-process metrics collection for TruthEngine AI.

Tracks request counts, latencies, cache hit rates, agent calls, crawler stats,
and job execution. Designed for single-process deployments (PythonAnywhere).
No external dependencies required.
"""

import time
import threading
from collections import defaultdict
from typing import Any


class _Counter:
    """Thread-safe monotonic counter."""

    __slots__ = ("_value", "_lock")

    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def inc(self, amount: int = 1) -> None:
        with self._lock:
            self._value += amount

    @property
    def value(self) -> int:
        return self._value

    def reset(self) -> None:
        with self._lock:
            self._value = 0


class _Gauge:
    """Thread-safe gauge (can go up or down)."""

    __slots__ = ("_value", "_lock")

    def __init__(self) -> None:
        self._value: float = 0
        self._lock = threading.Lock()

    def set(self, value: float) -> None:
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1) -> None:
        with self._lock:
            self._value -= amount

    @property
    def value(self) -> float:
        return self._value


class _Histogram:
    """Thread-safe histogram for latency/duration tracking."""

    __slots__ = ("_count", "_total", "_min", "_max", "_lock")

    def __init__(self) -> None:
        self._count = 0
        self._total = 0.0
        self._min = float("inf")
        self._max = 0.0
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        with self._lock:
            self._count += 1
            self._total += value
            if value < self._min:
                self._min = value
            if value > self._max:
                self._max = value

    @property
    def count(self) -> int:
        return self._count

    @property
    def avg(self) -> float:
        return self._total / self._count if self._count else 0.0

    @property
    def summary(self) -> dict[str, Any]:
        with self._lock:
            return {
                "count": self._count,
                "total": round(self._total, 4),
                "avg": round(self._total / self._count, 4) if self._count else 0,
                "min": round(self._min, 4) if self._count else 0,
                "max": round(self._max, 4) if self._count else 0,
            }

    def reset(self) -> None:
        with self._lock:
            self._count = 0
            self._total = 0.0
            self._min = float("inf")
            self._max = 0.0


class MetricsCollector:
    """Centralized metrics registry for the application."""

    def __init__(self) -> None:
        self._start_time = time.monotonic()

        # Request metrics
        self.requests_total = _Counter()
        self.requests_by_method = defaultdict(_Counter)
        self.requests_by_status = defaultdict(_Counter)
        self.requests_by_path = defaultdict(_Counter)
        self.request_latency = _Histogram()

        # Cache metrics
        self.cache_hits = _Counter()
        self.cache_misses = _Counter()

        # Agent metrics
        self.agent_calls = defaultdict(_Counter)    # keyed by agent name
        self.agent_errors = defaultdict(_Counter)
        self.agent_latency = defaultdict(_Histogram)  # keyed by agent name

        # Crawler metrics
        self.crawl_requests = _Counter()
        self.crawl_failures = _Counter()
        self.crawl_latency = _Histogram()
        self.pages_crawled = _Counter()

        # Ingestion pipeline metrics
        self.ingestions_started = _Counter()
        self.ingestions_completed = _Counter()
        self.ingestions_failed = _Counter()

        # Scheduler metrics
        self.jobs_executed = defaultdict(_Counter)
        self.jobs_failed = defaultdict(_Counter)

        # Active connections
        self.active_requests = _Gauge()

    @property
    def uptime_seconds(self) -> float:
        return time.monotonic() - self._start_time

    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time snapshot of all metrics."""
        return {
            "uptime_seconds": round(self.uptime_seconds, 1),
            "requests": {
                "total": self.requests_total.value,
                "active": self.active_requests.value,
                "by_method": {k: v.value for k, v in self.requests_by_method.items()},
                "by_status": {str(k): v.value for k, v in self.requests_by_status.items()},
                "latency": self.request_latency.summary,
            },
            "cache": {
                "hits": self.cache_hits.value,
                "misses": self.cache_misses.value,
                "hit_rate": round(
                    self.cache_hits.value
                    / max(self.cache_hits.value + self.cache_misses.value, 1),
                    4,
                ),
            },
            "agents": {
                name: {
                    "calls": self.agent_calls[name].value,
                    "errors": self.agent_errors[name].value,
                    "latency": self.agent_latency[name].summary,
                }
                for name in self.agent_calls
            },
            "crawler": {
                "requests": self.crawl_requests.value,
                "failures": self.crawl_failures.value,
                "pages_crawled": self.pages_crawled.value,
                "latency": self.crawl_latency.summary,
            },
            "ingestion": {
                "started": self.ingestions_started.value,
                "completed": self.ingestions_completed.value,
                "failed": self.ingestions_failed.value,
            },
            "scheduler": {
                name: {
                    "executed": self.jobs_executed[name].value,
                    "failed": self.jobs_failed[name].value,
                }
                for name in self.jobs_executed
            },
        }


# Global singleton
metrics = MetricsCollector()
