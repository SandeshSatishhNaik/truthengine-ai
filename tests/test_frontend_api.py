"""Tests for frontend API client types — ensures backend and frontend models agree."""

import pytest

from backend.models import (
    ToolResponse,
    SearchResponse,
    SearchResult,
    ComparisonResponse,
    IngestURLRequest,
    IngestionStatus,
)


class TestToolResponseModel:
    def test_constructs_from_full_dict(self, sample_tool):
        t = ToolResponse(**sample_tool)
        assert t.name == "TestTool"
        assert t.tags == ["coding", "ai", "free"]

    def test_handles_none_tags(self, sample_tool):
        sample_tool["tags"] = None
        t = ToolResponse(**sample_tool)
        assert t.tags is None

    def test_handles_missing_optional_fields(self):
        t = ToolResponse(id="x", name="Minimal")
        assert t.core_function is None
        assert t.tags == []

    def test_extra_fields_ignored(self, sample_tool):
        sample_tool["unknown_field"] = "should be ignored"
        t = ToolResponse(**sample_tool)
        assert t.name == "TestTool"


class TestSearchResponseModel:
    def test_search_response_with_results(self, sample_tool):
        tool = ToolResponse(**sample_tool)
        sr = SearchResult(tool=tool, similarity=0.91)
        resp = SearchResponse(query="test", results=[sr], answer="A great tool.")
        assert resp.query == "test"
        assert len(resp.results) == 1
        assert resp.answer == "A great tool."

    def test_search_response_no_answer(self, sample_tool):
        resp = SearchResponse(query="q", results=[], answer=None)
        assert resp.answer is None


class TestComparisonResponseModel:
    def test_comparison_response(self, sample_tool):
        tool = ToolResponse(**sample_tool)
        resp = ComparisonResponse(
            tools=[tool], comparison_text="Tool A is better for X."
        )
        assert len(resp.tools) == 1
        assert "better" in resp.comparison_text


class TestIngestURLRequest:
    def test_valid_url(self):
        req = IngestURLRequest(url="https://example.ai")
        assert str(req.url) == "https://example.ai/"

    def test_with_category(self):
        req = IngestURLRequest(url="https://example.ai", category="coding")
        assert req.category == "coding"


class TestIngestionStatus:
    def test_queued_status(self):
        status = IngestionStatus(url="https://x.ai", status="queued", message="OK")
        assert status.status == "queued"
