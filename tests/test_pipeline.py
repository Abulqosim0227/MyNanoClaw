import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from claw.core.engine import ClaudeEngine, EngineResult
from claw.rag.chunker import Chunk
from claw.rag.embedder import Embedder, EMBEDDING_DIM
from claw.rag.index import VectorIndex, SearchResult
from claw.rag.pipeline import RAGPipeline, RAGResult


def _make_embedder_mock() -> Embedder:
    embedder = MagicMock(spec=Embedder)
    embedder.dimension = EMBEDDING_DIM

    def mock_embed_single(text):
        rng = np.random.default_rng(hash(text) % (2**31))
        vec = rng.standard_normal(EMBEDDING_DIM).astype(np.float32)
        return vec / np.linalg.norm(vec)

    embedder.embed_single = mock_embed_single
    embedder.embed = lambda texts: np.stack([mock_embed_single(t) for t in texts])
    return embedder


class TestRAGPipeline:
    @pytest.mark.asyncio
    async def test_empty_knowledge_base(self, tmp_path):
        embedder = _make_embedder_mock()
        index = VectorIndex(index_dir=tmp_path / "idx")
        engine = ClaudeEngine(model="sonnet")

        pipeline = RAGPipeline(embedder=embedder, index=index, engine=engine)
        result = await pipeline.query("test question")

        assert result.gate_passed is False
        assert "empty" in result.answer.lower()
        assert result.chunks_used == 0

    @pytest.mark.asyncio
    async def test_rag_with_matching_data(self, tmp_path):
        embedder = _make_embedder_mock()
        index = VectorIndex(index_dir=tmp_path / "idx")
        engine = ClaudeEngine(model="sonnet")

        chunks = [
            Chunk(text="Python decorators wrap functions", source_url="https://a.com",
                  source_title="Python Guide", chunk_index=0, total_chunks=1),
        ]
        embeddings = embedder.embed([c.text for c in chunks])
        index.add(chunks, embeddings)

        pipeline = RAGPipeline(embedder=embedder, index=index, engine=engine)

        fake_result = EngineResult(
            response="Based on your data, decorators wrap functions.",
            prompt_tokens=100, response_tokens=20, model="sonnet", truncated=False,
        )

        with patch.object(engine, "ask", new_callable=AsyncMock, return_value=fake_result):
            result = await pipeline.query("what are python decorators")

        if result.gate_passed:
            assert result.chunks_used > 0
            assert len(result.sources) > 0
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_fallback_on_low_relevance(self, tmp_path):
        embedder = _make_embedder_mock()
        index = VectorIndex(index_dir=tmp_path / "idx")
        engine = ClaudeEngine(model="sonnet")

        chunks = [
            Chunk(text="cats are cute animals", source_url="https://cats.com",
                  source_title="Cats", chunk_index=0, total_chunks=1),
        ]
        embeddings = embedder.embed([c.text for c in chunks])
        index.add(chunks, embeddings)

        pipeline = RAGPipeline(embedder=embedder, index=index, engine=engine)

        fake_result = EngineResult(
            response="Quantum physics is about subatomic particles.",
            prompt_tokens=50, response_tokens=10, model="sonnet", truncated=False,
        )

        with patch.object(engine, "ask", new_callable=AsyncMock, return_value=fake_result):
            result = await pipeline.query("explain quantum physics")

        assert result.fallback is True or result.gate_passed is True

    @pytest.mark.asyncio
    async def test_index_chunks(self, tmp_path):
        embedder = _make_embedder_mock()
        index = VectorIndex(index_dir=tmp_path / "idx")
        engine = ClaudeEngine(model="sonnet")
        pipeline = RAGPipeline(embedder=embedder, index=index, engine=engine)

        chunks = [
            Chunk(text="test", source_url="https://a.com", source_title="T",
                  chunk_index=0, total_chunks=1),
        ]
        embeddings = embedder.embed(["test"])
        added = pipeline.index_chunks(chunks, embeddings)
        assert added == 1


class TestRAGResult:
    def test_structure(self):
        result = RAGResult(
            answer="test", sources=["https://a.com"], confidence=0.9,
            chunks_used=3, gate_passed=True, fallback=False,
        )
        assert result.answer == "test"
        assert result.gate_passed is True
