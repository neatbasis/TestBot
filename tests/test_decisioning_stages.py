from testbot.context_resolution import ContinuityPosture, resolve as resolve_context
from testbot.intent_resolution import resolve as resolve_intent
from testbot.intent_router import IntentType
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import EvidencePosture, decide
from testbot.sat_chatbot_memory_v2 import ROUTE_TO_ASK_ANSWER


def test_context_resolution_exposes_typed_continuity_inputs() -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=ROUTE_TO_ASK_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )

    context = resolve_context(utterance="yes", prior_pipeline_state=prior_state)

    assert context.prior_intent is IntentType.CAPABILITIES_HELP
    assert context.continuity_posture is ContinuityPosture.PRESERVE_PRIOR_INTENT
    assert "clarification_continuity" in context.history_anchors
    assert "short_affirmation" in context.ambiguity_flags


def test_intent_resolution_consumes_context_continuity_posture() -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=ROUTE_TO_ASK_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )

    affirmative = resolve_intent(utterance="yes", context=resolve_context(utterance="yes", prior_pipeline_state=prior_state))
    non_affirmative = resolve_intent(
        utterance="what is ontology?",
        context=resolve_context(utterance="what is ontology?", prior_pipeline_state=prior_state),
    )

    assert affirmative.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert affirmative.resolved_intent is IntentType.CAPABILITIES_HELP
    assert non_affirmative.resolved_intent is IntentType.KNOWLEDGE_QUESTION


def test_policy_decision_derives_empty_vs_scored_empty_posture() -> None:
    empty = decide(
        utterance="what is ontology?",
        intent=IntentType.KNOWLEDGE_QUESTION,
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    scored_empty = decide(
        utterance="what is ontology?",
        intent=IntentType.KNOWLEDGE_QUESTION,
        retrieval_candidates_considered=4,
        hit_count=0,
    )

    assert empty.retrieval_branch == "memory_retrieval"
    assert empty.evidence_posture is EvidencePosture.EMPTY_EVIDENCE
    assert scored_empty.evidence_posture is EvidencePosture.SCORED_EMPTY
