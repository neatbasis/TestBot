from __future__ import annotations

import arrow
from langchain_core.documents import Document

from testbot.rerank import (
    ContextConfidenceThresholds,
    has_sufficient_context_confidence_from_objective,
    mix_source_evidence_with_memory_cards,
    rerank_docs_with_time_and_type_outcome,
    rerank_objective_score_components,
)


def _doc(doc_id: str, *, ts: str, card_type: str) -> Document:
    return Document(page_content=doc_id, id=doc_id, metadata={"doc_id": doc_id, "ts": ts, "type": card_type})


def test_rerank_uses_deterministic_tie_break_priority() -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    docs_and_scores = [
        (_doc("older", ts="2026-03-10T11:00:00+00:00", card_type="user_utterance"), 0.9),
        (_doc("newer", ts="2026-03-10T11:05:00+00:00", card_type="user_utterance"), 0.9),
    ]

    outcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        near_tie_delta=0.05,
    )

    assert outcome.docs[0].id == "newer"
    assert not outcome.ambiguity_detected


def test_rerank_marks_unresolved_ambiguity_when_tie_break_cannot_decide() -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    docs_and_scores = [
        (Document(page_content="a", id="", metadata={"doc_id": "", "type": "memory", "ts": ""}), 0.8),
        (Document(page_content="b", id="", metadata={"doc_id": "", "type": "memory", "ts": ""}), 0.79),
    ]

    outcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        near_tie_delta=0.05,
    )

    assert outcome.ambiguity_detected
    assert len(outcome.near_tie_candidates) == 2


def test_rerank_near_tie_delta_controls_ambiguity_window() -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    docs_and_scores = [
        (_doc("a", ts="", card_type="memory"), 0.8),
        (_doc("b", ts="", card_type="memory"), 0.79),
    ]

    strict = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        near_tie_delta=0.001,
    )
    relaxed = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        near_tie_delta=0.05,
    )

    assert len(strict.near_tie_candidates) == 1
    assert len(relaxed.near_tie_candidates) == 2


def test_rerank_includes_objective_component_breakdown() -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    docs_and_scores = [(_doc("winner", ts="2026-03-10T12:00:00+00:00", card_type="memory"), 0.85)]

    outcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
    )

    assert len(outcome.scored_candidates) == 1
    scored = outcome.scored_candidates[0]
    assert scored["doc_id"] == "winner"
    assert scored["objective"] == "semantic_temporal_type_v1"
    assert float(scored["final_score"]) > 0.0


def test_objective_components_apply_reflection_type_prior() -> None:
    target = arrow.get("2026-03-10T12:00:00+00:00")
    base = {
        "sim_score": 1.0,
        "doc_ts_iso": "2026-03-10T12:00:00+00:00",
        "target": target,
        "sigma_seconds": 3600.0,
    }

    reflection = rerank_objective_score_components(**base, doc_type="reflection")
    memory = rerank_objective_score_components(**base, doc_type="memory")

    assert float(reflection["type_prior"]) == 0.7
    assert float(memory["type_prior"]) == 1.0
    assert float(reflection["final_score"]) < float(memory["final_score"])


def test_mix_source_evidence_with_memory_cards_keeps_source_quota() -> None:
    docs_and_scores = [
        (_doc("m1", ts="2026-03-10T10:00:00+00:00", card_type="memory"), 0.91),
        (_doc("s1", ts="2026-03-10T10:01:00+00:00", card_type="source_evidence"), 0.88),
        (_doc("m2", ts="2026-03-10T10:02:00+00:00", card_type="memory"), 0.87),
        (_doc("s2", ts="2026-03-10T10:03:00+00:00", card_type="source_evidence"), 0.86),
    ]

    mixed = mix_source_evidence_with_memory_cards(docs_and_scores, top_k=3, source_quota=1)

    assert len(mixed) == 3
    source_count = sum(1 for doc, _ in mixed if doc.metadata.get("type") == "source_evidence")
    assert source_count == 1


def test_mix_source_evidence_with_memory_cards_falls_back_to_original_when_no_source() -> None:
    docs_and_scores = [
        (_doc("a", ts="2026-03-10T10:00:00+00:00", card_type="memory"), 0.9),
        (_doc("b", ts="2026-03-10T10:01:00+00:00", card_type="memory"), 0.8),
    ]

    mixed = mix_source_evidence_with_memory_cards(docs_and_scores, top_k=2, source_quota=1)

    assert [doc.id for doc, _ in mixed] == ["a", "b"]


def test_context_confidence_rejects_high_similarity_when_temporal_signal_is_weak() -> None:
    confident = has_sufficient_context_confidence_from_objective(
        scored_candidates=[
            {"doc_id": "stale-high-sim", "final_score": 0.19},
            {"doc_id": "runner-up", "final_score": 0.17},
        ],
        ambiguity_detected=False,
    )

    assert not confident


def test_context_confidence_respects_second_place_margin_threshold() -> None:
    thresholds = ContextConfidenceThresholds(top_final_score_min=0.2, min_margin_to_second=0.02)
    confident = has_sufficient_context_confidence_from_objective(
        scored_candidates=[
            {"doc_id": "a", "final_score": 0.42},
            {"doc_id": "b", "final_score": 0.41},
        ],
        ambiguity_detected=False,
        thresholds=thresholds,
    )

    assert not confident
