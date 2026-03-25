from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import faiss
import numpy as np

from claw.rag.chunker import Chunk
from claw.rag.embedder import EMBEDDING_DIM

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float


@dataclass
class VectorIndex:
    index_dir: Path
    _index: faiss.IndexFlatIP = field(default=None, repr=False)
    _chunks: list[Chunk] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._load_or_create()

    def _load_or_create(self) -> None:
        index_path = self.index_dir / "faiss.index"
        meta_path = self.index_dir / "chunks.json"

        if index_path.exists() and meta_path.exists():
            self._index = faiss.read_index(str(index_path))
            raw = json.loads(meta_path.read_text(encoding="utf-8"))
            self._chunks = [
                Chunk(
                    text=c["text"],
                    source_url=c["source_url"],
                    source_title=c["source_title"],
                    chunk_index=c["chunk_index"],
                    total_chunks=c["total_chunks"],
                )
                for c in raw
            ]
            logger.info("Loaded index: %d vectors", self._index.ntotal)
        else:
            self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
            self._chunks = []

    def add(self, chunks: Sequence[Chunk], embeddings: np.ndarray) -> int:
        if len(chunks) == 0 or embeddings.shape[0] == 0:
            return 0
        self._index.add(embeddings)
        self._chunks.extend(chunks)
        self._save()
        return len(chunks)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        if self._index.ntotal == 0:
            return []

        top_k = min(top_k, self._index.ntotal)
        query = query_embedding.reshape(1, -1)
        scores, indices = self._index.search(query, top_k)

        results: list[SearchResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            results.append(SearchResult(
                chunk=self._chunks[idx],
                score=float(score),
            ))

        return results

    def remove_by_url(self, url: str) -> int:
        keep_indices = [i for i, c in enumerate(self._chunks) if c.source_url != url]
        removed = len(self._chunks) - len(keep_indices)

        if removed == 0:
            return 0

        if not keep_indices:
            self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
            self._chunks = []
            self._save()
            return removed

        all_vectors = faiss.rev_swig_ptr(self._index.get_xb(), self._index.ntotal * EMBEDDING_DIM)
        all_vectors = all_vectors.reshape(self._index.ntotal, EMBEDDING_DIM).copy()

        keep_vectors = all_vectors[keep_indices]
        keep_chunks = [self._chunks[i] for i in keep_indices]

        self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self._index.add(keep_vectors)
        self._chunks = keep_chunks
        self._save()

        return removed

    def _save(self) -> None:
        faiss.write_index(self._index, str(self.index_dir / "faiss.index"))
        meta = [
            {
                "text": c.text,
                "source_url": c.source_url,
                "source_title": c.source_title,
                "chunk_index": c.chunk_index,
                "total_chunks": c.total_chunks,
            }
            for c in self._chunks
        ]
        (self.index_dir / "chunks.json").write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8"
        )

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal

    def sources(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for c in self._chunks:
            counts[c.source_url] = counts.get(c.source_url, 0) + 1
        return counts
