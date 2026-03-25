from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1.0

HEADERS = {
    "User-Agent": "Claw/1.0 (Knowledge Collector)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

MAX_RESPONSE_SIZE = 10 * 1024 * 1024


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content: str
    content_type: str
    final_url: str
    size_bytes: int
    success: bool
    error: str

    @staticmethod
    def failure(url: str, error: str) -> FetchResult:
        return FetchResult(
            url=url, status_code=0, content="", content_type="",
            final_url=url, size_bytes=0, success=False, error=error,
        )


async def fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> FetchResult:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(timeout),
                headers=HEADERS,
                max_redirects=5,
            ) as client:
                response = await client.get(url)

                content_length = int(response.headers.get("content-length", 0))
                if content_length > MAX_RESPONSE_SIZE:
                    return FetchResult.failure(url, f"Response too large: {content_length} bytes")

                content = response.text
                if len(content.encode("utf-8")) > MAX_RESPONSE_SIZE:
                    return FetchResult.failure(url, "Response exceeded size limit")

                return FetchResult(
                    url=url,
                    status_code=response.status_code,
                    content=content,
                    content_type=response.headers.get("content-type", ""),
                    final_url=str(response.url),
                    size_bytes=len(content.encode("utf-8")),
                    success=200 <= response.status_code < 400,
                    error="" if 200 <= response.status_code < 400 else f"HTTP {response.status_code}",
                )

        except httpx.TimeoutException:
            if attempt == MAX_RETRIES:
                return FetchResult.failure(url, f"Timeout after {MAX_RETRIES} attempts")
            await asyncio.sleep(RETRY_DELAY * attempt)

        except httpx.TooManyRedirects:
            return FetchResult.failure(url, "Too many redirects")

        except httpx.RequestError as e:
            if attempt == MAX_RETRIES:
                return FetchResult.failure(url, f"Request failed: {type(e).__name__}")
            await asyncio.sleep(RETRY_DELAY * attempt)

    return FetchResult.failure(url, "Exhausted retries")
