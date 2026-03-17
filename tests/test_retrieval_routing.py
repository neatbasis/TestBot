from testbot.intent_router import IntentType
from testbot.policy_decision import decide
from testbot.retrieval_routing import decide_retrieval_routing


def test_retrieval_routing_memory_recall_queries_require_retrieval() -> None:
    decision = decide_retrieval_routing(utterance="what did I say yesterday?", intent=IntentType.MEMORY_RECALL)

    assert decision.retrieval_branch == "memory_retrieval"
    assert decision.requires_retrieval is True




def test_retrieval_routing_time_query_queries_require_retrieval() -> None:
    decision = decide_retrieval_routing(utterance="when was that again?", intent=IntentType.TIME_QUERY)

    assert decision.retrieval_branch == "memory_retrieval"
    assert decision.requires_retrieval is True

def test_retrieval_routing_definitional_knowledge_queries_require_retrieval() -> None:
    decision = decide_retrieval_routing(utterance="what is ontology?", intent=IntentType.KNOWLEDGE_QUESTION)

    assert decision.retrieval_branch == "memory_retrieval"
    assert decision.requires_retrieval is True


def test_retrieval_routing_non_definitional_knowledge_queries_use_direct_answer() -> None:
    decision = decide_retrieval_routing(utterance="how does photosynthesis work?", intent=IntentType.KNOWLEDGE_QUESTION)

    assert decision.retrieval_branch == "direct_answer"
    assert decision.requires_retrieval is False


def test_retrieval_routing_identity_guard_forces_retrieval() -> None:
    decision = decide_retrieval_routing(
        utterance="hello there",
        intent=IntentType.META_CONVERSATION,
        guard_forced_memory_retrieval=True,
    )

    assert decision.retrieval_branch == "memory_retrieval"
    assert decision.requires_retrieval is True
    assert decision.reason == "identity_continuity_guard_requires_memory_retrieval"


def test_policy_decision_consumes_shared_retrieval_routing_guard_input() -> None:
    policy = decide(
        utterance="hello there",
        intent=IntentType.META_CONVERSATION,
        guard_forced_memory_retrieval=True,
    )

    assert policy.retrieval_branch == "memory_retrieval"
    assert policy.reasoning["guard_forced_memory_retrieval"] is True
