"""Behave-facing runtime helpers.

These helpers keep feature step modules importing canonical service owners while
compatibility pipeline wiring is still transitional.
"""

from __future__ import annotations

from collections import deque
from functools import partial

from langchain_core.documents import Document
from langchain_ollama import ChatOllama

from testbot.application.services import answer_stage_presentation as answer_stage_presentation_service
from testbot.application.services import answer_stage_runtime as answer_stage_runtime_service
from testbot.application.services import context_retrieval_runtime as context_retrieval_runtime_service
from testbot.context_resolution import resolve as _resolve_context_from_domain
from testbot.domain import Clock
from testbot.evidence_retrieval import RetrievalInputRecord
from testbot.entrypoints.runtime_loop import _generate_reflection_yaml, _stage_rewrite_query
from testbot.entrypoints.runtime_transition_validation import validate_and_log_transition
from testbot.entrypoints.runtime_turn_pipeline import RuntimeTurnPipelineHooks, run_runtime_turn_pipeline
from testbot.entrypoints.runtime_turn_telemetry import intent_telemetry_payload
from testbot.logic.turn_policy import ambiguity_score as compute_turn_policy_ambiguity_score
from testbot.logic.turn_policy import optional_string as coerce_optional_string
from testbot.logic.turn_policy import selected_decision_from_confidence as project_selected_decision_from_confidence
from testbot.memory_cards import store_doc
from testbot.observability.session_log import append_session_log
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import DecisionObject
from testbot.policies.turn_policy import (
    INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
    RETRIEVAL_SCORE_THRESHOLD,
    intent_classifier_confidence as compute_intent_classifier_confidence,
    minimal_confidence_decision_for_direct_answer as build_minimal_confidence_decision_for_direct_answer,
)
from testbot.ports import MemoryStorePort
from testbot.reflection_policy import CapabilityStatus
from testbot.runtime_capability_service import CapabilitySnapshotData as CapabilitySnapshot
from testbot.runtime_capability_service import RuntimeCapabilityStatusData as RuntimeCapabilityStatus

ChatMsg = dict[str, str]


def _poll_background_source_ingestion_for_answer_stage(*, runtime: dict[str, object]) -> dict[str, object] | None:
    del runtime
    # Seeded answer-stage probes do not run background-ingestion side effects.
    return None


def _start_background_source_ingestion_for_answer_stage(*, runtime: dict[str, object], store: MemoryStorePort) -> dict[str, object]:
    del runtime, store
    return {"started": False, "ingestion_request_id": ""}


def _retrieval_input_from_document(doc: Document, *, score: float) -> RetrievalInputRecord:
    return context_retrieval_runtime_service.retrieval_input_from_document(doc, score=score)


def _document_from_retrieval_input(record: RetrievalInputRecord) -> Document:
    return context_retrieval_runtime_service.document_from_retrieval_input(record)


def _stage_retrieve_documents_for_answer_stage(
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
        (_document_from_retrieval_input(record), float(record.score))
        for record in retrieval_candidates
    ]


def _stage_retrieve_for_turn_service_answer_stage(
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
        stage_retrieve_fn=_stage_retrieve_documents_for_answer_stage,
        exclude_doc_ids=exclude_doc_ids,
        exclude_source_ids=exclude_source_ids,
        exclude_turn_scoped_ids=exclude_turn_scoped_ids,
        segment_ids=segment_ids,
        segment_types=segment_types,
    )


def _stage_rerank_documents_for_answer_stage(
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
        [_retrieval_input_from_document(doc, score=score) for doc, score in docs_and_scores],
        utterance=utterance,
        user_doc_id=user_doc_id,
        user_reflection_doc_id=user_reflection_doc_id,
        near_tie_delta=near_tie_delta,
        clock=clock,
        io_channel=io_channel,
    )
    return updated_state, [_document_from_retrieval_input(record) for record in reranked_records]


_BEHAVE_RUNTIME_TURN_HOOKS = RuntimeTurnPipelineHooks(
    append_session_log=append_session_log,
    validate_and_log_transition=validate_and_log_transition,
    stage_rewrite_query=_stage_rewrite_query,
    generate_reflection_yaml=_generate_reflection_yaml,
    intent_classifier_confidence=partial(
        compute_intent_classifier_confidence,
        confidence_threshold=INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
    ),
    optional_string=coerce_optional_string,
    should_force_memory_retrieval_for_identity_recall=context_retrieval_runtime_service.should_force_memory_retrieval_for_identity_recall,
    resolve_context_fn=lambda *args, **kwargs: context_retrieval_runtime_service.resolve_context(
        *args,
        resolve_context_fn=_resolve_context_from_domain,
        **kwargs,
    ),
    intent_telemetry_payload=intent_telemetry_payload,
    poll_background_source_ingestion=_poll_background_source_ingestion_for_answer_stage,
    start_background_source_ingestion=_start_background_source_ingestion_for_answer_stage,
    stage_retrieve=_stage_retrieve_for_turn_service_answer_stage,
    stage_rerank=lambda *args, **kwargs: context_retrieval_runtime_service.stage_rerank_for_turn_service(
        *args,
        stage_rerank_fn=_stage_rerank_documents_for_answer_stage,
        **kwargs,
    ),
    selected_decision_from_confidence=project_selected_decision_from_confidence,
    minimal_confidence_decision_for_direct_answer=partial(
        build_minimal_confidence_decision_for_direct_answer,
        retrieval_score_threshold=RETRIEVAL_SCORE_THRESHOLD,
    ),
    resolve_answer_routing_for_stage=answer_stage_runtime_service.resolve_answer_routing_for_stage,
    answer_assemble=lambda *args, **kwargs: answer_stage_runtime_service.answer_assemble_for_turn_service(
        *args,
        **kwargs,
        document_from_retrieval_input=_document_from_retrieval_input,
        render_context=answer_stage_presentation_service.render_context,
        answer_prompt=answer_stage_presentation_service.ANSWER_PROMPT,
        append_session_log=append_session_log,
    ),
    answer_validate=lambda *args, **kwargs: answer_stage_runtime_service.answer_validate_for_turn_service(
        *args,
        **kwargs,
        document_from_retrieval_input=_document_from_retrieval_input,
    ),
    detect_capability_offer=answer_stage_runtime_service.detect_capability_offer,
    ambiguity_score=compute_turn_policy_ambiguity_score,
    store_doc_fn=store_doc,
    intent_classifier_confidence_threshold=INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
    document_from_retrieval_input=_document_from_retrieval_input,
)


def _run_canonical_turn_pipeline_for_behave(
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
        hooks=_BEHAVE_RUNTIME_TURN_HOOKS,
    )


def run_answer_stage_flow(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg] | list[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None = None,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> PipelineState:
    """Canonical answer-stage entry used by behave step definitions.

    Behave probes depend directly on canonical runtime turn-pipeline owners.
    """

    return answer_stage_runtime_service.run_canonical_answer_stage_flow(
        llm,
        state,
        chat_history=deque(chat_history),
        hits=hits,
        capability_status=capability_status,
        selected_decision=selected_decision,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        timezone=timezone,
        run_canonical_turn_pipeline=_run_canonical_turn_pipeline_for_behave,
    )


__all__ = ["run_answer_stage_flow"]
