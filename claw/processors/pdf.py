from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)

MAX_PAGES = 500
MAX_FILE_SIZE = 50 * 1024 * 1024


@dataclass(frozen=True)
class PDFResult:
    text: str
    pages: int
    word_count: int
    title: str
    success: bool
    error: str


def extract_pdf(file_path: Path) -> PDFResult:
    if not file_path.exists():
        return PDFResult(text="", pages=0, word_count=0, title="", success=False, error="File not found")

    if file_path.stat().st_size > MAX_FILE_SIZE:
        return PDFResult(text="", pages=0, word_count=0, title="", success=False, error="File too large (50MB max)")

    try:
        doc = fitz.open(str(file_path))
    except Exception as e:
        return PDFResult(text="", pages=0, word_count=0, title="", success=False, error=f"Cannot open PDF: {e}")

    try:
        page_count = min(doc.page_count, MAX_PAGES)
        title = doc.metadata.get("title", "") or file_path.stem

        parts: list[str] = []
        for i in range(page_count):
            page = doc.load_page(i)
            text = page.get_text("text")
            if text.strip():
                parts.append(text.strip())

        full_text = "\n\n".join(parts)
        words = full_text.split()

        return PDFResult(
            text=full_text,
            pages=page_count,
            word_count=len(words),
            title=title,
            success=True,
            error="",
        )
    finally:
        doc.close()
