from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from langchain_core.documents import Document

from testbot.stabilization import StabilizedTurnState


class EvidencePosture(StrEnum):
    NOT_REQUESTED = "not_requested"
    EMPTY_EVIDENCE = "empty_evidence"
    SCORED_EMPTY = "scored_empty"
    SCORED_NON_EMPTY = "scored_non_empty"


@dataclass(frozen=True)
class EvidenceRecord:
    ref_id: str
    score: float = 0.0
    content: str = ""
    source_type: str = ""


@dataclass(frozen=True)
class EvidenceBundle:
    structured_facts: tuple[EvidenceRecord, ...] = ()
    episodic_utterances: tuple[EvidenceRecord, ...] = ()
    repair_anchors_offers: tuple[EvidenceRecord, ...] = ()
    reflections_hypotheses: tuple[EvidenceRecord, ...] = ()
    source_evidence: tuple[EvidenceRecord, ...] = ()

    def total_records(self) -> int:
        return sum(
            (
                len(self.structured_facts),
                len(self.episodic_utterances),
                len(self.repair_anchors_offers),
                len(self.reflections_hypotheses),
                len(self.source_evidence),
            )
        )


@dataclass(frozen=True)
class RetrievalResult:
    evidence_bundle: EvidenceBundle
    evidence_posture: EvidencePosture
    retrieval_candidates_considered: int
    hit_count: int
    rationale: str
    reasoning: dict[str, object] = field(default_factory=dict)


def build_evidence_bundle(
    *,
    stabilized_state: StabilizedTurnState,
    structured_facts: tuple[EvidenceRecord, ...] = (),
    episodic_utterances: tuple[EvidenceRecord, ...] = (),
    repair_anchors_offers: tuple[EvidenceRecord, ...] = (),
    reflections_hypotheses: tuple[EvidenceRecord, ...] = (),
    source_evidence: tuple[EvidenceRecord, ...] = (),
) -> EvidenceBundle:
    del stabilized_state
    return EvidenceBundle(
        structured_facts=structured_facts,
        episodic_utterances=episodic_utterances,
        repair_anchors_offers=repair_anchors_offers,
        reflections_hypotheses=reflections_hypotheses,
        source_evidence=source_evidence,
    )


def _to_evidence_record(*, doc: Document, score: float) -> EvidenceRecord:
    metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
    return EvidenceRecord(
        ref_id=str(doc.id or metadata.get("doc_id") or ""),
        score=float(score),
        content=str(doc.page_content or ""),
        source_type=str(metadata.get("source_type") or metadata.get("type") or metadata.get("record_kind") or ""),
    )


def _route_record_channel(*, doc: Document) -> str:
    metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
    record_kind = str(metadata.get("record_kind") or "").lower()
    card_type = str(metadata.get("type") or "").lower()
    promotion_category = str(metadata.get("promotion_category") or "").lower()

    if card_type == "source_evidence" or record_kind == "source_evidence":
        return "source_evidence"

    if card_type == "promoted_context" and promotion_category == "clarified_intent":
        return "repair_anchors_offers"

    if card_type == "reflection" or record_kind == "reflection_hypothesis":
        return "reflections_hypotheses"

    if card_type in {"user_utterance", "assistant_utterance", "utterance_memory"} or record_kind == "utterance_memory":
        return "episodic_utterances"

    return "structured_facts"


def build_evidence_bundle_from_docs_and_scores(
    docs_and_scores: list[tuple[Document, float]],
) -> EvidenceBundle:
    structured_facts: list[EvidenceRecord] = []
    episodic_utterances: list[EvidenceRecord] = []
    repair_anchors_offers: list[EvidenceRecord] = []
    reflections_hypotheses: list[EvidenceRecord] = []
    source_evidence: list[EvidenceRecord] = []

    for doc, score in docs_and_scores:
        record = _to_evidence_record(doc=doc, score=score)
        channel = _route_record_channel(doc=doc)
        if channel == "source_evidence":
            source_evidence.append(record)
        elif channel == "repair_anchors_offers":
            repair_anchors_offers.append(record)
        elif channel == "reflections_hypotheses":
            reflections_hypotheses.append(record)
        elif channel == "episodic_utterances":
            episodic_utterances.append(record)
        else:
            structured_facts.append(record)

    return EvidenceBundle(
        structured_facts=tuple(structured_facts),
        episodic_utterances=tuple(episodic_utterances),
        repair_anchors_offers=tuple(repair_anchors_offers),
        reflections_hypotheses=tuple(reflections_hypotheses),
        source_evidence=tuple(source_evidence),
    )


def build_evidence_bundle_from_hits(hits: list[Document]) -> EvidenceBundle:
    # Hits already represent post-rerank confident records, so use a neutral fixed score.
    return build_evidence_bundle_from_docs_and_scores([(doc, 1.0) for doc in hits])


def retrieval_result(
    *,
    evidence_bundle: EvidenceBundle,
    retrieval_candidates_considered: int | None,
    hit_count: int | None,
) -> RetrievalResult:
    considered = retrieval_candidates_considered if retrieval_candidates_considered is not None else 0
    hits = hit_count if hit_count is not None else evidence_bundle.total_records()
    if considered <= 0:
        posture = EvidencePosture.EMPTY_EVIDENCE
        rationale = "retrieval scan returned no candidates"
    elif hits <= 0:
        posture = EvidencePosture.SCORED_EMPTY
        rationale = "retrieval produced scored candidates but none survived confidence/rerank"
    else:
        posture = EvidencePosture.SCORED_NON_EMPTY
        rationale = "retrieval produced scored candidates with confident evidence"

    return RetrievalResult(
        evidence_bundle=evidence_bundle,
        evidence_posture=posture,
        retrieval_candidates_considered=considered,
        hit_count=max(0, hits),
        rationale=rationale,
        reasoning={
            "empty_evidence": posture is EvidencePosture.EMPTY_EVIDENCE,
            "scored_empty": posture is EvidencePosture.SCORED_EMPTY,
            "channel_sizes": {
                "structured_facts": len(evidence_bundle.structured_facts),
                "episodic_utterances": len(evidence_bundle.episodic_utterances),
                "repair_anchors_offers": len(evidence_bundle.repair_anchors_offers),
                "reflections_hypotheses": len(evidence_bundle.reflections_hypotheses),
                "source_evidence": len(evidence_bundle.source_evidence),
            },
        },
    )
