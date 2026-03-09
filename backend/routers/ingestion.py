"""URL ingestion endpoints."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from backend.middleware import limiter
from backend.models import IngestURLRequest, AnalysisReport
from workers.ingestion_worker import run_ingestion_pipeline

router = APIRouter()

# Dedicated thread pool so ingestion doesn't starve other requests
_ingest_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ingest")

# Maximum time (seconds) before the endpoint gives up
_INGEST_TIMEOUT = 180  # 3 minutes


@router.post("/ingest", response_model=AnalysisReport)
@limiter.limit("10/minute")
async def ingest_url(request: Request, body: IngestURLRequest):
    """Submit a URL for AI tool ingestion, analysis, alternatives, and comparison."""
    url_str = str(body.url)
    logger.info(f"Ingestion request received: {url_str}")

    loop = asyncio.get_event_loop()
    try:
        report = await asyncio.wait_for(
            loop.run_in_executor(_ingest_pool, run_ingestion_pipeline, url_str, body.category),
            timeout=_INGEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error(f"Ingestion timed out after {_INGEST_TIMEOUT}s for: {url_str}")
        raise HTTPException(status_code=504, detail=f"Ingestion timed out after {_INGEST_TIMEOUT}s. The site may be slow or blocking crawlers.")

    if report is None:
        raise HTTPException(status_code=422, detail="Ingestion failed. Could not crawl or extract tool info.")

    return report
