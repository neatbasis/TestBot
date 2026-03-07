from __future__ import annotations

import uuid
from dataclasses import dataclass

import yaml

from testbot.memory_cards import make_reflection_card, store_doc
from testbot.vector_store import MemoryStore


@dataclass(frozen=True)
class PromotionItem:
    text: str
    category: str
    confidence: float


@dataclass(frozen=True)
class PromotionDecision:
    items: list[PromotionItem]
    rejected_reasons: list[str]


@dataclass(frozen=True)
class ReflectionClaimRecord:
    text: str
    category: str
    reliability: str
    source: str


@dataclass(frozen=True)
class ReflectionPayload:
    claims: list[ReflectionClaimRecord]
    uncertainties: list[str]
    confidence: float


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _infer_claim_category(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("intent", "goal", "objective", "asking for", "requesting")):
        return "clarified_intent"
    if any(
        token in lowered
        for token in (
            "definition",
            "means",
            "refers to",
            "domain context",
            "relevant summary",
            "source evidence",
            "evidence from",
            "context",
        )
    ):
        return "accepted_context"
    return "other"


def _infer_claim_reliability(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("maybe", "might", "unsure", "conflict", "contradict")):
        return "uncertain"
    return "reliable"


def _normalize_claim_record(raw_claim: object) -> ReflectionClaimRecord | None:
    if isinstance(raw_claim, str):
        text = raw_claim.strip()
        if not text:
            return None
        return ReflectionClaimRecord(
            text=text,
            category=_infer_claim_category(text),
            reliability=_infer_claim_reliability(text),
            source="reflection_text",
        )

    if not isinstance(raw_claim, dict):
        return None

    text = str(raw_claim.get("text") or raw_claim.get("claim") or "").strip()
    if not text and len(raw_claim) == 1:
        key, value = next(iter(raw_claim.items()))
        key_text = str(key).strip()
        value_text = str(value).strip()
        text = f"{key_text}: {value_text}" if value_text else key_text
    if not text:
        return None

    category = str(raw_claim.get("category") or _infer_claim_category(text)).strip().lower()
    reliability = str(raw_claim.get("reliability") or _infer_claim_reliability(text)).strip().lower()
    source = str(raw_claim.get("source") or "reflection_structured").strip().lower()

    return ReflectionClaimRecord(
        text=text,
        category=category or "other",
        reliability=reliability or "unknown",
        source=source or "unknown",
    )


def _parse_reflection_yaml(reflection_yaml: str) -> ReflectionPayload:
    try:
        payload = yaml.safe_load(reflection_yaml or "")
    except yaml.YAMLError:
        return ReflectionPayload(claims=[], uncertainties=[], confidence=0.0)
    if not isinstance(payload, dict):
        return ReflectionPayload(claims=[], uncertainties=[], confidence=0.0)

    raw_claims = payload.get("claims")
    claims: list[ReflectionClaimRecord] = []
    if isinstance(raw_claims, list):
        for raw_claim in raw_claims:
            normalized = _normalize_claim_record(raw_claim)
            if normalized is not None:
                claims.append(normalized)

    return ReflectionPayload(
        claims=claims,
        uncertainties=_safe_str_list(payload.get("uncertainties")),
        confidence=_safe_float(payload.get("confidence", 0.0)),
    )


def _contains_internal_debug(claim: ReflectionClaimRecord) -> bool:
    lowered = f"{claim.text} {claim.category} {claim.source}".lower()
    return any(token in lowered for token in ("debug", "internal", "trace", "stack"))


def evaluate_promotion_policy(
    *,
    reflection_yaml: str,
    min_confidence: float = 0.75,
) -> PromotionDecision:
    parsed = _parse_reflection_yaml(reflection_yaml)
    claims = parsed.claims
    uncertainties = parsed.uncertainties
    confidence = parsed.confidence

    rejected: list[str] = []
    if confidence < min_confidence:
        rejected.append("confidence_below_threshold")
    if uncertainties:
        rejected.append("has_uncertainties")

    items: list[PromotionItem] = []
    for claim in claims:
        if _contains_internal_debug(claim):
            rejected.append("contains_internal_debug")
            continue
        if claim.reliability in {"uncertain", "conflicting", "unknown", "low"}:
            rejected.append("claim_uncertain_or_conflicting")
            continue

        if claim.category in {"clarified_intent", "intent", "user_intent", "goal", "objective"}:
            items.append(PromotionItem(text=claim.text, category="clarified_intent", confidence=confidence))
            continue
        if claim.category in {
            "accepted_context",
            "definition",
            "domain_context",
            "source_evidence",
            "context",
            "relevant_summary",
        }:
            items.append(PromotionItem(text=claim.text, category="accepted_context", confidence=confidence))

    if rejected:
        items = []

    return PromotionDecision(items=items, rejected_reasons=sorted(set(rejected)))


def persist_promoted_context(
    *,
    store: MemoryStore,
    ts_iso: str,
    source_doc_id: str,
    source_reflection_id: str,
    reflection_yaml: str,
    channel: str,
) -> list[str]:
    decision = evaluate_promotion_policy(reflection_yaml=reflection_yaml)
    promoted_ids: list[str] = []
    if not decision.items:
        return promoted_ids

    for item in decision.items:
        doc_id = str(uuid.uuid4())
        promoted_yaml = (
            f"claims:\n"
            f"  - {item.text}\n"
            "commitments: []\n"
            "preferences: []\n"
            "uncertainties: []\n"
            "followups: []\n"
            f"confidence: {item.confidence:.2f}"
        )
        content = make_reflection_card(
            ts_iso=ts_iso,
            about="promotion_policy",
            source_doc_id=source_doc_id,
            doc_id=doc_id,
            reflection_yaml=promoted_yaml,
        )
        store_doc(
            store,
            doc_id=doc_id,
            content=content,
            metadata={
                "ts": ts_iso,
                "type": "promoted_context",
                "promotion_category": item.category,
                "source_doc_id": source_doc_id,
                "source_reflection_id": source_reflection_id,
                "channel": channel,
                "doc_id": doc_id,
                "raw": item.text,
            },
        )
        promoted_ids.append(doc_id)

    return promoted_ids
