"""Tests for FastAPI API endpoints."""

from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture()
def client():
    return TestClient(app)


# ── Health ─────────────────────────────────────────────────────────────


class TestHealthEndpoint:
    @patch("backend.routers.health.get_supabase_client")
    def test_health_healthy(self, mock_client, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock(data=[{"id": "1"}])
        )
        mock_client.return_value = mock_sb

        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["services"]["database"] == "healthy"

    @patch("backend.routers.health.get_supabase_client")
    def test_health_degraded(self, mock_client, client):
        mock_client.side_effect = RuntimeError("No DB")

        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "degraded"


# ── Ingestion ──────────────────────────────────────────────────────────


class TestIngestionEndpoint:
    @patch("backend.routers.ingestion.run_ingestion_pipeline")
    def test_ingest_returns_queued(self, mock_pipeline, client, sample_tool):
        mock_pipeline.return_value = {
            "tool": sample_tool,
            "alternatives": [],
            "comparison": None,
        }
        resp = client.post(
            "/api/v1/ingest",
            json={"url": "https://example-tool.ai", "category": "AI coding"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool"]["name"] == "TestTool"

    def test_ingest_invalid_url_format(self, client):
        resp = client.post("/api/v1/ingest", json={"url": "not-a-url"})
        assert resp.status_code == 422  # Pydantic validation


# ── Tools ──────────────────────────────────────────────────────────────


class TestToolsEndpoints:
    @patch("backend.routers.tools.list_tools")
    def test_list_tools(self, mock_list, client, sample_tool):
        mock_list.return_value = [sample_tool]
        resp = client.get("/api/v1/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "TestTool"

    @patch("backend.routers.tools.list_tools")
    def test_list_tools_empty(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/v1/tools")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.routers.tools.get_tools_by_category")
    def test_list_tools_by_category(self, mock_cat, client, sample_tool):
        mock_cat.return_value = [sample_tool]
        resp = client.get("/api/v1/tools?category=AI+coding")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("backend.routers.tools.get_tool_by_id")
    def test_get_tool_by_id(self, mock_get, client, sample_tool):
        mock_get.return_value = sample_tool
        resp = client.get(f"/api/v1/tools/{sample_tool['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "TestTool"

    @patch("backend.routers.tools.get_tool_by_id")
    def test_get_tool_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/v1/tools/missing-id")
        assert resp.status_code == 404


# ── Search ─────────────────────────────────────────────────────────────


class TestSearchEndpoint:
    @patch("backend.routers.search.generate_answer", new_callable=AsyncMock)
    @patch("backend.routers.search.vector_search")
    @patch("backend.routers.search.generate_embedding", new_callable=AsyncMock)
    def test_search_returns_results(
        self, mock_embed, mock_vsearch, mock_answer, client, sample_tool
    ):
        mock_embed.return_value = [0.1] * 384
        mock_vsearch.return_value = [{**sample_tool, "similarity": 0.9}]
        mock_answer.return_value = "TestTool is great for coding."

        resp = client.post("/api/v1/search", json={"query": "best coding tool"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "best coding tool"
        assert len(data["results"]) == 1
        assert data["answer"] is not None

    @patch("backend.routers.search.generate_embedding", new_callable=AsyncMock)
    def test_search_embedding_unavailable(self, mock_embed, client):
        mock_embed.return_value = None
        resp = client.post("/api/v1/search", json={"query": "test"})
        assert resp.status_code == 503


# ── Comparison ─────────────────────────────────────────────────────────


class TestComparisonEndpoint:
    @patch("backend.routers.comparison.compare_tools", new_callable=AsyncMock)
    @patch("backend.routers.comparison.get_tool_by_id")
    def test_compare_tools(self, mock_get, mock_compare, client, sample_tool):
        tool2 = {**sample_tool, "id": "ddd-eee-fff", "name": "AnotherTool"}
        mock_get.side_effect = [sample_tool, tool2]
        mock_compare.return_value = "TestTool is better for X, AnotherTool for Y."

        resp = client.post(
            "/api/v1/compare",
            json={"tool_ids": ["aaa-bbb-ccc", "ddd-eee-fff"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tools"]) == 2
        assert "comparison_text" in data

    @patch("backend.routers.comparison.get_tool_by_id")
    def test_compare_tool_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.post(
            "/api/v1/compare",
            json={"tool_ids": ["missing-1", "missing-2"]},
        )
        assert resp.status_code == 404
