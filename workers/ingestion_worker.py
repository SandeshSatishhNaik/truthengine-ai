"""Ingestion Worker — full pipeline: URL → crawl → extract → verify → store → embed → find alternatives → compare."""

import asyncio
from urllib.parse import urlparse

from loguru import logger

from crawler.web_crawler import crawl_tool_website, is_valid_url
from crawler.search_crawler import search_external_references, _reset_ddg_circuit
from crawler.source_storage import store_crawled_sources, store_external_sources
from agents.extraction_agent import extract_tool_info
from agents.verification_agent import verify_extraction
from agents.embedding_agent import generate_tool_embedding
from agents.alternatives_agent import find_alternatives_and_compare
from database.operations import (
    create_tool,
    update_tool,
    get_tool_by_id,
    get_tool_by_website,
    store_embedding,
)
from backend.models import ToolResponse, AnalysisReport


def run_ingestion_pipeline(url: str, category: str | None = None, source_type: str = "submitted") -> AnalysisReport | None:
    """
    Full ingestion pipeline (runs synchronously).
    Returns an AnalysisReport with the tool, alternatives, and comparison.
    """
    from backend.metrics import metrics

    metrics.ingestions_started.inc()
    logger.info(f"Starting ingestion pipeline for: {url}")

    # Reset DDG circuit-breaker for each new pipeline run
    _reset_ddg_circuit()

    # 1. Validate URL
    if not is_valid_url(url):
        logger.error(f"Invalid URL: {url}")
        metrics.ingestions_failed.inc()
        return None

    # Normalize URL
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    cat = category or "uncategorized"

    # 2. Check for duplicates — if exists, skip to alternatives
    existing = get_tool_by_website(base_url)
    if existing:
        logger.info(f"Tool already exists for {base_url}: {existing['id']}")
        tool_data = existing
        tool_id = existing["id"]
    else:
        tool_data, tool_id = _ingest_new_tool(url, base_url, parsed, cat, metrics, source_type)
        if tool_data is None:
            return None

    # 11. Find alternatives and auto-compare
    logger.info("Phase: Finding alternatives and comparing")
    alternatives, comparison_text = find_alternatives_and_compare(
        tool_id=tool_id,
        tool_data=tool_data,
        category=cat,
        exclude_url=base_url,
    )

    report = AnalysisReport(
        tool=ToolResponse(**{k: v for k, v in tool_data.items()
                             if k in ToolResponse.model_fields}),
        alternatives=alternatives,
        comparison=comparison_text,
    )

    logger.info(
        f"Ingestion complete for: {tool_data.get('name', url)} — "
        f"{len(alternatives)} alternatives, comparison={'yes' if comparison_text else 'no'}"
    )
    metrics.ingestions_completed.inc()
    return report


def _ingest_new_tool(url, base_url, parsed, category, metrics, source_type="submitted"):
    """Core ingestion phases 3-10. Returns (tool_data, tool_id) or (None, None)."""
    # 3. Crawl website
    logger.info("Phase: Crawling website")
    crawl_results = crawl_tool_website(url)
    if not crawl_results:
        # Fallback: use DuckDuckGo search to gather info when direct crawl fails (e.g. 403)
        logger.warning(f"Direct crawl failed for {url}, falling back to search-based ingestion")
        domain = parsed.netloc.replace("www.", "")
        search_refs = search_external_references(domain, max_results=5)
        if not search_refs:
            logger.error(f"Both crawl and search fallback failed for {url}")
            metrics.ingestions_failed.inc()
            return None, None
        # Build a synthetic crawl result from search snippets
        combined_text = "\n".join(
            f"{ref.get('title', '')}: {ref.get('body', '')}" for ref in search_refs
        )
        crawl_results = {
            "homepage": {
                "url": url,
                "text": combined_text,
                "metadata": {
                    "title": search_refs[0].get("title", domain) if search_refs else domain,
                    "description": search_refs[0].get("body", "") if search_refs else "",
                    "url": url,
                },
            }
        }
        logger.info(f"Built synthetic crawl data from {len(search_refs)} search results")

    # 4. Create initial tool record (placeholder)
    domain = parsed.netloc.replace("www.", "")
    tool_record = create_tool({
        "name": domain,
        "website": base_url,
        "category": category,
        "source_type": source_type,
    })
    if not tool_record:
        logger.error("Failed to create tool record")
        metrics.ingestions_failed.inc()
        return None, None

    tool_id = tool_record["id"]
    logger.info(f"Created tool record: {tool_id}")

    # 5. Store crawled sources
    logger.info("Phase: Storing crawled sources")
    store_crawled_sources(tool_id, crawl_results)

    # 6. Search external references
    tool_name_guess = crawl_results.get("homepage", {}).get("metadata", {}).get("title", domain)
    logger.info(f"Phase: Searching external references for '{tool_name_guess}'")
    external_refs = search_external_references(tool_name_guess, max_results=3)
    store_external_sources(tool_id, external_refs)

    # 7. Extract structured info via AI
    logger.info("Phase: AI extraction")
    source_texts = []
    for page_type, data in crawl_results.items():
        text = data.get("text", "")
        if text:
            source_texts.append(f"[{page_type}] {text}")
    for ref in external_refs:
        body = ref.get("body", "")
        if body:
            source_texts.append(f"[external] {body}")

    extraction = extract_tool_info(source_texts)
    if not extraction:
        logger.warning("AI extraction failed, tool record remains with placeholder data")
        metrics.ingestions_failed.inc()
        return None, None

    # 8. Verify extracted info
    logger.info("Phase: Truth verification")
    verification = verify_extraction(extraction.model_dump(), source_texts)
    trust_score = verification.get("trust_score", 0.0)

    # 9. Update tool record with extracted data
    update_data = {
        "name": extraction.tool_name,
        "core_function": extraction.core_function,
        "pricing_model": extraction.pricing_model,
        "free_tier_limits": extraction.free_tier_limits,
        "community_verdict": extraction.community_verdict,
        "trust_score": trust_score,
        "tags": extraction.tags,
    }
    update_tool(tool_id, update_data)
    logger.info(f"Updated tool '{extraction.tool_name}' with trust score {trust_score}")

    # 10. Generate and store embedding
    logger.info("Phase: Embedding generation")
    embedding_data = {**update_data, "category": category}
    loop = asyncio.new_event_loop()
    try:
        embedding = loop.run_until_complete(generate_tool_embedding(embedding_data))
    except Exception as e:
        logger.warning(f"Embedding generation failed (non-fatal): {e}")
        embedding = None
    finally:
        loop.close()
    if embedding:
        store_embedding(tool_id, embedding)
        logger.info(f"Stored embedding for tool {tool_id}")
    else:
        logger.warning(f"Embedding generation failed for tool {tool_id}")

    # Fetch the full tool record for the report
    full_tool = get_tool_by_id(tool_id) or {**tool_record, **update_data}
    return full_tool, tool_id
