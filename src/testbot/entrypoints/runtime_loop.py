"""Canonical runtime loop entrypoint helpers.

Ownership:
- This module is the canonical runtime-loop owner used by CLI/runtime mode
  entrypoints.
- Runtime loop control-flow authority lives here.
- ``testbot.sat_chatbot_memory_v2`` is compatibility-only for this boundary and
  delegates to this module for loop sequencing.
- Satellite output transport ownership lives in
  ``testbot.adapters.ha_satellite_output``; ``sat_say`` is retained only as
  a compatibility wrapper.
"""

from __future__ import annotations

from collections import deque
import uuid

from homeassistant_api import Client
from langchain_ollama import ChatOllama

from testbot.adapters.ha_satellite_output import send_satellite_output
from testbot.entrypoints.runtime_turn_pipeline import RuntimeTurnPipelineHooks, run_runtime_turn_pipeline
from testbot import sat_chatbot_memory_v2 as _legacy_runtime
from testbot.domain import Clock
from testbot.ports import MemoryStorePort

ChatMsg = dict[str, str]


def run_chat_loop(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    io_channel: str,
    capability_status: str,
    capability_snapshot: object,
    read_user_utterance,
    send_assistant_text,
    clock: Clock,
) -> None:
    runtime = runtime or {}
    runtime.setdefault("source_ingest_background_future", None)
    runtime.setdefault("source_ingest_background_in_progress", False)
    runtime.setdefault("source_ingest_background_request_id", "")
    runtime.setdefault("pending_ingestion_registry", {})
    runtime.setdefault("dead_letter_ingestion_registry", {})

    last_user_message_ts = ""
    prior_pipeline_state = None

    while True:
        _legacy_runtime._poll_pending_ingestion_obligations(runtime=runtime)
        last_user_message_ts, prior_pipeline_state, _ = _legacy_runtime._process_background_ingestion_completion(
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
        )

        utterance = read_user_utterance()
        if utterance is None:
            return

        utterance = utterance.strip()
        if not utterance:
            send_assistant_text("I heard silence. Try again.")
            continue

        _legacy_runtime.append_session_log(
            "user_utterance_ingest",
            {
                "channel": io_channel,
                "utterance": utterance,
            },
        )

        low = utterance.lower()
        if low in {"stop", "quit", "exit"}:
            send_assistant_text("Stopping. Bye.")
            break

        state = _legacy_runtime.PipelineState(
            user_input=utterance,
            last_user_message_ts=last_user_message_ts,
            classified_intent=_legacy_runtime.IntentType.KNOWLEDGE_QUESTION.value,
            resolved_intent="",
            prior_unresolved_intent=(
                prior_pipeline_state.prior_unresolved_intent
                if prior_pipeline_state is not None
                else ""
            ),
            confidence_decision={},
        )
        _legacy_runtime.append_pipeline_snapshot(
            "ingest",
            state,
            time_provider=_legacy_runtime._ClockBackedSnapshotTimeProvider(clock=clock),
        )
        turn_id = str(uuid.uuid4())

        state, hits = run_runtime_turn_pipeline(
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
                append_session_log=_legacy_runtime.append_session_log,
                validate_and_log_transition=_legacy_runtime._validate_and_log_transition,
                stage_rewrite_query=_legacy_runtime.stage_rewrite_query,
                generate_reflection_yaml=_legacy_runtime.generate_reflection_yaml,
                intent_classifier_confidence=_legacy_runtime._intent_classifier_confidence,
                optional_string=_legacy_runtime._optional_string,
                should_force_memory_retrieval_for_identity_recall=(
                    _legacy_runtime._should_force_memory_retrieval_for_identity_recall
                ),
                resolve_context_fn=_legacy_runtime.resolve_context,
                intent_telemetry_payload=_legacy_runtime._intent_telemetry_payload,
                poll_background_source_ingestion=_legacy_runtime._poll_background_source_ingestion,
                start_background_source_ingestion=_legacy_runtime._start_background_source_ingestion,
                stage_retrieve=_legacy_runtime._stage_retrieve_for_turn_service,
                stage_rerank=_legacy_runtime._stage_rerank_for_turn_service,
                selected_decision_from_confidence=_legacy_runtime._selected_decision_from_confidence,
                minimal_confidence_decision_for_direct_answer=(
                    _legacy_runtime._minimal_confidence_decision_for_direct_answer
                ),
                resolve_answer_routing_for_stage=_legacy_runtime._resolve_answer_routing_for_stage,
                answer_assemble=_legacy_runtime._answer_assemble_for_turn_service,
                answer_validate=_legacy_runtime._answer_validate_for_turn_service,
                detect_capability_offer=_legacy_runtime._detect_capability_offer,
                ambiguity_score=_legacy_runtime._ambiguity_score,
                store_doc_fn=_legacy_runtime.store_doc,
                intent_classifier_confidence_threshold=_legacy_runtime.INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
                document_from_retrieval_input=_legacy_runtime._document_from_retrieval_input,
            ),
        )

        ambiguity_score = _legacy_runtime._ambiguity_score(state.confidence_decision)
        chosen_action = str(state.invariant_decisions.get("fallback_action", "NONE"))
        followup_proxy = _legacy_runtime._user_followup_signal_proxy(
            final_answer=state.final_answer,
            fallback_action=chosen_action,
            ambiguity_score=ambiguity_score,
        )

        _legacy_runtime.append_session_log(
            "fallback_action_selected",
            _legacy_runtime._intent_telemetry_payload(
                state=state,
                utterance=utterance,
                extra={
                    "ambiguity_score": ambiguity_score,
                    "chosen_action": chosen_action,
                    "user_followup_signal_proxy": followup_proxy,
                },
            ),
        )
        _legacy_runtime.append_session_log(
            "provenance_summary",
            _legacy_runtime._intent_telemetry_payload(
                state=state,
                utterance=utterance,
                extra={
                    "ambiguity_score": ambiguity_score,
                    "chosen_action": chosen_action,
                    "user_followup_signal_proxy": followup_proxy,
                    "claims": state.claims,
                    "provenance_types": [p.value for p in state.provenance_types],
                    "used_memory_refs": state.used_memory_refs,
                    "used_source_evidence_refs": state.used_source_evidence_refs,
                    "source_evidence_attribution": state.source_evidence_attribution,
                    "basis_statement": state.basis_statement,
                },
            ),
        )
        _legacy_runtime.append_session_log(
            "alignment_decision_evaluated",
            _legacy_runtime._intent_telemetry_payload(
                state=state,
                utterance=utterance,
                extra={
                    "alignment_decision": state.alignment_decision.to_dict(),
                    "alignment_dimension_inputs_raw": state.alignment_decision.typed_dimension_inputs().get("raw", {}),
                    "alignment_dimension_inputs_normalized": state.alignment_decision.typed_dimension_inputs().get(
                        "normalized", {}
                    ),
                    "alignment_dimensions": dict(state.alignment_decision.dimensions),
                },
            ),
        )

        if capability_snapshot.runtime_capability_status.debug_enabled:
            debug_payload = _legacy_runtime._build_debug_turn_payload(
                state=state,
                intent_label=state.resolved_intent,
                hits=hits,
            )
            debug_trace = _legacy_runtime._format_debug_turn_trace_payload(
                payload=debug_payload,
                verbose=capability_snapshot.runtime_capability_status.debug_verbose,
            )
            _legacy_runtime.append_session_log(
                "debug_turn_trace",
                {
                    "utterance": utterance,
                    "payload": debug_payload,
                    "trace": debug_trace,
                },
            )
            send_assistant_text(debug_trace)

        unresolved_intent = (
            state.resolved_intent
            if _legacy_runtime.is_clarification_answer(state.final_answer)
            or _legacy_runtime._is_capabilities_help_answer(state.final_answer)
            else ""
        )
        state = _legacy_runtime.replace(state, prior_unresolved_intent=unresolved_intent)
        send_assistant_text(state.final_answer)

        pending_request_id = state.commit_receipt.pending_ingestion_request_id
        if pending_request_id:
            pending_registry = runtime.setdefault("pending_ingestion_registry", {})
            if isinstance(pending_registry, dict):
                now_iso = _legacy_runtime._utc_now_iso()
                deadline_at = _legacy_runtime.arrow.get(now_iso).shift(
                    seconds=_legacy_runtime.BACKGROUND_INGESTION_OBLIGATION_TIMEOUT_SECONDS
                ).isoformat()
                pending_registry[pending_request_id] = {
                    "ingestion_request_id": pending_request_id,
                    "utterance": utterance,
                    "turn_id": turn_id,
                    "source_context": {
                        "utterance_doc_id": str(state.candidate_facts.turn_id or ""),
                        "same_turn_exclusion_doc_ids": list(state.same_turn_exclusion.get("excluded_doc_ids", [])),
                    },
                    "prior_pipeline_state": prior_pipeline_state,
                    "created_at": now_iso,
                    "last_polled_at": now_iso,
                    "attempt_count": 0,
                    "deadline_at": deadline_at,
                    "status": "pending",
                }
                _legacy_runtime._emit_obligation_transition(
                    ingestion_request_id=pending_request_id,
                    status="created",
                    created_at=now_iso,
                    last_polled_at=now_iso,
                    attempt_count=0,
                    deadline_at=deadline_at,
                )

        last_user_message_ts = clock.now().isoformat()
        chat_history.append({"role": "user", "content": utterance})
        chat_history.append({"role": "assistant", "content": state.final_answer})
        prior_pipeline_state = state

        _legacy_runtime.answer_commit_persistence(
            llm=llm,
            store=store,
            state=state,
            io_channel=io_channel,
            clock=clock,
        )


def sat_say(client: Client, entity_id: str, text: str) -> None:
    send_satellite_output(client, entity_id, text)


__all__ = ["run_chat_loop", "sat_say"]
