import pytest
import numpy as np

from claw.rag.chunker import Chunk
from claw.rag.index import VectorIndex, SearchResult
from claw.rag.embedder import EMBEDDING_DIM


def _make_chunks(n: int, url: str = "https://a.com") -> list[Chunk]:
    return [
        Chunk(text=f"chunk {i}", source_url=url, source_title="T", chunk_index=i, total_chunks=n)
        for i in range(n)
    ]


def _make_embeddings(n: int) -> np.ndarray:
    rng = np.random.default_rng(42)
    vecs = rng.standard_normal((n, EMBEDDING_DIM)).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms


class TestVectorIndex:
    def test_create_empty(self, tmp_path):
        idx = VectorIndex(index_dir=tmp_path / "idx")
        assert idx.total_chunks == 0
        assert idx.total_vectors == 0

    def test_add_and_search(self, tmp_path):
        idx = VectorIndex(index_dir=tmp_path / "idx")
        chunks = _make_chunks(5)
        embeddings = _make_embeddings(5)
        added = idx.add(chunks, embeddings)
        assert added == 5
        assert idx.total_chunks == 5

        results = idx.search(embeddings[0], top_k=3)
        assert len(results) == 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].score >= results[1].score

    def test_persistence(self, tmp_path):
        idx_dir = tmp_path / "idx"
        idx1 = VectorIndex(index_dir=idx_dir)
        idx1.add(_make_chunks(3), _make_embeddings(3))

        idx2 = VectorIndex(index_dir=idx_dir)
        assert idx2.total_chunks == 3
        assert idx2.total_vectors == 3

    def test_search_empty_index(self, tmp_path):
        idx = VectorIndex(index_dir=tmp_path / "idx")
        query = _make_embeddings(1)[0]
        results = idx.search(query)
        assert results == []

    def test_remove_by_url(self, tmp_path):
        idx = VectorIndex(index_dir=tmp_path / "idx")
        chunks_a = _make_chunks(3, url="https://a.com")
        chunks_b = _make_chunks(2, url="https://b.com")
        emb = _make_embeddings(5)

        idx.add(chunks_a, emb[:3])
        idx.add(chunks_b, emb[3:])
        assert idx.total_chunks == 5

        removed = idx.remove_by_url("https://a.com")
        assert removed == 3
        assert idx.total_chunks == 2

    def test_remove_all_by_url(self, tmp_path):
        idx = VectorIndex(index_dir=tmp_path / "idx")
        chunks = _make_chunks(3, url="https://a.com")
        idx.add(chunks, _make_embeddings(3))

        removed = idx.remove_by_url("https://a.com")
        assert removed == 3
        assert idx.total_chunks == 0

    def test_remove_nonexistent_url(self, tmp_path):
        idx = VectorIndex(index_dir=tmp_path / "idx")
        idx.add(_make_chunks(2), _make_embeddings(2))
        removed = idx.remove_by_url("https://nope.com")
        assert removed == 0

    def test_sources(self, tmp_path):
        idx = VectorIndex(index_dir=tmp_path / "idx")
        idx.add(_make_chunks(3, "https://a.com"), _make_embeddings(3))
        idx.add(_make_chunks(2, "https://b.com"), _make_embeddings(2))
        sources = idx.sources()
        assert sources["https://a.com"] == 3
        assert sources["https://b.com"] == 2

    def test_add_empty(self, tmp_path):
        idx = VectorIndex(index_dir=tmp_path / "idx")
        added = idx.add([], np.empty((0, EMBEDDING_DIM), dtype=np.float32))
        assert added == 0
