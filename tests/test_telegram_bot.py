"""Tests for Telegram bot command handlers."""

from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from tgbot.bot import start_command, help_command, search_command, list_command


@pytest.fixture()
def update():
    """Build a mock Telegram Update object."""
    upd = AsyncMock()
    upd.effective_user = MagicMock(first_name="Tester")
    upd.message = AsyncMock()
    upd.message.reply_text = AsyncMock()
    return upd


@pytest.fixture()
def context():
    ctx = AsyncMock()
    ctx.args = []
    return ctx


# ── /start ─────────────────────────────────────────────────────────────


class TestStartCommand:
    @pytest.mark.asyncio
    async def test_start_greets_user(self, update, context):
        await start_command(update, context)
        update.message.reply_text.assert_called_once()
        text = update.message.reply_text.call_args[0][0]
        assert "Tester" in text or "TruthEngine" in text


# ── /help ──────────────────────────────────────────────────────────────


class TestHelpCommand:
    @pytest.mark.asyncio
    async def test_help_shows_commands(self, update, context):
        await help_command(update, context)
        update.message.reply_text.assert_called_once()
        text = update.message.reply_text.call_args[0][0]
        assert "/search" in text
        assert "/save" in text


# ── /search ────────────────────────────────────────────────────────────


class TestSearchCommand:
    @pytest.mark.asyncio
    async def test_search_no_query(self, update, context):
        context.args = []
        await search_command(update, context)
        text = update.message.reply_text.call_args[0][0]
        assert "Usage" in text or "usage" in text.lower() or "/search" in text

    @pytest.mark.asyncio
    @patch("tgbot.bot.generate_embedding", new_callable=AsyncMock)
    @patch("tgbot.bot.vector_search")
    @patch("tgbot.bot.get_tool_by_id")
    @patch("tgbot.bot.generate_answer", new_callable=AsyncMock)
    async def test_search_with_results(
        self, mock_answer, mock_get_tool, mock_vsearch, mock_embed, update, context
    ):
        context.args = ["coding", "assistant"]
        mock_embed.return_value = [0.1] * 384
        mock_vsearch.return_value = [{"tool_id": "aaa", "similarity": 0.9}]
        mock_get_tool.return_value = {
            "id": "aaa",
            "name": "TestTool",
            "core_function": "AI coding",
        }
        mock_answer.return_value = "TestTool is great."
        await search_command(update, context)
        update.message.reply_text.assert_called()


# ── /list ──────────────────────────────────────────────────────────────


class TestListCommand:
    @pytest.mark.asyncio
    @patch("tgbot.bot.list_tools")
    async def test_list_shows_tools(self, mock_list, update, context):
        mock_list.return_value = [
            {"id": "aaa", "name": "Tool1", "category": "coding"},
            {"id": "bbb", "name": "Tool2", "category": "writing"},
        ]
        await list_command(update, context)
        text = update.message.reply_text.call_args[0][0]
        assert "Tool1" in text

    @pytest.mark.asyncio
    @patch("tgbot.bot.list_tools")
    async def test_list_empty(self, mock_list, update, context):
        mock_list.return_value = []
        await list_command(update, context)
        text = update.message.reply_text.call_args[0][0]
        assert "No tools" in text or "no tools" in text.lower() or "empty" in text.lower()
