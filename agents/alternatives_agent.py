"""Alternatives Agent — finds similar tools from KB and the web, then compares."""

import asyncio
import time
from urllib.parse import urlparse

from loguru import logger

from backend.config import get_settings
from backend.models import ToolResponse, AlternativeTool
from agents.embedding_agent import generate_tool_embedding
from agents.comparison_agent import compare_tools
from crawler.search_crawler import search_alternatives
from crawler.web_crawler import crawl_tool_website, is_valid_url
from crawler.source_storage import store_crawled_sources
from agents.extraction_agent import extract_tool_info
from agents.verification_agent import verify_extraction
from database.operations import (
    create_tool,
    update_tool,
    get_tool_by_website,
    store_embedding,
    vector_search,
)


def _find_kb_alternatives(tool_id: str, tool_data: dict, limit: int = 5) -> list[AlternativeTool]:
    """Find similar tools already in the knowledge base via vector search."""
    loop = asyncio.new_event_loop()
    try:
        embedding = loop.run_until_complete(generate_tool_embedding(tool_data))
    finally:
        loop.close()

    if not embedding:
        return []

    results = vector_search(embedding, limit=limit + 1)
    alternatives = []
    for row in results:
        if row.get("id") == tool_id:
            continue
        alternatives.append(AlternativeTool(
            tool=ToolResponse(**{k: v for k, v in row.items() if k != "similarity"}),
            similarity=row.get("similarity", 0.0),
            source="knowledge_base",
        ))
    return alternatives[:limit]


def _ingest_single_alternative(url: str, category: str) -> dict | None:
    """Lightweight ingestion of a single alternative (crawl → extract → store → embed)."""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    existing = get_tool_by_website(base_url)
    if existing:
        return existing

    crawl_results = crawl_tool_website(url)
    if not crawl_results:
        return None

    domain = parsed.netloc.replace("www.", "")
    tool_record = create_tool({
        "name": domain,
        "website": base_url,
        "category": category,
    })
    if not tool_record:
        return None

    tool_id = tool_record["id"]
    store_crawled_sources(tool_id, crawl_results)

    source_texts = []
    for page_type, data in crawl_results.items():
        text = data.get("text", "")
        if text:
            source_texts.append(f"[{page_type}] {text}")

    extraction = extract_tool_info(source_texts)
    if not extraction:
        return tool_record

    verification = verify_extraction(extraction.model_dump(), source_texts)
    trust_score = verification.get("trust_score", 0.0)

    update_data = {
        "name": extraction.tool_name,
        "core_function": extraction.core_function,
        "pricing_model": extraction.pricing_model,
        "free_tier_limits": extraction.free_tier_limits,
        "community_verdict": extraction.community_verdict,
        "trust_score": trust_score,
        "tags": extraction.tags,
    }
    updated = update_tool(tool_id, update_data)

    embedding_data = {**update_data, "category": category}
    loop = asyncio.new_event_loop()
    try:
        emb = loop.run_until_complete(generate_tool_embedding(embedding_data))
    finally:
        loop.close()
    if emb:
        store_embedding(tool_id, emb)

    return updated or {**tool_record, **update_data}


def _find_web_alternatives(tool_name: str, tags: list[str], category: str,
                           exclude_url: str, max_results: int = 3) -> list[AlternativeTool]:
    """Search the web for alternative tools and ingest them."""
    web_results = search_alternatives(tool_name, tags, max_results=max_results * 2)
    if not web_results:
        return []

    alternatives = []
    for result in web_results:
        url = result.get("url", "")
        if not url or not is_valid_url(url):
            continue

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if base_url.rstrip("/") == exclude_url.rstrip("/"):
            continue

        logger.info(f"Ingesting web alternative: {base_url}")
        try:
            tool_data = _ingest_single_alternative(url, category)
            if tool_data and tool_data.get("name"):
                alternatives.append(AlternativeTool(
                    tool=ToolResponse(**{k: v for k, v in tool_data.items()
                                         if k in ToolResponse.model_fields}),
                    source="web_discovery",
                ))
        except Exception as e:
            logger.warning(f"Failed to ingest alternative {url}: {e}")

        if len(alternatives) >= max_results:
            break

    return alternatives


def find_alternatives_and_compare(
    tool_id: str,
    tool_data: dict,
    category: str,
    exclude_url: str,
) -> tuple[list[AlternativeTool], str | None]:
    """
    Main entry: find alternatives from KB + web, then auto-compare.
    Returns (alternatives, comparison_text).
    """
    logger.info(f"Finding alternatives for: {tool_data.get('name', 'unknown')}")

    # 1. Check knowledge base for similar tools
    kb_alts = _find_kb_alternatives(tool_id, tool_data, limit=3)
    logger.info(f"Found {len(kb_alts)} alternatives in knowledge base")

    # 2. Search web for more alternatives
    tool_name = tool_data.get("name", "")
    tags = tool_data.get("tags", [])
    web_alts = _find_web_alternatives(
        tool_name, tags, category, exclude_url, max_results=3,
    )
    logger.info(f"Found {len(web_alts)} alternatives from web")

    # Merge and deduplicate (prefer KB results which have similarity scores)
    seen_ids = set()
    all_alts: list[AlternativeTool] = []
    for alt in kb_alts + web_alts:
        if alt.tool.id not in seen_ids:
            seen_ids.add(alt.tool.id)
            all_alts.append(alt)

    # 3. Auto-compare if we have alternatives
    comparison_text = None
    if all_alts:
        primary = ToolResponse(**{k: v for k, v in tool_data.items()
                                   if k in ToolResponse.model_fields})
        tools_to_compare = [primary] + [a.tool for a in all_alts[:4]]
        try:
            loop = asyncio.new_event_loop()
            try:
                comparison_text = loop.run_until_complete(compare_tools(tools_to_compare))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Auto-comparison failed: {e}")

    return all_alts, comparison_text
