from __future__ import annotations

import logging
from dataclasses import dataclass

from claw.core.engine import ClaudeEngine, EngineResult
from claw.rag.embedder import Embedder
from claw.rag.gate import apply_gate, GateResult
from claw.rag.index import VectorIndex, SearchResult

logger = logging.getLogger(__name__)

TOP_K = 5

RAG_SYSTEM_PROMPT = """You are answering based ONLY on the provided context from the user's knowledge base.

Rules:
1. Only use information from the provided context chunks.
2. If the context doesn't contain enough information, say so clearly.
3. Cite sources by referencing the source URL after each claim.
4. Be precise and factual. Do not add information not in the context.
5. Keep answers concise but complete."""


@dataclass(frozen=True)
class RAGResult:
    answer: str
    sources: list[str]
    confidence: float
    chunks_used: int
    gate_passed: bool
    fallback: bool


@dataclass
class RAGPipeline:
    embedder: Embedder
    index: VectorIndex
    engine: ClaudeEngine

    async def query(self, question: str, top_k: int = TOP_K) -> RAGResult:
        if self.index.total_vectors == 0:
            return RAGResult(
                answer="Your knowledge base is empty. Send me some URLs to scrape first.",
                sources=[],
                confidence=0.0,
                chunks_used=0,
                gate_passed=False,
                fallback=False,
            )

        query_vec = self.embedder.embed_single(question)
        search_results = self.index.search(query_vec, top_k=top_k)
        gate = apply_gate(search_results)

        if not gate.passed:
            result = await self.engine.ask(question)
            return RAGResult(
                answer=f"{result.response}\n\n(Answered from general knowledge — no strong match in your data. {gate.reason})",
                sources=[],
                confidence=gate.best_score,
                chunks_used=0,
                gate_passed=False,
                fallback=True,
            )

        context = self._build_context(gate.results)
        prompt = f"{RAG_SYSTEM_PROMPT}\n\n{context}\n\nQuestion: {question}"

        result = await self.engine.ask(prompt)

        sources = list(dict.fromkeys(r.chunk.source_url for r in gate.results))

        logger.info(
            "RAG query=%s chunks=%d confidence=%.2f sources=%d",
            question[:50], len(gate.results), gate.best_score, len(sources),
        )

        return RAGResult(
            answer=result.response,
            sources=sources,
            confidence=gate.best_score,
            chunks_used=len(gate.results),
            gate_passed=True,
            fallback=False,
        )

    def _build_context(self, results: list[SearchResult]) -> str:
        parts: list[str] = ["Context from your knowledge base:\n"]
        for i, r in enumerate(results, 1):
            parts.append(
                f"[{i}] Source: {r.chunk.source_title} ({r.chunk.source_url})\n"
                f"Relevance: {r.score:.2f}\n"
                f"{r.chunk.text}\n"
            )
        return "\n".join(parts)

    def index_chunks(self, chunks: list, embeddings) -> int:
        return self.index.add(chunks, embeddings)
