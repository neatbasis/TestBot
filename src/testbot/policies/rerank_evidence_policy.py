"""Rerank-evidence policy helpers.

Ownership:
- Canonical owner for rerank threshold/profile policy in ``retrieve.evidence``.
- Deterministic rerank transforms/projections remain outside this module.
- Runtime/service orchestration remains in application services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from testbot.rerank import ContextConfidenceThresholds, rerank_confidence_thresholds


@dataclass(frozen=True)
class RerankThresholdProfilePolicy:
    top_final_score_min: float
    min_margin_to_second: float
    allow_ambiguity_override: bool
    ambiguity_override_top_final_score_min: float


def default_rerank_threshold_profile_policy(
    *,
    rerank_confidence_thresholds_fn: Callable[[], ContextConfidenceThresholds] = rerank_confidence_thresholds,
) -> RerankThresholdProfilePolicy:
    thresholds = rerank_confidence_thresholds_fn()
    return RerankThresholdProfilePolicy(
        top_final_score_min=float(thresholds.top_final_score_min),
        min_margin_to_second=float(thresholds.min_margin_to_second),
        allow_ambiguity_override=bool(thresholds.allow_ambiguity_override),
        ambiguity_override_top_final_score_min=float(thresholds.ambiguity_override_top_final_score_min),
    )


__all__ = ["RerankThresholdProfilePolicy", "default_rerank_threshold_profile_policy"]
