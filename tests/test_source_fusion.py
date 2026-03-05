from __future__ import annotations

from collections import deque

from langchain_core.documents import Document

from testbot.history_packer import PackedHistory
from testbot.pipeline_state import ProvenanceType
from testbot.rerank import mix_source_evidence_with_memory_cards
from testbot.sat_chatbot_memory_v2 import build_provenance_metadata, collect_used_source_evidence_refs


def _packed_history() -> PackedHistory:
    return PackedHistory(
        last_user_turns=[],
        last_assistant_turns=[],
        open_questions=[],
        topic_entity_hints=[],
        constraints=[],
    )


def test_source_fusion_prioritizes_source_then_memory_then_remaining_source() -> None:
    docs_and_scores = [
        (Document(id="m1", page_content="memory 1", metadata={"type": "memory", "ts": "2026-03-10T10:00:00Z"}), 0.92),
        (
            Document(
                id="s1",
                page_content="source 1",
                metadata={"type": "source_evidence", "ts": "2026-03-10T10:05:00Z", "source_uri": "calendar://1"},
            ),
            0.87,
        ),
        (Document(id="m2", page_content="memory 2", metadata={"type": "memory", "ts": "2026-03-10T09:59:00Z"}), 0.9),
        (
            Document(
                id="s2",
                page_content="source 2",
                metadata={"record_kind": "source_evidence", "ts": "2026-03-10T10:03:00Z", "source_uri": "calendar://2"},
            ),
            0.89,
        ),
    ]

    mixed = mix_source_evidence_with_memory_cards(docs_and_scores, top_k=4, source_quota=1)

    assert [doc.id for doc, _ in mixed] == ["s2", "m1", "m2", "s1"]


def test_collect_used_source_evidence_refs_dedupes_refs_and_attribution() -> None:
    source_hit = Document(
        id="src-1",
        page_content="schedule update",
        metadata={
            "type": "source_evidence",
            "source_type": "calendar",
            "source_uri": "calendar://work/event-1",
            "retrieved_at": "2026-03-10T11:10:00Z",
            "trust_tier": "high",
        },
    )

    refs, attribution = collect_used_source_evidence_refs(
        [source_hit, source_hit, Document(id="mem-1", page_content="memory", metadata={"type": "memory"})]
    )

    assert refs == ["src-1"]
    assert attribution == [
        {
            "doc_id": "src-1",
            "source_type": "calendar",
            "source_uri": "calendar://work/event-1",
            "retrieved_at": "2026-03-10T11:10:00Z",
            "trust_tier": "high",
        }
    ]


def test_build_provenance_metadata_assigns_source_backed_provenance_fields() -> None:
    source_hit = Document(
        id="src-42",
        page_content="utility bill due Friday",
        metadata={
            "type": "source_evidence",
            "source_type": "home_automation",
            "source_uri": "ha://tasks/utility-bill",
            "retrieved_at": "2026-03-10T09:00:00Z",
            "trust_tier": "medium",
        },
    )

    provenance, claims, basis, memory_refs, source_refs, source_attr = build_provenance_metadata(
        final_answer="Your utility bill is due Friday based on synced task data.",
        hits=[source_hit],
        chat_history=deque(),
        packed_history=_packed_history(),
    )

    assert ProvenanceType.MEMORY in provenance
    assert ProvenanceType.GENERAL_KNOWLEDGE not in provenance
    assert basis == "Answer synthesized from reranked source evidence documents."
    assert memory_refs == []
    assert source_refs == ["src-42"]
    assert source_attr[0]["source_uri"] == "ha://tasks/utility-bill"
    assert claims
