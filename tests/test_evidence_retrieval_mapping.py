from __future__ import annotations

from langchain_core.documents import Document

from testbot.evidence_retrieval import (
    EvidenceBundle,
    build_evidence_bundle_from_docs_and_scores,
    build_evidence_bundle_from_hits,
    build_evidence_bundle_from_input_records,
    retrieval_result,
)
from testbot.intent_router import IntentType
from testbot.policy_decision import DecisionClass, DecisionObject, DecisionReasoning, decide_from_evidence
from testbot.sat_chatbot_memory_v2 import _retrieval_input_from_document


def test_build_evidence_bundle_from_docs_and_scores_keeps_class_separation() -> None:
    docs_and_scores = [
        (
            Document(
                id="mem-1",
                page_content="I asked about Friday",
                metadata={
                    "type": "user_utterance",
                    "memory_stratum": "episodic",
                    "segment_type": "contiguous_topic",
                    "segment_id": "seg-1",
                    "segment_membership_edge_refs": ["edge:seg-1:mem-1"],
                },
            ),
            0.91,
        ),
        (Document(id="reflect-1", page_content="possible ambiguity", metadata={"type": "reflection"}), 0.84),
        (
            Document(
                id="promoted-1",
                page_content="clarified desired reminder scope",
                metadata={"type": "promoted_context", "promotion_category": "clarified_intent"},
            ),
            0.77,
        ),
        (
            Document(
                id="src-1",
                page_content="calendar evidence",
                metadata={"type": "source_evidence", "source_type": "calendar"},
            ),
            0.88,
        ),
        (Document(id="fact-1", page_content="name=Sam", metadata={"type": "profile_fact"}), 0.79),
    ]

    bundle = build_evidence_bundle_from_docs_and_scores(docs_and_scores)

    assert [record.ref_id for record in bundle.episodic_utterances] == ["mem-1"]
    assert bundle.episodic_utterances[0].segment_id == "seg-1"
    assert bundle.episodic_utterances[0].segment_type == "contiguous_topic"
    assert bundle.episodic_utterances[0].segment_membership_edge_refs == ("edge:seg-1:mem-1",)
    assert [record.ref_id for record in bundle.reflections_hypotheses] == ["reflect-1"]
    assert [record.ref_id for record in bundle.repair_anchors_offers] == ["promoted-1"]
    assert [record.ref_id for record in bundle.source_evidence] == ["src-1"]
    assert [record.ref_id for record in bundle.structured_facts] == ["fact-1"]
    assert [record.ref_id for record in bundle.records_for_policy()] == [
        "fact-1",
        "mem-1",
        "promoted-1",
        "reflect-1",
        "src-1",
    ]


def test_confident_hits_produce_non_empty_bundle_for_memory_recall_decision() -> None:
    hits = [
        Document(id="mem-2", page_content="You asked about package pickup", metadata={"type": "user_utterance"}),
        Document(
            id="src-2",
            page_content="courier scan timeline",
            metadata={"type": "source_evidence", "source_type": "tracking"},
        ),
    ]

    bundle = build_evidence_bundle_from_hits(hits)
    retrieval = retrieval_result(
        evidence_bundle=bundle,
        retrieval_candidates_considered=4,
        hit_count=len(hits),
    )

    assert bundle.total_records() == 2
    assert retrieval.evidence_bundle.total_records() == 2
    assert retrieval.reasoning["channel_sizes"]["episodic_utterances"] == 1
    assert retrieval.reasoning["channel_sizes"]["source_evidence"] == 1

    decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=retrieval)
    assert decision.decision_class == DecisionClass.ANSWER_FROM_MEMORY


def test_adapter_edge_document_to_input_record_mapping_preserves_bundle_parity() -> None:
    docs_and_scores = [
        (Document(id="fact-1", page_content="name=Sam", metadata={"type": "profile_fact"}), 0.79),
        (Document(id="src-1", page_content="calendar evidence", metadata={"type": "source_evidence", "source_type": "calendar"}), 0.88),
        (Document(id="mem-1", page_content="I asked about Friday", metadata={"type": "user_utterance"}), 0.91),
    ]

    bundle_from_docs = build_evidence_bundle_from_docs_and_scores(docs_and_scores)
    bundle_from_inputs = build_evidence_bundle_from_input_records(
        [_retrieval_input_from_document(doc, score=score) for doc, score in docs_and_scores]
    )

    assert bundle_from_inputs == bundle_from_docs


def test_memory_recall_scored_empty_remains_clarification_not_generic_knowledge() -> None:
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=2,
        hit_count=0,
    )

    decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=retrieval)

    assert decision.decision_class is DecisionClass.ASK_FOR_CLARIFICATION
    assert decision.retrieval_branch == "memory_retrieval"
    assert decision.reasoning["empty_vs_scored"] == "scored_empty"


def test_memory_recall_empty_evidence_with_background_ingestion_uses_pending_lookup_decision() -> None:
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )

    decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=retrieval, repair_required=True)

    assert decision.decision_class is DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION
    assert decision.reasoning["background_ingestion_in_progress"] is True
    assert decision.reasoning["evidence_posture"] == "empty_evidence"


def test_policy_decision_reasoning_legacy_dict_round_trips_with_typed_access() -> None:
    legacy_reasoning = {
        "evidence_posture": "scored_empty",
        "empty_vs_scored": "scored_empty",
        "repair_required": True,
        "background_ingestion_in_progress": False,
        "retrieval_candidates_considered": 3,
    }
    decision = DecisionObject(
        decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
        retrieval_branch="memory_retrieval",
        rationale="test",
        reasoning=legacy_reasoning,
    )

    assert isinstance(decision.reasoning, DecisionReasoning)
    assert decision.reasoning.to_dict() == legacy_reasoning
