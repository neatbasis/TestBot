from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import CLARIFY_ANSWER, resolve_turn_intent
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


def test_classify_intent_capabilities_help_what_can_you_do() -> None:
    assert classify_intent("what can you do") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_help() -> None:
    assert classify_intent("help") is IntentType.CAPABILITIES_HELP


def test_classify_intent_capabilities_help_capabilities() -> None:
    assert classify_intent("capabilities") is IntentType.CAPABILITIES_HELP


def test_classify_intent_knowledge_question_when_is_prompt() -> None:
    assert classify_intent("when is my next utility event?") is IntentType.KNOWLEDGE_QUESTION


def test_classify_intent_meta_conversation_relevance_summary() -> None:
    assert classify_intent("summarize our conversation") is IntentType.META_CONVERSATION


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
