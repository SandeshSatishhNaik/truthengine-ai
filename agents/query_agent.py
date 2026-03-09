"""Query Agent — handles natural language search and answer generation."""

from groq import Groq
from loguru import logger

from backend.config import get_settings
from backend.retry import retry

ANSWER_PROMPT = """You are TruthEngine AI, an expert assistant on AI tools. Use the retrieved context below to answer the user's question clearly and concisely.

Context (retrieved AI tool information):
{context}

User question: {query}

Instructions:
- Answer based ONLY on the provided context.
- If the context doesn't contain enough information, say so honestly.
- Be specific about pricing, features, and limitations.
- Keep the answer concise but informative.
"""


async def generate_answer(query: str, context_texts: list[str]) -> str | None:
    import time as _time
    from backend.metrics import metrics

    settings = get_settings()
    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY not configured")
        return None
    if not context_texts:
        return None

    metrics.agent_calls["query"].inc()
    start = _time.perf_counter()
    try:
        result = _call_groq_answer(query, context_texts)
        metrics.agent_latency["query"].observe(_time.perf_counter() - start)
        return result
    except Exception as e:
        metrics.agent_errors["query"].inc()
        metrics.agent_latency["query"].observe(_time.perf_counter() - start)
        logger.error(f"Answer generation failed permanently: {e}")
        return None


@retry(max_attempts=3, base_delay=1.5, retryable_exceptions=(Exception,))
def _call_groq_answer(query: str, context_texts: list[str]) -> str:
    """Call Groq LLM for answer generation. Retries on transient failures."""
    settings = get_settings()
    context = "\n\n".join(context_texts[:5])
    prompt = ANSWER_PROMPT.format(context=context, query=query)

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": "You are a helpful AI tool expert. Answer questions based on provided context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    answer = response.choices[0].message.content.strip()
    logger.info(f"Generated answer for query: {query[:50]}...")
    return answer
