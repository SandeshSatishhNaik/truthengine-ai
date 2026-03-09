"""Tool CRUD endpoints."""

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from backend.cache import tools_cache
from backend.middleware import limiter
from backend.models import ToolResponse, UpdateToolRequest, AlternativeTool
from backend.services.alternatives_service import get_alternatives
from database.operations import get_tool_by_id, list_tools, get_tools_by_category, delete_tool, update_tool

router = APIRouter()


@router.get("/tools", response_model=list[ToolResponse])
@limiter.limit("30/minute")
async def get_tools(request: Request, category: str | None = None, limit: int = 20, offset: int = 0):
    """List all tools, optionally filtered by category."""
    cache_key = f"tools:{category}:{limit}:{offset}"
    cached = tools_cache.get(cache_key)
    if cached is not None:
        return cached

    if category:
        rows = get_tools_by_category(category, limit=limit, offset=offset)
    else:
        rows = list_tools(limit=limit, offset=offset)

    result = [ToolResponse(**row) for row in rows]
    tools_cache.set(cache_key, result)
    return result


@router.get("/tools/{tool_id}", response_model=ToolResponse)
@limiter.limit("30/minute")
async def get_tool(request: Request, tool_id: str):
    """Get a single tool by ID."""
    cache_key = f"tool:{tool_id}"
    cached = tools_cache.get(cache_key)
    if cached is not None:
        return cached

    tool = get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")
    result = ToolResponse(**tool)
    tools_cache.set(cache_key, result)
    return result


@router.patch("/tools/{tool_id}", response_model=ToolResponse)
@limiter.limit("20/minute")
async def patch_tool(request: Request, tool_id: str, body: UpdateToolRequest):
    """Update tool fields (category, pricing, tags)."""
    tool = get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    updated = update_tool(tool_id, updates)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update tool.")
    tools_cache.clear()
    return ToolResponse(**updated)


@router.delete("/tools/{tool_id}")
@limiter.limit("10/minute")
async def remove_tool(request: Request, tool_id: str):
    """Delete a tool and all related data."""
    tool = get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")
    
    success = delete_tool(tool_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete tool.")
    
    # Invalidate cache
    tools_cache.clear()
    return {"message": f"Tool '{tool.get('name', tool_id)}' deleted successfully."}


@router.get("/tools/{tool_id}/alternatives", response_model=list[AlternativeTool])
@limiter.limit("20/minute")
async def get_tool_alternatives(request: Request, tool_id: str, limit: int = 5):
    """Return top-N similar tools based on embedding similarity."""
    tool = get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")

    limit = min(limit, 10)
    alternatives = get_alternatives(tool_id, limit=limit)
    return alternatives
