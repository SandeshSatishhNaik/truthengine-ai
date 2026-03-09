"""Tests for AI extraction and verification agents."""

import json
from unittest.mock import patch, MagicMock

import pytest

from agents.extraction_agent import extract_tool_info
from agents.verification_agent import verify_extraction
from backend.models import ToolExtraction


# ── Extraction Agent ───────────────────────────────────────────────────


class TestExtractToolInfo:
    @patch("agents.extraction_agent.Groq")
    def test_successful_extraction(self, MockGroq, sample_extraction):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(sample_extraction)))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        MockGroq.return_value = mock_client

        result = extract_tool_info(["TestTool is a great AI code assistant."])
        assert result is not None
        assert isinstance(result, ToolExtraction)
        assert result.tool_name == "TestTool"
        assert result.pricing_model == "Freemium"

    @patch("agents.extraction_agent.Groq")
    def test_extraction_with_markdown_fences(self, MockGroq, sample_extraction):
        json_with_fences = f"```json\n{json.dumps(sample_extraction)}\n```"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json_with_fences))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        MockGroq.return_value = mock_client

        result = extract_tool_info(["Some source text"])
        assert result is not None
        assert result.tool_name == "TestTool"

    @patch("backend.retry.time.sleep")
    @patch("agents.extraction_agent.Groq")
    def test_extraction_invalid_json(self, MockGroq, mock_sleep):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This is not JSON at all"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        MockGroq.return_value = mock_client

        result = extract_tool_info(["Some source text"])
        assert result is None

    @patch("agents.extraction_agent.get_settings")
    def test_extraction_no_api_key(self, mock_settings):
        mock_settings.return_value = MagicMock(groq_api_key="")
        result = extract_tool_info(["Some source text"])
        assert result is None

    @patch("backend.retry.time.sleep")
    @patch("agents.extraction_agent.Groq")
    def test_extraction_api_failure(self, MockGroq, mock_sleep):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        MockGroq.return_value = mock_client

        result = extract_tool_info(["Some source text"])
        assert result is None


# ── Verification Agent ─────────────────────────────────────────────────


class TestVerifyExtraction:
    @patch("agents.verification_agent.Groq")
    def test_successful_verification(self, MockGroq):
        report = {
            "tool_name": {"status": "VERIFIED", "notes": ""},
            "trust_score": 0.9,
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(report)))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        MockGroq.return_value = mock_client

        result = verify_extraction({"tool_name": "TestTool"}, ["source text"])
        assert result["trust_score"] == 0.9

    @patch("agents.verification_agent.Groq")
    def test_verification_clamps_score(self, MockGroq):
        report = {"trust_score": 1.5}  # Out of range
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(report)))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        MockGroq.return_value = mock_client

        result = verify_extraction({"tool_name": "T"}, ["source"])
        assert result["trust_score"] == 1.0

    @patch("agents.verification_agent.get_settings")
    def test_verification_no_api_key(self, mock_settings):
        mock_settings.return_value = MagicMock(groq_api_key="")
        result = verify_extraction({}, [])
        assert result == {"trust_score": 0.0}

    @patch("backend.retry.time.sleep")
    @patch("agents.verification_agent.Groq")
    def test_verification_invalid_json(self, MockGroq, mock_sleep):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Not JSON"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        MockGroq.return_value = mock_client

        result = verify_extraction({"tool_name": "T"}, ["source"])
        assert result["trust_score"] == 0.0
