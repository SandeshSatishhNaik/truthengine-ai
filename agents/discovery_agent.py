"""Discovery Agent — automatically finds new AI tools online."""

from loguru import logger

from crawler.search_crawler import discover_ai_tools
from crawler.web_crawler import crawl_tool_website, is_valid_url

AI_CATEGORIES = [
    "AI writing",
    "AI coding",
    "AI image generation",
    "AI video",
    "AI audio",
    "AI chatbot",
    "AI productivity",
    "AI data analysis",
    "AI design",
    "AI automation",
]


def run_discovery(categories: list[str] | None = None, max_per_category: int = 5) -> list[dict]:
    """
    Discover new AI tools across specified categories.
    Returns a list of discovered tools with basic info.
    """
    if categories is None:
        categories = AI_CATEGORIES

    discovered = []
    seen_urls = set()

    for category in categories:
        logger.info(f"Discovering tools in category: {category}")
        results = discover_ai_tools(category=category, max_results=max_per_category)

        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls and is_valid_url(url):
                seen_urls.add(url)
                discovered.append({
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "category": category,
                })

    logger.info(f"Total discovered: {len(discovered)} potential AI tools")
    return discovered
