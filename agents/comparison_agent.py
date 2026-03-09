"""Comparison Agent — compares AI tools using Groq LLM."""

from groq import Groq
from loguru import logger

from backend.config import get_settings
from backend.models import ToolResponse
from backend.retry import retry

COMPARISON_PROMPT = """You are TruthEngine AI, an expert at comparing AI tools. Compare the following tools based on features, pricing, and limitations.

Tools to compare:
{tools_info}

Provide a structured comparison covering:
1. **Core Features** — What each tool does
2. **Pricing** — Free tier limits and paid plans
3. **Strengths** — Key advantages of each
4. **Weaknesses** — Limitations of each
5. **Verdict** — Which tool is best for different use cases

Be factual and balanced. Use only the provided information."""


async def compare_tools(tools: list[ToolResponse]) -> str:
    import time as _time
    from backend.metrics import metrics

    settings = get_settings()
    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY not configured")
        return "Comparison service unavailable."

    metrics.agent_calls["comparison"].inc()
    start = _time.perf_counter()
    try:
        result = _call_groq_comparison(tools)
        metrics.agent_latency["comparison"].observe(_time.perf_counter() - start)
        return result
    except Exception as e:
        metrics.agent_errors["comparison"].inc()
        metrics.agent_latency["comparison"].observe(_time.perf_counter() - start)
        logger.error(f"Comparison agent failed permanently: {e}")
        return "An error occurred while generating the comparison."


@retry(max_attempts=3, base_delay=1.5, retryable_exceptions=(Exception,))
def _call_groq_comparison(tools: list[ToolResponse]) -> str:
    """Call Groq LLM for comparison. Retries on transient failures."""
    settings = get_settings()
    tools_info = "\n\n".join(
        f"**{t.name}**\n"
        f"- Function: {t.core_function or 'N/A'}\n"
        f"- Pricing: {t.pricing_model or 'N/A'}\n"
        f"- Free tier: {t.free_tier_limits or 'N/A'}\n"
        f"- Community: {t.community_verdict or 'N/A'}\n"
        f"- Trust score: {t.trust_score or 'N/A'}"
        for t in tools
    )

    prompt = COMPARISON_PROMPT.format(tools_info=tools_info)

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": "You are an unbiased AI tool comparison expert."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()
