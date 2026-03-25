import pytest
from claw.rag.gate import apply_gate, GateResult, RELEVANCE_THRESHOLD
from claw.rag.index import SearchResult
from claw.rag.chunker import Chunk


def _make_result(score: float) -> SearchResult:
    chunk = Chunk(text="test", source_url="https://a.com", source_title="T", chunk_index=0, total_chunks=1)
    return SearchResult(chunk=chunk, score=score)


class TestApplyGate:
    def test_empty_results(self):
        gate = apply_gate([])
        assert gate.passed is False
        assert gate.best_score == 0.0
        assert "no results" in gate.reason.lower()

    def test_below_threshold(self):
        results = [_make_result(0.1), _make_result(0.15)]
        gate = apply_gate(results)
        assert gate.passed is False
        assert gate.best_score == 0.15

    def test_above_threshold(self):
        results = [_make_result(0.8), _make_result(0.5)]
        gate = apply_gate(results)
        assert gate.passed is True
        assert len(gate.results) == 2
        assert gate.best_score == 0.8

    def test_mixed_scores(self):
        results = [_make_result(0.9), _make_result(0.1)]
        gate = apply_gate(results)
        assert gate.passed is True
        assert len(gate.results) == 1

    def test_custom_threshold(self):
        results = [_make_result(0.5)]
        gate = apply_gate(results, threshold=0.6)
        assert gate.passed is False

        gate = apply_gate(results, threshold=0.4)
        assert gate.passed is True

    def test_gate_result_immutable(self):
        gate = apply_gate([])
        with pytest.raises(AttributeError):
            gate.passed = True
