"""Compatibility façade for the legacy SAT runtime module.

This module intentionally retains only a governed compatibility surface
while canonical ownership lives in extracted runtime/service modules.
Keep wrappers thin and add new runtime behavior in canonical owners.
"""

from __future__ import annotations

import logging
import os
import re
import sys
import uuid
import warnings
from argparse import Namespace
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path

import arrow
from homeassistant_api import Client

from testbot.clock import Clock, SystemClock
from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc, utc_now_iso
from testbot.observability.session_log import SESSION_LOG_SCHEMA_VERSION, append_session_log as _append_session_log
from testbot.observability.turn_debug_payload import (
    build_debug_turn_payload as _build_debug_turn_payload,
    format_debug_turn_trace as _format_debug_turn_trace,
    format_debug_turn_trace_payload as _format_debug_turn_trace_payload,
)
from testbot.memory_strata import (
    MemoryStratum,
    SegmentDescriptor,
    SegmentType,
    apply_persistence_metadata,
    derive_segment_descriptor,
)
from testbot.pipeline_state import (
    CandidateHit,
    ConfidenceDecision,
    PipelineState,
    ProvenanceType,
    append_pipeline_snapshot,
)
from testbot.promotion_policy import persist_promoted_context
from testbot.reflection_policy import CapabilityStatus, decide_fallback_action, fallback_reason as derive_fallback_reason
from testbot.answer_policy import AnswerPolicyInput, AnswerRoutingDecision, resolve_answer_mode, resolve_answer_routing
from testbot.rerank import (
    adaptive_sigma_fractional,
    has_sufficient_context_confidence_from_objective,
    mix_source_evidence_with_memory_cards,
    rerank_docs_with_time_and_type_outcome,
)
from testbot.stage_transitions import (
    append_transition_validation_log,
    validate_answer_assemble_pre,
    validate_answer_commit_post,
    validate_answer_commit_pre,
    validate_answer_render_post,
    validate_answer_render_pre,
    validate_answer_validate_post,
    validate_answer_validate_pre,
    validate_context_resolve_post,
    validate_context_resolve_pre,
    validate_encode_candidates_post,
    validate_encode_candidates_pre,
    validate_intent_resolve_post,
    validate_intent_resolve_pre,
    validate_observe_turn_post,
    validate_observe_turn_pre,
    validate_policy_decide_post,
    validate_policy_decide_pre,
    validate_retrieve_evidence_post,
    validate_retrieve_evidence_pre,
    validate_stabilize_pre_route_post,
    validate_stabilize_pre_route_pre,
)
from testbot.intent_router import (
    IntentType,
    classify_intent,
    extract_intent_facets,
    is_satellite_action_request,
    planning_pathway_for_intent,
)
from testbot.time_reasoning import elapsed_since_last_user_message, resolve_relative_date
from testbot.source_ingest import SourceIngestor
from testbot.history_packer import PackedHistory, pack_chat_history, render_packed_history
from testbot.response_planner import build_response_plan, plan_to_dict, render_response_plan_block
from testbot.reject_taxonomy import derive_reject_signal
from testbot.turn_observation import observe_turn
from testbot.candidate_encoding import encode_turn_candidates
from testbot.stabilization import StabilizedTurnState, stabilize_pre_route
from testbot.context_resolution import resolve as _resolve_context_from_domain
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.evidence_retrieval import (
    EvidenceBundle,
    RetrievalInputRecord,
    build_evidence_bundle_from_docs_and_scores,
    build_evidence_bundle_from_hits,
    continuity_evidence_from_prior_state,
    retrieval_result,
)
from testbot.policy_decision import (
    DecisionClass,
    DecisionObject,
    decide as decide_policy,
    decide_from_evidence,
)
from testbot.logic.alignment import (
    ALIGNMENT_OBJECTIVE_VERSION,
    GENERAL_KNOWLEDGE_CONFIDENCE_MIN,
    GENERAL_KNOWLEDGE_MARKER_PREFIX,
    GENERAL_KNOWLEDGE_SUPPORT_MIN,
    assess_general_knowledge_contract,
    evaluate_alignment_decision as _evaluate_alignment_decision,
    has_general_knowledge_marker,
    has_required_memory_citation,
    is_unsafe_user_request,
    passes_general_knowledge_confidence_gate,
    raw_claim_like_text_detected,
    response_contains_claims,
    validate_answer_contract,
    validate_general_knowledge_contract,
)
from testbot.logic.provenance import (
    build_provenance_metadata as build_provenance_metadata_from_logic,
    collect_used_source_evidence_refs as collect_used_source_evidence_refs_from_logic,
)
from testbot.retrieval_routing import decide_retrieval_routing, is_definitional_query_form
from testbot.adapters.ask_gateway import AskGateway
from testbot.adapters.ha_satellite_output import send_satellite_output
from testbot.runtime_capability_service import (
    CapabilitySnapshotData as CapabilitySnapshot,
    RuntimeCapabilityStatusData as RuntimeCapabilityStatus,
    build_capability_snapshot as build_capability_snapshot_from_service,
    ha_connection_error as ha_connection_error_from_service,
    ollama_connection_error as ollama_connection_error_from_service,
    resolve_effective_mode as resolve_effective_mode_from_service,
    resolve_mode as resolve_mode_from_service,
    validate_ollama_base_url as validate_ollama_base_url_from_service,
)
from testbot.startup_status_presenter import print_startup_status as print_startup_status_from_presenter
from testbot.runtime_cli_args import parse_args as parse_runtime_cli_args
from testbot.source_ingestion_startup import (
    build_source_connector as build_startup_source_connector,
    run_source_ingestion as run_startup_source_ingestion,
)
from testbot.entrypoints import runtime_bootstrap as runtime_bootstrap_entrypoint
from testbot.entrypoints.runtime_background_ingestion import (
    RuntimeBackgroundIngestionDependencies,
    emit_obligation_transition as emit_runtime_obligation_transition,
    format_background_ingestion_completion_message as format_runtime_background_ingestion_completion_message,
    poll_background_source_ingestion as poll_runtime_background_source_ingestion,
    poll_pending_ingestion_obligations as poll_runtime_pending_ingestion_obligations,
    process_background_ingestion_completion as process_runtime_background_ingestion_completion,
    start_background_source_ingestion as start_runtime_background_source_ingestion,
)
from testbot.entrypoints.runtime_commit_persistence import (
    RuntimeCommitPersistenceDependencies,
    answer_commit_persistence as persist_runtime_answer_commit,
)
from testbot.entrypoints.runtime_turn_pipeline import RuntimeTurnPipelineHooks, run_runtime_turn_pipeline
from testbot.application.services import context_retrieval_runtime as context_retrieval_runtime_service
from testbot.canonical_turn_orchestrator import CanonicalTurnOrchestrator as _CanonicalTurnOrchestrator
from testbot.logic.decision_helpers import (
    decision_object_from_assembled as _decision_object_from_fallback_action,
    resolve_answer_routing_for_stage as _resolve_answer_routing_for_stage_service,
    resolve_answer_routing_from_decision_object as _resolve_answer_routing_from_decision_object_service,
    selected_decision_from_confidence as _selected_decision_from_confidence_service,
)
from testbot.application.services import background_ingestion_runtime as background_ingestion_runtime_service
from testbot.application.services import answer_stage_runtime as answer_stage_runtime_service
from testbot.answer_contract_constants import (
    ASSIST_ALTERNATIVES_ANSWER,
    CLARIFY_ANSWER,
    DENY_ANSWER,
    FALLBACK_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    ROUTE_TO_ASK_ANSWER,
)

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from testbot.ports import MemoryStorePort
from langchain_ollama import ChatOllama, OllamaEmbeddings


