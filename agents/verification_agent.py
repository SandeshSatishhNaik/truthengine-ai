"""Truth Verification Agent — cross-checks extracted info against multiple sources."""

import json

from groq import Groq
from loguru import logger

from backend.config import get_settings
from backend.retry import retry

VERIFICATION_PROMPT = """You are a fact-checking AI. Given the extracted information about an AI tool and the raw source texts, verify the accuracy of each claim.

Extracted information:
{extracted_info}

Raw sources:
{sources}

For each field, determine if the information is:
- VERIFIED: Confirmed by multiple sources
- PARTIALLY_VERIFIED: Found in at least one source but not fully confirmed
- UNVERIFIED: Cannot be confirmed from sources

Return ONLY valid JSON:
{{
    "tool_name": {{"status": "VERIFIED|PARTIALLY_VERIFIED|UNVERIFIED", "notes": ""}},
    "core_function": {{"status": "VERIFIED|PARTIALLY_VERIFIED|UNVERIFIED", "notes": ""}},
    "pricing_model": {{"status": "VERIFIED|PARTIALLY_VERIFIED|UNVERIFIED", "notes": ""}},
    "free_tier_limits": {{"status": "VERIFIED|PARTIALLY_VERIFIED|UNVERIFIED", "notes": ""}},
    "community_verdict": {{"status": "VERIFIED|PARTIALLY_VERIFIED|UNVERIFIED", "notes": ""}},
    "trust_score": 0.0
}}

trust_score should be between 0.0 and 1.0 based on overall confidence."""


def verify_extraction(extracted_info: dict, sources_text: list[str]) -> dict:
    import time as _time
    from backend.metrics import metrics

    settings = get_settings()
    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY not configured")
        return {"trust_score": 0.0}

    metrics.agent_calls["verification"].inc()
    start = _time.perf_counter()
    try:
        result = _call_groq_verification(extracted_info, sources_text)
        metrics.agent_latency["verification"].observe(_time.perf_counter() - start)
        return result
    except Exception as e:
        metrics.agent_errors["verification"].inc()
        metrics.agent_latency["verification"].observe(_time.perf_counter() - start)
        logger.error(f"Verification agent failed permanently: {e}")
        return {"trust_score": 0.0}


@retry(max_attempts=3, base_delay=2.0, retryable_exceptions=(Exception,))
def _call_groq_verification(extracted_info: dict, sources_text: list[str]) -> dict:
    """Call Groq LLM to verify extraction. Retries on transient failures."""
    settings = get_settings()

    combined_sources = "\n\n---\n\n".join(s[:2000] for s in sources_text[:5])
    prompt = VERIFICATION_PROMPT.format(
        extracted_info=json.dumps(extracted_info, indent=2),
        sources=combined_sources,
    )

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": "You are a fact-checking assistant. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=1024,
    )

    raw_text = response.choices[0].message.content.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()

    report = json.loads(raw_text)
    trust_score = float(report.get("trust_score", 0.0))
    trust_score = max(0.0, min(1.0, trust_score))
    report["trust_score"] = trust_score

    logger.info(f"Verification complete — trust score: {trust_score}")
    return report
