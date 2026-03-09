"""Tests for embedding generation and vector search flow."""

from unittest.mock import patch, MagicMock, AsyncMock

import numpy as np
import pytest

from agents.embedding_agent import generate_embedding, generate_tool_embedding


# ── Generate Embedding ─────────────────────────────────────────────────


class TestGenerateEmbedding:
    @pytest.mark.asyncio
    async def test_successful_embedding(self):
        fake_embedding = np.array([0.1] * 384, dtype=np.float32)

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = fake_embedding

            result = await generate_embedding("test text")
            assert result is not None
            assert len(result) == 384

    @pytest.mark.asyncio
    async def test_model_loading_503(self):
        """When the HF API raises an exception, generate_embedding propagates it."""
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Model is currently loading")

            with pytest.raises(Exception, match="Model is currently loading"):
                await generate_embedding("test text")

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self):
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = TimeoutError("timeout")

            with pytest.raises(TimeoutError):
                await generate_embedding("test")

    @pytest.mark.asyncio
    async def test_no_api_token(self):
        with patch("agents.embedding_agent.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(hf_api_token="")
            result = await generate_embedding("test")
            assert result is None

    @pytest.mark.asyncio
    async def test_nested_embedding_unwrapped(self):
        """HuggingFace feature_extraction returns a numpy array that gets flattened."""
        inner = np.array([0.5] * 384, dtype=np.float32)

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = inner

            result = await generate_embedding("test")
            assert result is not None
            assert len(result) == 384
            assert abs(result[0] - 0.5) < 0.01


# ── Generate Tool Embedding ────────────────────────────────────────────


class TestGenerateToolEmbedding:
    @pytest.mark.asyncio
    async def test_combines_fields(self):
        with patch("agents.embedding_agent.generate_embedding", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = [0.1] * 384
            result = await generate_tool_embedding({
                "name": "TestTool",
                "core_function": "AI assistant",
                "pricing_model": "Free",
                "category": "coding",
                "tags": ["ai", "code"],
            })
            assert result is not None
            # Check that the combined text was passed
            call_text = mock_gen.call_args[0][0]
            assert "TestTool" in call_text
            assert "coding" in call_text

    @pytest.mark.asyncio
    async def test_empty_data_returns_none(self):
        result = await generate_tool_embedding({})
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_missing_tags(self):
        with patch("agents.embedding_agent.generate_embedding", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = [0.1] * 384
            result = await generate_tool_embedding({"name": "Tool"})
            assert result is not None
