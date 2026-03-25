from __future__ import annotations

from dataclasses import dataclass

from claw.scraper.fetcher import fetch
from claw.scraper.parser import parse_html
from claw.scraper.storage import PageStorage


@dataclass(frozen=True)
class VerifyResult:
    url: str
    status: str
    word_count_original: int
    word_count_current: int
    content_changed: bool


async def verify_page(storage: PageStorage, url: str) -> VerifyResult:
    stored = storage.load(url)
    if not stored:
        return VerifyResult(
            url=url, status="not_found",
            word_count_original=0, word_count_current=0, content_changed=False,
        )

    result = await fetch(url)
    if not result.success:
        return VerifyResult(
            url=url, status=f"fetch_failed: {result.error}",
            word_count_original=stored.word_count, word_count_current=0,
            content_changed=False,
        )

    parsed = parse_html(result.content, base_url=result.final_url)
    changed = not storage.is_duplicate(url, parsed.text)

    return VerifyResult(
        url=url,
        status="changed" if changed else "verified",
        word_count_original=stored.word_count,
        word_count_current=parsed.word_count,
        content_changed=changed,
    )