# ---------------------------
# HA satellite output
# ---------------------------
def sat_say(client: Client, entity_id: str, text: str) -> None:
    send_satellite_output(client, entity_id, text)


# ---------------------------
# Chat history (short-term memory)
# ---------------------------
ChatMsg = dict[str, str]

BACKGROUND_INGESTION_PROGRESS_ANSWER = "I'm ingesting external sources in the background now…"
BACKGROUND_INGESTION_COMPLETION_MESSAGE_TEMPLATE = (
    "Background ingestion completed for request {correlation_id}. "
    "Here is the newly grounded answer:"
)
BACKGROUND_INGESTION_OBLIGATION_TIMEOUT_SECONDS = int(os.getenv("SOURCE_INGEST_OBLIGATION_TIMEOUT_SECONDS", "900"))


@dataclass(frozen=True)
class _ClockBackedSnapshotTimeProvider:
    clock: Clock

    def now_iso(self) -> str:
        return self.clock.now().isoformat()


def _utc_now_iso() -> str:
    return arrow.utcnow().isoformat()


def _runtime_background_ingestion_deps() -> RuntimeBackgroundIngestionDependencies:
    return RuntimeBackgroundIngestionDependencies(
        append_session_log=append_session_log,
        build_source_connector=_build_source_connector,
        source_ingestor_cls=SourceIngestor,
        answer_commit_persistence=answer_commit_persistence,
        run_canonical_turn_pipeline=_run_canonical_turn_pipeline,
        pipeline_state_cls=PipelineState,
        knowledge_question_intent=IntentType.KNOWLEDGE_QUESTION.value,
    )


def _emit_obligation_transition(
    *,
    ingestion_request_id: str,
    status: str,
    created_at: str,
    last_polled_at: str,
    attempt_count: int,
    deadline_at: str,
) -> None:
    emit_runtime_obligation_transition(
        deps=_runtime_background_ingestion_deps(),
        ingestion_request_id=ingestion_request_id,
        status=status,
        created_at=created_at,
        last_polled_at=last_polled_at,
        attempt_count=attempt_count,
        deadline_at=deadline_at,
    )


def _poll_pending_ingestion_obligations(*, runtime: dict[str, object]) -> None:
    poll_runtime_pending_ingestion_obligations(
        runtime=runtime,
        deps=_runtime_background_ingestion_deps(),
        obligation_timeout_seconds=BACKGROUND_INGESTION_OBLIGATION_TIMEOUT_SECONDS,
    )
_LOGGER = logging.getLogger(__name__)

CanonicalTurnOrchestrator = _CanonicalTurnOrchestrator
"""Compatibility re-export; canonical owner remains `testbot.canonical_turn_orchestrator`."""

__all__ = [
    "ASSIST_ALTERNATIVES_ANSWER",
    "AnswerAssembleResult",
    "CLARIFY_ANSWER",
    # Compatibility-only façade export; canonical owner remains testbot.canonical_turn_orchestrator.
    "CanonicalTurnOrchestrator",
    "CapabilitySnapshot",
    "DENY_ANSWER",
    "FALLBACK_ANSWER",
    "NON_KNOWLEDGE_UNCERTAINTY_ANSWER",
    "ROUTE_TO_ASK_ANSWER",
    "RuntimeCapabilityStatus",
    "answer_assemble",
    "append_session_log",
    "build_capability_snapshot",
    "build_runtime_memory_store",
    "build_debug_turn_payload",
    "build_provenance_metadata",
    "collect_used_source_evidence_refs",
    "decision_object_from_assembled",
    "evaluate_alignment_decision",
    "format_debug_turn_trace",
    "format_debug_turn_trace_payload",
    "generate_reflection_yaml",
    "has_required_memory_citation",
    "has_sufficient_context_confidence",
    "parse_args",
    "print_startup_status",
    "raw_claim_like_text_detected",
    "read_runtime_env",
    "render_context",
    "resolve_answer_routing_from_decision_object",
    "resolve_mode",
    "resolve_turn_intent",
    "response_contains_claims",
    "run_answer_stage_flow",
    "run_canonical_answer_stage_flow",
    "run_chat_loop",
    "run_source_ingestion",
    "stage_rerank",
    "stage_rewrite_query",
    "validate_answer_contract",
]

_DEPRECATED_COMPATIBILITY_ALIASES: dict[str, dict[str, str]] = {
    "run_answer_stage_flow": {
        "canonical_symbol": "run_canonical_answer_stage_flow",
        "removal_date": "2026-04-01",
        "removal_criteria": "all internal callers and non-compatibility tests import run_canonical_answer_stage_flow",
    },
    "evaluate_alignment_decision": {
        "canonical_symbol": "testbot.logic.alignment.evaluate_alignment_decision",
        "removal_date": "2026-04-01",
        "removal_criteria": "all callers import from testbot.logic.alignment with compatibility shim coverage retained",
    },
}

_COMPATIBILITY_REEXPORTS: dict[str, dict[str, str]] = {
    "CanonicalTurnOrchestrator": {
        "canonical_symbol": "testbot.canonical_turn_orchestrator.CanonicalTurnOrchestrator",
        "status": "compatibility re-export",
        "owner_decision": "compatibility_only",
        "introduced_for_compatibility_on": "2026-03-20",
        "review_after": "2026-06-30",
        "removal_criteria": "remove after all in-repo imports and non-compatibility tests stop using testbot.sat_chatbot_memory_v2.CanonicalTurnOrchestrator",
        "deprecation_note": "Prefer importing from testbot.canonical_turn_orchestrator in new code.",
    },
}


def _emit_deprecated_alias_warning(name: str) -> None:
    alias_metadata = _DEPRECATED_COMPATIBILITY_ALIASES[name]
    warnings.warn(
        (
            f"{name}(...) is deprecated; use {alias_metadata['canonical_symbol']} instead. "
            f"Removal target: {alias_metadata['removal_date']} once {alias_metadata['removal_criteria']}."
        ),
        DeprecationWarning,
        stacklevel=2,
    )


