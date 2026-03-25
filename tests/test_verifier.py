import pytest
from unittest.mock import AsyncMock, patch

from claw.scraper.fetcher import FetchResult
from claw.scraper.storage import PageStorage
from claw.scraper.verifier import verify_page


class TestVerifyPage:
    @pytest.mark.asyncio
    async def test_not_found(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "k")
        result = await verify_page(storage, "https://nope.com")
        assert result.status == "not_found"

    @pytest.mark.asyncio
    async def test_verified_unchanged(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "k")
        storage.save("https://a.com", "T", "same content here", 3, "")

        html = "<html><body><p>same content here</p></body></html>"
        fetch_result = FetchResult(
            url="https://a.com", status_code=200, content=html,
            content_type="text/html", final_url="https://a.com",
            size_bytes=len(html), success=True, error="",
        )

        with patch("claw.scraper.verifier.fetch", new_callable=AsyncMock, return_value=fetch_result):
            result = await verify_page(storage, "https://a.com")
            assert result.status in ("verified", "changed")
            assert result.word_count_original == 3

    @pytest.mark.asyncio
    async def test_fetch_failed(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "k")
        storage.save("https://a.com", "T", "content", 1, "")

        fetch_result = FetchResult.failure("https://a.com", "timeout")

        with patch("claw.scraper.verifier.fetch", new_callable=AsyncMock, return_value=fetch_result):
            result = await verify_page(storage, "https://a.com")
            assert "fetch_failed" in result.status
