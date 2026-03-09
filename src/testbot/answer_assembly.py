from __future__ import annotations

from dataclasses import dataclass

from testbot.evidence_retrieval import EvidenceBundle
from testbot.policy_decision import DecisionClass, DecisionObject


@dataclass(frozen=True)
class AnswerCandidate:
    """Contract-first answer assembly output.

    Assembly is intentionally restricted to decision + evidence contracts so
    downstream stages can validate and render against a deterministic payload.
    """

    decision_class: str
    rendered_class: str
    retrieval_branch: str
    rationale: str
    evidence_counts: dict[str, int]
    pending_repair_state: dict[str, object]
    resolved_obligations: list[str]
    remaining_obligations: list[str]
    confirmed_user_facts: list[str]


def assemble_answer_contract(*, decision: DecisionObject, evidence_bundle: EvidenceBundle) -> AnswerCandidate:
    evidence_counts = {
        "structured_facts": len(evidence_bundle.structured_facts),
        "episodic_utterances": len(evidence_bundle.episodic_utterances),
        "repair_anchors_offers": len(evidence_bundle.repair_anchors_offers),
        "reflections_hypotheses": len(evidence_bundle.reflections_hypotheses),
        "source_evidence": len(evidence_bundle.source_evidence),
    }

    pending_repair_required = decision.decision_class in {
        DecisionClass.CONTINUE_REPAIR_RECONSTRUCTION,
        DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION,
    }
    confirmed_user_facts = [record.content for record in evidence_bundle.structured_facts if record.content]

    resolved_obligations: list[str] = []
    remaining_obligations: list[str] = []
    if pending_repair_required:
        if decision.decision_class is DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION:
            remaining_obligations.append("pending_lookup_background_ingestion")
        else:
            remaining_obligations.append("continue_repair_reconstruction")
    else:
        resolved_obligations.append("repair_state_not_required")

    rendered_class = decision.decision_class.value
    return AnswerCandidate(
        decision_class=decision.decision_class.value,
        rendered_class=rendered_class,
        retrieval_branch=decision.retrieval_branch,
        rationale=decision.rationale,
        evidence_counts=evidence_counts,
        pending_repair_state={
            "required": pending_repair_required,
            "reason": "decision_requires_repair" if pending_repair_required else "none",
        },
        resolved_obligations=resolved_obligations,
        remaining_obligations=remaining_obligations,
        confirmed_user_facts=confirmed_user_facts,
    )



# Backward-compatible alias while canonical naming converges.
AnswerAssemblyResult = AnswerCandidate
