"""Health check and metrics endpoints."""

from fastapi import APIRouter, Request
from loguru import logger

from backend.cache import tools_cache, search_cache, embedding_cache
from backend.metrics import metrics
from backend.middleware import limiter
from backend.models import HealthResponse
from database.connection import get_supabase_client

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
async def health_check(request: Request):
    services = {}

    # Check Supabase
    try:
        client = get_supabase_client()
        client.table("tools").select("id").limit(1).execute()
        services["database"] = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        services["database"] = "unavailable"

    services["scheduler"] = "healthy"
    services["cache_entries"] = str(tools_cache.size + search_cache.size + embedding_cache.size)

    overall = "healthy" if services["database"] == "healthy" else "degraded"
    return HealthResponse(status=overall, services=services)


@router.get("/metrics")
@limiter.limit("30/minute")
async def get_metrics(request: Request):
    """Return current application metrics snapshot."""
    return metrics.snapshot()
