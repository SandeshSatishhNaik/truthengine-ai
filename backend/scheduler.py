"""Background job scheduler for periodic tasks.

Uses APScheduler to run recurring jobs like:
- Tool discovery
- Cache cleanup
- Stale data refresh
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from backend.metrics import metrics

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(
            job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 120},
        )
    return _scheduler


def _wrap_job(name: str, func):
    """Wrap a job function with metrics and error handling."""

    def wrapper():
        logger.info(f"Scheduled job started: {name}")
        metrics.jobs_executed[name].inc()
        try:
            func()
            logger.info(f"Scheduled job completed: {name}")
        except Exception as e:
            metrics.jobs_failed[name].inc()
            logger.error(f"Scheduled job failed: {name} — {e}")

    wrapper.__name__ = f"job_{name}"
    return wrapper


def _cache_cleanup_job():
    """Evict expired entries from all caches."""
    from backend.cache import tools_cache, search_cache, embedding_cache

    before = tools_cache.size + search_cache.size + embedding_cache.size
    tools_cache._evict_expired()
    search_cache._evict_expired()
    embedding_cache._evict_expired()
    after = tools_cache.size + search_cache.size + embedding_cache.size
    logger.debug(f"Cache cleanup: {before} → {after} entries")


def _stale_check_job():
    """Log metrics snapshot for monitoring."""
    snap = metrics.snapshot()
    logger.info(
        "metrics_snapshot",
        uptime=snap["uptime_seconds"],
        total_requests=snap["requests"]["total"],
        cache_hit_rate=snap["cache"]["hit_rate"],
        ingestions=snap["ingestion"]["completed"],
    )


def _discovery_job():
    """Run AI tool discovery across default categories."""
    from agents.discovery_agent import run_discovery

    results = run_discovery(max_per_category=3)
    logger.info(f"Discovery found {len(results)} potential tools")


def setup_scheduler() -> AsyncIOScheduler:
    """Configure and return the scheduler with default jobs."""
    scheduler = get_scheduler()

    # Discovery: every 6 hours
    scheduler.add_job(
        _wrap_job("discovery", _discovery_job),
        trigger=IntervalTrigger(hours=6),
        id="discovery",
        replace_existing=True,
    )

    # Cache cleanup: every 10 minutes
    scheduler.add_job(
        _wrap_job("cache_cleanup", _cache_cleanup_job),
        trigger=IntervalTrigger(minutes=10),
        id="cache_cleanup",
        replace_existing=True,
    )

    # Metrics snapshot: every 5 minutes
    scheduler.add_job(
        _wrap_job("metrics_snapshot", _stale_check_job),
        trigger=IntervalTrigger(minutes=5),
        id="metrics_snapshot",
        replace_existing=True,
    )

    logger.info("Background scheduler configured with 3 jobs")
    return scheduler
