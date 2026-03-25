import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from claw.scraper.fetcher import fetch, FetchResult, MAX_RESPONSE_SIZE


class TestFetchResult:
    def test_failure_factory(self):
        result = FetchResult.failure("https://x.com", "timeout")
        assert result.success is False
        assert result.error == "timeout"
        assert result.status_code == 0

    def test_immutable(self):
        result = FetchResult.failure("https://x.com", "err")
        with pytest.raises(AttributeError):
            result.url = "changed"


class TestFetch:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>content</html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("claw.scraper.fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetch("https://example.com")
            assert result.success is True
            assert result.status_code == 200
            assert "content" in result.content

    @pytest.mark.asyncio
    async def test_timeout_retries(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("claw.scraper.fetcher.httpx.AsyncClient", return_value=mock_client):
            with patch("claw.scraper.fetcher.RETRY_DELAY", 0):
                result = await fetch("https://example.com")
                assert result.success is False
                assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_too_many_redirects(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TooManyRedirects("too many"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("claw.scraper.fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetch("https://example.com")
            assert result.success is False
            assert "redirect" in result.error.lower()

    @pytest.mark.asyncio
    async def test_http_error_status(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com/missing"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("claw.scraper.fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetch("https://example.com/missing")
            assert result.success is False
            assert "404" in result.error

    @pytest.mark.asyncio
    async def test_oversized_content_length(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "small"
        mock_response.headers = {"content-type": "text/html", "content-length": str(MAX_RESPONSE_SIZE + 1)}
        mock_response.url = "https://example.com"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("claw.scraper.fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetch("https://example.com")
            assert result.success is False
            assert "large" in result.error.lower()
