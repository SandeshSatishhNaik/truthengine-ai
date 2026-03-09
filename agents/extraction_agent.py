"""AI Extraction Agent — uses Groq LLM to extract structured tool info from crawled content."""

import json

from groq import Groq
from loguru import logger

from backend.config import get_settings
from backend.models import ToolExtraction
from backend.retry import retry

EXTRACTION_PROMPT = """You are an AI tool analyst. Analyze the provided sources about an AI tool and extract structured information.

Sources:
{sources}

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
    "tool_name": "Name of the tool",
    "core_function": "What the tool does in 1-2 sentences",
    "pricing_model": "Pricing details (free, freemium, paid, etc.)",
    "free_tier_limits": "Specific limits of the free tier",
    "community_verdict": "General community opinion in 1-2 sentences",
    "tags": ["tag1", "tag2", "tag3"]
}}

If information is not available for a field, use an empty string or empty list.
Be factual and precise. Do not hallucinate information not present in the sources."""


def extract_tool_info(sources_text: list[str]) -> ToolExtraction | None:
    import time as _time
    from backend.metrics import metrics

    settings = get_settings()
    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY not configured")
        return None

    metrics.agent_calls["extraction"].inc()
    start = _time.perf_counter()
    try:
        result = _call_groq_extraction(sources_text)
        metrics.agent_latency["extraction"].observe(_time.perf_counter() - start)
        return result
    except Exception as e:
        metrics.agent_errors["extraction"].inc()
        metrics.agent_latency["extraction"].observe(_time.perf_counter() - start)
        logger.error(f"Extraction agent failed permanently: {e}")
        return None


@retry(max_attempts=3, base_delay=2.0, retryable_exceptions=(Exception,))
def _call_groq_extraction(sources_text: list[str]) -> ToolExtraction | None:
    """
    Call Groq LLM to extract structured tool information from source texts.
    Retries up to 3 times on transient failures.
    """
    settings = get_settings()

    combined_sources = "\n\n---\n\n".join(s[:3000] for s in sources_text[:5])
    prompt = EXTRACTION_PROMPT.format(sources=combined_sources)

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": "You are a precise data extraction assistant. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=1024,
    )

    raw_text = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()

    data = json.loads(raw_text)
    extraction = ToolExtraction(**data)
    logger.info(f"Extracted tool info: {extraction.tool_name}")
    return extraction
