"""Semantic search endpoints."""

import hashlib

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from backend.cache import search_cache, embedding_cache
from backend.middleware import limiter
from backend.models import SearchRequest, SearchResponse, SearchResult, ToolResponse
from agents.embedding_agent import generate_embedding
from agents.query_agent import generate_answer
from database.operations import vector_search

router = APIRouter()


def _query_cache_key(query: str, limit: int) -> str:
    h = hashlib.sha256(f"{query}:{limit}".encode()).hexdigest()[:16]
    return f"search:{h}"


@router.post("/search", response_model=SearchResponse)
@limiter.limit("20/minute")
async def semantic_search(request: Request, body: SearchRequest):
    """Perform semantic search across the AI tool knowledge base."""
    logger.info(f"Search query: {body.query}")

    # Check search cache
    cache_key = _query_cache_key(body.query, body.limit)
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    # Check embedding cache
    emb_key = f"emb:{hashlib.sha256(body.query.encode()).hexdigest()[:16]}"
    query_embedding = embedding_cache.get(emb_key)
    if query_embedding is None:
        query_embedding = await generate_embedding(body.query)
        if query_embedding is None:
            raise HTTPException(status_code=503, detail="Embedding service unavailable.")
        embedding_cache.set(emb_key, query_embedding)

    # Vector search
    raw_results = vector_search(query_embedding, limit=body.limit)

    results = []
    for row in raw_results:
        results.append(SearchResult(
            tool=ToolResponse(**{k: v for k, v in row.items() if k != "similarity"}),
            similarity=row.get("similarity", 0.0),
        ))

    # Generate natural language answer
    answer = None
    if results:
        context_texts = [
            f"{r.tool.name}: {r.tool.core_function or ''} — {r.tool.pricing_model or ''}"
            for r in results[:5]
        ]
        answer = await generate_answer(body.query, context_texts)

    response = SearchResponse(query=body.query, results=results, answer=answer)
    search_cache.set(cache_key, response)
    return response
