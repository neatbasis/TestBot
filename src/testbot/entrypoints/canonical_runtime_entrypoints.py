from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
import uuid
from typing import Callable

import arrow
from langchain_core.documents import Document
from langchain_ollama import ChatOllama

from testbot.clock import Clock, SystemClock
from testbot.intent_router import IntentType
from testbot.pipeline_state import PipelineState, append_pipeline_snapshot
from testbot.reflection_policy import CapabilityStatus
from testbot.vector_store import MemoryStore

ChatMsg = dict[str, str]
@dataclass(frozen=True)
class RuntimeCapabilityStatus:
    ollama_available: bool
    ha_available: bool
    effective_mode: str
    requested_mode: str
    daemon_mode: bool
    fallback_reason: str | None
    memory_backend: str
    debug_enabled: bool
    debug_verbose: bool
    text_clarification_available: bool
    satellite_ask_available: bool


@dataclass(frozen=True)
class CapabilitySnapshot:
    runtime: dict[str, object]
    requested_mode: str
    daemon_mode: bool
    effective_mode: str | None
    fallback_reason: str | None
    exit_reason: str | None
    ha_error: str | None
    ollama_error: str | None
    runtime_capability_status: RuntimeCapabilityStatus


@dataclass(frozen=True)
class _ClockBackedSnapshotTimeProvider:
    clock: Clock

    def now_iso(self) -> str:
        return self.clock.now().isoformat()


class UnsupportedCompatibilityPathError(ValueError):
    """Raised when deprecated seeded-path overrides attempt to bypass canonical sequencing."""


@dataclass(frozen=True)
class CanonicalRuntimeEntrypointDependencies:
    run_canonical_turn_pipeline: Callable[..., tuple[PipelineState, list[Document]]]
    build_default_runtime_capability_status: Callable[[], RuntimeCapabilityStatus]
    build_capability_snapshot: Callable[[RuntimeCapabilityStatus], CapabilitySnapshot]
    poll_pending_ingestion_obligations: Callable[..., None]
    emit_obligation_transition: Callable[..., None]
    process_background_ingestion_completion: Callable[..., tuple[str, PipelineState | None, bool]]
    append_session_log: Callable[[str, dict[str, object]], None]
    ambiguity_score: Callable[[dict[str, object]], float]
    user_followup_signal_proxy: Callable[..., float]
    intent_telemetry_payload: Callable[..., dict[str, object]]
    build_debug_turn_payload: Callable[..., dict[str, object]]
    format_debug_turn_trace_payload: Callable[..., str]
    is_clarification_answer: Callable[[str], bool]
    is_capabilities_help_answer: Callable[[str], bool]
    answer_commit_persistence: Callable[..., None]
    utc_now_iso: Callable[[], str]
    obligation_timeout_seconds: int


def _default_runtime_capability_status() -> RuntimeCapabilityStatus:
    return RuntimeCapabilityStatus(
        ollama_available=True,
        ha_available=False,
        effective_mode="cli",
        requested_mode="cli",
        daemon_mode=False,
        fallback_reason=None,
        memory_backend="in_memory",
        debug_enabled=False,
        debug_verbose=False,
        text_clarification_available=True,
        satellite_ask_available=False,
    )


def _default_capability_snapshot(status: RuntimeCapabilityStatus) -> CapabilitySnapshot:
    return CapabilitySnapshot(
        runtime={},
        requested_mode=status.requested_mode,
        daemon_mode=status.daemon_mode,
        effective_mode=status.effective_mode,
        fallback_reason=status.fallback_reason,
        exit_reason=None,
        ha_error=None,
        ollama_error=None,
        runtime_capability_status=status,
    )


def run_canonical_answer_stage_flow_entrypoint(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    selected_decision=None,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
    deps: CanonicalRuntimeEntrypointDependencies,
) -> PipelineState:
    if selected_decision is not None:
        raise UnsupportedCompatibilityPathError(
            "selected_decision is not supported on canonical entrypoint; policy.decide stage is authoritative"
        )
    if timezone != "Europe/Helsinki":
        raise UnsupportedCompatibilityPathError(
            "timezone override is not supported on canonical entrypoint; canonical clock policy is authoritative"
        )

    class _SeededMemoryStore:
        def __init__(self, seeded_hits: list[Document]):
            self._seeded_hits = list(seeded_hits)

        def add_documents(self, documents: list[Document]) -> None:
            self._seeded_hits.extend(documents)

        def similarity_search_with_score(self, *_args, **_kwargs) -> list[tuple[Document, float]]:
            return [(doc, 1.0) for doc in self._seeded_hits]

    status = runtime_capability_status or deps.build_default_runtime_capability_status()
    snapshot = deps.build_capability_snapshot(status)
    seeded_state = replace(
        state,
        classified_intent=state.classified_intent or IntentType.KNOWLEDGE_QUESTION.value,
        resolved_intent=state.resolved_intent or "",
        confidence_decision=dict(state.confidence_decision),
    )
    final_state, _ = deps.run_canonical_turn_pipeline(
        runtime={},
        llm=llm,
        store=_SeededMemoryStore(hits),
        state=seeded_state,
        utterance=seeded_state.user_input,
        prior_pipeline_state=None,
        turn_id=str(uuid.uuid4()),
        near_tie_delta=0.05,
        chat_history=chat_history,
        capability_status=capability_status,
        capability_snapshot=snapshot,
        clock=clock or SystemClock(),
        io_channel="cli",
    )
    return final_state


