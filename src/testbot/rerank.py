from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import arrow
from langchain_core.documents import Document

from testbot.vector_store import (
    RECORD_KIND_PROMOTED_CONTEXT,
    RECORD_KIND_REFLECTION_HYPOTHESIS,
    RECORD_KIND_SOURCE_EVIDENCE,
    RECORD_KIND_UTTERANCE_MEMORY,
    RecordKind,
    is_valid_record_kind,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RerankOutcome:
    docs: list[Document]
    ambiguity_detected: bool
    near_tie_candidates: list[dict[str, float | str]]
    scored_candidates: list[dict[str, float | str]]


DEFAULT_RERANK_OBJECTIVE_CONFIG_PATH = Path("config/rerank_objective.json")
RERANK_OBJECTIVE_CONFIG_ENV = "TESTBOT_RERANK_OBJECTIVE_CONFIG"


@dataclass(frozen=True)
class ContextConfidenceThresholds:
    top_final_score_min: float = 0.2
    min_margin_to_second: float = 0.0
    allow_ambiguity_override: bool = False
    ambiguity_override_top_final_score_min: float = 0.6


DEFAULT_CONTEXT_CONFIDENCE_THRESHOLDS = ContextConfidenceThresholds()


@dataclass(frozen=True)
class RerankObjectiveCoefficients:
    base_temporal_blend: float = 0.25
    gaussian_temporal_blend: float = 0.75
    reflection_type_prior: float = 0.7
    default_type_prior: float = 1.0
    neutral_temporal_prior: float = 0.5
    lane_coefficients: dict[RecordKind, float] | None = None


DEFAULT_LANE_COEFFICIENTS: dict[RecordKind, float] = {
    RECORD_KIND_UTTERANCE_MEMORY: 1.0,
    RECORD_KIND_REFLECTION_HYPOTHESIS: 0.7,
    RECORD_KIND_PROMOTED_CONTEXT: 1.05,
    RECORD_KIND_SOURCE_EVIDENCE: 1.1,
}


DEFAULT_RERANK_COEFFICIENTS = RerankObjectiveCoefficients()


@dataclass(frozen=True)
class RerankObjectiveConfig:
    objective_name: str
    objective_version: str
    coefficients: RerankObjectiveCoefficients
    confidence_thresholds: ContextConfidenceThresholds
    lane_fusion: dict[RecordKind, int]


DEFAULT_RERANK_OBJECTIVE_CONFIG = RerankObjectiveConfig(
    objective_name="semantic_temporal_type",
    objective_version="v2",
    coefficients=RerankObjectiveCoefficients(
        base_temporal_blend=DEFAULT_RERANK_COEFFICIENTS.base_temporal_blend,
        gaussian_temporal_blend=DEFAULT_RERANK_COEFFICIENTS.gaussian_temporal_blend,
        reflection_type_prior=DEFAULT_RERANK_COEFFICIENTS.reflection_type_prior,
        default_type_prior=DEFAULT_RERANK_COEFFICIENTS.default_type_prior,
        neutral_temporal_prior=DEFAULT_RERANK_COEFFICIENTS.neutral_temporal_prior,
        lane_coefficients=DEFAULT_LANE_COEFFICIENTS,
    ),
    confidence_thresholds=DEFAULT_CONTEXT_CONFIDENCE_THRESHOLDS,
    lane_fusion={
        RECORD_KIND_SOURCE_EVIDENCE: 2,
        RECORD_KIND_PROMOTED_CONTEXT: 1,
        RECORD_KIND_UTTERANCE_MEMORY: 4,
        RECORD_KIND_REFLECTION_HYPOTHESIS: 0,
    },
)


_CARD_TYPE_PRIORITY: dict[str, int] = {
    "user_utterance": 0,
    "assistant_utterance": 1,
    "memory": 2,
    "source_evidence": 3,
    "reflection": 4,
}

_LANE_FUSION_ORDER: tuple[RecordKind, ...] = (
    RECORD_KIND_SOURCE_EVIDENCE,
    RECORD_KIND_PROMOTED_CONTEXT,
    RECORD_KIND_UTTERANCE_MEMORY,
    RECORD_KIND_REFLECTION_HYPOTHESIS,
)


_RERANK_OBJECTIVE_CONFIG_CACHE: RerankObjectiveConfig | None = None
_RERANK_OBJECTIVE_CONFIG_CACHE_PATH: Path | None = None


def _objective_label(config: RerankObjectiveConfig) -> str:
    return f"{config.objective_name}_{config.objective_version}"


def rerank_objective_name() -> str:
    return _objective_label(load_rerank_objective_config())


def _config_path() -> Path:
    import os

    configured = os.getenv(RERANK_OBJECTIVE_CONFIG_ENV)
    if configured:
        return Path(configured)
    return DEFAULT_RERANK_OBJECTIVE_CONFIG_PATH


def _require_mapping(raw: object, *, where: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be an object")
    return raw


def _require_float(raw: object, *, where: str, minimum: float, maximum: float) -> float:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ValueError(f"{where} must be a number")
    value = float(raw)
    if value < minimum or value > maximum:
        raise ValueError(f"{where} out of bounds [{minimum}, {maximum}]: {value}")
    return value


def _parse_coefficients(raw: object) -> RerankObjectiveCoefficients:
    mapping = _require_mapping(raw, where="coefficients")
    required = {
        "base_temporal_blend",
        "gaussian_temporal_blend",
        "reflection_type_prior",
        "default_type_prior",
    }
    missing = required.difference(mapping)
    if missing:
        raise ValueError(f"coefficients missing keys: {sorted(missing)}")
    lane_coefficients_raw = mapping.get("lane_coefficients", DEFAULT_LANE_COEFFICIENTS)
    lane_coefficients_mapping = _require_mapping(lane_coefficients_raw, where="coefficients.lane_coefficients")
    lane_coefficients: dict[RecordKind, float] = {}
    for lane_name, lane_value in lane_coefficients_mapping.items():
        lane_key = str(lane_name)
        if not is_valid_record_kind(lane_key):
            raise ValueError(f"coefficients.lane_coefficients contains invalid lane: {lane_name}")
        lane_coefficients[lane_key] = _require_float(
            lane_value,
            where=f"coefficients.lane_coefficients.{lane_key}",
            minimum=0.0,
            maximum=3.0,
        )

    return RerankObjectiveCoefficients(
        base_temporal_blend=_require_float(
            mapping["base_temporal_blend"],
            where="coefficients.base_temporal_blend",
            minimum=0.0,
            maximum=1.0,
        ),
        gaussian_temporal_blend=_require_float(
            mapping["gaussian_temporal_blend"],
            where="coefficients.gaussian_temporal_blend",
            minimum=0.0,
            maximum=1.0,
        ),
        reflection_type_prior=_require_float(
            mapping["reflection_type_prior"],
            where="coefficients.reflection_type_prior",
            minimum=0.0,
            maximum=2.0,
        ),
        default_type_prior=_require_float(
            mapping["default_type_prior"],
            where="coefficients.default_type_prior",
            minimum=0.0,
            maximum=2.0,
        ),
        neutral_temporal_prior=_require_float(
            mapping.get("neutral_temporal_prior", DEFAULT_RERANK_COEFFICIENTS.neutral_temporal_prior),
            where="coefficients.neutral_temporal_prior",
            minimum=0.0,
            maximum=1.0,
        ),
        lane_coefficients=lane_coefficients,
    )


def _parse_lane_fusion(raw: object) -> dict[RecordKind, int]:
    mapping = _require_mapping(raw, where="lane_fusion")
    parsed: dict[RecordKind, int] = {}
    for lane_name, lane_quota in mapping.items():
        lane_key = str(lane_name)
        if not is_valid_record_kind(lane_key):
            raise ValueError(f"lane_fusion contains invalid lane: {lane_name}")
        if isinstance(lane_quota, bool) or not isinstance(lane_quota, int):
            raise ValueError(f"lane_fusion.{lane_key} must be an integer")
        if lane_quota < 0:
            raise ValueError(f"lane_fusion.{lane_key} must be >= 0")
        parsed[lane_key] = lane_quota

    for lane_name in _LANE_FUSION_ORDER:
        parsed.setdefault(lane_name, DEFAULT_RERANK_OBJECTIVE_CONFIG.lane_fusion[lane_name])
    return parsed


def _parse_confidence_thresholds(raw: object) -> ContextConfidenceThresholds:
    mapping = _require_mapping(raw, where="confidence_thresholds")
    required = {
        "top_final_score_min",
        "min_margin_to_second",
        "allow_ambiguity_override",
        "ambiguity_override_top_final_score_min",
    }
    missing = required.difference(mapping)
    if missing:
        raise ValueError(f"confidence_thresholds missing keys: {sorted(missing)}")
    allow_override = mapping["allow_ambiguity_override"]
    if not isinstance(allow_override, bool):
        raise ValueError("confidence_thresholds.allow_ambiguity_override must be boolean")
    return ContextConfidenceThresholds(
        top_final_score_min=_require_float(
            mapping["top_final_score_min"],
            where="confidence_thresholds.top_final_score_min",
            minimum=0.0,
            maximum=1.0,
        ),
        min_margin_to_second=_require_float(
            mapping["min_margin_to_second"],
            where="confidence_thresholds.min_margin_to_second",
            minimum=0.0,
            maximum=1.0,
        ),
        allow_ambiguity_override=allow_override,
        ambiguity_override_top_final_score_min=_require_float(
            mapping["ambiguity_override_top_final_score_min"],
            where="confidence_thresholds.ambiguity_override_top_final_score_min",
            minimum=0.0,
            maximum=1.0,
        ),
    )


def _parse_objective_config(raw: object) -> RerankObjectiveConfig:
    mapping = _require_mapping(raw, where="root")
    objective_name = mapping.get("objective_name")
    objective_version = mapping.get("objective_version")
    if not isinstance(objective_name, str) or not objective_name.strip():
        raise ValueError("objective_name must be a non-empty string")
    if not isinstance(objective_version, str) or not objective_version.strip():
        raise ValueError("objective_version must be a non-empty string")
    if "coefficients" not in mapping:
        raise ValueError("missing required key: coefficients")
    if "confidence_thresholds" not in mapping:
        raise ValueError("missing required key: confidence_thresholds")
    if "lane_fusion" not in mapping:
        raise ValueError("missing required key: lane_fusion")
    return RerankObjectiveConfig(
        objective_name=objective_name.strip(),
        objective_version=objective_version.strip(),
        coefficients=_parse_coefficients(mapping["coefficients"]),
        confidence_thresholds=_parse_confidence_thresholds(mapping["confidence_thresholds"]),
        lane_fusion=_parse_lane_fusion(mapping["lane_fusion"]),
    )


def load_rerank_objective_config(*, force_reload: bool = False) -> RerankObjectiveConfig:
    global _RERANK_OBJECTIVE_CONFIG_CACHE
    global _RERANK_OBJECTIVE_CONFIG_CACHE_PATH

    path = _config_path()
    if (
        _RERANK_OBJECTIVE_CONFIG_CACHE is not None
        and not force_reload
        and _RERANK_OBJECTIVE_CONFIG_CACHE_PATH == path
    ):
        return _RERANK_OBJECTIVE_CONFIG_CACHE

    try:
        if not path.exists():
            _RERANK_OBJECTIVE_CONFIG_CACHE = DEFAULT_RERANK_OBJECTIVE_CONFIG
            _RERANK_OBJECTIVE_CONFIG_CACHE_PATH = path
            return _RERANK_OBJECTIVE_CONFIG_CACHE
        raw = json.loads(path.read_text(encoding="utf-8"))
        _RERANK_OBJECTIVE_CONFIG_CACHE = _parse_objective_config(raw)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning(
            "Failed to load rerank objective config from %s due to %s: %s; using default rerank objective config.",
            path,
            type(exc).__name__,
            exc,
        )
        _RERANK_OBJECTIVE_CONFIG_CACHE = DEFAULT_RERANK_OBJECTIVE_CONFIG

    _RERANK_OBJECTIVE_CONFIG_CACHE_PATH = path
    return _RERANK_OBJECTIVE_CONFIG_CACHE


def rerank_coefficients() -> RerankObjectiveCoefficients:
    return load_rerank_objective_config().coefficients


def rerank_confidence_thresholds() -> ContextConfidenceThresholds:
    return load_rerank_objective_config().confidence_thresholds


LaneName = Literal[
    "utterance_memory",
    "reflection_hypothesis",
    "promoted_context",
    "source_evidence",
]


def _normalize_lane_name(raw: object) -> LaneName:
    value = str(raw or "").strip()
    if value in {RECORD_KIND_SOURCE_EVIDENCE, "source_evidence"}:
        return RECORD_KIND_SOURCE_EVIDENCE
    if value in {RECORD_KIND_PROMOTED_CONTEXT, "promoted_context"}:
        return RECORD_KIND_PROMOTED_CONTEXT
    if value in {RECORD_KIND_REFLECTION_HYPOTHESIS, "reflection"}:
        return RECORD_KIND_REFLECTION_HYPOTHESIS
    return RECORD_KIND_UTTERANCE_MEMORY


def doc_lane(doc: Document) -> LaneName:
    record_kind = _normalize_lane_name(doc.metadata.get("record_kind"))
    if record_kind != RECORD_KIND_UTTERANCE_MEMORY:
        return record_kind

    doc_type = str(doc.metadata.get("type") or "").strip()
    if doc_type == "source_evidence":
        return RECORD_KIND_SOURCE_EVIDENCE
    if doc_type == "promoted_context":
        return RECORD_KIND_PROMOTED_CONTEXT
    if doc_type == "reflection":
        return RECORD_KIND_REFLECTION_HYPOTHESIS
    return RECORD_KIND_UTTERANCE_MEMORY


def is_source_evidence_doc(doc: Document) -> bool:
    return doc_lane(doc) == RECORD_KIND_SOURCE_EVIDENCE


def _lane_rank(lane: LaneName) -> int:
    return _LANE_FUSION_ORDER.index(lane)


def mix_source_evidence_with_memory_cards(
    docs_and_scores: list[tuple[Document, float]],
    *,
    top_k: int,
    source_quota: int = 2,
) -> list[tuple[Document, float]]:
    """Compatibility wrapper for lane-based selection preserving legacy source quota behavior."""
    lane_quotas: dict[LaneName, int] = {
        RECORD_KIND_SOURCE_EVIDENCE: max(source_quota, 0),
        RECORD_KIND_UTTERANCE_MEMORY: max(top_k - source_quota, 0),
        RECORD_KIND_PROMOTED_CONTEXT: 0,
        RECORD_KIND_REFLECTION_HYPOTHESIS: 0,
    }
    return fuse_ranked_candidates_by_lane(docs_and_scores=docs_and_scores, top_k=top_k, lane_quotas=lane_quotas)


def _sorted_lane_candidates(docs_and_scores: list[tuple[Document, float]]) -> dict[LaneName, list[tuple[Document, float]]]:
    lanes: dict[LaneName, list[tuple[Document, float]]] = {lane: [] for lane in _LANE_FUSION_ORDER}
    for doc, score in docs_and_scores:
        lanes[doc_lane(doc)].append((doc, score))
    for lane in _LANE_FUSION_ORDER:
        lanes[lane].sort(key=lambda item: _stable_rank_key(item[1], item[0]))
    return lanes


def fuse_ranked_candidates_by_lane(
    *,
    docs_and_scores: list[tuple[Document, float]],
    top_k: int,
    lane_quotas: dict[LaneName, int],
) -> list[tuple[Document, float]]:
    if top_k <= 0 or not docs_and_scores:
        return []

    lanes = _sorted_lane_candidates(docs_and_scores)
    selected: list[tuple[Document, float]] = []
    consumed: dict[LaneName, int] = {lane: 0 for lane in _LANE_FUSION_ORDER}

    for lane in _LANE_FUSION_ORDER:
        quota = max(lane_quotas.get(lane, 0), 0)
        if quota == 0:
            continue
        lane_docs = lanes[lane]
        take = min(quota, top_k - len(selected), len(lane_docs))
        if take <= 0:
            continue
        selected.extend(lane_docs[:take])
        consumed[lane] = take
        if len(selected) >= top_k:
            return selected

    leftovers: list[tuple[Document, float]] = []
    for lane in _LANE_FUSION_ORDER:
        leftovers.extend(lanes[lane][consumed[lane] :])
    leftovers.sort(key=lambda item: (_stable_rank_key(item[1], item[0]), _lane_rank(doc_lane(item[0]))))
    selected.extend(leftovers[: max(top_k - len(selected), 0)])
    return selected


def adaptive_sigma_fractional(
    *,
    now: arrow.Arrow,
    target: arrow.Arrow,
    frac: float = 0.25,  # σ = 25% of |target-now|
    sigma_min: float = 10 * 60,  # 10 min
    sigma_max: float = 30 * 24 * 3600,  # 30 days
) -> float:
    d = abs((target - now).total_seconds())
    sigma = frac * d
    return max(sigma_min, min(sigma, sigma_max))


def _temporal_weight_and_quality(
    doc_ts_iso: str,
    *,
    target: arrow.Arrow,
    sigma_seconds: float,
    neutral_temporal_prior: float,
) -> tuple[float, str]:
    raw_ts = str(doc_ts_iso or "").strip()
    if not raw_ts:
        return float(neutral_temporal_prior), "missing"

    try:
        ts = arrow.get(raw_ts)
    except Exception:
        return float(neutral_temporal_prior), "invalid"

    dt = (ts - target).total_seconds()
    return math.exp(-(dt * dt) / (2.0 * sigma_seconds * sigma_seconds)), "valid"


def time_weight(doc_ts_iso: str, target: arrow.Arrow, sigma_seconds: float) -> float:
    return _temporal_weight_and_quality(
        doc_ts_iso,
        target=target,
        sigma_seconds=sigma_seconds,
        neutral_temporal_prior=DEFAULT_RERANK_COEFFICIENTS.neutral_temporal_prior,
    )[0]


def similarity_with_time_and_type_score(
    *,
    sim_score: float,
    doc_type: str,
    doc_ts_iso: str,
    target: arrow.Arrow,
    sigma_seconds: float,
) -> float:
    return rerank_objective_score_components(
        sim_score=sim_score,
        doc_type=doc_type,
        doc_ts_iso=doc_ts_iso,
        target=target,
        sigma_seconds=sigma_seconds,
    )["final_score"]


def rerank_objective_score_components(
    *,
    sim_score: float,
    doc_type: str,
    doc_ts_iso: str,
    target: arrow.Arrow,
    sigma_seconds: float,
    coefficients: RerankObjectiveCoefficients | None = None,
) -> dict[str, float | str]:
    active_config = load_rerank_objective_config()
    effective_coefficients = coefficients or active_config.coefficients
    temporal_gaussian_weight, timestamp_quality = _temporal_weight_and_quality(
        doc_ts_iso,
        target=target,
        sigma_seconds=sigma_seconds,
        neutral_temporal_prior=effective_coefficients.neutral_temporal_prior,
    )
    inferred_lane = _normalize_lane_name(doc_type)
    type_prior = (
        effective_coefficients.reflection_type_prior if inferred_lane == RECORD_KIND_REFLECTION_HYPOTHESIS else effective_coefficients.default_type_prior
    )
    lane_coefficients = effective_coefficients.lane_coefficients or DEFAULT_LANE_COEFFICIENTS
    lane_prior = lane_coefficients.get(inferred_lane, 1.0)
    temporal_blend = (
        effective_coefficients.base_temporal_blend
        + (effective_coefficients.gaussian_temporal_blend * temporal_gaussian_weight)
    )
    final_score = type_prior * lane_prior * float(sim_score) * temporal_blend
    return {
        "objective": _objective_label(active_config),
        "objective_version": active_config.objective_version,
        "semantic_score": float(sim_score),
        "semantic_similarity": float(sim_score),
        "temporal_gaussian_weight": float(temporal_gaussian_weight),
        "time_decay_freshness": float(temporal_gaussian_weight),
        "temporal_blend": float(temporal_blend),
        "timestamp_quality": timestamp_quality,
        "type_prior": float(type_prior),
        "lane_prior": float(lane_prior),
        "lane": inferred_lane,
        "final_score": float(final_score),
    }


def _doc_id(doc: Document) -> str:
    return str(doc.id or doc.metadata.get("doc_id") or "").strip()


def _ts_epoch(doc: Document) -> float:
    raw = str(doc.metadata.get("ts") or "").strip()
    if not raw:
        return float("-inf")
    try:
        return arrow.get(raw).float_timestamp
    except Exception:
        return float("-inf")


def _card_rank(doc: Document) -> int:
    doc_type = str(doc.metadata.get("type") or "")
    return _CARD_TYPE_PRIORITY.get(doc_type, 2)


def _tie_break_key(doc: Document) -> tuple[float, int, str]:
    # Newer timestamp first; non-reflection cards first; doc_id lexical for stable ordering.
    return (_ts_epoch(doc), -_card_rank(doc), _doc_id(doc))


def _stable_rank_key(score: float, doc: Document) -> tuple[float, float, int, str]:
    # Normalize floating-point noise so ordering is deterministic under near-ties.
    return (-round(score, 12), -_ts_epoch(doc), _card_rank(doc), _doc_id(doc))


def rerank_docs_with_time_and_type(
    docs_and_scores: list[tuple[Document, float]],
    *,
    now: arrow.Arrow,
    target: arrow.Arrow,
    sigma_seconds: float,
    exclude_doc_ids: set[str],
    exclude_source_ids: set[str],
    top_k: int = 4,
    near_tie_delta: float = 0.02,
) -> list[Document]:
    return rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=target,
        sigma_seconds=sigma_seconds,
        exclude_doc_ids=exclude_doc_ids,
        exclude_source_ids=exclude_source_ids,
        top_k=top_k,
        near_tie_delta=near_tie_delta,
    ).docs


def rerank_docs_with_time_and_type_outcome(
    docs_and_scores: list[tuple[Document, float]],
    *,
    now: arrow.Arrow,
    target: arrow.Arrow,
    sigma_seconds: float,
    exclude_doc_ids: set[str],
    exclude_source_ids: set[str],
    top_k: int = 4,
    near_tie_delta: float = 0.02,
) -> RerankOutcome:
    """
    docs_and_scores: output of similarity_search_with_score -> [(doc, sim_score), ...]
    """
    del now  # kept for call-site signature parity.

    scored: list[tuple[float, Document, dict[str, float | str]]] = []

    for doc, sim in docs_and_scores:
        doc_id = _doc_id(doc)
        if doc_id and doc_id in exclude_doc_ids:
            continue
        if doc.metadata.get("source_doc_id") in exclude_source_ids:
            continue

        objective_components = rerank_objective_score_components(
            sim_score=sim,
            doc_type=doc.metadata.get("type", ""),
            doc_ts_iso=doc.metadata.get("ts", ""),
            target=target,
            sigma_seconds=sigma_seconds,
        )
        scored.append((float(objective_components["final_score"]), doc, objective_components))

    scored.sort(key=lambda x: _stable_rank_key(x[0], x[1]))
    fusion_config = load_rerank_objective_config().lane_fusion
    lane_quotas: dict[LaneName, int] = {
        lane: fusion_config.get(lane, 0)
        for lane in _LANE_FUSION_ORDER
    }
    fused_docs_and_scores = fuse_ranked_candidates_by_lane(
        docs_and_scores=[(doc, score) for score, doc, _ in scored],
        top_k=top_k,
        lane_quotas=lane_quotas,
    )
    docs = [doc for doc, _ in fused_docs_and_scores]
    threshold = rerank_confidence_thresholds().top_final_score_min
    component_by_doc_id: dict[str, dict[str, float | str]] = {}
    for score, doc, components in scored:
        doc_id = _doc_id(doc)
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        has_provenance_fields = bool(doc_id and str(metadata.get("ts") or ""))
        provenance_citation_factor = 1.0 if has_provenance_fields else 0.85
        component_by_doc_id[doc_id] = {
            "doc_id": doc_id,
            "doc_type": str(metadata.get("type") or ""),
            "ts": str(metadata.get("ts") or ""),
            "provenance_citation_factor": float(provenance_citation_factor),
            "threshold": float(threshold),
            "passes_threshold": bool(float(components.get("final_score", 0.0) or 0.0) >= threshold),
            **components,
        }
    scored_candidates = [component_by_doc_id.get(_doc_id(doc), {}) for doc, _ in fused_docs_and_scores]

    near_tie_candidates: list[dict[str, float | str]] = []
    ambiguity_detected = False
    if scored:
        top_score = scored[0][0]
        epsilon = 1e-12
        near_tie = [(score, doc) for score, doc, _ in scored if (top_score - score) <= (near_tie_delta + epsilon)]
        near_tie_candidates = [
            {
                "doc_id": _doc_id(doc),
                "score": float(score),
            }
            for score, doc in near_tie
        ]

        if len(near_tie) > 1:
            top_key = _tie_break_key(near_tie[0][1])
            unresolved = [doc for _, doc in near_tie if _tie_break_key(doc) == top_key]
            ambiguity_detected = len(unresolved) > 1

    return RerankOutcome(
        docs=docs,
        ambiguity_detected=ambiguity_detected,
        near_tie_candidates=near_tie_candidates,
        scored_candidates=scored_candidates,
    )


def has_sufficient_context_confidence_from_objective(
    *,
    scored_candidates: list[dict[str, float | str]],
    ambiguity_detected: bool,
    thresholds: ContextConfidenceThresholds | None = None,
) -> bool:
    effective_thresholds = thresholds or rerank_confidence_thresholds()
    if not scored_candidates:
        return False

    top_score = float(scored_candidates[0].get("final_score", 0.0) or 0.0)
    if top_score < effective_thresholds.top_final_score_min:
        return False

    if len(scored_candidates) > 1:
        second_score = float(scored_candidates[1].get("final_score", 0.0) or 0.0)
        if (top_score - second_score) < effective_thresholds.min_margin_to_second:
            return False

    if not ambiguity_detected:
        return True

    if not effective_thresholds.allow_ambiguity_override:
        return False
    return top_score >= effective_thresholds.ambiguity_override_top_final_score_min
