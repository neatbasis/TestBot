from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER, resolve_turn_intent
from testbot.intent_router import IntentType, classify_intent


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


def test_classify_intent_capabilities_help_ask_via_satellite() -> None:
    assert classify_intent("ask via satellite") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_use_satellite() -> None:
    assert classify_intent("use satellite") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_start_satellite_conversation() -> None:
    assert classify_intent("start satellite conversation") is IntentType.CAPABILITIES_HELP
