"""Tests for web_crawler and search_crawler modules."""

from unittest.mock import patch, MagicMock

import pytest

from crawler.web_crawler import (
    is_valid_url,
    fetch_page,
    extract_readable_text,
    extract_metadata,
    find_pricing_page,
    find_docs_page,
    crawl_tool_website,
)
from crawler.search_crawler import search_external_references, discover_ai_tools


# ── URL Validation ─────────────────────────────────────────────────────


class TestIsValidUrl:
    def test_valid_https(self):
        assert is_valid_url("https://example.com") is True

    def test_valid_http(self):
        assert is_valid_url("http://example.com") is True

    def test_valid_with_path(self):
        assert is_valid_url("https://example.com/pricing") is True

    def test_invalid_no_scheme(self):
        assert is_valid_url("example.com") is False

    def test_invalid_ftp(self):
        assert is_valid_url("ftp://example.com") is False

    def test_invalid_empty_string(self):
        assert is_valid_url("") is False

    def test_invalid_random_text(self):
        assert is_valid_url("not-a-url") is False


# ── HTML Extraction ────────────────────────────────────────────────────


class TestExtractReadableText:
    def test_extracts_main_content(self, sample_html):
        text = extract_readable_text(sample_html)
        assert "TestTool" in text
        assert "AI coding assistant" in text or "write faster" in text

    def test_handles_empty_html(self):
        text = extract_readable_text("<html><body></body></html>")
        assert isinstance(text, str)


class TestExtractMetadata:
    def test_extracts_title_and_description(self, sample_html):
        meta = extract_metadata(sample_html, "https://testtool.ai")
        assert meta["title"] == "TestTool - AI Code Assistant"
        assert "AI-powered code completion" in meta["description"]
        assert meta["url"] == "https://testtool.ai"

    def test_handles_missing_title(self):
        html = "<html><head></head><body>Hello</body></html>"
        meta = extract_metadata(html, "https://x.com")
        assert meta["title"] == ""

    def test_handles_missing_description(self):
        html = "<html><head><title>A Title</title></head><body></body></html>"
        meta = extract_metadata(html, "https://x.com")
        assert meta["description"] == ""


class TestFindPricingPage:
    def test_finds_pricing_link(self, sample_html):
        url = find_pricing_page(sample_html, "https://testtool.ai")
        assert url == "https://testtool.ai/pricing"

    def test_returns_none_when_no_pricing_link(self):
        html = "<html><body><a href='/about'>About</a></body></html>"
        assert find_pricing_page(html, "https://x.com") is None


class TestFindDocsPage:
    def test_finds_docs_link(self, sample_html):
        url = find_docs_page(sample_html, "https://testtool.ai")
        assert url == "https://testtool.ai/docs"

    def test_returns_none_when_no_docs_link(self):
        html = "<html><body><a href='/about'>About</a></body></html>"
        assert find_docs_page(html, "https://x.com") is None


# ── Fetch Page ─────────────────────────────────────────────────────────


class TestFetchPage:
    @patch("crawler.web_crawler.requests.get")
    def test_fetch_success(self, mock_get):
        resp = MagicMock()
        resp.text = "<html>OK</html>"
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        html = fetch_page("https://example.com")
        assert html == "<html>OK</html>"

    @patch("backend.retry.time.sleep")
    @patch("crawler.web_crawler.requests.get")
    def test_fetch_timeout(self, mock_get, mock_sleep):
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()
        assert fetch_page("https://example.com") is None

    def test_fetch_invalid_url(self):
        assert fetch_page("not-a-url") is None


# ── Crawl Tool Website ────────────────────────────────────────────────


class TestCrawlToolWebsite:
    @patch("crawler.web_crawler.fetch_page")
    def test_crawl_returns_homepage(self, mock_fetch, sample_html):
        mock_fetch.return_value = sample_html
        results = crawl_tool_website("https://testtool.ai")

        assert "homepage" in results
        assert results["homepage"]["url"] == "https://testtool.ai"
        assert "text" in results["homepage"]

    @patch("crawler.web_crawler.fetch_page")
    def test_crawl_handles_failure(self, mock_fetch):
        mock_fetch.return_value = None
        results = crawl_tool_website("https://down.com")
        assert results == {}


# ── Search Crawler ────────────────────────────────────────────────────


class TestSearchExternalReferences:
    @patch("crawler.search_crawler.DDGS")
    def test_returns_results(self, MockDDGS):
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "Review", "href": "https://blog.com/review", "body": "Great tool"},
        ]
        MockDDGS.return_value = mock_ddgs

        results = search_external_references("TestTool", max_results=2)
        assert len(results) >= 1
        assert results[0]["url"] == "https://blog.com/review"

    @patch("crawler.search_crawler.DDGS")
    def test_handles_ddg_exception(self, MockDDGS):
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.side_effect = Exception("Rate limit")
        MockDDGS.return_value = mock_ddgs

        results = search_external_references("TestTool")
        assert results == []


class TestDiscoverAITools:
    @patch("crawler.search_crawler.DDGS")
    def test_returns_discovered(self, MockDDGS):
        # Reset circuit breaker state from previous tests
        import crawler.search_crawler as sc
        sc._ddg_consecutive_failures = 0

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "New Tool", "href": "https://newtool.ai", "body": "A new tool"},
        ]
        MockDDGS.return_value = mock_ddgs

        results = discover_ai_tools(category="AI coding", max_results=2)
        assert len(results) >= 1
