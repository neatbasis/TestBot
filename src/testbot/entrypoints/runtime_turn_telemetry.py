"""Canonical runtime-owned turn telemetry/debug emission helpers.

Ownership:
- This module is the canonical owner for loop-level telemetry/debug emission
  wiring used by runtime loop entrypoints.
- Compatibility façades may delegate helper implementations via dependency
  injection during retirement windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from langchain_core.documents import Document

from testbot.answer_contract_constants import CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER
from testbot.pipeline_state import PipelineState


def intent_telemetry_payload(
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


def user_followup_signal_proxy(*, final_answer: str, fallback_action: str, ambiguity_score: float) -> float:
    if final_answer in {CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER}:
        return 1.0
    if fallback_action in {"ASK_CLARIFYING_QUESTION", "ROUTE_TO_ASK"}:
        return 0.9
    if fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        return round(max(0.2, ambiguity_score), 4)
    return round(max(0.0, ambiguity_score * 0.5), 4)


@dataclass(frozen=True)
class RuntimeTurnTelemetryDependencies:
    append_session_log: Callable[[str, dict[str, object]], None]
    intent_telemetry_payload: Callable[..., dict[str, object]]
    ambiguity_score: Callable[[dict[str, object]], float]
    user_followup_signal_proxy: Callable[..., object]
    build_debug_turn_payload: Callable[..., dict[str, object]]
    format_debug_turn_trace_payload: Callable[..., str]


def emit_runtime_turn_telemetry(
    *,
    state: PipelineState,
    utterance: str,
    hits: list[Document],
    capability_snapshot: object,
    send_assistant_text: Callable[[str], None],
    deps: RuntimeTurnTelemetryDependencies,
) -> None:
    ambiguity_score = deps.ambiguity_score(state.confidence_decision)
    chosen_action = str(state.invariant_decisions.get("fallback_action", "NONE"))
    followup_proxy = deps.user_followup_signal_proxy(
        final_answer=state.final_answer,
        fallback_action=chosen_action,
        ambiguity_score=ambiguity_score,
    )

    deps.append_session_log(
        "fallback_action_selected",
        deps.intent_telemetry_payload(
            state=state,
            utterance=utterance,
            extra={
                "ambiguity_score": ambiguity_score,
                "chosen_action": chosen_action,
                "user_followup_signal_proxy": followup_proxy,
            },
        ),
    )
    deps.append_session_log(
        "provenance_summary",
        deps.intent_telemetry_payload(
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
    deps.append_session_log(
        "alignment_decision_evaluated",
        deps.intent_telemetry_payload(
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
        debug_payload = deps.build_debug_turn_payload(
            state=state,
            intent_label=state.resolved_intent,
            hits=hits,
        )
        debug_trace = deps.format_debug_turn_trace_payload(
            payload=debug_payload,
            verbose=capability_snapshot.runtime_capability_status.debug_verbose,
        )
        deps.append_session_log(
            "debug_turn_trace",
            {
                "utterance": utterance,
                "payload": debug_payload,
                "trace": debug_trace,
            },
        )
        send_assistant_text(debug_trace)


__all__ = [
    "RuntimeTurnTelemetryDependencies",
    "emit_runtime_turn_telemetry",
    "intent_telemetry_payload",
    "user_followup_signal_proxy",
]
