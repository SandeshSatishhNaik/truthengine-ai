"""External search crawler using DuckDuckGo."""

import time

from duckduckgo_search import DDGS
from loguru import logger

# Circuit-breaker: track consecutive DDG failures to skip remaining queries fast
_ddg_consecutive_failures: int = 0
_DDG_CIRCUIT_THRESHOLD: int = 2  # after 2 consecutive failures, skip remaining
_DDG_TIMEOUT: int = 10  # seconds per DDG request


def _reset_ddg_circuit():
    global _ddg_consecutive_failures
    _ddg_consecutive_failures = 0


def _is_ddg_circuit_open() -> bool:
    return _ddg_consecutive_failures >= _DDG_CIRCUIT_THRESHOLD


def _ddg_search(ddgs: DDGS, query: str, max_results: int) -> list[dict]:
    """Execute a single DDGS search with short timeout. No retries — fail fast."""
    global _ddg_consecutive_failures
    try:
        results = ddgs.text(query, max_results=max_results)
        _ddg_consecutive_failures = 0  # reset on success
        return results
    except Exception as e:
        _ddg_consecutive_failures += 1
        logger.warning(f"DDG search failed ({_ddg_consecutive_failures}x): {e}")
        raise


def search_external_references(tool_name: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo for external references about an AI tool.
    Returns list of {title, url, body} dicts.
    Uses circuit-breaker: skips remaining queries if DDG is consistently down.
    """
    from backend.metrics import metrics

    queries = [
        f"{tool_name} review",
        f"{tool_name} pricing free tier",
        f"{tool_name} alternative reddit",
    ]

    all_results = []
    seen_urls = set()

    with DDGS(timeout=_DDG_TIMEOUT) as ddgs:
        for query in queries:
            if _is_ddg_circuit_open():
                logger.warning("DDG circuit-breaker open — skipping remaining searches")
                break
            try:
                metrics.crawl_requests.inc()
                results = _ddg_search(ddgs, query, max_results)
                for r in results:
                    url = r.get("href", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({
                            "title": r.get("title", ""),
                            "url": url,
                            "body": r.get("body", ""),
                            "query": query,
                        })
            except Exception:
                pass  # already logged in _ddg_search
            time.sleep(0.5)  # short delay between queries

    logger.info(f"Found {len(all_results)} external references for '{tool_name}'")
    return all_results


def discover_ai_tools(category: str = "AI", max_results: int = 10) -> list[dict]:
    """
    Discover new AI tools by searching for trending/new tools.
    Returns list of {title, url, body} dicts.
    """
    discovery_queries = [
        f"new {category} tools 2026",
        f"best free {category} tools",
        f"top {category} AI tools launch",
        f"{category} tool alternative free",
    ]

    all_results = []
    seen_urls = set()

    with DDGS(timeout=_DDG_TIMEOUT) as ddgs:
        for query in discovery_queries:
            if _is_ddg_circuit_open():
                logger.warning("DDG circuit-breaker open — skipping remaining discovery searches")
                break
            try:
                results = _ddg_search(ddgs, query, max_results)
                for r in results:
                    url = r.get("href", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({
                            "title": r.get("title", ""),
                            "url": url,
                            "body": r.get("body", ""),
                            "query": query,
                        })
            except Exception:
                pass  # already logged in _ddg_search
            time.sleep(0.5)

    logger.info(f"Discovered {len(all_results)} potential AI tools in '{category}'")
    return all_results


def search_alternatives(tool_name: str, tags: list[str] | None = None,
                        max_results: int = 6) -> list[dict]:
    """
    Search for alternative tools to a given tool.
    Uses tool name and tags to build targeted queries.
    Returns list of {title, url, body} dicts pointing to tool homepages.
    Uses circuit-breaker: skips remaining queries if DDG is down.
    """
    from urllib.parse import urlparse as _urlparse

    tag_str = " ".join(tags[:3]) if tags else "AI"
    queries = [
        f"{tool_name} alternatives",
        f"tools similar to {tool_name}",
        f"best {tag_str} tools like {tool_name}",
    ]

    all_results = []
    seen_domains: set[str] = set()

    # Exclude aggregator/list sites — we want actual tool homepages
    skip_domains = {
        "reddit.com", "quora.com", "medium.com", "twitter.com", "x.com",
        "youtube.com", "github.com", "producthunt.com", "alternativeto.net",
        "g2.com", "capterra.com", "trustradius.com", "wikipedia.org",
    }

    with DDGS(timeout=_DDG_TIMEOUT) as ddgs:
        for query in queries:
            if _is_ddg_circuit_open():
                logger.warning("DDG circuit-breaker open — skipping remaining alternative searches")
                break
            try:
                results = _ddg_search(ddgs, query, max_results)
                for r in results:
                    url = r.get("href", "")
                    if not url:
                        continue
                    domain = _urlparse(url).netloc.replace("www.", "")
                    if domain in seen_domains or domain in skip_domains:
                        continue
                    seen_domains.add(domain)
                    all_results.append({
                        "title": r.get("title", ""),
                        "url": url,
                        "body": r.get("body", ""),
                    })
            except Exception:
                pass  # already logged in _ddg_search
            time.sleep(0.5)

    logger.info(f"Found {len(all_results)} potential alternatives for '{tool_name}'")
    return all_results