def _execute_source_ingestion(
    *,
    runtime: dict[str, object],
    store: MemoryStorePort,
    background: bool = False,
    ingestion_request_id: str = "",
) -> dict[str, object]:
    return background_ingestion_runtime_service.execute_source_ingestion(
        runtime=runtime,
        store=store,
        build_source_connector=_build_source_connector,
        source_ingestor_cls=SourceIngestor,
        append_session_log=append_session_log,
        background=background,
        ingestion_request_id=ingestion_request_id,
    )


def _start_background_source_ingestion(
    *,
    runtime: dict[str, object],
    store: MemoryStorePort,
    ingestion_request_id: str = "",
) -> dict[str, object]:
    return start_runtime_background_source_ingestion(
        runtime=runtime,
        store=store,
        deps=_runtime_background_ingestion_deps(),
        ingestion_request_id=ingestion_request_id,
    )


def _poll_background_source_ingestion(*, runtime: dict[str, object]) -> dict[str, object] | None:
    return poll_runtime_background_source_ingestion(
        runtime=runtime,
        deps=_runtime_background_ingestion_deps(),
    )


def _format_background_ingestion_completion_message(*, correlation_id: str) -> str:
    return format_runtime_background_ingestion_completion_message(correlation_id=correlation_id)


def _process_background_ingestion_completion(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    capability_status: CapabilityStatus,
    capability_snapshot: CapabilitySnapshot,
    clock: Clock,
    io_channel: str,
    send_assistant_text,
    last_user_message_ts: str,
    prior_pipeline_state: PipelineState | None,
) -> tuple[str, PipelineState | None, bool]:
    return process_runtime_background_ingestion_completion(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        clock=clock,
        io_channel=io_channel,
        send_assistant_text=send_assistant_text,
        last_user_message_ts=last_user_message_ts,
        prior_pipeline_state=prior_pipeline_state,
        deps=_runtime_background_ingestion_deps(),
    )
INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.75
RETRIEVAL_SCORE_THRESHOLD = 0.0


AnswerAssembleResult = answer_stage_runtime_service.AnswerAssembleResult
AnswerValidateResult = answer_stage_runtime_service.AnswerValidateResult


def _format_capabilities_help_answer(*, status: RuntimeCapabilityStatus, capability_status: CapabilityStatus) -> str:
    return answer_stage_runtime_service.format_capabilities_help_answer(
        status=status,
        capability_status=capability_status,
    )


def _format_satellite_action_alternatives(*, status: RuntimeCapabilityStatus) -> str:
    return answer_stage_runtime_service.format_satellite_action_alternatives(status=status)

def _parse_args(argv: list[str] | None = None) -> Namespace:
    return parse_runtime_cli_args(argv)


def _read_runtime_env() -> dict[str, object]:
    return runtime_bootstrap_entrypoint.read_runtime_env()


def _build_runtime_memory_store(*, runtime: dict[str, object], embeddings: Embeddings) -> MemoryStorePort:
    return runtime_bootstrap_entrypoint.build_runtime_memory_store(runtime=runtime, embeddings=embeddings)


def _ha_connection_error(api_url: str, token: str, entity_id: str) -> str | None:
    return ha_connection_error_from_service(api_url, token, entity_id, client_factory=Client)


def _validate_ollama_base_url(base_url: str) -> str | None:
    return validate_ollama_base_url_from_service(base_url)


def _ollama_connection_error(
    base_url: str,
    chat_model: str,
    embedding_model: str,
    *,
    x_ollama_key: str | None = None,
) -> str | None:
    return ollama_connection_error_from_service(
        base_url,
        chat_model,
        embedding_model,
        x_ollama_key=x_ollama_key,
    )


def _resolve_mode(requested_mode: str, ha_error: str | None) -> str:
    return resolve_mode_from_service(requested_mode, ha_error)


def _resolve_effective_mode(
    *,
    requested_mode: str,
    daemon_mode: bool,
    ha_error: str | None,
    ollama_error: str | None,
) -> tuple[str | None, str | None, str | None]:
    return resolve_effective_mode_from_service(
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        ha_error=ha_error,
        ollama_error=ollama_error,
    )



def _build_source_connector(runtime: dict[str, object]):
    """Compatibility wrapper; canonical owner is testbot.source_ingestion_startup.build_source_connector."""
    return build_startup_source_connector(runtime=runtime, append_session_log=append_session_log)


def _run_source_ingestion(*, runtime: dict[str, object], store: MemoryStorePort) -> None:
    run_startup_source_ingestion(runtime=runtime, store=store, append_session_log=append_session_log)

def _print_startup_status(*, snapshot: CapabilitySnapshot) -> None:
    print_startup_status_from_presenter(snapshot=snapshot)


def append_session_log(event: str, payload: dict, *, log_path: Path = Path("./logs/session.jsonl")) -> None:
    """Compatibility shim; canonical owner is testbot.observability.session_log.append_session_log."""

    _append_session_log(event=event, payload=payload, log_path=log_path)


def _intent_telemetry_payload(
    *,
    state: PipelineState,
    utterance: str | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "intent": state.resolved_intent,
        "intent_classified": state.classified_intent,
        "intent_resolved": state.resolved_intent,
    }
    if utterance is not None:
        payload["utterance"] = utterance
    if extra:
        payload.update(extra)
    return payload


def doc_to_candidate_hit(doc: Document, score: float) -> CandidateHit:
    return CandidateHit(
        doc_id=str(doc.id or doc.metadata.get("doc_id") or ""),
        score=float(score),
        ts=str(doc.metadata.get("ts") or ""),
        card_type=str(doc.metadata.get("type") or ""),
    )


