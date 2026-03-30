"""Deterministic retrieval-stage projection helpers.

Ownership:
- Canonical owner for retrieval-stage deterministic transforms/projections.
- Policy-aware orchestration remains in application services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from langchain_core.documents import Document

from testbot.pipeline_state import CandidateHit
from testbot.rerank import mix_source_evidence_with_memory_cards


@dataclass(frozen=True)
class RetrievalStageProjection:
    docs_and_scores: list[tuple[Document, float]]
    retrieval_candidates: list[CandidateHit]
    retrieval_telemetry: dict[str, object]


def _doc_to_candidate_hit(doc: Document, score: float) -> CandidateHit:
    metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
    return CandidateHit(
        doc_id=str(doc.id or metadata.get("doc_id") or ""),
        score=float(score),
        ts=str(metadata.get("ts") or ""),
        card_type=str(metadata.get("type") or ""),
    )


def project_retrieval_stage_outputs(
    *,
    raw_docs_and_scores: list[tuple[Document, float]],
    retrieval_score_threshold: float,
    exclude_doc_ids: set[str],
    exclude_source_ids: set[str],
    exclude_turn_scoped_ids: set[str],
    segment_ids: set[str],
    segment_types: set[str],
    top_k: int = 12,
    source_quota: int = 3,
    mix_source_evidence_with_memory_cards_fn: Callable[..., list[tuple[Document, float]]] = mix_source_evidence_with_memory_cards,
) -> RetrievalStageProjection:
    docs_and_scores = mix_source_evidence_with_memory_cards_fn(
        raw_docs_and_scores,
        top_k=top_k,
        source_quota=source_quota,
    )
    return RetrievalStageProjection(
        docs_and_scores=docs_and_scores,
        retrieval_candidates=[_doc_to_candidate_hit(doc, score) for doc, score in docs_and_scores],
        retrieval_telemetry={
            "retrieval_candidates_considered": len(raw_docs_and_scores),
            "retrieval_returned_top_k": len(docs_and_scores),
            "retrieval_threshold": float(retrieval_score_threshold),
            "retrieval_exclude_doc_ids": sorted(exclude_doc_ids),
            "retrieval_exclude_source_ids": sorted(exclude_source_ids),
            "retrieval_exclude_turn_scoped_ids": sorted(exclude_turn_scoped_ids),
            "retrieval_exclusion_invariant": "retrieve_stage_primary",
            "retrieval_segment_ids": sorted(segment_ids),
            "retrieval_segment_types": sorted(segment_types),
        },
    )


__all__ = ["RetrievalStageProjection", "project_retrieval_stage_outputs"]
