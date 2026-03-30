from __future__ import annotations

from types import SimpleNamespace

from testbot.entrypoints.runtime_turn_telemetry import (
    RuntimeTurnTelemetryDependencies,
    emit_runtime_turn_telemetry,
    intent_telemetry_payload,
    user_followup_signal_proxy,
)
from testbot.sat_chatbot_memory_v2 import _intent_telemetry_payload, _user_followup_signal_proxy


class _AlignmentDecisionStub:
    dimensions = {"grounding": 1.0}

    def to_dict(self) -> dict[str, object]:
        return {"decision": "allow"}

    def typed_dimension_inputs(self) -> dict[str, dict[str, object]]:
        return {"raw": {"grounding": 1.0}, "normalized": {"grounding": 1.0}}


def _deps(events: list[tuple[str, dict[str, object]]]) -> RuntimeTurnTelemetryDependencies:
    return RuntimeTurnTelemetryDependencies(
        append_session_log=lambda event, payload: events.append((event, payload)),
        intent_telemetry_payload=lambda *, state, utterance=None, extra=None: {
            "intent": state.resolved_intent,
            "utterance": utterance,
            **(extra or {}),
        },
        ambiguity_score=lambda _decision: 0.42,
        user_followup_signal_proxy=lambda **_kwargs: "low",
        build_debug_turn_payload=lambda **_kwargs: {"debug": True},
        format_debug_turn_trace_payload=lambda *, payload, verbose=False: f"trace:{payload['debug']}:{verbose}",
    )


def _state() -> object:
    return SimpleNamespace(
        confidence_decision={"context_confident": True},
        invariant_decisions={"fallback_action": "NONE"},
        final_answer="Grounded",
        claims=["claim"],
        provenance_types=[SimpleNamespace(value="memory")],
        used_memory_refs=["m1"],
        used_source_evidence_refs=["s1"],
        source_evidence_attribution=[{"ref_id": "s1"}],
        basis_statement="memory evidence",
        alignment_decision=_AlignmentDecisionStub(),
        resolved_intent="knowledge_question",
        classified_intent="knowledge_question",
    )


def test_emit_runtime_turn_telemetry_emits_core_turn_events_without_debug() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    sent: list[str] = []

    emit_runtime_turn_telemetry(
        state=_state(),
        utterance="What changed?",
        hits=[],
        capability_snapshot=SimpleNamespace(
            runtime_capability_status=SimpleNamespace(debug_enabled=False, debug_verbose=False)
        ),
        send_assistant_text=sent.append,
        deps=_deps(events),
    )

    assert [event for event, _payload in events] == [
        "fallback_action_selected",
        "provenance_summary",
        "alignment_decision_evaluated",
    ]
    assert sent == []


def test_emit_runtime_turn_telemetry_emits_debug_trace_when_enabled() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    sent: list[str] = []

    emit_runtime_turn_telemetry(
        state=_state(),
        utterance="What changed?",
        hits=[],
        capability_snapshot=SimpleNamespace(
            runtime_capability_status=SimpleNamespace(debug_enabled=True, debug_verbose=True)
        ),
        send_assistant_text=sent.append,
        deps=_deps(events),
    )

    assert [event for event, _payload in events][-1] == "debug_turn_trace"
    assert sent == ["trace:True:True"]


def test_intent_telemetry_payload_is_canonical_for_runtime_turn_telemetry() -> None:
    state = _state()

    payload = intent_telemetry_payload(
        state=state,
        utterance="What changed?",
        extra={"ambiguity_score": 0.42},
    )

    assert payload == {
        "intent": "knowledge_question",
        "intent_classified": "knowledge_question",
        "intent_resolved": "knowledge_question",
        "utterance": "What changed?",
        "ambiguity_score": 0.42,
    }


def test_sat_runtime_intent_payload_wrapper_matches_runtime_telemetry_owner() -> None:
    state = _state()

    assert _intent_telemetry_payload(state=state, utterance="U", extra={"x": 1}) == intent_telemetry_payload(
        state=state,
        utterance="U",
        extra={"x": 1},
    )


def test_sat_runtime_followup_wrapper_matches_runtime_telemetry_owner() -> None:
    kwargs = {
        "final_answer": "I can disambiguate this with a quick follow-up question.",
        "fallback_action": "NONE",
        "ambiguity_score": 0.3,
    }

    assert _user_followup_signal_proxy(**kwargs) == user_followup_signal_proxy(**kwargs)
