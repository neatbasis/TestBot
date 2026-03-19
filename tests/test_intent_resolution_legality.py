from testbot.context_resolution import ContinuityPosture, ResolvedContext
from testbot.intent_resolution import IntentResolutionInput, resolve
from testbot.intent_router import IntentFacets, IntentType, validate_intent_facet_legality
from testbot.stabilization import StabilizedTurnState
from testbot.candidate_encoding import FactCandidate


def _stabilized(utterance: str) -> StabilizedTurnState:
    return StabilizedTurnState(
        turn_id="t-1",
        utterance_card="u",
        utterance_doc_id="u-1",
        reflection_doc_id="r-1",
        dialogue_state_doc_id="d-1",
        segment_type="contiguous_topic",
        segment_id="seg-1",
        segment_membership_edge_refs=[],
        same_turn_exclusion_doc_ids=[],
        candidate_facts=[FactCandidate(key="utterance_raw", value=utterance, confidence=1.0)],
        candidate_speech_acts=[],
        candidate_dialogue_state=[],
    )


def test_validate_intent_facet_legality_rejects_invalid_combo() -> None:
    result = validate_intent_facet_legality(
        IntentType.CAPABILITIES_HELP,
        IntentFacets(temporal=False, memory=False, capability=False, control=False),
    )
    assert result.valid is False
    assert result.reason == "capabilities_help_requires_capability"


def test_intent_resolution_continuity_override_allows_capabilities_followup() -> None:
    resolved = resolve(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized("what is ontology?"),
            context=ResolvedContext(
                history_anchors=("commit.pending_repair_state:repair_offered_to_user",),
                ambiguity_flags=(),
                continuity_posture=ContinuityPosture.REEVALUATE,
                prior_intent=IntentType.CAPABILITIES_HELP,
            ),
            fallback_utterance="what is ontology?",
        )
    )

    assert resolved.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert resolved.resolved_intent is IntentType.CAPABILITIES_HELP
    assert resolved.conflicts == ()


def test_intent_resolution_records_conflict_when_control_classification_overrides() -> None:
    resolved = resolve(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized("stop"),
            context=ResolvedContext(
                history_anchors=(),
                ambiguity_flags=(),
                continuity_posture=ContinuityPosture.PRESERVE_PRIOR_INTENT,
                prior_intent=IntentType.MEMORY_RECALL,
            ),
            fallback_utterance="stop",
        )
    )

    assert resolved.classified_intent is IntentType.CONTROL
    assert resolved.resolved_intent is IntentType.CONTROL
    assert "classified_control_overrides_resolved" in resolved.conflicts