def run_chat_loop_entrypoint(
    *,
    runtime: dict[str, object] | None = None,
    llm: ChatOllama,
    store: MemoryStore,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    io_channel: str,
    capability_status: CapabilityStatus,
    capability_snapshot: CapabilitySnapshot,
    read_user_utterance,
    send_assistant_text,
    clock: Clock,
    deps: CanonicalRuntimeEntrypointDependencies,
) -> None:
    runtime = runtime or {}
    runtime.setdefault("source_ingest_background_future", None)
    runtime.setdefault("source_ingest_background_in_progress", False)
    runtime.setdefault("source_ingest_background_request_id", "")
    runtime.setdefault("pending_ingestion_registry", {})
    runtime.setdefault("dead_letter_ingestion_registry", {})
    last_user_message_ts = ""
    prior_pipeline_state: PipelineState | None = None
    while True:
        deps.poll_pending_ingestion_obligations(runtime=runtime)
        last_user_message_ts, prior_pipeline_state, _ = deps.process_background_ingestion_completion(
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

        deps.append_session_log("user_utterance_ingest", {"channel": io_channel, "utterance": utterance})

        if utterance.lower() in {"stop", "quit", "exit"}:
            send_assistant_text("Stopping. Bye.")
            break

        state = PipelineState(
            user_input=utterance,
            last_user_message_ts=last_user_message_ts,
            classified_intent=IntentType.KNOWLEDGE_QUESTION.value,
            resolved_intent="",
            prior_unresolved_intent=(prior_pipeline_state.prior_unresolved_intent if prior_pipeline_state is not None else ""),
            confidence_decision={},
        )
        append_pipeline_snapshot("ingest", state, time_provider=_ClockBackedSnapshotTimeProvider(clock=clock))
        turn_id = str(uuid.uuid4())

        state, hits = deps.run_canonical_turn_pipeline(
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
        )

        ambiguity = deps.ambiguity_score(state.confidence_decision)
        chosen_action = str(state.invariant_decisions.get("fallback_action", "NONE"))
        followup_proxy = deps.user_followup_signal_proxy(
            final_answer=state.final_answer,
            fallback_action=chosen_action,
            ambiguity_score=ambiguity,
        )
        payload_base = {
            "ambiguity_score": ambiguity,
            "chosen_action": chosen_action,
            "user_followup_signal_proxy": followup_proxy,
        }
        deps.append_session_log("fallback_action_selected", deps.intent_telemetry_payload(state=state, utterance=utterance, extra=payload_base))
        deps.append_session_log(
            "provenance_summary",
            deps.intent_telemetry_payload(
                state=state,
                utterance=utterance,
                extra={
                    **payload_base,
                    "claims": state.claims,
                    "provenance_types": [p.value for p in state.provenance_types],
                    "used_memory_refs": state.used_memory_refs,
                    "used_source_evidence_refs": state.used_source_evidence_refs,
                    "source_evidence_attribution": state.source_evidence_attribution,
                    "basis_statement": state.basis_statement,
                },
            ),
        )
        deps.append_session_log(
            "alignment_decision_evaluated",
            deps.intent_telemetry_payload(
                state=state,
                utterance=utterance,
                extra={
                    "alignment_decision": state.alignment_decision.to_dict(),
                    "alignment_dimension_inputs_raw": state.alignment_decision.typed_dimension_inputs().get("raw", {}),
                    "alignment_dimension_inputs_normalized": state.alignment_decision.typed_dimension_inputs().get("normalized", {}),
                    "alignment_dimensions": dict(state.alignment_decision.dimensions),
                },
            ),
        )

        if capability_snapshot.runtime_capability_status.debug_enabled:
            debug_payload = deps.build_debug_turn_payload(state=state, intent_label=state.resolved_intent, hits=hits)
            debug_trace = deps.format_debug_turn_trace_payload(
                payload=debug_payload,
                verbose=capability_snapshot.runtime_capability_status.debug_verbose,
            )
            deps.append_session_log("debug_turn_trace", {"utterance": utterance, "payload": debug_payload, "trace": debug_trace})
            send_assistant_text(debug_trace)

        unresolved_intent = state.resolved_intent if deps.is_clarification_answer(state.final_answer) or deps.is_capabilities_help_answer(state.final_answer) else ""
        state = replace(state, prior_unresolved_intent=unresolved_intent)
        send_assistant_text(state.final_answer)

        pending_request_id = state.commit_receipt.pending_ingestion_request_id
        if pending_request_id:
            pending_registry = runtime.setdefault("pending_ingestion_registry", {})
            if isinstance(pending_registry, dict):
                now_iso = deps.utc_now_iso()
                deadline_at = arrow.get(now_iso).shift(seconds=deps.obligation_timeout_seconds).isoformat()
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
                deps.emit_obligation_transition(
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

        deps.answer_commit_persistence(
            llm=llm,
            store=store,
            state=state,
            io_channel=io_channel,
            clock=clock,
        )


__all__ = [
    "CanonicalRuntimeEntrypointDependencies",
    "UnsupportedCompatibilityPathError",
    "run_canonical_answer_stage_flow_entrypoint",
    "run_chat_loop_entrypoint",
]
