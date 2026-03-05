from __future__ import annotations

from testbot.promotion_policy import evaluate_promotion_policy, persist_promoted_context
from dataclasses import dataclass

from langchain_core.documents import Document


@dataclass
class FakeMemoryStore:
    docs: list[Document]

    def add_documents(self, documents: list[Document]) -> None:
        self.docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4):
        query_lower = query.lower()
        hits = [doc for doc in self.docs if query_lower.split()[0] in doc.page_content.lower()]
        return [(doc, 0.9) for doc in hits[:k]]


def test_promotion_occurs_only_when_thresholds_met() -> None:
    passing_yaml = (
        "claims:\n"
        "  - User intent: wants to schedule a reminder for medication\n"
        "  - Definition: maintenance mode means reduced automation actions\n"
        "uncertainties: []\n"
        "confidence: 0.92"
    )
    failing_yaml = (
        "claims:\n"
        "  - User intent: might want a reminder\n"
        "uncertainties:\n"
        "  - unsure if reminder is for weekdays\n"
        "confidence: 0.61"
    )

    passing = evaluate_promotion_policy(reflection_yaml=passing_yaml)
    failing = evaluate_promotion_policy(reflection_yaml=failing_yaml)

    assert len(passing.items) == 2
    assert {item.category for item in passing.items} == {"clarified_intent", "accepted_context"}
    assert not failing.items
    assert "confidence_below_threshold" in failing.rejected_reasons
    assert "has_uncertainties" in failing.rejected_reasons


def test_promoted_items_are_retrievable_in_later_turns() -> None:
    store = FakeMemoryStore(docs=[])
    reflection_yaml = (
        "claims:\n"
        "  - User intent: wants to track daily water intake\n"
        "uncertainties: []\n"
        "confidence: 0.96"
    )

    promoted_ids = persist_promoted_context(
        store=store,
        ts_iso="2026-03-05T12:00:00+00:00",
        source_doc_id="assistant-doc-1",
        source_reflection_id="assistant-ref-1",
        reflection_yaml=reflection_yaml,
        channel="cli",
    )

    hits = store.similarity_search_with_score("water intake intent", k=5)

    assert promoted_ids
    assert any(doc.metadata.get("type") == "promoted_context" for doc, _ in hits)
    assert any((doc.metadata.get("raw") or "").startswith("User intent") for doc, _ in hits)


def test_no_debug_or_internal_leakage_promoted() -> None:
    reflection_yaml = (
        "claims:\n"
        "  - Internal debug: stack trace says route branch x\n"
        "  - User intent: wants lights dimmed after 9 pm\n"
        "uncertainties: []\n"
        "confidence: 0.95"
    )

    decision = evaluate_promotion_policy(reflection_yaml=reflection_yaml)

    assert not decision.items
    assert "contains_internal_debug" in decision.rejected_reasons


def test_relevance_and_source_evidence_claims_promote_as_accepted_context() -> None:
    reflection_yaml = (
        "claims:\n"
        "  - Relevant summary: the user is focused on ontology follow-ups\n"
        "  - Source evidence confirms next event is from calendar feed\n"
        "uncertainties: []\n"
        "confidence: 0.89"
    )

    decision = evaluate_promotion_policy(reflection_yaml=reflection_yaml)

    assert len(decision.items) == 2
    assert {item.category for item in decision.items} == {"accepted_context"}
