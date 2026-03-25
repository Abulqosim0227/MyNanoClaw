from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from aiogram import Router, Bot
from aiogram.types import Message

from claw.processors.document import extract_text_file, extract_docx
from claw.processors.pdf import extract_pdf
from claw.processors.voice import transcribe_voice
from claw.rag.chunker import split_text
from claw.rag.embedder import Embedder
from claw.rag.index import VectorIndex
from claw.scraper.storage import PageStorage

logger = logging.getLogger(__name__)

router = Router()

_storage: PageStorage | None = None
_embedder: Embedder | None = None
_index: VectorIndex | None = None

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc", ".csv", ".json", ".py", ".js", ".html"}


def setup(
    storage: PageStorage,
    embedder: Embedder | None = None,
    index: VectorIndex | None = None,
) -> None:
    global _storage, _embedder, _index
    _storage = storage
    _embedder = embedder
    _index = index


def _index_text(source: str, title: str, text: str) -> int:
    if not _embedder or not _index or not text.strip():
        return 0

    chunks = split_text(text, source_url=source, source_title=title)
    if not chunks:
        return 0

    embeddings = _embedder.embed([c.text for c in chunks])
    return _index.add(chunks, embeddings)


async def _download_file(bot: Bot, file_id: str, suffix: str) -> Path:
    file = await bot.get_file(file_id)
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    await bot.download_file(file.file_path, tmp.name)
    tmp.close()
    return Path(tmp.name)


@router.message(lambda m: m.document is not None)
async def handle_document(message: Message) -> None:
    doc = message.document
    file_name = doc.file_name or "unknown"
    ext = Path(file_name).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        await message.answer(f"Unsupported file type: {ext}\nSupported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        return

    processing = await message.answer(f"Processing {file_name}...")

    try:
        file_path = await _download_file(message.bot, doc.file_id, ext)
    except Exception as e:
        await processing.edit_text(f"Download failed: {e}")
        return

    try:
        if ext == ".pdf":
            result = extract_pdf(file_path)
            if not result.success:
                await processing.edit_text(f"PDF error: {result.error}")
                return
            text, title, word_count = result.text, result.title, result.word_count
            extra = f"{result.pages} pages"

        elif ext == ".docx":
            result = extract_docx(file_path)
            if not result.success:
                await processing.edit_text(f"DOCX error: {result.error}")
                return
            text, title, word_count = result.text, result.title, result.word_count
            extra = "DOCX"

        else:
            result = extract_text_file(file_path)
            if not result.success:
                await processing.edit_text(f"Read error: {result.error}")
                return
            text, title, word_count = result.text, result.title, result.word_count
            extra = ext.lstrip(".")

        if word_count < 5:
            await processing.edit_text("File has no meaningful content.")
            return

        source = f"file://{file_name}"
        _storage.save(url=source, title=title, text=text, word_count=word_count, description=f"Uploaded {extra}")
        chunks_added = _index_text(source, title, text)

        lines = [
            f"Saved: {title}",
            f"{word_count:,} words ({extra})",
        ]
        if chunks_added:
            lines.append(f"Indexed: {chunks_added} chunks for search")

        await processing.edit_text("\n".join(lines))
        logger.info("file=%s words=%d chunks=%d", file_name, word_count, chunks_added)

    finally:
        file_path.unlink(missing_ok=True)


@router.message(lambda m: m.voice is not None)
async def handle_voice(message: Message) -> None:
    processing = await message.answer("Transcribing voice...")

    try:
        file_path = await _download_file(message.bot, message.voice.file_id, ".ogg")
    except Exception as e:
        await processing.edit_text(f"Download failed: {e}")
        return

    try:
        result = transcribe_voice(file_path)

        if not result.success:
            await processing.edit_text(f"Transcription failed: {result.error}")
            return

        lines = [
            f"Transcribed ({result.duration_seconds:.0f}s):",
            "",
            result.text,
        ]
        await processing.edit_text("\n".join(lines))
        logger.info("voice duration=%.0fs words=%d", result.duration_seconds, len(result.text.split()))

    finally:
        file_path.unlink(missing_ok=True)
