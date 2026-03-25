from __future__ import annotations

from dataclasses import dataclass

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 50


@dataclass(frozen=True)
class Chunk:
    text: str
    source_url: str
    source_title: str
    chunk_index: int
    total_chunks: int


def split_text(
    text: str,
    source_url: str,
    source_title: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    if not text or not text.strip():
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [Chunk(
            text=text.strip(),
            source_url=source_url,
            source_title=source_title,
            chunk_index=0,
            total_chunks=1,
        )]

    chunks: list[Chunk] = []
    start = 0
    step = max(1, chunk_size - overlap)

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_text = " ".join(words[start:end])

        if len(chunk_text.split()) >= MIN_CHUNK_SIZE or start == 0:
            chunks.append(Chunk(
                text=chunk_text,
                source_url=source_url,
                source_title=source_title,
                chunk_index=len(chunks),
                total_chunks=0,
            ))

        start += step

    final: list[Chunk] = []
    for c in chunks:
        final.append(Chunk(
            text=c.text,
            source_url=c.source_url,
            source_title=c.source_title,
            chunk_index=c.chunk_index,
            total_chunks=len(chunks),
        ))

    return final
