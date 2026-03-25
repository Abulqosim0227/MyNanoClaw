from __future__ import annotations

import logging

from aiogram.types import Message

from claw.rag.chunker import split_text
from claw.rag.embedder import Embedder
from claw.rag.index import VectorIndex
from claw.scraper.crawler import Crawler, CrawlProgress
from claw.scraper.storage import PageStorage

logger = logging.getLogger(__name__)

_storage: PageStorage | None = None
_crawler: Crawler | None = None
_embedder: Embedder | None = None
_index: VectorIndex | None = None


def setup(
    storage: PageStorage,
    embedder: Embedder | None = None,
    index: VectorIndex | None = None,
) -> None:
    global _storage, _crawler, _embedder, _index

    _storage = storage
    _embedder = embedder
    _index = index
    _crawler = Crawler(storage=storage)


def _index_page(url: str, title: str, text: str) -> int:
    if not _embedder or not _index:
        return 0

    chunks = split_text(text, source_url=url, source_title=title)
    if not chunks:
        return 0

    texts = [c.text for c in chunks]
    embeddings = _embedder.embed(texts)
    return _index.add(chunks, embeddings)


async def handle_scrape(message: Message, url: str) -> None:
    processing = await message.answer(f"Scraping {url}...")

    stored, error = await _crawler.scrape_single(url)

    if error:
        await processing.edit_text(f"Skipped: {error}")
        return

    chunks_added = _index_page(stored.url, stored.title, stored.text)

    lines = [
        f"Saved: {stored.title or 'Untitled'}",
        f"{stored.word_count:,} words from {stored.url}",
    ]
    if chunks_added:
        lines.append(f"Indexed: {chunks_added} chunks for search")

    await processing.edit_text("\n".join(lines))
    logger.info("scraped url=%s words=%d chunks=%d", url, stored.word_count, chunks_added)


async def handle_crawl(message: Message, url: str, depth: int) -> None:
    status_msg = await message.answer(f"Crawling {url} (depth {depth})...")

    update_counter = 0

    async def on_progress(progress: CrawlProgress) -> None:
        nonlocal update_counter
        update_counter += 1
        if update_counter % 5 == 0:
            try:
                await status_msg.edit_text(
                    f"Crawling... {progress.completed} pages processed\n"
                    f"Current: {progress.current_url[:60]}"
                )
            except Exception:
                pass

    _crawler.on_progress = on_progress
    result = await _crawler.crawl(start_url=url, max_depth=depth)

    total_chunks = 0
    if _embedder and _index:
        for page_meta in _storage.list_pages():
            page = _storage.load(page_meta["url"])
            if page:
                total_chunks += _index_page(page.url, page.title, page.text)

    lines = [
        f"Crawl complete: {url}",
        f"Saved: {result.pages_saved} pages",
        f"Skipped: {result.pages_skipped} (duplicates/empty)",
        f"Failed: {result.pages_failed}",
        f"Total words: {result.total_words:,}",
    ]
    if total_chunks:
        lines.append(f"Indexed: {total_chunks} chunks for search")
    if result.errors:
        lines.append(f"\nFirst errors:")
        for err in result.errors[:3]:
            lines.append(f"  {err[:80]}")

    await status_msg.edit_text("\n".join(lines))
    logger.info(
        "crawl url=%s saved=%d failed=%d words=%d chunks=%d",
        url, result.pages_saved, result.pages_failed, result.total_words, total_chunks,
    )


async def handle_sources(message: Message) -> None:
    pages = _storage.list_pages()
    if not pages:
        await message.answer("No saved pages yet. Send me a URL to start.")
        return

    lines = [f"Knowledge base: {len(pages)} pages\n"]
    for page in pages[:20]:
        title = page.get("title", "Untitled")[:40]
        words = page.get("word_count", 0)
        url = page.get("url", "")[:50]
        lines.append(f"  {title}\n  {url} ({words:,} words)\n")

    if len(pages) > 20:
        lines.append(f"\n...and {len(pages) - 20} more")

    await message.answer("\n".join(lines))


async def handle_knowledge_stats(message: Message) -> None:
    stats = _storage.stats()
    chunks = _index.total_chunks if _index else 0
    await message.answer(
        f"Pages: {stats['total_pages']}\n"
        f"Words: {stats['total_words']:,}\n"
        f"Chunks indexed: {chunks}\n"
        f"Estimated tokens: ~{stats['estimated_tokens']:,}"
    )


async def handle_delete(message: Message, url: str) -> None:
    deleted = _storage.delete(url)
    removed_chunks = 0
    if deleted and _index:
        removed_chunks = _index.remove_by_url(url)

    if deleted:
        msg = f"Deleted: {url}"
        if removed_chunks:
            msg += f"\nRemoved {removed_chunks} chunks from search index"
        await message.answer(msg)
    else:
        await message.answer(f"Not found: {url}")
