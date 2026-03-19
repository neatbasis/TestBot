from __future__ import annotations

import inspect

from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import ValidatedAnswer
from testbot.candidate_encoding import EncodedTurnCandidates, FactCandidate, SpeechActCandidate
from testbot.context_resolution import ContinuityPosture, ResolvedContext
from testbot.domain import (
    CandidateEncodingSet,
    ContextResolvedState,
    EvidenceSet,
    PolicyDecision,
    PreRouteState,
    RenderedResponse,
    ValidationResult,
    candidate_encoding_set_from_encoded_turn_candidates,
    context_resolved_state_from_resolved_context,
    evidence_set_from_evidence_bundle,
    policy_decision_from_decision_object,
    pre_route_state_from_stabilized_turn_state,
    rendered_response_from_rendered_answer,
    validation_result_from_validated_answer,
)
from testbot.evidence_retrieval import EvidenceBundle, EvidenceRecord
from testbot.policy_decision import DecisionClass, DecisionObject
from testbot.stabilization import StabilizedTurnState


def test_candidate_encoding_set_has_explicit_constructor_and_legacy_adapter() -> None:
    legacy = EncodedTurnCandidates(
        rewritten_query="who am i",
        speech_acts=[SpeechActCandidate(label="query", confidence=0.9, rationale="question_mark")],
        facts=[FactCandidate(key="user_name", value="Ada", confidence=0.95)],
    )

    canonical = candidate_encoding_set_from_encoded_turn_candidates(legacy)
    assert canonical.rewritten_query == "who am i"
    assert canonical.facts[0].key == "user_name"
    assert canonical.to_encoded_turn_candidates() == legacy


def test_pre_route_state_has_explicit_constructor_and_legacy_adapter() -> None:
    legacy = StabilizedTurnState(
        turn_id="turn-1",
        utterance_card="card",
        utterance_doc_id="u1",
        reflection_doc_id="r1",
        dialogue_state_doc_id="d1",
        segment_type="dialogue",
        segment_id="seg-1",
        segment_membership_edge_refs=["edge-1"],
        same_turn_exclusion_doc_ids=["u1", "r1", "d1"],
        candidate_facts=[FactCandidate(key="foo", value="bar", confidence=0.8)],
        candidate_speech_acts=[SpeechActCandidate(label="inform", confidence=0.6, rationale="default")],
        candidate_dialogue_state=[],
    )

    canonical = pre_route_state_from_stabilized_turn_state(legacy)
    assert canonical.segment_membership_edge_refs == ("edge-1",)
    assert canonical.to_stabilized_turn_state() == legacy


def test_context_resolved_state_has_explicit_constructor_and_legacy_adapter() -> None:
    legacy = ResolvedContext(
        history_anchors=("prior_intent:memory_recall",),
        ambiguity_flags=("short_affirmation",),
        continuity_posture=ContinuityPosture.PRESERVE_PRIOR_INTENT,
        prior_intent=None,
    )

    canonical = context_resolved_state_from_resolved_context(legacy)
    assert canonical.history_anchors == legacy.history_anchors
    assert canonical.to_resolved_context() == legacy


def test_evidence_set_has_explicit_constructor_and_legacy_adapter() -> None:
    record = EvidenceRecord(ref_id="doc-1", score=1.0, content="hello")
    legacy = EvidenceBundle(structured_facts=(record,))

    canonical = evidence_set_from_evidence_bundle(legacy)
    assert canonical.structured_facts[0].ref_id == "doc-1"
    assert canonical.to_evidence_bundle() == legacy


def test_policy_decision_has_explicit_constructor_and_legacy_adapter() -> None:
    legacy = DecisionObject(
        decision_class=DecisionClass.ANSWER_FROM_MEMORY,
        retrieval_branch="memory_retrieval",
        rationale="has evidence",
    )

    canonical = policy_decision_from_decision_object(legacy)
    assert canonical.decision_class == DecisionClass.ANSWER_FROM_MEMORY
    assert canonical.to_decision_object() == legacy


def test_validation_result_has_explicit_constructor_and_legacy_adapter() -> None:
    legacy = ValidatedAnswer(passed=True, failures=[], final_answer="ok")

    canonical = validation_result_from_validated_answer(legacy)
    assert canonical.passed is True
    assert canonical.to_validated_answer() == legacy


def test_rendered_response_has_explicit_constructor_and_legacy_adapter() -> None:
    legacy = RenderedAnswer(rendered_text="hello", response_contract="validated_normal")

    canonical = rendered_response_from_rendered_answer(legacy)
    assert canonical.rendered_text == "hello"
    assert canonical.to_rendered_answer() == legacy


def test_canonical_dtos_do_not_require_ad_hoc_dict_constructor_fields() -> None:
    signatures = {
        CandidateEncodingSet: inspect.signature(CandidateEncodingSet),
        PreRouteState: inspect.signature(PreRouteState),
        ContextResolvedState: inspect.signature(ContextResolvedState),
        EvidenceSet: inspect.signature(EvidenceSet),
        PolicyDecision: inspect.signature(PolicyDecision),
        ValidationResult: inspect.signature(ValidationResult),
        RenderedResponse: inspect.signature(RenderedResponse),
    }

    for signature in signatures.values():
        for param in signature.parameters.values():
            assert param.kind not in {inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL}
