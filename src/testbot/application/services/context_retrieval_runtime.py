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

import arrow
from langchain_core.documents import Document

from testbot.context_resolution import resolve as _resolve_context_from_domain
from testbot.evidence_retrieval import RetrievalInputRecord
from testbot.pipeline_state import PipelineState
from testbot.ports import MemorySearchQuery, MemoryStorePort
from testbot.rerank import (
    ContextConfidenceThresholds,
    RerankOutcome,
    rerank_confidence_thresholds,
    rerank_docs_with_time_and_type_outcome,
)
from testbot.time_parse import parse_target_time
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

_ANAPHORA_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(it|that|this|those|them)\b", re.IGNORECASE),
    re.compile(r"\b(he|she|they|him|her)\b", re.IGNORECASE),
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


@dataclass(frozen=True)
class RerankInvocationPolicy:
    sigma_seconds: float
    exclude_doc_ids: set[str]
    exclude_source_ids: set[str]
    top_k: int
    near_tie_delta: float


@dataclass(frozen=True)
class RerankThresholdProfilePolicy:
    top_final_score_min: float
    min_margin_to_second: float
    allow_ambiguity_override: bool
    ambiguity_override_top_final_score_min: float


@dataclass(frozen=True)
class RerankDecisionPolicy:
    invocation_policy: RerankInvocationPolicy
    threshold_profile_policy: RerankThresholdProfilePolicy


@dataclass(frozen=True)
class ScorerExecutionRequest:
    docs_and_scores: list[tuple[Document, float]]
    now: arrow.Arrow
    target: arrow.Arrow
    sigma_seconds: float
    exclude_doc_ids: set[str]
    exclude_source_ids: set[str]
    top_k: int
    near_tie_delta: float


@dataclass(frozen=True)
class ScorerExecutionResult:
    rerank_outcome: RerankOutcome


def execute_rerank_scorer_contract(
    request: ScorerExecutionRequest,
    *,
    scorer_fn: Callable[..., RerankOutcome] = rerank_docs_with_time_and_type_outcome,
) -> ScorerExecutionResult:
    return ScorerExecutionResult(
        rerank_outcome=scorer_fn(
            request.docs_and_scores,
            now=request.now,
            target=request.target,
            sigma_seconds=request.sigma_seconds,
            exclude_doc_ids=request.exclude_doc_ids,
            exclude_source_ids=request.exclude_source_ids,
            top_k=request.top_k,
            near_tie_delta=request.near_tie_delta,
        )
    )


def project_rerank_confidence_decision(
    *,
    prior_confidence_decision: dict[str, object],
    has_context: bool,
    rerank_outcome: RerankOutcome,
    temporal_bridge: dict[str, object],
    threshold_profile_policy: RerankThresholdProfilePolicy,
    now: arrow.Arrow,
    target: arrow.Arrow,
    sigma_seconds: float,
) -> dict[str, object]:
    scored_candidates = rerank_outcome.scored_candidates
    objective = scored_candidates[0].get("objective", "") if scored_candidates else ""
    objective_version = scored_candidates[0].get("objective_version", "") if scored_candidates else ""
    return {
        **prior_confidence_decision,
        "context_confident": has_context,
        "ambiguity_detected": rerank_outcome.ambiguity_detected,
        "anaphora_detected": bool(temporal_bridge.get("anaphora_detected", False)),
        "anchor_candidates": temporal_bridge.get("anchor_candidates", []),
        "selected_anchor_doc_id": str(temporal_bridge.get("selected_anchor_doc_id") or ""),
        "selected_anchor_ts": str(temporal_bridge.get("selected_anchor_ts") or ""),
        "computed_delta_raw_seconds": temporal_bridge.get("delta_seconds_raw"),
        "computed_delta_humanized": str(temporal_bridge.get("delta_humanized") or ""),
        "ambiguous_candidates": rerank_outcome.near_tie_candidates,
        "scored_candidates": scored_candidates,
        "memory_hit_count": len(rerank_outcome.docs),
        "objective": objective,
        "objective_version": objective_version,
        "top_final_score_min": threshold_profile_policy.top_final_score_min,
        "min_margin_to_second": threshold_profile_policy.min_margin_to_second,
        "allow_ambiguity_override": threshold_profile_policy.allow_ambiguity_override,
        "ambiguity_override_top_final_score_min": threshold_profile_policy.ambiguity_override_top_final_score_min,
        "now_ts": now.isoformat(),
        "target_ts": target.isoformat(),
        "sigma_seconds": sigma_seconds,
        "time_window": str(temporal_bridge.get("time_window") or ""),
        "window_start": str(temporal_bridge.get("window_start") or ""),
        "window_end": str(temporal_bridge.get("window_end") or ""),
    }


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


