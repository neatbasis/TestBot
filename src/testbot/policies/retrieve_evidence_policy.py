"""Retrieve-evidence policy helpers.

Ownership:
- Canonical owner for retrieve.evidence policy decisions that select retrieval
  branch/shape under resolved intent + discourse continuity signals.
- Deterministic retrieval projection remains in ``testbot.logic``.
- Runtime orchestration remains in application services.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from testbot.pipeline_state import PipelineState

_SELF_REFERENTIAL_IDENTITY_RECALL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*who\s+am\s+i\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:\s+is|'s)\s+my\s+name\b", re.IGNORECASE),
    re.compile(r"\bremind\s+me\s+(?:what\s+)?my\s+name\s+is\b", re.IGNORECASE),
)

_PRIOR_IDENTITY_CANDIDATE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi\s*(?:am|'m|’m)\s+[\w'-]+", re.IGNORECASE),
    re.compile(r"\bmy\s+name\s+is\s+[\w'-]+", re.IGNORECASE),
)


@dataclass(frozen=True)
class RetrieveEvidenceExecutionPolicy:
    search_top_k: int
    projection_top_k: int
    projection_source_quota: int


def default_retrieve_evidence_execution_policy() -> RetrieveEvidenceExecutionPolicy:
    return RetrieveEvidenceExecutionPolicy(
        search_top_k=18,
        projection_top_k=12,
        projection_source_quota=3,
    )


def is_self_referential_identity_recall_query(utterance: str) -> bool:
    return any(pattern.search(utterance or "") is not None for pattern in _SELF_REFERENTIAL_IDENTITY_RECALL_PATTERNS)


def has_prior_identity_candidates_or_continuity_markers(
    *,
    prior_state: PipelineState | None,
    continuity_evidence: tuple[str, ...],
    context_history_anchors: tuple[str, ...],
) -> bool:
    if any(anchor.startswith("commit.confirmed_user_facts:") for anchor in continuity_evidence):
        return True
    if any(anchor.startswith("commit.confirmed_user_facts:") for anchor in context_history_anchors):
        return True
    if prior_state is None:
        return False

    for fact in prior_state.candidate_facts.facts:
        if not isinstance(fact, dict):
            continue
        if str(fact.get("key") or "").strip() == "user_name":
            return True

    prior_utterance = str(prior_state.user_input or "")
    return any(pattern.search(prior_utterance) is not None for pattern in _PRIOR_IDENTITY_CANDIDATE_PATTERNS)


def should_force_memory_retrieval_for_identity_recall(
    *,
    utterance: str,
    prior_state: PipelineState | None,
    continuity_evidence: tuple[str, ...],
    context_history_anchors: tuple[str, ...],
) -> bool:
    return is_self_referential_identity_recall_query(utterance) and has_prior_identity_candidates_or_continuity_markers(
        prior_state=prior_state,
        continuity_evidence=continuity_evidence,
        context_history_anchors=context_history_anchors,
    )


__all__ = [
    "RetrieveEvidenceExecutionPolicy",
    "default_retrieve_evidence_execution_policy",
    "has_prior_identity_candidates_or_continuity_markers",
    "is_self_referential_identity_recall_query",
    "should_force_memory_retrieval_for_identity_recall",
]
