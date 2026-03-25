from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import trafilatura
from trafilatura.settings import use_config

_CONFIG = use_config()
_CONFIG.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")


@dataclass(frozen=True)
class ParsedPage:
    title: str
    text: str
    word_count: int
    links: list[str]
    description: str


def parse_html(html: str, base_url: str = "") -> ParsedPage:
    metadata = trafilatura.extract_metadata(html, default_url=base_url)

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_links=False,
        include_images=False,
        favor_precision=True,
        config=_CONFIG,
    ) or ""

    title = ""
    description = ""
    if metadata:
        title = metadata.title or ""
        description = metadata.description or ""

    links: list[str] = []
    if base_url:
        links = _extract_same_domain_links(html, base_url)

    words = text.split()
    return ParsedPage(
        title=title,
        text=text,
        word_count=len(words),
        links=links,
        description=description,
    )


def _extract_same_domain_links(html: str, base_url: str) -> list[str]:
    from lxml import etree
    from io import StringIO

    base_domain = urlparse(base_url).netloc
    seen: set[str] = set()
    result: list[str] = []

    try:
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html), parser)
    except Exception:
        return []

    for element in tree.iter("a"):
        href = element.get("href")
        if not href:
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc != base_domain:
            continue

        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        if clean not in seen:
            seen.add(clean)
            result.append(clean)

    return result
