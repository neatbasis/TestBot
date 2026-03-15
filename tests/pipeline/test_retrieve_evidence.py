from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pytest


class IntentClass(str, Enum):
    KNOWLEDGE_QUESTION = "knowledge_question"
    META_CONVERSATION = "meta_conversation"
    CAPABILITIES_HELP = "capabilities_help"
    MEMORY_RECALL = "memory_recall"
    TIME_QUERY = "time_query"
    CONTROL = "control"


@dataclass(frozen=True)
class SpatialContext:
    place_id: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class EvidenceItem:
    doc_id: str
    score: float


@dataclass(frozen=True)
class EvidenceSet:
    items: tuple[EvidenceItem, ...]
    is_empty: bool
    retrieval_branch: str

    def has_evidence(self) -> bool:
        return bool(self.items)


@dataclass(frozen=True)
class RetrievalRequest:
    utterance: str
    slots: dict[str, str]
    spatial_context: SpatialContext | None = None


class RetrieverSpy:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self._responses: dict[str, tuple[EvidenceItem, ...]] = {}

    def set_response(self, method_name: str, items: tuple[EvidenceItem, ...]) -> None:
        self._responses[method_name] = items

    def _record(self, method_name: str, *, utterance: str, slots: dict[str, str], spatial_context: SpatialContext | None) -> tuple[EvidenceItem, ...]:
        self.calls.append(
            (
                method_name,
                {
                    "utterance": utterance,
                    "slots": dict(slots),
                    "spatial_context": spatial_context,
                },
            )
        )
        return self._responses.get(method_name, ())

    def retrieve_memory(self, *, utterance: str, slots: dict[str, str], spatial_context: SpatialContext | None) -> tuple[EvidenceItem, ...]:
        return self._record("retrieve_memory", utterance=utterance, slots=slots, spatial_context=spatial_context)

    def retrieve_time(self, *, utterance: str, slots: dict[str, str], spatial_context: SpatialContext | None) -> tuple[EvidenceItem, ...]:
        return self._record("retrieve_time", utterance=utterance, slots=slots, spatial_context=spatial_context)

    def retrieve_knowledge(self, *, utterance: str, slots: dict[str, str], spatial_context: SpatialContext | None) -> tuple[EvidenceItem, ...]:
        return self._record("retrieve_knowledge", utterance=utterance, slots=slots, spatial_context=spatial_context)


def retrieve_evidence(*, intent: IntentClass, request: RetrievalRequest, retriever: RetrieverSpy) -> EvidenceSet:
    if intent is IntentClass.MEMORY_RECALL:
        branch = "memory_retrieval"
        items = retriever.retrieve_memory(
            utterance=request.utterance,
            slots=request.slots,
            spatial_context=request.spatial_context,
        )
    elif intent is IntentClass.TIME_QUERY:
        branch = "time_retrieval"
        items = retriever.retrieve_time(
            utterance=request.utterance,
            slots=request.slots,
            spatial_context=request.spatial_context,
        )
    elif intent is IntentClass.KNOWLEDGE_QUESTION:
        branch = "knowledge_retrieval"
        items = retriever.retrieve_knowledge(
            utterance=request.utterance,
            slots=request.slots,
            spatial_context=request.spatial_context,
        )
    else:
        return EvidenceSet(items=(), is_empty=True, retrieval_branch=f"no_retrieval:{intent.value}")

    return EvidenceSet(items=items, is_empty=not bool(items), retrieval_branch=branch)


def policy_decide(*, intent: IntentClass, evidence: EvidenceSet) -> str:
    if evidence.has_evidence():
        return "answer_from_evidence"

    if intent in {IntentClass.MEMORY_RECALL, IntentClass.TIME_QUERY, IntentClass.KNOWLEDGE_QUESTION}:
        return "ask_for_clarification"

    return "direct_answer"


