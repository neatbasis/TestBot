from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

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

