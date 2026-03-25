import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from claw.scraper.storage import PageStorage, StoredPage
from claw.scraper.crawler import Crawler, CrawlResult
from claw.telegram.handlers import scrape


@pytest.fixture
def setup_scrape(tmp_path):
    storage = PageStorage(base_dir=tmp_path / "knowledge")
    scrape.setup(storage)
    return storage


def _make_message() -> MagicMock:
    msg = MagicMock()
    msg.answer = AsyncMock(return_value=MagicMock(edit_text=AsyncMock()))
    return msg


class TestHandleScrape:
    @pytest.mark.asyncio
    async def test_scrape_success(self, setup_scrape):
        msg = _make_message()
        processing = MagicMock(edit_text=AsyncMock())
        msg.answer = AsyncMock(return_value=processing)

        stored = StoredPage(
            url="https://example.com", title="Example", text="content",
            word_count=100, description="", scraped_at="2024-01-01",
            content_hash="abc", source_file="/tmp/x.txt",
        )

        with patch.object(scrape._crawler, "scrape_single", new_callable=AsyncMock, return_value=(stored, "")):
            await scrape.handle_scrape(msg, "https://example.com")
            processing.edit_text.assert_awaited_once()
            assert "100" in processing.edit_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_scrape_error(self, setup_scrape):
        msg = _make_message()
        processing = MagicMock(edit_text=AsyncMock())
        msg.answer = AsyncMock(return_value=processing)

        with patch.object(scrape._crawler, "scrape_single", new_callable=AsyncMock, return_value=(None, "Connection refused")):
            await scrape.handle_scrape(msg, "https://bad.com")
            assert "Connection refused" in processing.edit_text.call_args[0][0]


class TestHandleSources:
    @pytest.mark.asyncio
    async def test_empty_sources(self, setup_scrape):
        msg = _make_message()
        msg.answer = AsyncMock()
        await scrape.handle_sources(msg)
        assert "no saved" in msg.answer.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_lists_sources(self, setup_scrape, tmp_path):
        storage = setup_scrape
        storage.save("https://a.com", "Page A", "text", 100, "")
        msg = _make_message()
        msg.answer = AsyncMock()
        await scrape.handle_sources(msg)
        assert "Page A" in msg.answer.call_args[0][0]


class TestHandleKnowledgeStats:
    @pytest.mark.asyncio
    async def test_shows_stats(self, setup_scrape):
        storage = setup_scrape
        storage.save("https://a.com", "A", "one two three", 3, "")
        msg = _make_message()
        msg.answer = AsyncMock()
        await scrape.handle_knowledge_stats(msg)
        response = msg.answer.call_args[0][0]
        assert "1" in response
        assert "3" in response


class TestHandleDelete:
    @pytest.mark.asyncio
    async def test_delete_existing(self, setup_scrape):
        storage = setup_scrape
        storage.save("https://a.com", "A", "text", 1, "")
        msg = _make_message()
        msg.answer = AsyncMock()
        await scrape.handle_delete(msg, "https://a.com")
        assert "deleted" in msg.answer.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, setup_scrape):
        msg = _make_message()
        msg.answer = AsyncMock()
        await scrape.handle_delete(msg, "https://nope.com")
        assert "not found" in msg.answer.call_args[0][0].lower()
