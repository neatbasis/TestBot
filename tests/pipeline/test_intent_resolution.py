from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pytest

from testbot.candidate_encoding import FactCandidate
from testbot.context_resolution import resolve as resolve_context
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.intent_router import IntentFacets, IntentType, classify_intent, extract_intent_facets
from testbot.pipeline_state import PipelineState
from testbot.stabilization import StabilizedTurnState


class IntentClass(str, Enum):
    KNOWLEDGE_QUESTION = IntentType.KNOWLEDGE_QUESTION.value
    META_CONVERSATION = IntentType.META_CONVERSATION.value
    CAPABILITIES_HELP = IntentType.CAPABILITIES_HELP.value
    MEMORY_RECALL = IntentType.MEMORY_RECALL.value
    TIME_QUERY = IntentType.TIME_QUERY.value
    CONTROL = IntentType.CONTROL.value


@dataclass(frozen=True)
class InterpretedIntent:
    resolved_intent: IntentClass
    facets: IntentFacets

    def validate(self) -> list[str]:
        violations: list[str] = []
        if self.resolved_intent is IntentClass.CONTROL:
            if not self.facets.control:
                violations.append("control intent requires control=true")
            if self.facets.temporal or self.facets.memory or self.facets.capability:
                violations.append("control intent cannot set temporal/memory/capability")
        elif self.resolved_intent is IntentClass.TIME_QUERY:
            if not self.facets.temporal:
                violations.append("time_query requires temporal=true")
            if self.facets.control:
                violations.append("time_query cannot set control=true")
        elif self.resolved_intent is IntentClass.MEMORY_RECALL:
            if not self.facets.memory:
                violations.append("memory_recall requires memory=true")
            if self.facets.control:
                violations.append("memory_recall cannot set control=true")
        elif self.resolved_intent is IntentClass.CAPABILITIES_HELP:
            if not self.facets.capability:
                violations.append("capabilities_help requires capability=true")
            if self.facets.control or self.facets.temporal or self.facets.memory:
                violations.append("capabilities_help cannot set control/temporal/memory")
        elif self.resolved_intent is IntentClass.META_CONVERSATION:
            if self.facets.control or self.facets.temporal or self.facets.memory:
                violations.append("meta_conversation cannot set control/temporal/memory")
        elif self.resolved_intent is IntentClass.KNOWLEDGE_QUESTION:
            if self.facets.control:
                violations.append("knowledge_question cannot set control=true")
        return violations

    @classmethod
    def from_utterance(cls, utterance: str, *, force_invalid_intent: str | None = None) -> "InterpretedIntent":
        classified = classify_intent(utterance)
        facets = extract_intent_facets(utterance)

        if force_invalid_intent is not None:
            raw_intent = force_invalid_intent
        else:
            raw_intent = classified.value

        try:
            resolved = IntentClass(raw_intent)
        except ValueError:
            resolved = IntentClass.KNOWLEDGE_QUESTION

        return cls(resolved_intent=resolved, facets=facets)


def _stabilized(utterance: str) -> StabilizedTurnState:
    return StabilizedTurnState(
        turn_id="turn-1",
        utterance_card="UTTERANCE CARD",
        utterance_doc_id="u1",
        reflection_doc_id="r1",
        dialogue_state_doc_id="d1",
        segment_type="episodic",
        segment_id="seg-1",
        segment_membership_edge_refs=[],
        same_turn_exclusion_doc_ids=[],
        candidate_facts=[FactCandidate(key="utterance_raw", value=utterance, confidence=1.0)],
        candidate_speech_acts=[],
        candidate_dialogue_state=[],
        candidate_repairs=[],
    )


@pytest.mark.parametrize(
    ("utterance", "expected"),
    [
        ("use satellite; how many minutes ago did we talk?", IntentType.TIME_QUERY),
        ("stop and use satellite route please", IntentType.CONTROL),
        ("STOP and what did I ask before?", IntentType.CONTROL),
        ("How Many Minutes Ago did we talk before?", IntentType.TIME_QUERY),
    ],
)
def test_overlap_utterances_follow_canonical_precedence(utterance: str, expected: IntentType) -> None:
    assert classify_intent(utterance) is expected


@pytest.mark.parametrize("utterance", ["", "   ", "...?!"])
def test_edge_cases_fall_back_to_knowledge_question(utterance: str) -> None:
    assert classify_intent(utterance) is IntentType.KNOWLEDGE_QUESTION


def test_repair_offer_continuity_supersedes_knowledge_route_words() -> None:
    prior_state = PipelineState(
        user_input="What is ontology?",
        final_answer="I can look that up if you want.",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        prior_unresolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        commit_receipt={
            "committed": True,
            "commit_id": "commit-1",
            "pending_repair_state": {
                "repair_required_by_policy": False,
                "repair_offered_to_user": True,
            },
        },
    )
    utterance = "Define this route for me"
    context = resolve_context(utterance=utterance, prior_pipeline_state=prior_state)
    resolved = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized(utterance),
            context=context,
            fallback_utterance=utterance,
        )
    )

    assert resolved.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert resolved.resolved_intent is IntentType.CAPABILITIES_HELP


@pytest.mark.parametrize(
    ("intent", "facets", "expected_fragment"),
    [
        (
            IntentClass.CONTROL,
            IntentFacets(control=True, temporal=True, memory=True, capability=True),
            "cannot set temporal/memory/capability",
        ),
        (
            IntentClass.CAPABILITIES_HELP,
            IntentFacets(capability=True, temporal=True),
            "cannot set control/temporal/memory",
        ),
        (
            IntentClass.TIME_QUERY,
            IntentFacets(temporal=False),
            "requires temporal=true",
        ),
    ],
)
def test_interpreted_intent_validate_enforces_facet_contracts(
    intent: IntentClass,
    facets: IntentFacets,
    expected_fragment: str,
) -> None:
    interpreted = InterpretedIntent(resolved_intent=intent, facets=facets)

    violations = interpreted.validate()

    assert violations
    assert any(expected_fragment in violation for violation in violations)


def test_taxonomy_violation_falls_back_to_knowledge_question() -> None:
    interpreted = InterpretedIntent.from_utterance(
        "WHAT can you do?",
        force_invalid_intent="not_a_valid_intent",
    )

    assert interpreted.resolved_intent is IntentClass.KNOWLEDGE_QUESTION
