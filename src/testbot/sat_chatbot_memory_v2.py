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
from functools import partial
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
    PipelineState,
    ProvenanceType,
    append_pipeline_snapshot,
)
from testbot.promotion_policy import persist_promoted_context
from testbot.reflection_policy import CapabilityStatus, decide_fallback_action, fallback_reason as derive_fallback_reason
from testbot.answer_policy import AnswerPolicyInput, AnswerRoutingDecision, resolve_answer_mode, resolve_answer_routing
from testbot.rerank import (
    has_sufficient_context_confidence_from_objective,
    rerank_docs_with_time_and_type_outcome,
)
from testbot.stage_transitions import (
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
from testbot.application.services.answer_stage_presentation import (
    ANSWER_PROMPT as CANONICAL_ANSWER_PROMPT,
    render_context as canonical_render_context,
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
from testbot.retrieval_routing import decide_retrieval_routing
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
    format_background_ingestion_completion_message as format_runtime_background_ingestion_completion_message,
)
from testbot.entrypoints.runtime_commit_persistence import (
    RuntimeCommitPersistenceDependencies,
    answer_commit_persistence as persist_runtime_answer_commit,
)
from testbot.entrypoints.runtime_snapshot_support import RuntimeClockBackedSnapshotTimeProvider
from testbot.entrypoints import runtime_loop as runtime_loop_entrypoint
from testbot.entrypoints import runtime_turn_pipeline as runtime_turn_pipeline_entrypoint
from testbot.entrypoints.runtime_transition_validation import (
    validate_and_log_transition as validate_and_log_runtime_transition,
)
from testbot.application.services import context_retrieval_runtime as context_retrieval_runtime_service
from testbot.application.services import background_ingestion_runtime as background_ingestion_runtime_service
from testbot.application.services.background_ingestion_runtime import BackgroundIngestionReplayRequest
from testbot.canonical_turn_orchestrator import CanonicalTurnOrchestrator as _CanonicalTurnOrchestrator
from testbot.logic.decision_helpers import (
    decision_object_from_assembled as _decision_object_from_fallback_action,
    resolve_answer_routing_for_stage as _resolve_answer_routing_for_stage_service,
    resolve_answer_routing_from_decision_object as _resolve_answer_routing_from_decision_object_service,
)
from testbot.logic.turn_policy import ambiguity_score as compute_turn_policy_ambiguity_score
from testbot.logic.turn_policy import optional_string as coerce_optional_string
from testbot.logic.turn_policy import selected_decision_from_confidence as project_selected_decision_from_confidence
from testbot.policies import turn_policy as turn_policy_policies
from testbot.application.services import answer_stage_runtime as answer_stage_runtime_service
from testbot.application.services import continuity_runtime as continuity_runtime_service
from testbot.application.services import intent_routing_diagnostics as intent_routing_diagnostics_service
from testbot.answer_contract_constants import (
    ASSIST_ALTERNATIVES_ANSWER,
    CLARIFY_ANSWER,
    DENY_ANSWER,
    FALLBACK_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    ROUTE_TO_ASK_ANSWER,
)

from langchain_core.documents import Document
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
class _ClockBackedSnapshotTimeProvider(RuntimeClockBackedSnapshotTimeProvider):
    """Compatibility alias; canonical owner is runtime_snapshot_support."""


def _utc_now_iso() -> str:
    return arrow.utcnow().isoformat()


def _sat_execute_source_ingestion(
    *,
    runtime: dict[str, object],
    store: MemoryStorePort,
    background: bool = False,
    ingestion_request_id: str = "",
) -> dict[str, object]:
    return background_ingestion_runtime_service.execute_source_ingestion(
        runtime=runtime,
        store=store,
        build_source_connector=lambda configured_runtime: build_startup_source_connector(
            runtime=configured_runtime,
            append_session_log=append_session_log,
        ),
        source_ingestor_cls=SourceIngestor,
        append_session_log=append_session_log,
        background=background,
        ingestion_request_id=ingestion_request_id,
    )


def _sat_start_background_source_ingestion(*, runtime: dict[str, object], store: MemoryStorePort, ingestion_request_id: str = "") -> dict[str, object]:
    return background_ingestion_runtime_service.start_background_source_ingestion(
        runtime=runtime,
        store=store,
        execute_source_ingestion=_sat_execute_source_ingestion,
        append_session_log=append_session_log,
        ingestion_request_id=ingestion_request_id,
    )


def _sat_poll_background_source_ingestion(*, runtime: dict[str, object]) -> dict[str, object] | None:
    return background_ingestion_runtime_service.poll_background_source_ingestion(
        runtime=runtime,
        append_session_log=append_session_log,
    )


def _build_sat_compat_runtime_turn_pipeline_hooks(
    *,
    answer_assemble_hook,
    answer_validate_hook,
):
    """Temporary SAT-only hook bundle.

    Compatibility-only helper that centralizes SAT hook assembly while the SAT
    facade is being retired. This must not become a third canonical execution
    profile.
    """

    return runtime_loop_entrypoint.build_runtime_turn_pipeline_hooks(
        append_session_log=append_session_log,
        validate_and_log_transition=validate_and_log_runtime_transition,
        stage_rewrite_query=runtime_loop_entrypoint._stage_rewrite_query,
        generate_reflection_yaml=runtime_loop_entrypoint._generate_reflection_yaml,
        intent_classifier_confidence=partial(
            turn_policy_policies.intent_classifier_confidence,
            confidence_threshold=INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
        ),
        optional_string=coerce_optional_string,
        should_force_memory_retrieval_for_identity_recall=context_retrieval_runtime_service.should_force_memory_retrieval_for_identity_recall,
        resolve_context_fn=partial(
            context_retrieval_runtime_service.resolve_context,
            resolve_context_fn=_resolve_context_from_domain,
        ),
        intent_telemetry_payload=runtime_loop_entrypoint.intent_telemetry_payload,
        poll_background_source_ingestion=_sat_poll_background_source_ingestion,
        start_background_source_ingestion=_sat_start_background_source_ingestion,
        stage_retrieve=lambda *args, **kwargs: context_retrieval_runtime_service.stage_retrieve_for_turn_service(
            *args,
            retrieval_score_threshold=RETRIEVAL_SCORE_THRESHOLD,
            **kwargs,
        ),
        stage_rerank=lambda *args, **kwargs: context_retrieval_runtime_service.stage_rerank_for_turn_service(
            *args,
            **kwargs,
        ),
        selected_decision_from_confidence=project_selected_decision_from_confidence,
        minimal_confidence_decision_for_direct_answer=partial(
            turn_policy_policies.minimal_confidence_decision_for_direct_answer,
            retrieval_score_threshold=RETRIEVAL_SCORE_THRESHOLD,
        ),
        resolve_answer_routing_for_stage=partial(
            _resolve_answer_routing_for_stage_service,
            intent_class_for_policy=answer_stage_runtime_service.intent_class_for_policy,
        ),
        answer_assemble=answer_assemble_hook,
        answer_validate=answer_validate_hook,
        detect_capability_offer=answer_stage_runtime_service.detect_capability_offer,
        ambiguity_score=compute_turn_policy_ambiguity_score,
        store_doc_fn=store_doc,
        intent_classifier_confidence_threshold=INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
        document_from_retrieval_input=context_retrieval_runtime_service.document_from_retrieval_input,
    )


def _sat_replay_background_completion_turn(request: BackgroundIngestionReplayRequest) -> PipelineState:
    """Temporary SAT replay bridge.

    Compatibility-only seam: SAT delegates replay turn execution to canonical
    runtime replay orchestration while still injecting the SAT hook bundle.
    """

    def _answer_assemble_hook(
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
            document_from_retrieval_input=context_retrieval_runtime_service.document_from_retrieval_input,
            render_context=canonical_render_context,
            answer_prompt=CANONICAL_ANSWER_PROMPT,
            append_session_log=append_session_log,
        )

    def _answer_validate_hook(
        state: PipelineState,
        *,
        assembled,
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
            document_from_retrieval_input=context_retrieval_runtime_service.document_from_retrieval_input,
        )

    return runtime_loop_entrypoint._replay_background_completion_turn(
        request=request,
        hooks=_build_sat_compat_runtime_turn_pipeline_hooks(
            answer_assemble_hook=_answer_assemble_hook,
            answer_validate_hook=_answer_validate_hook,
        ),
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

def _format_background_ingestion_completion_message(*, correlation_id: str) -> str:
    return format_runtime_background_ingestion_completion_message(correlation_id=correlation_id)


INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD = turn_policy_policies.INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD
RETRIEVAL_SCORE_THRESHOLD = turn_policy_policies.RETRIEVAL_SCORE_THRESHOLD


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
    """Compatibility wrapper; canonical owner is runtime_turn_telemetry.intent_telemetry_payload."""

    from testbot.entrypoints.runtime_turn_telemetry import intent_telemetry_payload as _intent_telemetry_payload_owner

    return _intent_telemetry_payload_owner(state=state, utterance=utterance, extra=extra)


def doc_to_candidate_hit(doc: Document, score: float) -> CandidateHit:
    return CandidateHit(
        doc_id=str(doc.id or doc.metadata.get("doc_id") or ""),
        score=float(score),
        ts=str(doc.metadata.get("ts") or ""),
        card_type=str(doc.metadata.get("type") or ""),
    )


def resolve_context(*args, **kwargs):
    return context_retrieval_runtime_service.resolve_context(*args, resolve_context_fn=_resolve_context_from_domain, **kwargs)


def stage_rewrite_query(llm: ChatOllama, state: PipelineState) -> PipelineState:
    """Compatibility wrapper; canonical owner is ``testbot.entrypoints.runtime_loop``."""
    from testbot.entrypoints.runtime_loop import _stage_rewrite_query as _canonical_stage_rewrite_query

    return _canonical_stage_rewrite_query(llm, state)


def observe_stage(state: PipelineState) -> PipelineState:
    warnings.warn(
        "observe_stage is deprecated; use testbot.entrypoints.runtime_turn_pipeline.run_runtime_turn_pipeline instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return state


def encode_stage(llm: ChatOllama, state: PipelineState) -> PipelineState:
    warnings.warn(
        "encode_stage is deprecated; use testbot.entrypoints.runtime_turn_pipeline.run_runtime_turn_pipeline instead.",
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
    updated_state, retrieval_candidates = context_retrieval_runtime_service.stage_retrieve_for_turn_service(
        store,
        state,
        retrieval_score_threshold=RETRIEVAL_SCORE_THRESHOLD,
        exclude_doc_ids=exclude_doc_ids,
        exclude_source_ids=exclude_source_ids,
        exclude_turn_scoped_ids=exclude_turn_scoped_ids,
        segment_ids=segment_ids,
        segment_types=segment_types,
    )
    return updated_state, [
        (context_retrieval_runtime_service.document_from_retrieval_input(record), float(record.score))
        for record in retrieval_candidates
    ]


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
    updated_state, reranked_records = context_retrieval_runtime_service.stage_rerank_for_turn_service(
        state,
        [context_retrieval_runtime_service.retrieval_input_from_document(doc, score=score) for doc, score in docs_and_scores],
        utterance=utterance,
        user_doc_id=user_doc_id,
        user_reflection_doc_id=user_reflection_doc_id,
        near_tie_delta=near_tie_delta,
        clock=clock,
        io_channel=io_channel,
    )
    return updated_state, [context_retrieval_runtime_service.document_from_retrieval_input(record) for record in reranked_records]



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
    return answer_stage_runtime_service.is_clarification_answer(
        normalized,
        clarify_answer=CLARIFY_ANSWER,
        route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
    ) or _is_capabilities_help_answer(normalized)


def resolve_turn_intent(
    *,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    diagnostic_only: bool = True,
) -> tuple[IntentType, IntentType]:
    """Compatibility wrapper; canonical owner is intent_routing_diagnostics."""
    return intent_routing_diagnostics_service.resolve_turn_intent(
        utterance=utterance,
        prior_pipeline_state=prior_pipeline_state,
        diagnostic_only=diagnostic_only,
    )




def _intent_class_for_policy(intent: IntentType) -> str:
    return answer_stage_runtime_service.intent_class_for_policy(intent)


def _is_social_or_non_knowledge_intent(intent: IntentType) -> bool:
    return answer_stage_runtime_service.is_social_or_non_knowledge_intent(intent)


def _is_capabilities_help_request(intent: IntentType) -> bool:
    return answer_stage_runtime_service.is_capabilities_help_request(intent)


def _is_capabilities_help_answer(text: str) -> bool:
    return continuity_runtime_service.is_capabilities_help_answer(text)


def _intent_label(intent: IntentType) -> str:
    return intent.value


def _intent_classifier_confidence(*, utterance: str, predicted_intent: IntentType) -> float:
    return turn_policy_policies.intent_classifier_confidence(
        utterance=utterance,
        predicted_intent=predicted_intent,
        confidence_threshold=INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
    )


def _optional_string(value: object) -> str | None:
    return coerce_optional_string(value)


def _minimal_confidence_decision_for_direct_answer(*, branch: str, base_confidence_decision: dict[str, object]) -> dict[str, object]:
    return turn_policy_policies.minimal_confidence_decision_for_direct_answer(
        branch=branch,
        base_confidence_decision=base_confidence_decision,
        retrieval_score_threshold=RETRIEVAL_SCORE_THRESHOLD,
    )


def _ambiguity_score(confidence_decision: dict[str, object]) -> float:
    return compute_turn_policy_ambiguity_score(confidence_decision)


def _user_followup_signal_proxy(*, final_answer: str, fallback_action: str, ambiguity_score: float) -> float:
    """Compatibility wrapper; canonical owner is runtime_turn_telemetry.user_followup_signal_proxy."""

    from testbot.entrypoints.runtime_turn_telemetry import user_followup_signal_proxy as _user_followup_signal_proxy_owner

    return _user_followup_signal_proxy_owner(
        final_answer=final_answer,
        fallback_action=fallback_action,
        ambiguity_score=ambiguity_score,
    )


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
    return project_selected_decision_from_confidence(confidence_decision)

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
    def _answer_assemble_hook(
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
            document_from_retrieval_input=context_retrieval_runtime_service.document_from_retrieval_input,
            render_context=canonical_render_context,
            answer_prompt=CANONICAL_ANSWER_PROMPT,
            append_session_log=append_session_log,
        )

    def _answer_validate_hook(
        state: PipelineState,
        *,
        assembled,
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
            document_from_retrieval_input=context_retrieval_runtime_service.document_from_retrieval_input,
        )

    def _run_pipeline_with_sat_compat_hooks(**kwargs):
        return runtime_turn_pipeline_entrypoint.run_runtime_turn_pipeline(
            **kwargs,
            hooks=_build_sat_compat_runtime_turn_pipeline_hooks(
                answer_assemble_hook=_answer_assemble_hook,
                answer_validate_hook=_answer_validate_hook,
            ),
        )

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
        run_canonical_turn_pipeline=_run_pipeline_with_sat_compat_hooks,
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
    validate_and_log_runtime_transition(result)


def generate_reflection_yaml(llm: ChatOllama, *, speaker: str, text: str) -> str:
    """Compatibility wrapper; canonical owner is ``testbot.entrypoints.runtime_loop``."""
    from testbot.entrypoints.runtime_loop import _generate_reflection_yaml as _canonical_generate_reflection_yaml

    return _canonical_generate_reflection_yaml(llm, speaker=speaker, text=text)


# ---------------------------
# RAG prompt (uses chat history + retrieved memory)
# ---------------------------
# Compatibility re-export; canonical owner is
# testbot.application.services.answer_stage_presentation.
ANSWER_PROMPT = CANONICAL_ANSWER_PROMPT

def render_context(docs: list[Document], *, limit_chars: int = 5000) -> str:
    """Compatibility wrapper; canonical owner is answer_stage_presentation."""
    return canonical_render_context(docs, limit_chars=limit_chars)


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
        is_clarification_answer=lambda text: answer_stage_runtime_service.is_clarification_answer(
            text,
            clarify_answer=CLARIFY_ANSWER,
            route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
        ),
        is_capabilities_help_answer=_is_capabilities_help_answer,
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
        run_chat_loop=run_chat_loop,
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
        run_chat_loop=run_chat_loop,
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
    return runtime_bootstrap_entrypoint.read_runtime_env()


def build_runtime_memory_store(*, runtime: dict[str, object], embeddings: Embeddings) -> MemoryStorePort:
    return _build_runtime_memory_store(runtime=runtime, embeddings=embeddings)


def resolve_mode(requested_mode: str, ha_error: str | None) -> str:
    return _resolve_mode(requested_mode, ha_error)


def run_source_ingestion(*, runtime: dict[str, object], store: MemoryStorePort) -> None:
    run_startup_source_ingestion(runtime=runtime, store=store, append_session_log=append_session_log)


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
    from testbot.entrypoints.runtime_loop import run_chat_loop as _canonical_run_chat_loop

    _canonical_run_chat_loop(
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
        replay_background_completion_turn=_sat_replay_background_completion_turn,
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