def assemble_rerank_invocation_policy(
    *,
    sigma_seconds: float,
    user_doc_id: str,
    user_reflection_doc_id: str,
    near_tie_delta: float,
    top_k: int = 4,
) -> RerankInvocationPolicy:
    return RerankInvocationPolicy(
        sigma_seconds=float(sigma_seconds),
        exclude_doc_ids={value for value in {user_doc_id, user_reflection_doc_id} if value},
        exclude_source_ids={value for value in {user_doc_id} if value},
        top_k=int(top_k),
        near_tie_delta=float(near_tie_delta),
    )


def assemble_rerank_threshold_profile_policy(
    *,
    rerank_confidence_thresholds_fn: Callable[[], ContextConfidenceThresholds] = rerank_confidence_thresholds,
) -> RerankThresholdProfilePolicy:
    thresholds = rerank_confidence_thresholds_fn()
    return RerankThresholdProfilePolicy(
        top_final_score_min=float(thresholds.top_final_score_min),
        min_margin_to_second=float(thresholds.min_margin_to_second),
        allow_ambiguity_override=bool(thresholds.allow_ambiguity_override),
        ambiguity_override_top_final_score_min=float(thresholds.ambiguity_override_top_final_score_min),
    )


def assemble_rerank_decision_policy(
    *,
    sigma_seconds: float,
    user_doc_id: str,
    user_reflection_doc_id: str,
    near_tie_delta: float,
    top_k: int = 4,
    rerank_confidence_thresholds_fn: Callable[[], ContextConfidenceThresholds] = rerank_confidence_thresholds,
) -> RerankDecisionPolicy:
    return RerankDecisionPolicy(
        invocation_policy=assemble_rerank_invocation_policy(
            sigma_seconds=sigma_seconds,
            user_doc_id=user_doc_id,
            user_reflection_doc_id=user_reflection_doc_id,
            near_tie_delta=near_tie_delta,
            top_k=top_k,
        ),
        threshold_profile_policy=assemble_rerank_threshold_profile_policy(
            rerank_confidence_thresholds_fn=rerank_confidence_thresholds_fn
        ),
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


def _contains_anaphora_cue(utterance: str) -> bool:
    text = utterance or ""
    return any(pattern.search(text) is not None for pattern in _ANAPHORA_PATTERNS)


def _contains_elapsed_time_cue(utterance: str) -> bool:
    text = (utterance or "").lower()
    return "how long ago" in text


def _contains_yesterday_cue(utterance: str) -> bool:
    return "yesterday" in (utterance or "").lower()


def _humanize_seconds_delta(delta_seconds: int) -> str:
    if delta_seconds < 60:
        return f"{delta_seconds} seconds ago"
    if delta_seconds < 3600:
        minutes = max(1, round(delta_seconds / 60))
        return f"{minutes} minutes ago"
    if delta_seconds < 86400:
        hours = max(1, round(delta_seconds / 3600))
        return f"{hours} hours ago"
    days = max(1, round(delta_seconds / 86400))
    return f"{days} days ago"


def _candidate_anchor_confidence(score: float) -> float:
    return round(max(0.0, min(1.0, float(score))), 4)


def resolve_temporal_anaphora_bridge(
    *,
    utterance: str,
    docs_and_scores: list[tuple[Document, float]],
    now: arrow.Arrow,
) -> dict[str, object]:
    anaphora_detected = _contains_anaphora_cue(utterance)
    elapsed_time_cue = _contains_elapsed_time_cue(utterance)
    yesterday_cue = _contains_yesterday_cue(utterance)

    anchor_candidates: list[dict[str, object]] = []
    for doc, score in docs_and_scores[:5]:
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        anchor_candidates.append(
            {
                "doc_id": str(doc.id or metadata.get("doc_id") or ""),
                "ts": str(metadata.get("ts") or ""),
                "confidence": _candidate_anchor_confidence(score),
            }
        )

    selected_anchor = anchor_candidates[0] if anchor_candidates else {"doc_id": "", "ts": "", "confidence": 0.0}
    selected_anchor_ts = str(selected_anchor.get("ts") or "")
    selected_anchor_doc_id = str(selected_anchor.get("doc_id") or "")

    delta_seconds: int | None = None
    if selected_anchor_ts and elapsed_time_cue:
        try:
            anchor_ts = arrow.get(selected_anchor_ts)
            delta_seconds = max(0, int((now - anchor_ts).total_seconds()))
        except Exception:
            delta_seconds = None

    target_override_ts = ""
    if selected_anchor_ts and (anaphora_detected or elapsed_time_cue):
        target_override_ts = selected_anchor_ts

    window_start = ""
    window_end = ""
    if yesterday_cue:
        window_start = now.shift(days=-1).floor("day").isoformat()
        window_end = now.shift(days=-1).ceil("day").isoformat()

    return {
        "anaphora_detected": anaphora_detected,
        "anchor_candidates": anchor_candidates,
        "selected_anchor_doc_id": selected_anchor_doc_id,
        "selected_anchor_ts": selected_anchor_ts,
        "target_override_ts": target_override_ts,
        "delta_seconds_raw": delta_seconds,
        "delta_humanized": _humanize_seconds_delta(delta_seconds) if delta_seconds is not None else "",
        "elapsed_time_cue": elapsed_time_cue,
        "time_window": "yesterday" if yesterday_cue else "",
        "window_start": window_start,
        "window_end": window_end,
    }


def filter_documents_for_temporal_window(
    *,
    docs_and_scores: list[tuple[Document, float]],
    bridge: dict[str, object],
) -> list[tuple[Document, float]]:
    window_start = str(bridge.get("window_start") or "")
    window_end = str(bridge.get("window_end") or "")
    if not window_start or not window_end:
        return docs_and_scores

    try:
        start_ts = arrow.get(window_start)
        end_ts = arrow.get(window_end)
    except Exception:
        return docs_and_scores

    filtered: list[tuple[Document, float]] = []
    for doc, score in docs_and_scores:
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        raw_ts = str(metadata.get("ts") or "")
        if not raw_ts:
            continue
        try:
            doc_ts = arrow.get(raw_ts)
        except Exception:
            continue
        if start_ts <= doc_ts <= end_ts:
            filtered.append((doc, score))
    return filtered


def resolve_rerank_target_time(
    *,
    utterance: str,
    bridge: dict[str, object],
    now: arrow.Arrow,
) -> arrow.Arrow:
    target = parse_target_time(utterance, now=now)
    target_override_ts = str(bridge.get("target_override_ts") or "")
    if target_override_ts:
        try:
            return arrow.get(target_override_ts)
        except Exception:
            return target
    return target


__all__ = [
    "RerankDecisionPolicy",
    "RerankInvocationPolicy",
    "RerankThresholdProfilePolicy",
    "ScorerExecutionRequest",
    "ScorerExecutionResult",
    "assemble_rerank_decision_policy",
    "assemble_rerank_invocation_policy",
    "assemble_rerank_threshold_profile_policy",
    "filter_documents_for_temporal_window",
    "document_from_retrieval_input",
    "execute_rerank_scorer_contract",
    "normalize_retrieval_filter_scope",
    "project_rerank_confidence_decision",
    "resolve_rerank_target_time",
    "resolve_temporal_anaphora_bridge",
    "resolve_context",
    "retrieval_input_from_document",
    "search_memory_documents_for_retrieval",
    "should_force_memory_retrieval_for_identity_recall",
    "stage_rerank_for_turn_service",
    "stage_retrieve_for_turn_service",
]
