from __future__ import annotations

from dataclasses import dataclass

from testbot.answer_assembly import AnswerCandidate
from testbot.answer_commit import commit_answer_stage
from testbot.answer_rendering import RenderedAnswer, render_answer
from testbot.answer_validation import ValidatedAnswer
from testbot.candidate_encoding import encode_turn_candidates
from testbot.memory_strata import derive_segment_descriptor
from testbot.pipeline_state import PipelineState
from testbot.stabilization import stabilize_pre_route
from testbot.turn_observation import observe_turn


@dataclass
class SpyStoreDoc:
    call_log: list[str]

    def __call__(self, store, *, doc_id: str, content: str, metadata: dict[str, object]) -> None:
        doc_type = str(metadata.get("type") or "")
        self.call_log.append(f"store_doc:{doc_type}:{doc_id}")


def _observation(state: PipelineState, *, turn_id: str = "turn-001"):
    return observe_turn(
        state,
        turn_id=turn_id,
        observed_at="2026-03-15T10:00:00Z",
        speaker="user",
        channel="cli",
    )


def test_observe_turn_preserves_raw_fields_exactly() -> None:
    state = PipelineState(
        user_input="  keep spacing\nverbatim  ",
        classified_intent="memory_recall",
        resolved_intent="memory_recall",
    )

    observed = _observation(state)

    assert observed.turn_id == "turn-001"
    assert observed.utterance == state.user_input
    assert observed.observed_at == "2026-03-15T10:00:00Z"
    assert observed.speaker == "user"
    assert observed.channel == "cli"
    assert observed.classified_intent == state.classified_intent
    assert observed.resolved_intent == state.resolved_intent


def test_encode_candidates_keeps_multiplicity_without_collapsing_candidate_classes() -> None:
    state = PipelineState(user_input="My name is Ava?")
    observed = _observation(state)

    encoded = encode_turn_candidates(state, observation=observed, rewritten_query="my name is ava")

    assert encoded.rewritten_query == "my name is ava"
    assert len(encoded.speech_acts) == 1
    assert len(encoded.facts) == 1
    assert len(encoded.dialogue_state) == 1
    assert encoded.speech_acts[0].label == "query"
    assert encoded.facts[0].key == "user_name"
    assert encoded.facts[0].value == "Ava"
    assert encoded.dialogue_state[0].label == "self_identification"


def test_stabilize_pre_route_persists_utterance_before_downstream_decision_logic() -> None:
    state = PipelineState(user_input="hello")
    observed = _observation(state, turn_id="turn-002")
    encoded = encode_turn_candidates(state, observation=observed, rewritten_query="hello")
    segment = derive_segment_descriptor(utterance=observed.utterance, has_dialogue_state=bool(encoded.dialogue_state))

    call_log: list[str] = []
    store_spy = SpyStoreDoc(call_log)
    _, stabilized = stabilize_pre_route(
        store=None,  # type: ignore[arg-type]
        state=state,
        observation=observed,
        encoded=encoded,
        response_plan={"pathway": "contract_test"},
        reflection_yaml="offline: true",
        segment=segment,
        store_doc_fn=store_spy,
    )
    call_log.append(f"decision_logic:{stabilized.turn_id}")

    assert call_log[0] == "store_doc:user_utterance:turn-002"
    assert call_log[-1] == "decision_logic:turn-002"


def test_answer_render_invalid_validation_routes_to_explicit_degraded_contract_without_semantic_text() -> None:
    assembly = AnswerCandidate(
        decision_class="answer_from_memory",
        rendered_class="answer_from_memory",
        retrieval_branch="memory_retrieval",
        rationale="test",
        evidence_counts={"structured_facts": 1},
        pending_repair_state={"repair_required_by_policy": False, "repair_offered_to_user": False},
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=[],
        confirmed_user_facts=[],
    )
    invalid = ValidatedAnswer(passed=False, failures=["invalid"], final_answer="Sensitive semantic text")

    rendered = render_answer(assembly=assembly, validation=invalid, preferred_text=invalid.final_answer)

    assert rendered.degraded_response is True
    assert rendered.response_contract in {"degraded_targeted_clarifier", "degraded_capability_alternatives"}
    assert rendered.rendered_text.startswith("[degraded:")
    assert "Sensitive semantic text" not in rendered.rendered_text


def test_answer_commit_merges_stabilized_facts_once_per_fact_without_duplicate_commit_effects() -> None:
    state = PipelineState(
        user_input="My name is Ava",
        candidate_facts={
            "turn_id": "turn-003",
            "facts": [{"key": "user_name", "value": "Ava"}],
        },
    )
    assembly = AnswerCandidate(
        decision_class="answer_from_memory",
        rendered_class="answer_from_memory",
        retrieval_branch="memory_retrieval",
        rationale="test",
        evidence_counts={"structured_facts": 1},
        pending_repair_state={"repair_required_by_policy": False, "repair_offered_to_user": False},
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=[],
        confirmed_user_facts=["timezone=UTC"],
    )
    validation = ValidatedAnswer(passed=True, failures=[], final_answer="All good")

    committed_state, committed = commit_answer_stage(
        state,
        assembly=assembly,
        validation=validation,
        rendered=RenderedAnswer(rendered_text="All good"),
    )

    assert committed.turn_id == "turn-003"
    assert committed_state.commit_receipt["commit_stage"] == "answer.commit"
    assert committed.confirmed_user_facts == ["timezone=UTC", "name=Ava"]
    assert committed.confirmed_user_facts.count("timezone=UTC") == 1
    assert committed.confirmed_user_facts.count("name=Ava") == 1


def test_answer_render_invalid_validation_uses_deny_fallback_only_for_explicit_deny_safety() -> None:
    assembly = AnswerCandidate(
        decision_class="answer_from_memory",
        rendered_class="answer_from_memory",
        retrieval_branch="memory_retrieval",
        rationale="test",
        evidence_counts={"structured_facts": 1},
        pending_repair_state={"repair_required_by_policy": False, "repair_offered_to_user": False},
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=[],
        confirmed_user_facts=[],
    )
    invalid = ValidatedAnswer(
        passed=False,
        failures=["invalid"],
        final_answer="Sensitive semantic text",
        invariant_decisions={"answer_mode": "deny"},
    )

    rendered = render_answer(assembly=assembly, validation=invalid, preferred_text=invalid.final_answer)

    assert rendered.degraded_response is True
    assert rendered.response_contract == "degraded_deny_safety_only"
    assert rendered.rendered_text == "[degraded:deny] I don't know from memory."


def test_answer_render_invalid_validation_prefers_clarifier_for_clarification_decision_class() -> None:
    assembly = AnswerCandidate(
        decision_class="ask_for_clarification",
        rendered_class="ask_for_clarification",
        retrieval_branch="memory_retrieval",
        rationale="test",
        evidence_counts={"structured_facts": 0},
        pending_repair_state={"repair_required_by_policy": False, "repair_offered_to_user": False},
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=[],
        confirmed_user_facts=[],
    )
    invalid = ValidatedAnswer(passed=False, failures=["invalid"], final_answer="Sensitive semantic text")

    rendered = render_answer(assembly=assembly, validation=invalid, preferred_text=invalid.final_answer)

    assert rendered.degraded_response is True
    assert rendered.response_contract == "degraded_targeted_clarifier"
    assert "Which specific detail should I focus on first?" in rendered.rendered_text
    assert "Sensitive semantic text" not in rendered.rendered_text
