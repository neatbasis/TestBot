"""Canonical runtime turn-pipeline execution profile hook assembly.

Ownership:
- This module owns profile-based RuntimeTurnPipelineHooks assembly.
- Runtime entrypoints and harness seams delegate hook construction here.
"""

from __future__ import annotations

from enum import StrEnum

from testbot.entrypoints.runtime_turn_pipeline import RuntimeTurnPipelineHooks


class TurnPipelineExecutionProfile(StrEnum):
    RUNTIME_LIVE = "runtime_live"
    SEEDED_PROBE = "seeded_probe"


def build_runtime_turn_pipeline_hooks_for_profile(
    *,
    profile: TurnPipelineExecutionProfile,
    append_session_log,
    validate_and_log_transition,
    stage_rewrite_query,
    generate_reflection_yaml,
    intent_classifier_confidence,
    optional_string,
    should_force_memory_retrieval_for_identity_recall,
    resolve_context_fn,
    intent_telemetry_payload,
    poll_background_source_ingestion,
    start_background_source_ingestion,
    stage_retrieve,
    stage_rerank,
    selected_decision_from_confidence,
    minimal_confidence_decision_for_direct_answer,
    resolve_answer_routing_for_stage,
    answer_assemble,
    answer_validate,
    detect_capability_offer,
    ambiguity_score,
    store_doc_fn,
    intent_classifier_confidence_threshold: float,
    document_from_retrieval_input,
) -> RuntimeTurnPipelineHooks:
    if profile not in {
        TurnPipelineExecutionProfile.RUNTIME_LIVE,
        TurnPipelineExecutionProfile.SEEDED_PROBE,
    }:
        raise ValueError(f"Unsupported turn-pipeline execution profile: {profile!r}")

    return RuntimeTurnPipelineHooks(
        append_session_log=append_session_log,
        validate_and_log_transition=validate_and_log_transition,
        stage_rewrite_query=stage_rewrite_query,
        generate_reflection_yaml=generate_reflection_yaml,
        intent_classifier_confidence=intent_classifier_confidence,
        optional_string=optional_string,
        should_force_memory_retrieval_for_identity_recall=should_force_memory_retrieval_for_identity_recall,
        resolve_context_fn=resolve_context_fn,
        intent_telemetry_payload=intent_telemetry_payload,
        poll_background_source_ingestion=poll_background_source_ingestion,
        start_background_source_ingestion=start_background_source_ingestion,
        stage_retrieve=stage_retrieve,
        stage_rerank=stage_rerank,
        selected_decision_from_confidence=selected_decision_from_confidence,
        minimal_confidence_decision_for_direct_answer=minimal_confidence_decision_for_direct_answer,
        resolve_answer_routing_for_stage=resolve_answer_routing_for_stage,
        answer_assemble=answer_assemble,
        answer_validate=answer_validate,
        detect_capability_offer=detect_capability_offer,
        ambiguity_score=ambiguity_score,
        store_doc_fn=store_doc_fn,
        intent_classifier_confidence_threshold=intent_classifier_confidence_threshold,
        document_from_retrieval_input=document_from_retrieval_input,
    )


__all__ = [
    "TurnPipelineExecutionProfile",
    "build_runtime_turn_pipeline_hooks_for_profile",
]
