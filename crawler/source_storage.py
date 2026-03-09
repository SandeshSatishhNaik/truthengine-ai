"""Raw source storage — persists crawled content to the database."""

from loguru import logger

from database.operations import create_source


def store_crawled_sources(tool_id: str, crawl_results: dict) -> int:
    """
    Store crawled page content as source records.
    crawl_results: dict from web_crawler.crawl_tool_website()
    Returns the number of sources stored.
    """
    stored = 0
    for page_type, data in crawl_results.items():
        url = data.get("url", "")
        text = data.get("text", "")
        if url and text:
            result = create_source(tool_id, url, text[:50000])  # Cap at 50k chars
            if result:
                stored += 1
                logger.info(f"Stored {page_type} source for tool {tool_id}")
            else:
                logger.warning(f"Failed to store {page_type} source for tool {tool_id}")
    return stored


def store_external_sources(tool_id: str, search_results: list[dict]) -> int:
    """
    Store external search results as source records.
    search_results: list from search_crawler.search_external_references()
    """
    stored = 0
    for result in search_results:
        url = result.get("url", "")
        body = result.get("body", "")
        title = result.get("title", "")
        content = f"{title}\n\n{body}" if title else body
        if url and content.strip():
            rec = create_source(tool_id, url, content[:50000])
            if rec:
                stored += 1
    logger.info(f"Stored {stored} external sources for tool {tool_id}")
    return stored
