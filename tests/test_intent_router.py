from testbot.intent_router import IntentType, classify_intent


def test_classify_intent_memory_recall_ambiguous_what_did_i_ask() -> None:
    assert classify_intent("what did I ask?") is IntentType.MEMORY_RECALL


def test_classify_intent_meta_conversation_relevance_prompt() -> None:
    assert classify_intent("what's relevant to our conversation?") is IntentType.META_CONVERSATION


def test_classify_intent_knowledge_question_ontology() -> None:
    assert classify_intent("what is ontology?") is IntentType.KNOWLEDGE_QUESTION


def test_classify_intent_control_takes_precedence() -> None:
    assert classify_intent("stop and what did I ask?") is IntentType.CONTROL
