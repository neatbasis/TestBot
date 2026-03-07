from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from testbot.promotion_policy import evaluate_promotion_policy, persist_promoted_context
from testbot.evidence_retrieval import EvidenceBundle, EvidenceRecord, retrieval_result
from testbot.intent_router import IntentType
from testbot.policy_decision import DecisionClass, decide_from_evidence


@dataclass
class FakeMemoryStore:
    docs: list[Document]

    def add_documents(self, documents: list[Document]) -> None:
        self.docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
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


def test_structured_claims_route_by_category_not_legacy_phrasing() -> None:
    reflection_yaml = (
        "claims:\n"
        "  - text: The user hopes to get a reminder after dinner\n"
        "    category: clarified_intent\n"
        "    reliability: reliable\n"
        "    source: llm_structured_reflection\n"
        "  - text: Calendar feed confirms weekly recurring event\n"
        "    category: accepted_context\n"
        "    reliability: reliable\n"
        "    source: source_evidence\n"
        "uncertainties: []\n"
        "confidence: 0.89"
    )

    decision = evaluate_promotion_policy(reflection_yaml=reflection_yaml)

    assert len(decision.items) == 2
    assert {item.category for item in decision.items} == {"clarified_intent", "accepted_context"}


def test_uncertain_or_conflicting_claim_is_rejected_even_with_high_confidence() -> None:
    reflection_yaml = (
        "claims:\n"
        "  - text: We should send reminders weekdays\n"
        "    category: clarified_intent\n"
        "    reliability: uncertain\n"
        "    source: reflection\n"
        "uncertainties: []\n"
        "confidence: 0.99"
    )

    decision = evaluate_promotion_policy(reflection_yaml=reflection_yaml)

    assert not decision.items
    assert "claim_uncertain_or_conflicting" in decision.rejected_reasons


def test_invalid_confidence_value_deterministically_rejects_promotion() -> None:
    reflection_yaml = (
        "claims:\n"
        "  - User intent: wants reminders after dinner\n"
        "uncertainties: []\n"
        "confidence: not-a-number"
    )

    decision = evaluate_promotion_policy(reflection_yaml=reflection_yaml)

    assert not decision.items
    assert decision.rejected_reasons == ["confidence_below_threshold"]


def test_malformed_yaml_deterministically_rejects_promotion() -> None:
    malformed_yaml = "claims: [\nuncertainties: []\nconfidence: 0.98"

    decision = evaluate_promotion_policy(reflection_yaml=malformed_yaml)

    assert not decision.items
    assert decision.rejected_reasons == ["confidence_below_threshold"]


def test_reordered_fields_are_parsed_and_promoted() -> None:
    reflection_yaml = (
        "confidence: 0.93\n"
        "uncertainties: []\n"
        "claims:\n"
        "  - text: Please capture thermostat schedule preference\n"
        "    source: reflection\n"
        "    reliability: reliable\n"
        "    category: clarified_intent\n"
    )

    decision = evaluate_promotion_policy(reflection_yaml=reflection_yaml)

    assert len(decision.items) == 1
    assert decision.items[0].category == "clarified_intent"


def test_persist_promoted_context_returns_empty_ids_when_policy_rejects() -> None:
    store = FakeMemoryStore(docs=[])
    reflection_yaml = (
        "claims:\n"
        "  - Internal debug: route confidence tie\n"
        "uncertainties: []\n"
        "confidence: 0.95"
    )

    promoted_ids = persist_promoted_context(
        store=store,
        ts_iso="2026-03-05T12:00:00+00:00",
        source_doc_id="assistant-doc-2",
        source_reflection_id="assistant-ref-2",
        reflection_yaml=reflection_yaml,
        channel="cli",
    )

    assert promoted_ids == []
    assert store.docs == []


def test_evidence_bundle_channels_remain_class_separated_for_policy() -> None:
    bundle = EvidenceBundle(
        structured_facts=(EvidenceRecord(ref_id="fact-1", score=0.8, content="name=sebastian"),),
        episodic_utterances=(EvidenceRecord(ref_id="utt-1", score=0.7, content="what did I ask"),),
        repair_anchors_offers=(EvidenceRecord(ref_id="repair-1", score=0.6, content="Can you clarify"),),
        reflections_hypotheses=(EvidenceRecord(ref_id="reflection-1", score=0.5, content="possible ambiguity"),),
        source_evidence=(EvidenceRecord(ref_id="src-1", score=0.9, content="calendar event", source_type="calendar"),),
    )

    retrieval = retrieval_result(evidence_bundle=bundle, retrieval_candidates_considered=5, hit_count=3)

    assert retrieval.reasoning["channel_sizes"]["structured_facts"] == 1
    assert retrieval.reasoning["channel_sizes"]["source_evidence"] == 1


def test_decision_object_supports_repair_reconstruction_outcome() -> None:
    retrieval = retrieval_result(evidence_bundle=EvidenceBundle(), retrieval_candidates_considered=2, hit_count=0)

    decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=retrieval, repair_required=True)

    assert decision.decision_class is DecisionClass.CONTINUE_REPAIR_RECONSTRUCTION
