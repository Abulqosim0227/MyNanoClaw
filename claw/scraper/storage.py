from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class StoredPage:
    url: str
    title: str
    text: str
    word_count: int
    description: str
    scraped_at: str
    content_hash: str
    source_file: str


def _url_to_filename(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:32]


@dataclass
class PageStorage:
    base_dir: Path

    def __post_init__(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "pages").mkdir(exist_ok=True)
        (self.base_dir / "index").mkdir(exist_ok=True)

    def save(self, url: str, title: str, text: str, word_count: int, description: str) -> StoredPage:
        file_id = _url_to_filename(url)
        content_file = self.base_dir / "pages" / f"{file_id}.txt"
        meta_file = self.base_dir / "index" / f"{file_id}.json"

        content_file.write_text(text, encoding="utf-8")

        page = StoredPage(
            url=url,
            title=title,
            text=text,
            word_count=word_count,
            description=description,
            scraped_at=datetime.now(timezone.utc).isoformat(),
            content_hash=_content_hash(text),
            source_file=str(content_file),
        )

        meta = {k: v for k, v in asdict(page).items() if k != "text"}
        meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        return page

    def exists(self, url: str) -> bool:
        file_id = _url_to_filename(url)
        return (self.base_dir / "index" / f"{file_id}.json").exists()

    def is_duplicate(self, url: str, text: str) -> bool:
        file_id = _url_to_filename(url)
        meta_file = self.base_dir / "index" / f"{file_id}.json"
        if not meta_file.exists():
            return False
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        return meta.get("content_hash") == _content_hash(text)

    def load(self, url: str) -> Optional[StoredPage]:
        file_id = _url_to_filename(url)
        meta_file = self.base_dir / "index" / f"{file_id}.json"
        content_file = self.base_dir / "pages" / f"{file_id}.txt"

        if not meta_file.exists() or not content_file.exists():
            return None

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        text = content_file.read_text(encoding="utf-8")

        return StoredPage(text=text, **meta)

    def list_pages(self) -> list[dict]:
        pages = []
        for meta_file in sorted((self.base_dir / "index").glob("*.json")):
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            pages.append(meta)
        return pages

    def delete(self, url: str) -> bool:
        file_id = _url_to_filename(url)
        meta_file = self.base_dir / "index" / f"{file_id}.json"
        content_file = self.base_dir / "pages" / f"{file_id}.txt"

        deleted = False
        if meta_file.exists():
            meta_file.unlink()
            deleted = True
        if content_file.exists():
            content_file.unlink()
            deleted = True
        return deleted

    def stats(self) -> dict[str, int]:
        pages = self.list_pages()
        total_words = sum(p.get("word_count", 0) for p in pages)
        return {
            "total_pages": len(pages),
            "total_words": total_words,
            "estimated_tokens": total_words * 4 // 3,
        }
