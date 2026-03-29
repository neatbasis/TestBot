"""Canonical runtime-owned context/retrieval helper adapters.

Ownership:
- This module is the canonical owner for runtime-loop hook wiring around
  context resolution and retrieval-stage adapter surfaces.
- Compatibility façades may delegate here while legacy seams are retired.
- Scope note: this module owns the runtime-facing hook seam/control point, not
  the deeper retrieval/rerank policy-core semantics, which remain intentionally
  deferred in monolith policy-stage helpers for now.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from langchain_core.documents import Document

from testbot.context_resolution import resolve as _resolve_context_from_domain
from testbot.evidence_retrieval import RetrievalInputRecord
from testbot.pipeline_state import PipelineState
from testbot.ports import MemorySearchQuery, MemoryStorePort
from testbot.domain import Clock

_SELF_REFERENTIAL_IDENTITY_RECALL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*who\s+am\s+i\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:\s+is|'s)\s+my\s+name\b", re.IGNORECASE),
    re.compile(r"\bremind\s+me\s+(?:what\s+)?my\s+name\s+is\b", re.IGNORECASE),
)

_PRIOR_IDENTITY_CANDIDATE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi\s*(?:am|'m|’m)\s+[\w'-]+", re.IGNORECASE),
    re.compile(r"\bmy\s+name\s+is\s+[\w'-]+", re.IGNORECASE),
)


def _is_self_referential_identity_recall_query(utterance: str) -> bool:
    return any(pattern.search(utterance or "") is not None for pattern in _SELF_REFERENTIAL_IDENTITY_RECALL_PATTERNS)


def _has_prior_identity_candidates_or_continuity_markers(
    *,
    prior_state: PipelineState | None,
    continuity_evidence: tuple[str, ...],
    context_history_anchors: tuple[str, ...],
) -> bool:
    if any(anchor.startswith("commit.confirmed_user_facts:") for anchor in continuity_evidence):
        return True
    if any(anchor.startswith("commit.confirmed_user_facts:") for anchor in context_history_anchors):
        return True
    if prior_state is None:
        return False

    for fact in prior_state.candidate_facts.facts:
        if not isinstance(fact, dict):
            continue
        if str(fact.get("key") or "").strip() == "user_name":
            return True

    prior_utterance = str(prior_state.user_input or "")
    return any(pattern.search(prior_utterance) is not None for pattern in _PRIOR_IDENTITY_CANDIDATE_PATTERNS)


def should_force_memory_retrieval_for_identity_recall(
    *,
    utterance: str,
    prior_state: PipelineState | None,
    continuity_evidence: tuple[str, ...],
    context_history_anchors: tuple[str, ...],
) -> bool:
    return _is_self_referential_identity_recall_query(utterance) and _has_prior_identity_candidates_or_continuity_markers(
        prior_state=prior_state,
        continuity_evidence=continuity_evidence,
        context_history_anchors=context_history_anchors,
    )


def resolve_context(*args, resolve_context_fn: Callable[..., object] = _resolve_context_from_domain, **kwargs):
    return resolve_context_fn(*args, **kwargs)


def retrieval_input_from_document(doc: Document, *, score: float) -> RetrievalInputRecord:
    metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
    return RetrievalInputRecord(
        ref_id=str(doc.id or metadata.get("doc_id") or ""),
        score=float(score),
        content=str(doc.page_content or ""),
        metadata=metadata,
    )


def document_from_retrieval_input(record: RetrievalInputRecord) -> Document:
    metadata = record.metadata if isinstance(record.metadata, dict) else {}
    return Document(
        id=str(record.ref_id or metadata.get("doc_id") or ""),
        page_content=str(record.content or ""),
        metadata=metadata,
    )


def stage_retrieve_for_turn_service(
    store: MemoryStorePort,
    state: PipelineState,
    *,
    stage_retrieve_fn: Callable[..., tuple[PipelineState, list[tuple[Document, float]]]],
    exclude_doc_ids: set[str] | None = None,
    exclude_source_ids: set[str] | None = None,
    exclude_turn_scoped_ids: set[str] | None = None,
    segment_ids: set[str] | None = None,
    segment_types: set[str] | None = None,
) -> tuple[PipelineState, list[RetrievalInputRecord]]:
    updated_state, docs_and_scores = stage_retrieve_fn(
        store,
        state,
        exclude_doc_ids=exclude_doc_ids,
        exclude_source_ids=exclude_source_ids,
        exclude_turn_scoped_ids=exclude_turn_scoped_ids,
        segment_ids=segment_ids,
        segment_types=segment_types,
    )
    return updated_state, [retrieval_input_from_document(doc, score=score) for doc, score in docs_and_scores]


@dataclass(frozen=True)
class RetrievalFilterScope:
    exclude_doc_ids: set[str]
    exclude_source_ids: set[str]
    exclude_turn_scoped_ids: set[str]
    segment_ids: set[str]
    segment_types: set[str]


def normalize_retrieval_filter_scope(
    *,
    exclude_doc_ids: set[str] | None = None,
    exclude_source_ids: set[str] | None = None,
    exclude_turn_scoped_ids: set[str] | None = None,
    segment_ids: set[str] | None = None,
    segment_types: set[str] | None = None,
) -> RetrievalFilterScope:
    return RetrievalFilterScope(
        exclude_doc_ids={value for value in (exclude_doc_ids or set()) if value},
        exclude_source_ids={value for value in (exclude_source_ids or set()) if value},
        exclude_turn_scoped_ids={value for value in (exclude_turn_scoped_ids or set()) if value},
        segment_ids={value for value in (segment_ids or set()) if value},
        segment_types={value for value in (segment_types or set()) if value},
    )


def search_memory_documents_for_retrieval(
    store: MemoryStorePort,
    *,
    rewritten_query: str,
    filter_scope: RetrievalFilterScope,
    k: int = 18,
) -> list[tuple[Document, float]]:
    if hasattr(store, "search_memory_records"):
        return [
            (
                Document(
                    id=hit.document.doc_id,
                    page_content=hit.document.content,
                    metadata=dict(hit.document.metadata),
                ),
                hit.score,
            )
            for hit in store.search_memory_records(
                MemorySearchQuery(
                    query=rewritten_query,
                    k=k,
                    exclude_doc_ids=filter_scope.exclude_doc_ids,
                    exclude_source_ids=filter_scope.exclude_source_ids,
                    exclude_turn_scoped_ids=filter_scope.exclude_turn_scoped_ids,
                    segment_ids=filter_scope.segment_ids,
                    segment_types=filter_scope.segment_types,
                )
            )
        ]
    return store.similarity_search_with_score(
        rewritten_query,
        k=k,
        exclude_doc_ids=filter_scope.exclude_doc_ids,
        exclude_source_ids=filter_scope.exclude_source_ids,
        exclude_turn_scoped_ids=filter_scope.exclude_turn_scoped_ids,
        segment_ids=filter_scope.segment_ids,
        segment_types=filter_scope.segment_types,
    )


def stage_rerank_for_turn_service(
    state: PipelineState,
    retrieval_candidates: list[RetrievalInputRecord],
    *,
    stage_rerank_fn: Callable[..., tuple[PipelineState, list[Document]]],
    utterance: str,
    user_doc_id: str,
    user_reflection_doc_id: str,
    near_tie_delta: float,
    clock: Clock,
    io_channel: str = "cli",
) -> tuple[PipelineState, list[RetrievalInputRecord]]:
    del io_channel
    docs_and_scores = [(document_from_retrieval_input(record), float(record.score)) for record in retrieval_candidates]
    updated_state, hits = stage_rerank_fn(
        state,
        docs_and_scores,
        utterance=utterance,
        user_doc_id=user_doc_id,
        user_reflection_doc_id=user_reflection_doc_id,
        near_tie_delta=near_tie_delta,
        clock=clock,
    )
    return updated_state, [retrieval_input_from_document(doc, score=1.0) for doc in hits]


__all__ = [
    "document_from_retrieval_input",
    "normalize_retrieval_filter_scope",
    "resolve_context",
    "retrieval_input_from_document",
    "search_memory_documents_for_retrieval",
    "should_force_memory_retrieval_for_identity_recall",
    "stage_rerank_for_turn_service",
    "stage_retrieve_for_turn_service",
]
