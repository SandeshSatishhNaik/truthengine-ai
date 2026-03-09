"""Tests for database CRUD operations."""

from unittest.mock import MagicMock, patch

import pytest

from database.operations import (
    create_tool,
    update_tool,
    get_tool_by_id,
    get_tool_by_website,
    list_tools,
    get_tools_by_category,
    create_source,
    get_sources_for_tool,
    create_review,
    get_reviews_for_tool,
    store_embedding,
    vector_search,
)


# ── Tool CRUD ──────────────────────────────────────────────────────────


class TestCreateTool:
    def test_creates_tool(self, mock_supabase, sample_tool):
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            MagicMock(data=[sample_tool])
        )
        result = create_tool({"name": "TestTool", "website": "https://testtool.ai"})
        assert result is not None
        assert result["id"] == "aaa-bbb-ccc"

    def test_returns_none_on_error(self, mock_supabase):
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
            Exception("DB error")
        )
        result = create_tool({"name": "TestTool"})
        assert result is None


class TestUpdateTool:
    def test_updates_tool(self, mock_supabase, sample_tool):
        updated = {**sample_tool, "name": "Updated"}
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[updated])
        )
        result = update_tool("aaa-bbb-ccc", {"name": "Updated"})
        assert result is not None
        assert result["name"] == "Updated"

    def test_returns_none_on_error(self, mock_supabase):
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = (
            Exception("DB error")
        )
        result = update_tool("aaa", {"name": "X"})
        assert result is None


class TestGetToolById:
    def test_returns_tool(self, mock_supabase, sample_tool):
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
            MagicMock(data=sample_tool)
        )
        result = get_tool_by_id("aaa-bbb-ccc")
        assert result["name"] == "TestTool"

    def test_returns_none_on_missing(self, mock_supabase):
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = (
            Exception("Not found")
        )
        assert get_tool_by_id("missing") is None


class TestGetToolByWebsite:
    def test_finds_by_website(self, mock_supabase, sample_tool):
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            MagicMock(data=[sample_tool])
        )
        result = get_tool_by_website("https://testtool.ai")
        assert result is not None
        assert result["website"] == "https://testtool.ai"

    def test_returns_none_for_unknown(self, mock_supabase):
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            MagicMock(data=[])
        )
        assert get_tool_by_website("https://unknown.ai") is None


class TestListTools:
    def test_returns_list(self, mock_supabase, sample_tool):
        mock_supabase.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = (
            MagicMock(data=[sample_tool])
        )
        result = list_tools(limit=10)
        assert len(result) == 1

    def test_returns_empty_on_error(self, mock_supabase):
        mock_supabase.table.return_value.select.return_value.order.return_value.range.return_value.execute.side_effect = (
            Exception("DB error")
        )
        assert list_tools() == []


class TestGetToolsByCategory:
    def test_filters_by_category(self, mock_supabase, sample_tool):
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = (
            MagicMock(data=[sample_tool])
        )
        result = get_tools_by_category("AI coding")
        assert len(result) == 1
        assert result[0]["category"] == "AI coding"


# ── Source CRUD ────────────────────────────────────────────────────────


class TestCreateSource:
    def test_creates_source(self, mock_supabase):
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            MagicMock(data=[{"id": "src-1", "tool_id": "aaa", "source_url": "https://x.com"}])
        )
        result = create_source("aaa", "https://x.com", "some content")
        assert result is not None

    def test_returns_none_on_error(self, mock_supabase):
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
            Exception("DB error")
        )
        assert create_source("aaa", "https://x.com", "content") is None


class TestGetSourcesForTool:
    def test_returns_sources(self, mock_supabase):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[{"id": "src-1"}])
        )
        result = get_sources_for_tool("aaa")
        assert len(result) == 1


# ── Review CRUD ────────────────────────────────────────────────────────


class TestCreateReview:
    def test_creates_review(self, mock_supabase):
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            MagicMock(data=[{"id": "rev-1", "tool_id": "aaa"}])
        )
        result = create_review("aaa", "Great tool!", "positive")
        assert result is not None


class TestGetReviewsForTool:
    def test_returns_reviews(self, mock_supabase):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[{"id": "rev-1"}])
        )
        result = get_reviews_for_tool("aaa")
        assert len(result) == 1


# ── Embeddings ─────────────────────────────────────────────────────────


class TestStoreEmbedding:
    def test_stores_embedding(self, mock_supabase):
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = (
            MagicMock()
        )
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )
        result = store_embedding("aaa", [0.1] * 384)
        assert result is True

    def test_returns_false_on_error(self, mock_supabase):
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.side_effect = (
            Exception("DB error")
        )
        assert store_embedding("aaa", [0.1] * 384) is False


class TestVectorSearch:
    def test_returns_results(self, mock_supabase):
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[{"tool_id": "aaa", "similarity": 0.95}]
        )
        result = vector_search([0.1] * 384, limit=5)
        assert len(result) == 1
        assert result[0]["similarity"] == 0.95

    def test_returns_empty_on_error(self, mock_supabase):
        mock_supabase.rpc.return_value.execute.side_effect = Exception("RPC error")
        assert vector_search([0.1] * 384) == []
