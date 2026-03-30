"""Canonical runtime-owned turn-pipeline dependency assembly helpers.

Ownership:
- This module is the canonical owner for runtime-entrypoint dependency assembly
  before invoking the canonical turn service.
- Compatibility façades may delegate here during retirement windows.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

from langchain_core.documents import Document
from langchain_ollama import ChatOllama

from testbot.application.services.canonical_turn_runtime import run_canonical_turn_pipeline
from testbot.application.services.turn_service import TurnPipelineDependencies
from testbot.continuity_read_model import ContinuityReadModel
from testbot.domain import Clock
from testbot.pipeline_state import PipelineState
from testbot.ports import MemoryStorePort
from testbot.evidence_retrieval import RetrievalInputRecord

ChatMsg = dict[str, str]


@dataclass(frozen=True)
class RuntimeTurnPipelineHooks:
    append_session_log: Callable[..., object]
    validate_and_log_transition: Callable[..., object]
    stage_rewrite_query: Callable[..., object]
    generate_reflection_yaml: Callable[..., object]
    intent_classifier_confidence: Callable[..., object]
    optional_string: Callable[..., object]
    should_force_memory_retrieval_for_identity_recall: Callable[..., object]
    resolve_context_fn: Callable[..., object]
    intent_telemetry_payload: Callable[..., object]
    poll_background_source_ingestion: Callable[..., object]
    start_background_source_ingestion: Callable[..., object]
    stage_retrieve: Callable[..., object]
    stage_rerank: Callable[..., object]
    selected_decision_from_confidence: Callable[..., object]
    minimal_confidence_decision_for_direct_answer: Callable[..., object]
    resolve_answer_routing_for_stage: Callable[..., object]
    answer_assemble: Callable[..., object]
    answer_validate: Callable[..., object]
    detect_capability_offer: Callable[..., object]
    ambiguity_score: Callable[..., object]
    store_doc_fn: Callable[..., object]
    intent_classifier_confidence_threshold: float
    document_from_retrieval_input: Callable[[RetrievalInputRecord], Document]


def run_runtime_turn_pipeline(
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
    capability_status: object,
    capability_snapshot: object,
    clock: Clock,
    io_channel: str = "cli",
    hooks: RuntimeTurnPipelineHooks,
    prior_continuity: ContinuityReadModel | None = None,
) -> tuple[PipelineState, list[Document]]:
    deps = TurnPipelineDependencies(
        append_session_log=hooks.append_session_log,
        validate_and_log_transition=hooks.validate_and_log_transition,
        stage_rewrite_query=hooks.stage_rewrite_query,
        generate_reflection_yaml=hooks.generate_reflection_yaml,
        intent_classifier_confidence=hooks.intent_classifier_confidence,
        optional_string=hooks.optional_string,
        should_force_memory_retrieval_for_identity_recall=hooks.should_force_memory_retrieval_for_identity_recall,
        resolve_context_fn=hooks.resolve_context_fn,
        intent_telemetry_payload=hooks.intent_telemetry_payload,
        poll_background_source_ingestion=hooks.poll_background_source_ingestion,
        start_background_source_ingestion=hooks.start_background_source_ingestion,
        stage_retrieve=hooks.stage_retrieve,
        stage_rerank=hooks.stage_rerank,
        selected_decision_from_confidence=hooks.selected_decision_from_confidence,
        minimal_confidence_decision_for_direct_answer=hooks.minimal_confidence_decision_for_direct_answer,
        resolve_answer_routing_for_stage=hooks.resolve_answer_routing_for_stage,
        answer_assemble=hooks.answer_assemble,
        answer_validate=hooks.answer_validate,
        detect_capability_offer=hooks.detect_capability_offer,
        ambiguity_score=hooks.ambiguity_score,
        store_doc_fn=hooks.store_doc_fn,
        intent_classifier_confidence_threshold=hooks.intent_classifier_confidence_threshold,
    )
    next_state, normalized_hits = run_canonical_turn_pipeline(
        runtime=runtime,
        llm=llm,
        store=store,
        state=state,
        utterance=utterance,
        prior_pipeline_state=prior_pipeline_state,
        prior_continuity=prior_continuity,
        turn_id=turn_id,
        near_tie_delta=near_tie_delta,
        chat_history=chat_history,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        clock=clock,
        io_channel=io_channel,
        deps=deps,
    )
    return next_state, [hooks.document_from_retrieval_input(record) for record in normalized_hits]


__all__ = ["RuntimeTurnPipelineHooks", "run_runtime_turn_pipeline"]
