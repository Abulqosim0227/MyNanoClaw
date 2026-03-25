from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024


@dataclass(frozen=True)
class DocResult:
    text: str
    word_count: int
    title: str
    file_type: str
    success: bool
    error: str


def extract_text_file(file_path: Path) -> DocResult:
    if not file_path.exists():
        return DocResult(text="", word_count=0, title="", file_type="txt", success=False, error="File not found")

    if file_path.stat().st_size > MAX_FILE_SIZE:
        return DocResult(text="", word_count=0, title="", file_type="txt", success=False, error="File too large (20MB max)")

    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = file_path.read_text(encoding="latin-1")
        except Exception as e:
            return DocResult(text="", word_count=0, title="", file_type="txt", success=False, error=f"Cannot read: {e}")

    words = text.split()
    return DocResult(
        text=text.strip(),
        word_count=len(words),
        title=file_path.stem,
        file_type="txt",
        success=True,
        error="",
    )


def extract_docx(file_path: Path) -> DocResult:
    if not file_path.exists():
        return DocResult(text="", word_count=0, title="", file_type="docx", success=False, error="File not found")

    if file_path.stat().st_size > MAX_FILE_SIZE:
        return DocResult(text="", word_count=0, title="", file_type="docx", success=False, error="File too large (20MB max)")

    try:
        from docx import Document
        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n\n".join(paragraphs)
        words = text.split()

        return DocResult(
            text=text,
            word_count=len(words),
            title=file_path.stem,
            file_type="docx",
            success=True,
            error="",
        )
    except Exception as e:
        return DocResult(text="", word_count=0, title="", file_type="docx", success=False, error=f"Cannot read DOCX: {e}")
