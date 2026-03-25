from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import AsyncIterator, Callable, Optional, Awaitable

from claw.scraper.fetcher import fetch, FetchResult
from claw.scraper.parser import parse_html, ParsedPage
from claw.scraper.storage import PageStorage, StoredPage

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 5
MAX_PAGES = 200


@dataclass(frozen=True)
class CrawlProgress:
    completed: int
    total: int
    current_url: str
    status: str


@dataclass(frozen=True)
class CrawlResult:
    pages_saved: int
    pages_skipped: int
    pages_failed: int
    total_words: int
    errors: list[str]


@dataclass
class Crawler:
    storage: PageStorage
    on_progress: Optional[Callable[[CrawlProgress], Awaitable[None]]] = None

    async def scrape_single(self, url: str) -> tuple[StoredPage | None, str]:
        if self.storage.is_duplicate(url, ""):
            existing = self.storage.load(url)
            if existing:
                return None, "Already scraped with same content"

        result = await fetch(url)
        if not result.success:
            return None, result.error

        parsed = parse_html(result.content, base_url=result.final_url)
        if not parsed.text or parsed.word_count < 10:
            return None, "Page has no meaningful content"

        if self.storage.exists(url) and self.storage.is_duplicate(url, parsed.text):
            return None, "Content unchanged since last scrape"

        stored = self.storage.save(
            url=result.final_url,
            title=parsed.title,
            text=parsed.text,
            word_count=parsed.word_count,
            description=parsed.description,
        )
        return stored, ""

    async def crawl(self, start_url: str, max_depth: int = 2) -> CrawlResult:
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(start_url, 0)]
        saved = 0
        skipped = 0
        failed = 0
        total_words = 0
        errors: list[str] = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        async def process_url(url: str, depth: int) -> list[tuple[str, int]]:
            nonlocal saved, skipped, failed, total_words

            async with semaphore:
                if self.on_progress:
                    await self.on_progress(CrawlProgress(
                        completed=saved + skipped + failed,
                        total=len(visited),
                        current_url=url,
                        status="fetching",
                    ))

                result = await fetch(url)
                if not result.success:
                    failed += 1
                    errors.append(f"{url}: {result.error}")
                    return []

                parsed = parse_html(result.content, base_url=result.final_url)

                if not parsed.text or parsed.word_count < 10:
                    skipped += 1
                    return []

                if self.storage.exists(url) and self.storage.is_duplicate(url, parsed.text):
                    skipped += 1
                else:
                    self.storage.save(
                        url=result.final_url,
                        title=parsed.title,
                        text=parsed.text,
                        word_count=parsed.word_count,
                        description=parsed.description,
                    )
                    saved += 1
                    total_words += parsed.word_count

                child_urls = []
                if depth < max_depth:
                    for link in parsed.links:
                        if link not in visited and len(visited) < MAX_PAGES:
                            child_urls.append((link, depth + 1))

                return child_urls

        while queue:
            batch = []
            while queue and len(batch) < MAX_CONCURRENT:
                url, depth = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                batch.append((url, depth))

            if not batch:
                break

            tasks = [process_url(url, depth) for url, depth in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in results:
                if isinstance(r, Exception):
                    failed += 1
                    errors.append(str(r))
                elif isinstance(r, list):
                    queue.extend(r)

            if saved + skipped + failed >= MAX_PAGES:
                break

        return CrawlResult(
            pages_saved=saved,
            pages_skipped=skipped,
            pages_failed=failed,
            total_words=total_words,
            errors=errors[:10],
        )
