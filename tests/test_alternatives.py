"""Tests for the alternatives endpoint and service."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture()
def client():
    return TestClient(app)


SAMPLE_TOOL = {
    "id": "aaa-bbb-ccc",
    "name": "TestTool",
    "website": "https://testtool.ai",
    "category": "AI coding",
    "core_function": "AI code assistant",
    "pricing_model": "Freemium",
    "free_tier_limits": "100 requests/day",
    "community_verdict": "Great for beginners",
    "trust_score": 0.85,
    "tags": ["coding", "ai"],
    "created_at": "2025-01-01T00:00:00Z",
}

SIMILAR_TOOL = {
    "id": "ddd-eee-fff",
    "name": "SimilarTool",
    "website": "https://similartool.ai",
    "category": "AI coding",
    "core_function": "Another AI assistant",
    "pricing_model": "Free",
    "free_tier_limits": "Unlimited",
    "community_verdict": "Solid choice",
    "trust_score": 0.72,
    "tags": ["coding", "ai"],
    "created_at": "2025-01-02T00:00:00Z",
}


class TestAlternativesEndpoint:
    @patch("backend.routers.tools.get_alternatives")
    @patch("backend.routers.tools.get_tool_by_id")
    def test_returns_alternatives(self, mock_get_tool, mock_get_alts, client):
        """A valid tool with embeddings returns a list of alternatives."""
        from backend.models import AlternativeTool, ToolResponse

        mock_get_tool.return_value = SAMPLE_TOOL
        mock_get_alts.return_value = [
            AlternativeTool(
                tool=ToolResponse(**SIMILAR_TOOL),
                similarity=0.91,
                source="knowledge_base",
            )
        ]

        resp = client.get("/api/v1/tools/aaa-bbb-ccc/alternatives")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tool"]["name"] == "SimilarTool"
        assert data[0]["similarity"] == pytest.approx(0.91)
        assert data[0]["source"] == "knowledge_base"

    @patch("backend.routers.tools.get_tool_by_id")
    def test_tool_not_found_returns_404(self, mock_get_tool, client):
        """Non-existent tool_id returns 404."""
        mock_get_tool.return_value = None

        resp = client.get("/api/v1/tools/nonexistent-id/alternatives")
        assert resp.status_code == 404

    @patch("backend.routers.tools.get_alternatives")
    @patch("backend.routers.tools.get_tool_by_id")
    def test_tool_without_embedding_returns_empty(self, mock_get_tool, mock_get_alts, client):
        """Tool exists but has no embedding — returns an empty list."""
        mock_get_tool.return_value = SAMPLE_TOOL
        mock_get_alts.return_value = []

        resp = client.get("/api/v1/tools/aaa-bbb-ccc/alternatives")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("backend.routers.tools.get_alternatives")
    @patch("backend.routers.tools.get_tool_by_id")
    def test_limit_parameter_capped(self, mock_get_tool, mock_get_alts, client):
        """Limit parameter is capped at 10."""
        mock_get_tool.return_value = SAMPLE_TOOL
        mock_get_alts.return_value = []

        resp = client.get("/api/v1/tools/aaa-bbb-ccc/alternatives?limit=50")
        assert resp.status_code == 200
        # The service was called with limit=10 (capped)
        mock_get_alts.assert_called_once_with("aaa-bbb-ccc", limit=10)

    @patch("backend.routers.tools.get_alternatives")
    @patch("backend.routers.tools.get_tool_by_id")
    def test_default_limit_is_five(self, mock_get_tool, mock_get_alts, client):
        """Default limit is 5 when not specified."""
        mock_get_tool.return_value = SAMPLE_TOOL
        mock_get_alts.return_value = []

        resp = client.get("/api/v1/tools/aaa-bbb-ccc/alternatives")
        assert resp.status_code == 200
        mock_get_alts.assert_called_once_with("aaa-bbb-ccc", limit=5)


class TestAlternativesService:
    @patch("backend.services.alternatives_service.vector_search")
    @patch("backend.services.alternatives_service.get_embedding_for_tool")
    def test_excludes_source_tool(self, mock_embedding, mock_vsearch):
        """The source tool is excluded from the results."""
        from backend.services.alternatives_service import get_alternatives

        mock_embedding.return_value = [0.1] * 384
        mock_vsearch.return_value = [
            {"id": "aaa-bbb-ccc", "name": "TestTool", "similarity": 1.0},
            {"id": "ddd-eee-fff", "name": "SimilarTool", "similarity": 0.91},
        ]

        results = get_alternatives("aaa-bbb-ccc", limit=5)
        assert len(results) == 1
        assert results[0].tool.id == "ddd-eee-fff"

    @patch("backend.services.alternatives_service.get_embedding_for_tool")
    def test_no_embedding_returns_empty(self, mock_embedding):
        """Tool without stored embedding returns empty list."""
        from backend.services.alternatives_service import get_alternatives

        mock_embedding.return_value = None

        results = get_alternatives("no-embedding-id", limit=5)
        assert results == []

    @patch("backend.services.alternatives_service.vector_search")
    @patch("backend.services.alternatives_service.get_embedding_for_tool")
    def test_respects_limit(self, mock_embedding, mock_vsearch):
        """Only returns up to the requested limit of alternatives."""
        from backend.services.alternatives_service import get_alternatives

        mock_embedding.return_value = [0.1] * 384
        mock_vsearch.return_value = [
            {"id": f"tool-{i}", "name": f"Tool {i}", "similarity": 0.9 - i * 0.05}
            for i in range(6)
        ]

        results = get_alternatives("source-tool", limit=3)
        assert len(results) == 3
