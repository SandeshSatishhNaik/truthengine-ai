"""Tool comparison endpoints."""

import hashlib

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from backend.cache import search_cache
from backend.middleware import limiter
from backend.models import CompareRequest, ComparisonResponse, ToolResponse
from agents.comparison_agent import compare_tools
from database.operations import get_tool_by_id

router = APIRouter()


@router.post("/compare", response_model=ComparisonResponse)
@limiter.limit("10/minute")
async def compare(request: Request, body: CompareRequest):
    """Compare multiple AI tools side by side."""
    cache_key = f"compare:{hashlib.sha256(':'.join(sorted(body.tool_ids)).encode()).hexdigest()[:16]}"
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    tools = []
    for tid in body.tool_ids:
        tool = get_tool_by_id(tid)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tid} not found.")
        tools.append(ToolResponse(**tool))

    comparison_text = await compare_tools(tools)

    result = ComparisonResponse(tools=tools, comparison_text=comparison_text)
    search_cache.set(cache_key, result)
    return result
