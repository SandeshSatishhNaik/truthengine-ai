"""Discovery Worker — periodically discovers and ingests new AI tools."""

from loguru import logger

from agents.discovery_agent import run_discovery
from crawler.web_crawler import is_valid_url
from database.operations import get_tool_by_website
from workers.ingestion_worker import run_ingestion_pipeline


def run_discovery_pipeline(categories: list[str] | None = None, max_per_category: int = 3):
    """
    Discover new AI tools and run ingestion on each new one.
    Skips tools that already exist in the database.
    """
    logger.info("Starting discovery pipeline")

    discovered = run_discovery(categories=categories, max_per_category=max_per_category)

    new_count = 0
    for item in discovered:
        url = item.get("url", "")
        if not is_valid_url(url):
            continue

        # Check if already in database
        existing = get_tool_by_website(url)
        if existing:
            logger.debug(f"Skipping already known tool: {url}")
            continue

        logger.info(f"New tool discovered: {url}")
        category = item.get("category", "uncategorized")

        try:
            run_ingestion_pipeline(url, category=category, source_type="discovered")
            new_count += 1
        except Exception as e:
            logger.error(f"Ingestion failed for discovered tool {url}: {e}")

    logger.info(f"Discovery pipeline complete — {new_count} new tools ingested")
