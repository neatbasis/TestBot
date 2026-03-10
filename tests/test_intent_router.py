from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER, resolve_turn_intent
from testbot.intent_router import IntentType, classify_intent, extract_intent_facets, planning_pathway_for_intent
from testbot.evidence_retrieval import EvidenceBundle, EvidenceRecord, retrieval_result
from testbot.policy_decision import DecisionClass, decide_from_evidence
import pytest


def test_classify_intent_memory_recall_ambiguous_what_did_i_ask() -> None:
    assert classify_intent("what did I ask?") is IntentType.MEMORY_RECALL


def test_classify_intent_meta_conversation_relevance_prompt() -> None:
    assert classify_intent("what's relevant to our conversation?") is IntentType.META_CONVERSATION


def test_classify_intent_knowledge_question_ontology() -> None:
    assert classify_intent("what is ontology?") is IntentType.KNOWLEDGE_QUESTION


def test_classify_intent_control_takes_precedence() -> None:
    assert classify_intent("stop and what did I ask?") is IntentType.CONTROL


def test_classify_intent_time_query_minutes_ago() -> None:
    assert classify_intent("how many minutes ago did I ask?") is IntentType.TIME_QUERY


def test_classify_intent_time_query_tomorrow() -> None:
    assert classify_intent("what is tomorrow?") is IntentType.TIME_QUERY


def test_classify_intent_time_query_takes_precedence_over_memory_recall() -> None:
    assert classify_intent("how many days ago did we talk before?") is IntentType.TIME_QUERY


def test_classify_intent_capabilities_help_what_can_you_do() -> None:
    assert classify_intent("what can you do") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_help() -> None:
    assert classify_intent("help") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_capabilities() -> None:
    assert classify_intent("capabilities") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_satellite_overrides_meta_phrase() -> None:
    assert classify_intent("use satellite about this chat") is IntentType.CAPABILITIES_HELP


def test_classify_intent_knowledge_question_when_is_prompt() -> None:
    assert classify_intent("when is my next utility event?") is IntentType.KNOWLEDGE_QUESTION


def test_classify_intent_meta_conversation_relevance_summary() -> None:
    assert classify_intent("summarize our conversation") is IntentType.META_CONVERSATION


def test_classify_intent_empty_or_none_falls_back_to_knowledge_question() -> None:
    assert classify_intent("") is IntentType.KNOWLEDGE_QUESTION
    assert classify_intent(None) is IntentType.KNOWLEDGE_QUESTION


def test_classify_intent_profile_update_i_am_routes_non_knowledge() -> None:
    assert classify_intent("I am Alex") is IntentType.META_CONVERSATION


def test_classify_intent_profile_update_im_routes_non_knowledge() -> None:
    assert classify_intent("I'm Sam") is IntentType.META_CONVERSATION


def test_classify_intent_profile_update_my_name_is_routes_non_knowledge() -> None:
    assert classify_intent("my name is Jordan") is IntentType.META_CONVERSATION


def test_classify_intent_social_greeting_routes_non_knowledge() -> None:
    assert classify_intent("hello") is IntentType.META_CONVERSATION
    assert classify_intent("hi!") is IntentType.META_CONVERSATION


def test_classify_intent_say_hello_routes_to_command_intent() -> None:
    assert classify_intent("say hello") is IntentType.CONTROL


def test_classify_intent_note_taking_request_routes_non_knowledge() -> None:
    assert classify_intent("please make a note that i prefer tea") is IntentType.META_CONVERSATION


def test_classify_intent_memory_write_request_routes_non_knowledge() -> None:
    assert classify_intent("remember this: i parked on level 3") is IntentType.META_CONVERSATION

def test_resolve_turn_intent_affirmation_inherits_prior_clarification_intent() -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=CLARIFY_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )

    classified, resolved = resolve_turn_intent(utterance="yes", prior_pipeline_state=prior_state)

    assert classified is IntentType.KNOWLEDGE_QUESTION
    assert resolved is IntentType.CAPABILITIES_HELP


def test_resolve_turn_intent_affirmation_with_punctuation_inherits_prior_route_to_ask_intent() -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=ROUTE_TO_ASK_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )

    classified, resolved = resolve_turn_intent(utterance="okay!", prior_pipeline_state=prior_state)

    assert classified is IntentType.KNOWLEDGE_QUESTION
    assert resolved is IntentType.CAPABILITIES_HELP


def test_resolve_turn_intent_ontology_does_not_inherit_prior_clarification_intent() -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=CLARIFY_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )

    classified, resolved = resolve_turn_intent(utterance="what is ontology?", prior_pipeline_state=prior_state)

    assert classified is IntentType.KNOWLEDGE_QUESTION
    assert resolved is IntentType.KNOWLEDGE_QUESTION


