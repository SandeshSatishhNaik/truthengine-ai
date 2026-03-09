"""Rate limiting, security middleware, and global error handling."""

import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from backend.metrics import metrics

# Default rate limit — overridden at runtime via app.state.limiter if needed
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Adds request ID, logs every request/response, and catches unhandled errors."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        start = time.perf_counter()

        metrics.requests_total.inc()
        metrics.requests_by_method[request.method].inc()
        metrics.requests_by_path[request.url.path].inc()
        metrics.active_requests.inc()

        # Bind request context to logger for this request
        with logger.contextualize(request_id=request_id):
            logger.info(
                "request_started",
                method=request.method,
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )

            try:
                response = await call_next(request)
            except Exception as exc:
                elapsed = time.perf_counter() - start
                metrics.active_requests.dec()
                metrics.requests_by_status[500].inc()
                metrics.request_latency.observe(elapsed)
                logger.exception(
                    "unhandled_exception",
                    method=request.method,
                    path=request.url.path,
                    elapsed_ms=round(elapsed * 1000, 2),
                )
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error."},
                    headers={"X-Request-ID": request_id},
                )

            elapsed = time.perf_counter() - start
            metrics.active_requests.dec()
            metrics.requests_by_status[response.status_code].inc()
            metrics.request_latency.observe(elapsed)
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                elapsed_ms=round(elapsed * 1000, 2),
            )
            response.headers["X-Request-ID"] = request_id
            return response
