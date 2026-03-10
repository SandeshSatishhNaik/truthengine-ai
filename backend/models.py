"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


# --- Request Models ---

class IngestURLRequest(BaseModel):
    url: HttpUrl
    category: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class CompareRequest(BaseModel):
    tool_ids: list[str] = Field(..., min_length=2, max_length=5)


class UpdateToolRequest(BaseModel):
    category: Optional[str] = None
    pricing_model: Optional[str] = None
    tags: Optional[list[str]] = None


# --- Response Models ---

class ToolResponse(BaseModel):
    id: str
    name: str
    website: Optional[str] = None
    category: Optional[str] = None
    core_function: Optional[str] = None
    pricing_model: Optional[str] = None
    free_tier_limits: Optional[str] = None
    community_verdict: Optional[str] = None
    trust_score: Optional[float] = None
    tags: Optional[list[str]] = []
    source_type: Optional[str] = "submitted"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ToolExtraction(BaseModel):
    """Structured AI extraction output."""
    tool_name: str
    core_function: str = ""
    pricing_model: str = ""
    free_tier_limits: str = ""
    community_verdict: str = ""
    tags: list[str] = []


class SearchResult(BaseModel):
    tool: ToolResponse
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    answer: Optional[str] = None


class ComparisonResponse(BaseModel):
    tools: list[ToolResponse]
    comparison_text: str


class IngestionStatus(BaseModel):
    url: str
    status: str
    tool_id: Optional[str] = None
    message: str = ""


class AlternativeTool(BaseModel):
    """A similar/alternative tool found during analysis."""
    tool: ToolResponse
    similarity: Optional[float] = None
    source: str = ""  # "knowledge_base" or "web_discovery"


class AnalysisReport(BaseModel):
    """Full analysis report returned after ingesting a tool."""
    tool: ToolResponse
    alternatives: list[AlternativeTool] = []
    comparison: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"
    services: dict[str, str] = {}