@pytest.mark.parametrize(
    ("intent", "method_name", "expected_branch"),
    [
        (IntentClass.MEMORY_RECALL, "retrieve_memory", "memory_retrieval"),
        (IntentClass.TIME_QUERY, "retrieve_time", "time_retrieval"),
        (IntentClass.KNOWLEDGE_QUESTION, "retrieve_knowledge", "knowledge_retrieval"),
    ],
)
def test_retrieval_intents_invoke_expected_retriever_method_with_payload(
    intent: IntentClass,
    method_name: str,
    expected_branch: str,
) -> None:
    retriever = RetrieverSpy()
    payload_item = EvidenceItem(doc_id="doc-1", score=0.75)
    retriever.set_response(method_name, (payload_item,))
    request = RetrievalRequest(
        utterance="where did we meet?",
        slots={"person": "Ava", "topic": "meeting"},
        spatial_context=SpatialContext(place_id="city-1", latitude=40.7128, longitude=-74.0060),
    )

    evidence = retrieve_evidence(intent=intent, request=request, retriever=retriever)

    assert evidence.retrieval_branch == expected_branch
    assert not evidence.is_empty
    assert evidence.items == (payload_item,)
    assert len(retriever.calls) == 1
    called_method, payload = retriever.calls[0]
    assert called_method == method_name
    assert payload["utterance"] == request.utterance
    assert payload["slots"] == request.slots
    assert payload["spatial_context"] == request.spatial_context


@pytest.mark.parametrize(
    "intent",
    [
        IntentClass.META_CONVERSATION,
        IntentClass.CAPABILITIES_HELP,
        IntentClass.CONTROL,
    ],
)
def test_no_retrieval_intents_return_empty_evidence_set_with_branch(intent: IntentClass) -> None:
    retriever = RetrieverSpy()
    request = RetrievalRequest(utterance="thanks", slots={}, spatial_context=None)

    evidence = retrieve_evidence(intent=intent, request=request, retriever=retriever)

    assert evidence == EvidenceSet(items=(), is_empty=True, retrieval_branch=f"no_retrieval:{intent.value}")
    assert retriever.calls == []


def test_empty_retrieval_marks_is_empty_true_with_no_items() -> None:
    retriever = RetrieverSpy()
    retriever.set_response("retrieve_memory", ())
    request = RetrievalRequest(
        utterance="what did I say before?",
        slots={"window": "recent"},
        spatial_context=SpatialContext(place_id="office", latitude=37.0, longitude=-122.0),
    )

    evidence = retrieve_evidence(intent=IntentClass.MEMORY_RECALL, request=request, retriever=retriever)

    assert evidence.is_empty is True
    assert evidence.items == ()
    assert evidence.has_evidence() is False


def test_non_empty_low_or_zero_scores_still_report_has_evidence() -> None:
    retriever = RetrieverSpy()
    low_confidence_items = (
        EvidenceItem(doc_id="doc-zero", score=0.0),
        EvidenceItem(doc_id="doc-low", score=0.01),
    )
    retriever.set_response("retrieve_knowledge", low_confidence_items)
    request = RetrievalRequest(
        utterance="what is a monad?",
        slots={"domain": "programming"},
        spatial_context=None,
    )

    evidence = retrieve_evidence(intent=IntentClass.KNOWLEDGE_QUESTION, request=request, retriever=retriever)

    assert evidence.is_empty is False
    assert evidence.items == low_confidence_items
    assert evidence.has_evidence() is True


def test_policy_decide_uses_has_evidence_for_different_outcomes() -> None:
    empty_evidence = EvidenceSet(items=(), is_empty=True, retrieval_branch="memory_retrieval")
    low_score_but_present = EvidenceSet(
        items=(EvidenceItem(doc_id="doc-low", score=0.0),),
        is_empty=False,
        retrieval_branch="memory_retrieval",
    )

    empty_decision = policy_decide(intent=IntentClass.MEMORY_RECALL, evidence=empty_evidence)
    present_decision = policy_decide(intent=IntentClass.MEMORY_RECALL, evidence=low_score_but_present)

    assert empty_decision == "ask_for_clarification"
    assert present_decision == "answer_from_evidence"