def test_resolve_turn_intent_invalid_prior_intent_does_not_override_classification() -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=CLARIFY_ANSWER,
        resolved_intent="unsupported_intent",
        prior_unresolved_intent="unsupported_intent",
    )

    classified, resolved = resolve_turn_intent(utterance="yes", prior_pipeline_state=prior_state)

    assert classified is IntentType.KNOWLEDGE_QUESTION
    assert resolved is IntentType.KNOWLEDGE_QUESTION




def test_resolve_turn_intent_requires_diagnostic_only_mode() -> None:
    prior_state = PipelineState(user_input="who am i")

    with pytest.raises(RuntimeError, match="diagnostic-only and non-authoritative"):
        resolve_turn_intent(
            utterance="Who am I?",
            prior_pipeline_state=prior_state,
            diagnostic_only=False,
        )

def test_classify_intent_capabilities_help_ask_via_satellite() -> None:
    assert classify_intent("ask via satellite") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_use_satellite() -> None:
    assert classify_intent("use satellite") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_start_satellite_conversation() -> None:
    assert classify_intent("start satellite conversation") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_repair_offer_followup_family() -> None:
    for utterance in (
        "please look up the definition",
        "go ahead",
        "please do",
        "look it up",
        "find the definition",
    ):
        assert classify_intent(utterance) is IntentType.CAPABILITIES_HELP


def test_extract_intent_facets_for_temporal_memory_mixed_utterance() -> None:
    facets = extract_intent_facets("how many minutes ago did we talk before?")

    assert facets.temporal is True
    assert facets.memory is True
    assert facets.capability is False
    assert facets.control is False


def test_extract_intent_facets_for_capabilities_in_context_utterance() -> None:
    utterance = "what is ontology with satellite context?"

    assert classify_intent(utterance) is IntentType.KNOWLEDGE_QUESTION
    facets = extract_intent_facets(utterance)

    assert facets.capability is True
    assert facets.temporal is False


def test_extract_intent_facets_for_memory_and_capability_mixed_utterance() -> None:
    utterance = "can you help me remember our satellite context?"

    assert classify_intent(utterance) is IntentType.MEMORY_RECALL
    facets = extract_intent_facets(utterance)

    assert facets.memory is True
    assert facets.capability is True


def test_policy_decision_object_general_knowledge_for_scored_empty() -> None:
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=3,
        hit_count=0,
    )

    decision = decide_from_evidence(intent=IntentType.KNOWLEDGE_QUESTION, retrieval=retrieval)

    assert decision.decision_class is DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED
    assert decision.reasoning["scored_empty"] is True


def test_policy_decision_object_general_knowledge_for_empty_evidence_knowledge_question() -> None:
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )

    decision = decide_from_evidence(intent=IntentType.KNOWLEDGE_QUESTION, retrieval=retrieval)

    assert decision.decision_class is DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED
    assert decision.reasoning["empty_evidence"] is True


def test_policy_decision_object_memory_recall_scored_empty_prefers_clarification_over_general_knowledge() -> None:
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=3,
        hit_count=0,
    )

    decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=retrieval)

    assert decision.decision_class is DecisionClass.ASK_FOR_CLARIFICATION
    assert decision.retrieval_branch == "memory_retrieval"
    assert decision.reasoning["scored_empty"] is True
    assert decision.reasoning["empty_vs_scored"] == "scored_empty"



def test_policy_decision_object_memory_recall_empty_evidence_preserves_memory_branch_and_reason_code() -> None:
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )

    decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=retrieval)

    assert decision.decision_class is DecisionClass.ASK_FOR_CLARIFICATION
    assert decision.retrieval_branch == "memory_retrieval"
    assert decision.reasoning["empty_evidence"] is True
    assert decision.reasoning["empty_vs_scored"] == "empty_evidence"


def test_policy_decision_object_meta_conversation_not_requested_uses_assistive_direct_answer_decision() -> None:
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )

    decision = decide_from_evidence(intent=IntentType.META_CONVERSATION, retrieval=retrieval)

    assert decision.decision_class is DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED
    assert decision.retrieval_branch == "direct_answer"

def test_policy_decision_object_memory_answer_for_scored_non_empty() -> None:
    bundle = EvidenceBundle(structured_facts=(EvidenceRecord(ref_id="fact-1", score=0.9, content="user_name=Sam"),))
    retrieval = retrieval_result(
        evidence_bundle=bundle,
        retrieval_candidates_considered=2,
        hit_count=1,
    )
    decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=retrieval)

    assert decision.decision_class is DecisionClass.ANSWER_FROM_MEMORY


def test_extract_intent_facets_control_is_exclusive() -> None:
    facets = extract_intent_facets("stop, can you help me remember what did I ask?")

    assert facets.control is True
    assert facets.memory is False
    assert facets.capability is False
    assert facets.temporal is False


def test_planning_pathway_control_precedence_over_capability_facet() -> None:
    descriptor = planning_pathway_for_intent(
        IntentType.CONTROL,
        extract_intent_facets("stop and use satellite"),
    )

    assert descriptor.pathway == "control"
