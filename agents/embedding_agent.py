"""Embedding Agent — generates vector embeddings using HuggingFace Inference API."""

import asyncio
from loguru import logger

from backend.config import get_settings
from backend.retry import async_retry


@async_retry(max_attempts=3, base_delay=2.0, retryable_exceptions=(Exception,))
async def generate_embedding(text: str) -> list[float] | None:
    """
    Generate a vector embedding for the given text using HuggingFace's free Inference API.
    Returns a list of floats or None on failure.
    """
    import time as _time
    from backend.metrics import metrics
    from huggingface_hub import InferenceClient

    settings = get_settings()
    if not settings.hf_api_token:
        logger.error("HF_API_TOKEN not configured")
        return None

    metrics.agent_calls["embedding"].inc()
    start = _time.perf_counter()

    # Truncate text to avoid exceeding model limits
    truncated = text[:512]

    try:
        client = InferenceClient(token=settings.hf_api_token)
        result = await asyncio.to_thread(
            client.feature_extraction, truncated, model=settings.embedding_model
        )
        embedding = result.flatten().tolist()

        if embedding and len(embedding) > 0:
            metrics.agent_latency["embedding"].observe(_time.perf_counter() - start)
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
        logger.warning(f"Unexpected embedding result: {type(result)}")
        metrics.agent_errors["embedding"].inc()
        return None
    except Exception:
        metrics.agent_errors["embedding"].inc()
        raise


async def generate_tool_embedding(tool_data: dict) -> list[float] | None:
    """
    Generate an embedding for a tool by combining its key fields into a text representation.
    """
    parts = [
        tool_data.get("name", ""),
        tool_data.get("core_function", ""),
        tool_data.get("pricing_model", ""),
        tool_data.get("category", ""),
    ]
    tags = tool_data.get("tags", [])
    if tags:
        parts.append(" ".join(tags))

    text = " — ".join(p for p in parts if p)
    if not text.strip():
        return None

    return await generate_embedding(text)