_SELF_IDENTITY_DECLARATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*i\s*(?:am|'m|’m)\s+[\w'-]+(?:\s+[\w'-]+)*\s*[.!?]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*my\s+name\s+is\s+[\w'-]+(?:\s+[\w'-]+)*\s*[.!?]*\s*$", re.IGNORECASE),
)

def _is_self_identity_declaration(utterance: str) -> bool:
    return any(pattern.match(utterance or "") is not None for pattern in _SELF_IDENTITY_DECLARATION_PATTERNS)


def _should_force_memory_retrieval_for_identity_recall(
    *,
    utterance: str,
    prior_state: PipelineState | None,
    continuity_evidence: tuple[str, ...],
    context_history_anchors: tuple[str, ...],
) -> bool:
    return context_retrieval_runtime_service.should_force_memory_retrieval_for_identity_recall(
        utterance=utterance,
        prior_state=prior_state,
        continuity_evidence=continuity_evidence,
        context_history_anchors=context_history_anchors,
    )


def resolve_context(*args, **kwargs):
    return context_retrieval_runtime_service.resolve_context(*args, resolve_context_fn=_resolve_context_from_domain, **kwargs)


def stage_rewrite_query(llm: ChatOllama, state: PipelineState) -> PipelineState:
    if _is_self_identity_declaration(state.user_input):
        return replace(state, rewritten_query=state.user_input)

    try:
        rewritten_query = llm.invoke(QUERY_REWRITE_PROMPT.format_messages(input=state.user_input)).content.strip() or state.user_input
    except Exception as exc:
        append_session_log(
            "query_rewrite_failed",
            {
                "error_class": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        rewritten_query = state.user_input
    return replace(state, rewritten_query=rewritten_query)


def observe_stage(state: PipelineState) -> PipelineState:
    warnings.warn(
        "observe_stage is deprecated; use _run_canonical_turn_pipeline/_observe_turn instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return state


def encode_stage(llm: ChatOllama, state: PipelineState) -> PipelineState:
    warnings.warn(
        "encode_stage is deprecated; use _run_canonical_turn_pipeline/_encode_candidates instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return stage_rewrite_query(llm, state)


def stage_retrieve(
    store: MemoryStorePort,
    state: PipelineState,
    *,
    exclude_doc_ids: set[str] | None = None,
    exclude_source_ids: set[str] | None = None,
    exclude_turn_scoped_ids: set[str] | None = None,
    segment_ids: set[str] | None = None,
    segment_types: set[str] | None = None,
) -> tuple[PipelineState, list[tuple[Document, float]]]:
    filter_scope = context_retrieval_runtime_service.normalize_retrieval_filter_scope(
        exclude_doc_ids=exclude_doc_ids,
        exclude_source_ids=exclude_source_ids,
        exclude_turn_scoped_ids=exclude_turn_scoped_ids,
        segment_ids=segment_ids,
        segment_types=segment_types,
    )
    raw_docs_and_scores = context_retrieval_runtime_service.search_memory_documents_for_retrieval(
        store,
        rewritten_query=state.rewritten_query,
        filter_scope=filter_scope,
        k=18,
    )
    docs_and_scores = mix_source_evidence_with_memory_cards(raw_docs_and_scores, top_k=12, source_quota=3)
    retrieval_candidates = [doc_to_candidate_hit(doc, score) for doc, score in docs_and_scores]
    retrieval_telemetry = {
        "retrieval_candidates_considered": len(raw_docs_and_scores),
        "retrieval_returned_top_k": len(docs_and_scores),
        "retrieval_threshold": RETRIEVAL_SCORE_THRESHOLD,
        "retrieval_exclude_doc_ids": sorted(filter_scope.exclude_doc_ids),
        "retrieval_exclude_source_ids": sorted(filter_scope.exclude_source_ids),
        "retrieval_exclude_turn_scoped_ids": sorted(filter_scope.exclude_turn_scoped_ids),
        "retrieval_exclusion_invariant": "retrieve_stage_primary",
        "retrieval_segment_ids": sorted(filter_scope.segment_ids),
        "retrieval_segment_types": sorted(filter_scope.segment_types),
    }
    return replace(
        state,
        retrieval_candidates=retrieval_candidates,
        confidence_decision={**state.confidence_decision, **retrieval_telemetry},
    ), docs_and_scores


def _retrieval_input_from_document(doc: Document, *, score: float) -> RetrievalInputRecord:
    return context_retrieval_runtime_service.retrieval_input_from_document(doc, score=score)


def _document_from_retrieval_input(record: RetrievalInputRecord) -> Document:
    return context_retrieval_runtime_service.document_from_retrieval_input(record)


def _stage_retrieve_for_turn_service(
    store: MemoryStorePort,
    state: PipelineState,
    *,
    exclude_doc_ids: set[str] | None = None,
    exclude_source_ids: set[str] | None = None,
    exclude_turn_scoped_ids: set[str] | None = None,
    segment_ids: set[str] | None = None,
    segment_types: set[str] | None = None,
) -> tuple[PipelineState, list[RetrievalInputRecord]]:
    return context_retrieval_runtime_service.stage_retrieve_for_turn_service(
        store,
        state,
        stage_retrieve_fn=stage_retrieve,
        exclude_doc_ids=exclude_doc_ids,
        exclude_source_ids=exclude_source_ids,
        exclude_turn_scoped_ids=exclude_turn_scoped_ids,
        segment_ids=segment_ids,
        segment_types=segment_types,
    )


def stage_rerank(
    state: PipelineState,
    docs_and_scores: list[tuple[Document, float]],
    *,
    utterance: str,
    user_doc_id: str,
    user_reflection_doc_id: str,
    near_tie_delta: float,
    clock: Clock,
    io_channel: str = "cli",
) -> tuple[PipelineState, list[Document]]:
    now = clock.now()
    temporal_bridge = context_retrieval_runtime_service.resolve_temporal_anaphora_bridge(
        utterance=utterance,
        docs_and_scores=docs_and_scores,
        now=now,
    )
    filtered_docs_and_scores = context_retrieval_runtime_service.filter_documents_for_temporal_window(
        docs_and_scores=docs_and_scores,
        bridge=temporal_bridge,
    )
    target = context_retrieval_runtime_service.resolve_rerank_target_time(
        utterance=utterance,
        bridge=temporal_bridge,
        now=now,
    )
    decision_policy = context_retrieval_runtime_service.assemble_rerank_decision_policy(
        sigma_seconds=adaptive_sigma_fractional(now=now, target=target, frac=0.25),
        user_doc_id=user_doc_id,
        user_reflection_doc_id=user_reflection_doc_id,
        near_tie_delta=near_tie_delta,
    )
    invocation_policy = decision_policy.invocation_policy
    sigma = invocation_policy.sigma_seconds
    rerank_outcome = rerank_docs_with_time_and_type_outcome(
        filtered_docs_and_scores,
        now=now,
        target=target,
        sigma_seconds=sigma,
        exclude_doc_ids=invocation_policy.exclude_doc_ids,
        exclude_source_ids=invocation_policy.exclude_source_ids,
        top_k=invocation_policy.top_k,
        near_tie_delta=invocation_policy.near_tie_delta,
    )
    hits = rerank_outcome.docs
    reranked_hits = [doc_to_candidate_hit(doc, score=0.0) for doc in hits]
    has_context = has_sufficient_context_confidence(
        rerank_outcome.scored_candidates,
        ambiguity_detected=rerank_outcome.ambiguity_detected,
    )
    threshold_profile_policy = decision_policy.threshold_profile_policy
    confidence_decision = context_retrieval_runtime_service.project_rerank_confidence_decision(
        prior_confidence_decision=dict(state.confidence_decision),
        has_context=has_context,
        rerank_outcome=rerank_outcome,
        temporal_bridge=temporal_bridge,
        threshold_profile_policy=threshold_profile_policy,
        now=now,
        target=target,
        sigma_seconds=sigma,
    )
    return replace(state, reranked_hits=reranked_hits, confidence_decision=confidence_decision), hits


def _answer_assemble_for_turn_service(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[RetrievalInputRecord],
    capability_status: CapabilityStatus,
    answer_routing: AnswerRoutingDecision | None = None,
    runtime_capability_status: CapabilityStatus | None = None,
    clock: Clock | None = None,
):
    return answer_stage_runtime_service.answer_assemble_for_turn_service(
        llm,
        state,
        chat_history=chat_history,
        hits=hits,
        capability_status=capability_status,
        answer_routing=answer_routing,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        document_from_retrieval_input=_document_from_retrieval_input,
        render_context=render_context,
        answer_prompt=ANSWER_PROMPT,
        build_partial_memory_clarifier=build_partial_memory_clarifier,
        append_session_log=append_session_log,
        deny_answer=DENY_ANSWER,
        route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
        assist_alternatives_answer=ASSIST_ALTERNATIVES_ANSWER,
        fallback_answer=FALLBACK_ANSWER,
        non_knowledge_uncertainty_answer=NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    )


def _answer_validate_for_turn_service(
    state: PipelineState,
    *,
    assembled: AssembledAnswer,
    hits: list[RetrievalInputRecord],
    chat_history: deque[ChatMsg],
    pending_lookup_override: bool = False,
):
    return answer_stage_runtime_service.answer_validate_for_turn_service(
        state,
        assembled=assembled,
        hits=hits,
        chat_history=chat_history,
        pending_lookup_override=pending_lookup_override,
        document_from_retrieval_input=_document_from_retrieval_input,
        build_provenance_metadata=build_provenance_metadata_from_logic,
        evaluate_alignment_decision=_evaluate_alignment_decision,
        fallback_answer=FALLBACK_ANSWER,
        deny_answer=DENY_ANSWER,
        assist_alternatives_answer=ASSIST_ALTERNATIVES_ANSWER,
        non_knowledge_uncertainty_answer=NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
        clarify_answer=CLARIFY_ANSWER,
        route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
    )



_AFFIRMATION_UTTERANCE_PATTERN = re.compile(r"^\s*(yes|yeah|yep|yup|ok|okay|sure|please|yes please|ok please|okay please)\s*[.!?]*\s*$", re.IGNORECASE)
_DEFINITIONAL_QUERY_PATTERN = re.compile(
    r"^\s*(what(?:\s+is|\s+are|'s)\b|who(?:\s+is|\s+are|'s)\b|define\b|definition\s+of\b|what\s+does\b.+\bmean\b)",
    re.IGNORECASE,
)


def _is_short_affirmation(user_input: str) -> bool:
    return bool(_AFFIRMATION_UTTERANCE_PATTERN.match((user_input or "").strip()))


def _is_clarification_or_capability_confirmation_answer(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    return is_clarification_answer(normalized) or _is_capabilities_help_answer(normalized)


# ---------------------------------------------------------------------------
# Diagnostics-only helpers (non-authoritative; never use for production routing)
# ---------------------------------------------------------------------------


def _enforce_diagnostics_only_guard(*, diagnostic_only: bool, helper_name: str) -> None:
    if diagnostic_only:
        return
    raise RuntimeError(
        f"{helper_name} is diagnostic-only and non-authoritative; "
        "production routing must use canonical orchestrator artifacts"
    )


def resolve_turn_intent(
    *,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    diagnostic_only: bool = True,
) -> tuple[IntentType, IntentType]:
    """Resolve intent for diagnostics-only parity checks.

    This helper intentionally runs outside the canonical turn pipeline and must
    not be used for authoritative production routing decisions.
    """
    _enforce_diagnostics_only_guard(diagnostic_only=diagnostic_only, helper_name="resolve_turn_intent")

    _LOGGER.warning(
        "resolve_turn_intent invoked in diagnostic-only mode; output is non-authoritative",
        extra={"authority": "non_authoritative", "helper": "resolve_turn_intent"},
    )
    seed_state = PipelineState(user_input=utterance)
    observation = observe_turn(
        seed_state,
        turn_id="offline-resolve-turn-intent",
        observed_at=utc_now_iso(),
        speaker="user",
        channel="offline",
    )
    encoded = encode_turn_candidates(seed_state, observation=observation, rewritten_query=utterance)
    segment = derive_segment_descriptor(
        utterance=observation.utterance,
        has_dialogue_state=bool(encoded.dialogue_state),
    )
    _, stabilized_turn_state = stabilize_pre_route(
        store=None,  # type: ignore[arg-type]
        state=seed_state,
        observation=observation,
        encoded=encoded,
        response_plan={"pathway": "offline_intent_resolution"},
        reflection_yaml="offline: true",
        segment=segment,
        store_doc_fn=lambda *args, **kwargs: None,
    )
    context_resolution = resolve_context(
        utterance=observation.utterance,
        prior_pipeline_state=prior_pipeline_state,
    )
    intent_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=stabilized_turn_state,
            context=context_resolution,
            fallback_utterance=observation.utterance,
        )
    )
    return intent_resolution.classified_intent, intent_resolution.resolved_intent




def _intent_class_for_policy(intent: IntentType) -> str:
    return answer_stage_runtime_service.intent_class_for_policy(intent)


def _is_social_or_non_knowledge_intent(intent: IntentType) -> bool:
    return answer_stage_runtime_service.is_social_or_non_knowledge_intent(intent)


def _is_capabilities_help_request(intent: IntentType) -> bool:
    return answer_stage_runtime_service.is_capabilities_help_request(intent)


def _is_capabilities_help_answer(text: str) -> bool:
    normalized = (text or "").strip().lower()
    return normalized.startswith("runtime mode:") and "memory recall:" in normalized and "home assistant" in normalized


def _detect_capability_offer(text: str) -> str:
    return answer_stage_runtime_service.detect_capability_offer(text)


def _intent_label(intent: IntentType) -> str:
    return intent.value


def _intent_classifier_confidence(*, utterance: str, predicted_intent: IntentType) -> float:
    normalized = (utterance or "").strip().lower()
    if not normalized:
        return INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD

    if predicted_intent == IntentType.KNOWLEDGE_QUESTION and not is_definitional_query_form(normalized):
        return 0.82

    return 0.95


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    as_string = str(value).strip()
    if not as_string:
        return None
    return as_string


def _minimal_confidence_decision_for_direct_answer(*, branch: str, base_confidence_decision: dict[str, object]) -> dict[str, object]:
    return {
        **base_confidence_decision,
        "context_confident": False,
        "ambiguity_detected": False,
        "ambiguous_candidates": [],
        "scored_candidates": [],
        "objective": "",
        "objective_version": "",
        "retrieval_branch": branch,
        "retrieval_candidates_considered": 0,
        "retrieval_returned_top_k": 0,
        "retrieval_threshold": RETRIEVAL_SCORE_THRESHOLD,
    }


def _ambiguity_score(confidence_decision: dict[str, object]) -> float:
    typed_confidence = ConfidenceDecision.from_mapping(confidence_decision)
    scored_candidates = typed_confidence.typed_scored_candidates()
    if len(scored_candidates) < 2:
        return 0.0
    first = scored_candidates[0] if isinstance(scored_candidates[0], dict) else {}
    second = scored_candidates[1] if isinstance(scored_candidates[1], dict) else {}
    first_score = float(first.get("final_score", 0.0) or 0.0)
    second_score = float(second.get("final_score", 0.0) or 0.0)
    if first_score <= 0.0:
        return 1.0
    separation = max(0.0, first_score - second_score) / first_score
    return round(max(0.0, min(1.0, 1.0 - separation)), 4)


def _user_followup_signal_proxy(*, final_answer: str, fallback_action: str, ambiguity_score: float) -> float:
    if final_answer in {CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER}:
        return 1.0
    if fallback_action in {"ASK_CLARIFYING_QUESTION", "ROUTE_TO_ASK"}:
        return 0.9
    if fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        return round(max(0.2, ambiguity_score), 4)
    return round(max(0.0, ambiguity_score * 0.5), 4)


def _derive_response_blocker_reason(
    *,
    answer_mode: str,
    fallback_action: str,
    context_confident: bool,
    hit_count: int,
    ambiguity_detected: bool,
    answer_contract_valid: bool,
    general_knowledge_contract_valid: bool,
    general_knowledge_contract_applicability: str = "applicable",
) -> str:
    signal = derive_reject_signal(
        intent_label="non_memory",
        answer_mode=answer_mode,
        fallback_action=fallback_action,
        context_confident=context_confident,
        context_score=0.0,
        hit_count=hit_count,
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
        general_knowledge_contract_applicability=general_knowledge_contract_applicability,
    )
    return signal.reason


def build_partial_memory_clarifier(hits: list[Document], *, max_items: int = 2) -> str:
    snippets: list[str] = []
    for doc in hits[:max_items]:
        snippet = (doc.page_content or "").strip()
        if snippet:
            snippets.append(snippet[:80])
    if snippets:
        joined = "; ".join(snippets)
        return (
            f"I found related memory fragments ({joined}), but not enough to answer precisely. "
            "Which person, event, or time window should I focus on?"
        )
    return CLARIFY_ANSWER


def _select_memory_recovery_hit(hits: list[Document]) -> Document | None:
    return answer_stage_runtime_service.select_memory_recovery_hit(hits)


def _build_memory_recall_recovery_answer(hit: Document) -> str:
    return answer_stage_runtime_service.build_memory_recall_recovery_answer(hit)


def is_clarification_answer(text: str) -> bool:
    return answer_stage_runtime_service.is_clarification_answer(
        text,
        clarify_answer=CLARIFY_ANSWER,
        route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
    )


def _build_time_answer(*, user_input: str, now: arrow.Arrow, last_user_message_ts: str | None, timezone: str) -> str:
    return answer_stage_runtime_service.build_time_answer(
        user_input=user_input,
        now=now,
        last_user_message_ts=last_user_message_ts,
        timezone=timezone,
    )


def answer_assemble(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    answer_routing: AnswerRoutingDecision,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> AnswerAssembleResult:
    return answer_stage_runtime_service.answer_assemble(
        llm,
        state,
        chat_history=chat_history,
        hits=hits,
        capability_status=capability_status,
        answer_routing=answer_routing,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        timezone=timezone,
        render_context=render_context,
        answer_prompt=ANSWER_PROMPT,
        build_partial_memory_clarifier=build_partial_memory_clarifier,
        append_session_log=append_session_log,
        deny_answer=DENY_ANSWER,
        route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
        assist_alternatives_answer=ASSIST_ALTERNATIVES_ANSWER,
        fallback_answer=FALLBACK_ANSWER,
        non_knowledge_uncertainty_answer=NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    )


def answer_validate(
    state: PipelineState,
    *,
    assembled: AnswerAssembleResult,
    hits: list[Document],
    chat_history: deque[ChatMsg],
    pending_lookup_override: bool | None = None,
) -> AnswerValidateResult:
    return answer_stage_runtime_service.answer_validate(
        state,
        assembled=assembled,
        hits=hits,
        chat_history=chat_history,
        pending_lookup_override=pending_lookup_override,
        build_provenance_metadata=build_provenance_metadata_from_logic,
        evaluate_alignment_decision=_evaluate_alignment_decision,
        fallback_answer=FALLBACK_ANSWER,
        deny_answer=DENY_ANSWER,
        assist_alternatives_answer=ASSIST_ALTERNATIVES_ANSWER,
        non_knowledge_uncertainty_answer=NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
        clarify_answer=CLARIFY_ANSWER,
        route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
    )




def _answer_routing_from_decision_object(
    decision: DecisionObject,
    *,
    capability_status: CapabilityStatus,
) -> AnswerRoutingDecision:
    """Deprecated bridge: use _resolve_answer_routing_from_decision_object instead."""
    warnings.warn(
        "_answer_routing_from_decision_object is deprecated; use _resolve_answer_routing_from_decision_object.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _resolve_answer_routing_from_decision_object(
        decision,
        capability_status=capability_status,
    )


def _resolve_answer_routing_from_decision_object(
    decision: DecisionObject,
    *,
    capability_status: CapabilityStatus,
) -> AnswerRoutingDecision:
    return _resolve_answer_routing_from_decision_object_service(decision, capability_status=capability_status)




def _selected_decision_from_confidence(confidence_decision: dict[str, object]) -> DecisionObject | None:
    return _selected_decision_from_confidence_service(confidence_decision)

def _resolve_answer_routing_for_stage(
    state: PipelineState,
    *,
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None,
) -> tuple[PipelineState, AnswerRoutingDecision]:
    return _resolve_answer_routing_for_stage_service(
        state,
        capability_status=capability_status,
        selected_decision=selected_decision,
        intent_class_for_policy=_intent_class_for_policy,
    )


def _decision_object_from_assembled(assembled: AnswerAssembleResult) -> DecisionObject:
    fallback_action = str(assembled.fallback_action or "")
    return _decision_object_from_fallback_action(fallback_action)


def run_canonical_answer_stage_flow(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None = None,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> PipelineState:
    return answer_stage_runtime_service.run_canonical_answer_stage_flow(
        llm,
        state,
        chat_history=chat_history,
        hits=hits,
        capability_status=capability_status,
        selected_decision=selected_decision,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        timezone=timezone,
        run_canonical_turn_pipeline=_run_canonical_turn_pipeline,
    )



def run_answer_stage_flow(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None = None,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> PipelineState:
    _emit_deprecated_alias_warning("run_answer_stage_flow")
    return run_canonical_answer_stage_flow(
        llm,
        state,
        chat_history=chat_history,
        hits=hits,
        capability_status=capability_status,
        selected_decision=selected_decision,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        timezone=timezone,
    )


def answer_commit_persistence(
    *,
    llm: ChatOllama,
    store: MemoryStorePort,
    state: PipelineState,
    io_channel: str,
    clock: Clock,
) -> None:
    persist_runtime_answer_commit(
        llm=llm,
        store=store,
        state=state,
        io_channel=io_channel,
        clock=clock,
        deps=RuntimeCommitPersistenceDependencies(
            append_session_log=append_session_log,
            generate_reflection_yaml=generate_reflection_yaml,
        ),
    )

def _validate_and_log_transition(result) -> None:
    append_transition_validation_log(result)
    if not result.passed:
        failures = ", ".join(result.failures)
        raise AssertionError(f"Stage transition validation failed at {result.stage}.{result.boundary}: {failures}")


# ---------------------------
# Reflection extraction (metacognition)
# ---------------------------
REFLECTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a metacognitive reflection extractor.\n"
            "Given an observed statement, produce compact YAML with ONLY these keys:\n"
            "claims: [..]\n"
            "commitments: [..]\n"
            "preferences: [..]\n"
            "uncertainties: [..]\n"
            "followups: [..]\n"
            "confidence: <0..1>\n"
            "Rules:\n"
            "- Keep each list item short.\n"
            "- If none, use empty list [].\n"
            "- Do NOT invent facts.\n"
            "- If uncertain, put it under uncertainties.\n"
            "- Output YAML only (no prose).\n",
        ),
        ("human", "speaker: {speaker}\ntext: {text}\n"),
    ]
)


def generate_reflection_yaml(llm: ChatOllama, *, speaker: str, text: str) -> str:
    msgs = REFLECTION_PROMPT.format_messages(speaker=speaker, text=text)
    try:
        out = llm.invoke(msgs).content
    except Exception as exc:
        append_session_log(
            "reflection_generation_failed",
            {
                "error_class": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        out = ""
    return (out or "").strip() or (
        "claims: []\ncommitments: []\npreferences: []\nuncertainties: []\nfollowups: []\nconfidence: 0.2"
    )


# ---------------------------
# RAG prompt (uses chat history + retrieved memory)
# ---------------------------
ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a careful assistant.\n"
            "Use ONLY the provided memory context and recent chat.\nHeuristic packed-history hints are advisory context only, never hard evidence.\n"
            "If memory is empty or low-confidence, ask one targeted clarifying question or offer at least two capability-based alternatives.\n"
            "If memory is partial or ambiguous, provide a short user-facing summary and one bridging clarifier.\n"
            "Keep the exact phrase \"I don't know from memory.\" only for explicit deny/safety-policy cases.\n"
            "For any factual claim, include at least one cited memory with both doc_id and ts.\n\n"
            "Recent chat:\n{chat_history}\n\n"
            "Memory context:\n{context}\n\n"
            "Deterministic response plan:\n{response_plan}\n",
        ),
        ("human", "{input}"),
    ]
)

QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "Rewrite the user's message into a short search query for retrieving relevant memory.\nReturn ONLY the query text."),
        ("human", "{input}"),
    ]
)


def render_context(docs: list[Document], *, limit_chars: int = 5000) -> str:
    chunks: list[str] = []
    total = 0
    for idx, d in enumerate(docs, start=1):
        snippet = re.sub(r"\s+", " ", (d.page_content or "").strip())
        if not snippet:
            continue
        doc_id = str(d.metadata.get("doc_id") or d.id or "")
        ts = str(d.metadata.get("ts") or "")
        doc_type = str(d.metadata.get("type") or "")
        block = (
            f"[doc_{idx}]\n"
            f"doc_id: {doc_id}\n"
            f"ts: {ts}\n"
            f"type: {doc_type}\n"
            f"content: {snippet}\n"
            "---\n"
        )
        if total + len(block) > limit_chars:
            break
        chunks.append(block)
        total += len(block)
    return "".join(chunks).strip()


def has_sufficient_context_confidence(
    scored_candidates: list[dict[str, float | str]], *, ambiguity_detected: bool
) -> bool:
    return has_sufficient_context_confidence_from_objective(
        scored_candidates=scored_candidates,
        ambiguity_detected=ambiguity_detected,
    )


def collect_used_source_evidence_refs(hits: list[Document]) -> tuple[list[str], list[dict[str, str]]]:
    """Compatibility wrapper; canonical owner is testbot.logic.provenance.collect_used_source_evidence_refs."""
    return collect_used_source_evidence_refs_from_logic(hits)


def build_provenance_metadata(
    *,
    final_answer: str,
    hits: list[Document],
    chat_history: deque[ChatMsg],
    packed_history: PackedHistory,
) -> tuple[list[ProvenanceType], list[str], str, list[str], list[str], list[dict[str, str]]]:
    """Compatibility wrapper; canonical owner is testbot.logic.provenance.build_provenance_metadata."""
    return build_provenance_metadata_from_logic(
        final_answer=final_answer,
        hits=hits,
        chat_history=chat_history,
        packed_history=packed_history,
    )




def _deprecated_alignment_function_notice(name: str) -> None:
    _emit_deprecated_alias_warning(name)


def evaluate_alignment_decision(
    *,
    user_input: str,
    draft_answer: str,
    final_answer: str,
    confidence_decision: dict[str, object],
    claims: list[str],
    provenance_types: list[ProvenanceType],
    basis_statement: str,
) -> dict[str, object]:
    """Compatibility shim; migrate imports to testbot.logic.alignment.evaluate_alignment_decision."""

    _deprecated_alignment_function_notice("evaluate_alignment_decision")
    return _evaluate_alignment_decision(
        user_input=user_input,
        draft_answer=draft_answer,
        final_answer=final_answer,
        confidence_decision=confidence_decision,
        claims=claims,
        provenance_types=provenance_types,
        basis_statement=basis_statement,
        is_clarification_answer=is_clarification_answer,
        is_capabilities_help_answer=_is_capabilities_help_answer,
    )




def _run_canonical_turn_pipeline(
    *,
    runtime: dict[str, object] | None = None,
    llm: ChatOllama,
    store: MemoryStorePort,
    state: PipelineState,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    turn_id: str,
    near_tie_delta: float,
    chat_history: deque[ChatMsg],
    capability_status: CapabilityStatus,
    capability_snapshot: CapabilitySnapshot,
    clock: Clock,
    io_channel: str = "cli",
) -> tuple[PipelineState, list[Document]]:
    return run_runtime_turn_pipeline(
        runtime=runtime,
        llm=llm,
        store=store,
        state=state,
        utterance=utterance,
        prior_pipeline_state=prior_pipeline_state,
        turn_id=turn_id,
        near_tie_delta=near_tie_delta,
        chat_history=chat_history,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        clock=clock,
        io_channel=io_channel,
        hooks=RuntimeTurnPipelineHooks(
            append_session_log=append_session_log,
            validate_and_log_transition=_validate_and_log_transition,
            stage_rewrite_query=stage_rewrite_query,
            generate_reflection_yaml=generate_reflection_yaml,
            intent_classifier_confidence=_intent_classifier_confidence,
            optional_string=_optional_string,
            should_force_memory_retrieval_for_identity_recall=_should_force_memory_retrieval_for_identity_recall,
            resolve_context_fn=resolve_context,
            intent_telemetry_payload=_intent_telemetry_payload,
            poll_background_source_ingestion=_poll_background_source_ingestion,
            start_background_source_ingestion=_start_background_source_ingestion,
            stage_retrieve=_stage_retrieve_for_turn_service,
            stage_rerank=lambda *args, **kwargs: context_retrieval_runtime_service.stage_rerank_for_turn_service(
                *args,
                stage_rerank_fn=stage_rerank,
                **kwargs,
            ),
            selected_decision_from_confidence=_selected_decision_from_confidence,
            minimal_confidence_decision_for_direct_answer=_minimal_confidence_decision_for_direct_answer,
            resolve_answer_routing_for_stage=_resolve_answer_routing_for_stage,
            answer_assemble=_answer_assemble_for_turn_service,
            answer_validate=_answer_validate_for_turn_service,
            detect_capability_offer=_detect_capability_offer,
            ambiguity_score=_ambiguity_score,
            store_doc_fn=store_doc,
            intent_classifier_confidence_threshold=INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
            document_from_retrieval_input=_document_from_retrieval_input,
        ),
    )

def _run_chat_loop(
    *,
    runtime: dict[str, object] | None = None,
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    io_channel: str,
    capability_status: CapabilityStatus,
    capability_snapshot: CapabilitySnapshot,
    read_user_utterance,
    send_assistant_text,
    clock: Clock,
) -> None:
    """Compatibility wrapper; canonical runtime-loop control flow lives in entrypoints.runtime_loop."""

    from testbot.entrypoints.runtime_loop import run_chat_loop as _canonical_run_chat_loop

    _canonical_run_chat_loop(
        runtime=runtime or {},
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel=io_channel,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        read_user_utterance=read_user_utterance,
        send_assistant_text=send_assistant_text,
        clock=clock,
    )



def _run_cli_mode(*, runtime: dict[str, object], llm: ChatOllama, store: MemoryStore, chat_history: deque[ChatMsg], near_tie_delta: float, capability_snapshot: CapabilitySnapshot, clock: Clock) -> None:
    from testbot.entrypoints.sat_runtime_modes import run_cli_mode

    run_cli_mode(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        capability_snapshot=capability_snapshot,
        clock=clock,
        ask_gateway=AskGateway.from_runtime(runtime),
        run_chat_loop=_run_chat_loop,
    )


def _run_satellite_mode(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    capability_snapshot: CapabilitySnapshot,
    clock: Clock,
) -> None:
    from testbot.entrypoints.sat_runtime_modes import run_satellite_mode

    run_satellite_mode(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        capability_snapshot=capability_snapshot,
        clock=clock,
        ask_gateway=AskGateway.from_runtime(runtime),
        run_chat_loop=_run_chat_loop,
        satellite_say=sat_say,
    )


def build_capability_snapshot(*, requested_mode: str, daemon_mode: bool, runtime: dict[str, object]) -> CapabilitySnapshot:
    return build_capability_snapshot_from_service(
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        runtime=runtime,
        ha_connection_error_fn=_ha_connection_error,
        ollama_connection_error_fn=_ollama_connection_error,
    )


def parse_args(argv: list[str] | None = None) -> Namespace:
    return _parse_args(argv)


def read_runtime_env() -> dict[str, object]:
    return _read_runtime_env()


def build_runtime_memory_store(*, runtime: dict[str, object], embeddings: Embeddings) -> MemoryStorePort:
    return _build_runtime_memory_store(runtime=runtime, embeddings=embeddings)


def resolve_mode(requested_mode: str, ha_error: str | None) -> str:
    return _resolve_mode(requested_mode, ha_error)


def run_source_ingestion(*, runtime: dict[str, object], store: MemoryStorePort) -> None:
    _run_source_ingestion(runtime=runtime, store=store)


def print_startup_status(*, snapshot: CapabilitySnapshot) -> None:
    _print_startup_status(snapshot=snapshot)


def ambiguity_score(confidence_decision: dict[str, object]) -> float:
    return _ambiguity_score(confidence_decision)


def user_followup_signal_proxy(*, final_answer: str, fallback_action: str, ambiguity_score: float) -> float:
    return _user_followup_signal_proxy(
        final_answer=final_answer,
        fallback_action=fallback_action,
        ambiguity_score=ambiguity_score,
    )


def derive_response_blocker_reason(
    *,
    state: PipelineState,
    intent_label: str,
    fallback_action: str,
    hits: list[Document],
    confidence_decision: dict[str, object],
) -> str:
    return _derive_response_blocker_reason(
        state=state,
        intent_label=intent_label,
        fallback_action=fallback_action,
        hits=hits,
        confidence_decision=confidence_decision,
    )


def build_debug_turn_payload(*, state: PipelineState, intent_label: str, hits: list[Document]) -> dict[str, object]:
    return _build_debug_turn_payload(state=state, intent_label=intent_label, hits=hits)


def format_debug_turn_trace_payload(*, payload: dict[str, object], verbose: bool = False) -> str:
    return _format_debug_turn_trace_payload(payload=payload, verbose=verbose)


def format_debug_turn_trace(*, state: PipelineState, intent_label: str, hits: list[Document], verbose: bool = False) -> str:
    return _format_debug_turn_trace(state=state, intent_label=intent_label, hits=hits, verbose=verbose)


def intent_label(intent: IntentType) -> str:
    return _intent_label(intent)


def resolve_answer_routing_from_decision_object(
    decision: DecisionObject, *, capability_status: str
) -> AnswerRoutingDecision:
    return _resolve_answer_routing_from_decision_object(
        decision,
        capability_status=capability_status,
    )


def decision_object_from_assembled(assembled: AnswerAssembleResult) -> DecisionObject:
    return _decision_object_from_assembled(assembled)


def run_chat_loop(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    io_channel: str,
    capability_status: str,
    capability_snapshot: CapabilitySnapshot,
    read_user_utterance,
    send_assistant_text,
    clock: Clock,
) -> None:
    _run_chat_loop(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel=io_channel,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        read_user_utterance=read_user_utterance,
        send_assistant_text=send_assistant_text,
        clock=clock,
    )


_LEGACY_MAIN_WARNING_EMITTED = False
_LEGACY_MAIN_WARNING = (
    "testbot.sat_chatbot_memory_v2.main(...) is a monolith-era compatibility entry surface and will be removed. "
    "Use testbot.entrypoints.cli.main(...) instead. "
    "Migration: update runtime launch and imports to call testbot.entrypoints.cli.main(argv)."
)


def _warn_legacy_main_once() -> None:
    global _LEGACY_MAIN_WARNING_EMITTED
    if _LEGACY_MAIN_WARNING_EMITTED:
        return
    warnings.warn(_LEGACY_MAIN_WARNING, DeprecationWarning, stacklevel=2)
    _LEGACY_MAIN_WARNING_EMITTED = True


def main(argv: list[str] | None = None) -> None:
    """Deprecated compatibility entrypoint; delegate to testbot.entrypoints.cli.main."""
    _warn_legacy_main_once()
    from testbot.entrypoints.cli import main as entrypoint_main

    entrypoint_main(argv)


if __name__ == "__main__":
    main()
