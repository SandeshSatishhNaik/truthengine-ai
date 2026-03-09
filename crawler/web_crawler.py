"""Web crawler using BeautifulSoup and readability-lxml."""

import asyncio
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document
from loguru import logger

from backend.config import get_settings
from backend.retry import retry

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Semaphore for concurrent crawl limiting (initialized lazily)
_crawl_semaphore: asyncio.Semaphore | None = None


def _get_crawl_semaphore() -> asyncio.Semaphore:
    global _crawl_semaphore
    if _crawl_semaphore is None:
        settings = get_settings()
        _crawl_semaphore = asyncio.Semaphore(settings.max_concurrent_crawls)
    return _crawl_semaphore


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def fetch_page(url: str) -> str | None:
    """Fetch raw HTML from a URL with timeout, retries, and error handling."""
    from backend.metrics import metrics

    if not is_valid_url(url):
        logger.warning(f"Invalid URL: {url}")
        return None

    metrics.crawl_requests.inc()
    try:
        html = _fetch_with_retry(url)
        metrics.pages_crawled.inc()
        return html
    except (requests.RequestException, CrawlBlockedError) as e:
        metrics.crawl_failures.inc()
        logger.error(f"Failed to fetch {url} after retries: {e}")
        return None


class CrawlBlockedError(Exception):
    """Raised when a site intentionally blocks crawling (403/401)."""
    pass


@retry(max_attempts=3, base_delay=2.0, retryable_exceptions=(requests.RequestException,))
def _fetch_with_retry(url: str) -> str:
    settings = get_settings()
    resp = requests.get(
        url,
        headers=HEADERS,
        timeout=settings.request_timeout,
        allow_redirects=True,
    )
    # Don't retry on 403/401 — these are intentional blocks, not transient errors
    if resp.status_code in (401, 403):
        raise CrawlBlockedError(f"{resp.status_code} blocked: {url}")
    resp.raise_for_status()
    return resp.text


def extract_readable_text(html: str) -> str:
    """Extract the main readable content from HTML using readability-lxml."""
    try:
        doc = Document(html)
        summary_html = doc.summary()
        soup = BeautifulSoup(summary_html, "lxml")
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        logger.warning(f"Readability extraction failed, falling back to raw: {e}")
        soup = BeautifulSoup(html, "lxml")
        # Remove script and style
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)


def extract_metadata(html: str, url: str) -> dict:
    """Extract title and meta description from HTML."""
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc["content"].strip()
    return {"title": title, "description": description, "url": url}


def find_pricing_page(html: str, base_url: str) -> str | None:
    """Attempt to find a pricing page link from the homepage HTML."""
    soup = BeautifulSoup(html, "lxml")
    pricing_keywords = ["pricing", "plans", "price", "billing"]
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        text = link.get_text(strip=True).lower()
        if any(kw in href or kw in text for kw in pricing_keywords):
            return urljoin(base_url, link["href"])
    return None


def find_docs_page(html: str, base_url: str) -> str | None:
    """Attempt to find a documentation page link."""
    soup = BeautifulSoup(html, "lxml")
    docs_keywords = ["docs", "documentation", "api", "guide", "getting-started"]
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        text = link.get_text(strip=True).lower()
        if any(kw in href or kw in text for kw in docs_keywords):
            return urljoin(base_url, link["href"])
    return None


def crawl_tool_website(url: str) -> dict:
    """
    Crawl an AI tool website. Extracts:
    - Homepage content
    - Pricing page content (if found)
    - Documentation page content (if found)

    Returns a dict with page_type → content mappings.
    """
    import time as _time
    from backend.metrics import metrics

    results = {}
    start = _time.perf_counter()

    # 1. Fetch homepage
    logger.info(f"Crawling homepage: {url}")
    homepage_html = fetch_page(url)
    if not homepage_html:
        return results

    results["homepage"] = {
        "url": url,
        "text": extract_readable_text(homepage_html),
        "metadata": extract_metadata(homepage_html, url),
    }

    settings = get_settings()

    # 2. Find and fetch pricing page
    pricing_url = find_pricing_page(homepage_html, url)
    if pricing_url and pricing_url != url:
        time.sleep(settings.crawl_delay_seconds)
        logger.info(f"Crawling pricing page: {pricing_url}")
        pricing_html = fetch_page(pricing_url)
        if pricing_html:
            results["pricing"] = {
                "url": pricing_url,
                "text": extract_readable_text(pricing_html),
                "metadata": extract_metadata(pricing_html, pricing_url),
            }

    # 3. Find and fetch docs page
    docs_url = find_docs_page(homepage_html, url)
    if docs_url and docs_url != url:
        time.sleep(settings.crawl_delay_seconds)
        logger.info(f"Crawling docs page: {docs_url}")
        docs_html = fetch_page(docs_url)
        if docs_html:
            results["docs"] = {
                "url": docs_url,
                "text": extract_readable_text(docs_html),
                "metadata": extract_metadata(docs_html, docs_url),
            }

    metrics.crawl_latency.observe(_time.perf_counter() - start)
    return results
