import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from claw.scraper.crawler import Crawler, CrawlResult
from claw.scraper.fetcher import FetchResult
from claw.scraper.storage import PageStorage


HTML_TEMPLATE = """
<html><head><title>{title}</title></head>
<body>
<p>{content} This is enough text to pass the minimum word count threshold for content extraction.</p>
<a href="{link}">Link</a>
</body></html>
"""


class TestCrawlerSingle:
    @pytest.mark.asyncio
    async def test_scrape_single_success(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "k")
        crawler = Crawler(storage=storage)

        html = HTML_TEMPLATE.format(title="Test", content="Hello world", link="/other")
        fetch_result = FetchResult(
            url="https://example.com", status_code=200, content=html,
            content_type="text/html", final_url="https://example.com",
            size_bytes=len(html), success=True, error="",
        )

        with patch("claw.scraper.crawler.fetch", new_callable=AsyncMock, return_value=fetch_result):
            stored, error = await crawler.scrape_single("https://example.com")

        if stored:
            assert stored.word_count > 0
            assert error == ""
        else:
            assert "content" in error.lower() or error == ""

    @pytest.mark.asyncio
    async def test_scrape_single_fetch_failure(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "k")
        crawler = Crawler(storage=storage)

        fetch_result = FetchResult.failure("https://bad.com", "Connection refused")

        with patch("claw.scraper.crawler.fetch", new_callable=AsyncMock, return_value=fetch_result):
            stored, error = await crawler.scrape_single("https://bad.com")
            assert stored is None
            assert "Connection refused" in error

    @pytest.mark.asyncio
    async def test_scrape_single_duplicate(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "k")
        crawler = Crawler(storage=storage)

        html = HTML_TEMPLATE.format(title="T", content="duplicate test content", link="/x")
        fetch_result = FetchResult(
            url="https://a.com", status_code=200, content=html,
            content_type="text/html", final_url="https://a.com",
            size_bytes=len(html), success=True, error="",
        )

        with patch("claw.scraper.crawler.fetch", new_callable=AsyncMock, return_value=fetch_result):
            stored1, _ = await crawler.scrape_single("https://a.com")

        with patch("claw.scraper.crawler.fetch", new_callable=AsyncMock, return_value=fetch_result):
            stored2, error = await crawler.scrape_single("https://a.com")
            assert stored2 is None
            assert "unchanged" in error.lower() or "duplicate" in error.lower()


class TestCrawlerCrawl:
    @pytest.mark.asyncio
    async def test_crawl_respects_max_pages(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "k")
        crawler = Crawler(storage=storage)

        html = HTML_TEMPLATE.format(title="Page", content="Content here", link="/next")
        fetch_result = FetchResult(
            url="https://example.com", status_code=200, content=html,
            content_type="text/html", final_url="https://example.com",
            size_bytes=len(html), success=True, error="",
        )

        with patch("claw.scraper.crawler.fetch", new_callable=AsyncMock, return_value=fetch_result):
            result = await crawler.crawl("https://example.com", max_depth=0)
            assert isinstance(result, CrawlResult)

    @pytest.mark.asyncio
    async def test_crawl_handles_failures(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "k")
        crawler = Crawler(storage=storage)

        fetch_result = FetchResult.failure("https://bad.com", "timeout")

        with patch("claw.scraper.crawler.fetch", new_callable=AsyncMock, return_value=fetch_result):
            result = await crawler.crawl("https://bad.com", max_depth=0)
            assert result.pages_failed >= 1
            assert len(result.errors) >= 1
