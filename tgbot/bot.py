"""TruthEngine AI Telegram Bot — /save, /search, /compare commands."""

import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from loguru import logger

from backend.config import get_settings
from crawler.web_crawler import is_valid_url
from workers.ingestion_worker import run_ingestion_pipeline
from agents.embedding_agent import generate_embedding
from agents.query_agent import generate_answer
from agents.comparison_agent import compare_tools
from database.operations import vector_search, get_tool_by_id, list_tools
from backend.models import ToolResponse


# ── Handlers ───────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 *TruthEngine AI*\n\n"
        "I help you discover and analyze AI tools.\n\n"
        "Commands:\n"
        "/save <url> — Save an AI tool for analysis\n"
        "/search <query> — Search the knowledge base\n"
        "/compare <id1> <id2> — Compare two tools\n"
        "/list — List recently added tools\n"
        "/help — Show this message",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /save <url> — ingest an AI tool URL."""
    if not context.args:
        await update.message.reply_text("Usage: /save <url>\nExample: /save https://example.ai")
        return

    url = context.args[0]
    if not is_valid_url(url):
        await update.message.reply_text("❌ Invalid URL. Please provide a valid HTTP/HTTPS URL.")
        return

    await update.message.reply_text(f"⏳ Processing: {url}\nAnalyzing tool, finding alternatives, and comparing...")

    # Run ingestion in a thread to avoid blocking the bot (with 3-min timeout)
    loop = asyncio.get_event_loop()
    category = context.args[1] if len(context.args) > 1 else None
    try:
        report = await asyncio.wait_for(
            loop.run_in_executor(None, run_ingestion_pipeline, url, category),
            timeout=180,
        )
        if report is None:
            await update.message.reply_text(f"❌ Could not analyze {url}. Crawling or extraction failed.")
            return

        # Format the main tool info
        t = report.tool
        lines = [
            f"✅ *{t.name}*",
            f"🌐 {t.website or 'N/A'}",
            f"📝 {t.core_function or 'N/A'}",
            f"💰 Pricing: {t.pricing_model or 'N/A'}",
            f"🆓 Free tier: {t.free_tier_limits or 'N/A'}",
            f"👥 Community: {t.community_verdict or 'N/A'}",
            f"🎯 Trust: {t.trust_score:.0%}" if t.trust_score else "",
            f"🏷️ Tags: {', '.join(t.tags)}" if t.tags else "",
        ]
        await update.message.reply_text(
            "\n".join(l for l in lines if l), parse_mode="Markdown"
        )

        # Format alternatives
        if report.alternatives:
            alt_lines = [f"🔄 *Alternatives Found ({len(report.alternatives)}):*\n"]
            for i, alt in enumerate(report.alternatives, 1):
                sim_str = f" ({alt.similarity:.0%} match)" if alt.similarity else ""
                src = "📚 KB" if alt.source == "knowledge_base" else "🌐 Web"
                alt_lines.append(
                    f"{i}. *{alt.tool.name}*{sim_str} [{src}]\n"
                    f"   {alt.tool.core_function or 'N/A'}\n"
                    f"   💰 {alt.tool.pricing_model or 'N/A'}\n"
                )
            text = "\n".join(alt_lines)
            # Telegram message limit is 4096 chars
            if len(text) > 4000:
                text = text[:4000] + "\n..."
            await update.message.reply_text(text, parse_mode="Markdown")

        # Format comparison
        if report.comparison:
            comp = f"⚖️ *Comparison:*\n\n{report.comparison}"
            # Split long comparisons into chunks
            while comp:
                chunk = comp[:4000]
                comp = comp[4000:]
                await update.message.reply_text(chunk, parse_mode="Markdown")

    except asyncio.TimeoutError:
        await update.message.reply_text(f"⏠ Processing timed out for {url}. The site may be slow or blocking crawlers.")
    except Exception as e:
        logger.error(f"Telegram /save failed: {e}")
        await update.message.reply_text(f"❌ Error processing URL: {e}")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search <query> — semantic search."""
    if not context.args:
        await update.message.reply_text("Usage: /search <query>\nExample: /search free image generation AI")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching for: {query}...")

    try:
        embedding = await generate_embedding(query)
        if not embedding:
            await update.message.reply_text("❌ Search service temporarily unavailable.")
            return

        results = vector_search(embedding, limit=5)
        if not results:
            await update.message.reply_text("No results found. Try a different query.")
            return

        # Build response
        tool_infos = []
        lines = ["*Search Results:*\n"]
        for i, row in enumerate(results, 1):
            sim = row.get("similarity", 0)
            name = row.get("name", "Unknown")
            lines.append(
                f"{i}. *{name}* ({sim:.0%} match)\n"
                f"   {row.get('core_function', 'N/A')}\n"
                f"   Pricing: {row.get('pricing_model', 'N/A')}\n"
            )
            tool_infos.append(
                f"{name}: {row.get('core_function', '')} — {row.get('pricing_model', '')}"
            )

        # Generate AI answer
        answer = await generate_answer(query, tool_infos)
        if answer:
            lines.append(f"\n💡 *AI Answer:*\n{answer}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Telegram /search failed: {e}")
        await update.message.reply_text(f"❌ Search error: {e}")


async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compare <id1> <id2> — compare two tools."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /compare <tool_id_1> <tool_id_2>")
        return

    tool_ids = context.args[:2]
    tools = []
    for tid in tool_ids:
        tool = get_tool_by_id(tid)
        if not tool:
            await update.message.reply_text(f"❌ Tool not found: {tid}")
            return
        tools.append(ToolResponse(**tool))

    await update.message.reply_text("⚖️ Comparing tools...")

    try:
        comparison = await compare_tools(tools)
        header = f"*{tools[0].name}* vs *{tools[1].name}*\n\n"
        await update.message.reply_text(header + comparison, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Telegram /compare failed: {e}")
        await update.message.reply_text(f"❌ Comparison error: {e}")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list — show recent tools."""
    tools = list_tools(limit=10)
    if not tools:
        await update.message.reply_text("No tools in the database yet. Use /save to add one.")
        return

    lines = ["*Recent AI Tools:*\n"]
    for i, t in enumerate(tools, 1):
        score = t.get("trust_score", 0) or 0
        lines.append(f"{i}. *{t['name']}* (trust: {score:.0%})\n   {t.get('core_function', 'N/A')}\n")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── Bot Setup ──────────────────────────────────────────────────────────

def create_bot() -> Application:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN must be set in environment.")

    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("save", save_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("compare", compare_command))
    app.add_handler(CommandHandler("list", list_command))

    return app


def run_bot():
    logger.info("Starting TruthEngine AI Telegram Bot")
    app = create_bot()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
