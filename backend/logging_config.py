"""Logging configuration for TruthEngine AI."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(debug: bool = False):
    """Configure loguru logger with structured fields and rotation."""
    Path("logs").mkdir(exist_ok=True)
    logger.remove()  # Remove all default handlers

    # Structured format with request_id support
    CONSOLE_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        "{extra[formatted_rid]} - "
        "<level>{message}</level>"
    )

    JSON_FORMAT = (
        "{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | "
        "{level: <8} | "
        "{name}:{function}:{line}"
        "{extra[formatted_rid]} - "
        "{message}"
    )

    def _format_rid(record):
        """Inject formatted request_id into extra for log output."""
        rid = record["extra"].get("request_id", "")
        record["extra"]["formatted_rid"] = f" [{rid}]" if rid else ""

    logger.configure(patcher=_format_rid)

    # Console output
    logger.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level="DEBUG" if debug else "INFO",
        colorize=True,
    )

    # File output (rotating) — structured for log aggregation
    logger.add(
        "logs/truthengine.log",
        format=JSON_FORMAT,
        level="DEBUG" if debug else "INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,  # thread-safe async writing
    )

    # Error-only file
    logger.add(
        "logs/errors.log",
        format=JSON_FORMAT,
        level="ERROR",
        rotation="5 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=True,  # include full traceback for errors
        diagnose=False,  # don't leak variable values in production
    )

    logger.info("Logging initialized", debug=debug)
