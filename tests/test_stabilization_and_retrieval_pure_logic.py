from __future__ import annotations

from testbot.candidate_encoding import EncodedTurnCandidates, FactCandidate
from testbot.evidence_retrieval import (
    RetrievalInputRecord,
    build_evidence_bundle_from_input_records,
    retrieval_result,
    route_record_channel,
)
from testbot.memory_strata import SegmentDescriptor, SegmentType
from testbot.pipeline_state import PipelineState
from testbot.stabilization import build_stabilization_plan, persist_stabilization_records
from testbot.turn_observation import TurnObservation


def test_build_stabilization_plan_runs_as_pure_logic_without_store() -> None:
    plan = build_stabilization_plan(
        state=PipelineState(user_input="my name is Ana"),
        observation=TurnObservation(
            turn_id="turn-100",
            observed_at="2026-03-18T10:00:00Z",
            speaker="user",
            channel="cli",
            utterance="my name is Ana",
            classified_intent="memory_recall",
            resolved_intent="memory_recall",
        ),
        encoded=EncodedTurnCandidates(
            rewritten_query="name ana",
            facts=[FactCandidate(key="user_name", value="Ana", confidence=0.9, provenance="unit")],
            speech_acts=[],
            dialogue_state=[],
            repairs=[],
        ),
        response_plan={"pathway": "test"},
        reflection_yaml="offline: true",
        segment=SegmentDescriptor(
            segment_type=SegmentType.CONTIGUOUS_TOPIC,
            segment_id="seg-100",
            continuity_key="k",
        ),
        reflection_doc_id="reflection-fixed",
        dialogue_state_doc_id="dialogue-fixed",
    )

    assert plan.stabilized.reflection_doc_id == "reflection-fixed"
    assert plan.stabilized.dialogue_state_doc_id == "dialogue-fixed"
    assert plan.stabilized.utterance_doc_id == "turn-100"
    assert len(plan.persistence_records) == 3
    assert plan.next_state.same_turn_exclusion["excluded_doc_ids"] == [
        "turn-100",
        "reflection-fixed",
        "dialogue-fixed",
    ]


def test_persist_stabilization_records_is_adapter_only() -> None:
    calls: list[str] = []

    def _store_doc(store, *, doc_id: str, content: str, metadata: dict[str, object]) -> None:
        del store, content
        calls.append(f"{metadata.get('type')}:{doc_id}")

    plan = build_stabilization_plan(
        state=PipelineState(user_input="hello"),
        observation=TurnObservation(
            turn_id="turn-101",
            observed_at="2026-03-18T10:00:00Z",
            speaker="user",
            channel="cli",
            utterance="hello",
            classified_intent="memory_recall",
            resolved_intent="memory_recall",
        ),
        encoded=EncodedTurnCandidates(rewritten_query="hello", facts=[], speech_acts=[], dialogue_state=[], repairs=[]),
        response_plan={"pathway": "test"},
        reflection_yaml="offline: true",
        segment=SegmentDescriptor(
            segment_type=SegmentType.CONTIGUOUS_TOPIC,
            segment_id="seg-101",
            continuity_key="k",
        ),
        reflection_doc_id="reflection-101",
        dialogue_state_doc_id="dialogue-101",
    )

    persist_stabilization_records(store=None, persistence_records=plan.persistence_records, store_doc_fn=_store_doc)  # type: ignore[arg-type]
    assert calls == [
        "user_utterance:turn-101",
        "reflection:reflection-101",
        "dialogue_state_snapshot:dialogue-101",
    ]


def test_retrieval_bundle_pure_logic_from_domain_inputs() -> None:
    records = [
        RetrievalInputRecord(
            ref_id="sem-1",
            score=0.9,
            content="profile fact",
            metadata={"type": "profile_fact", "memory_stratum": "semantic", "segment_id": "seg-5"},
        ),
        RetrievalInputRecord(
            ref_id="epi-1",
            score=0.8,
            content="utterance",
            metadata={"type": "user_utterance", "memory_stratum": "episodic", "segment_id": "seg-5"},
        ),
        RetrievalInputRecord(ref_id="src-1", score=0.7, content="source", metadata={"type": "source_evidence"}),
    ]

    bundle = build_evidence_bundle_from_input_records(records)
    retrieval = retrieval_result(evidence_bundle=bundle, retrieval_candidates_considered=3, hit_count=2)

    assert [entry.ref_id for entry in bundle.structured_facts] == ["sem-1"]
    assert [entry.ref_id for entry in bundle.episodic_utterances] == []
    assert [entry.ref_id for entry in bundle.source_evidence] == ["src-1"]
    assert retrieval.evidence_posture.value == "scored_non_empty"
    assert route_record_channel(metadata={"type": "promoted_context", "promotion_category": "clarified_intent"}) == (
        "repair_anchors_offers"
    )
