from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from claw.rag.index import SearchResult

RELEVANCE_THRESHOLD = 0.30
MIN_RESULTS = 1


@dataclass(frozen=True)
class GateResult:
    passed: bool
    results: list[SearchResult]
    best_score: float
    reason: str


def apply_gate(
    results: Sequence[SearchResult],
    threshold: float = RELEVANCE_THRESHOLD,
) -> GateResult:
    if not results:
        return GateResult(
            passed=False,
            results=[],
            best_score=0.0,
            reason="No results found in knowledge base.",
        )

    best_score = max(r.score for r in results)
    relevant = [r for r in results if r.score >= threshold]

    if len(relevant) < MIN_RESULTS:
        return GateResult(
            passed=False,
            results=[],
            best_score=best_score,
            reason=f"Best match score ({best_score:.2f}) below threshold ({threshold}). Not confident enough to answer from your data.",
        )

    return GateResult(
        passed=True,
        results=list(relevant),
        best_score=best_score,
        reason="",
    )
