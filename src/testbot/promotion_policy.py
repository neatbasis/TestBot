from __future__ import annotations

import uuid
from dataclasses import dataclass

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


def _parse_reflection_yaml(reflection_yaml: str) -> dict[str, object]:
    parsed: dict[str, object] = {"claims": [], "uncertainties": [], "confidence": 0.0}
    current_list: str | None = None

    for raw_line in (reflection_yaml or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("claims:"):
            current_list = "claims"
            if line.endswith("[]"):
                parsed["claims"] = []
            continue
        if line.startswith("uncertainties:"):
            current_list = "uncertainties"
            if line.endswith("[]"):
                parsed["uncertainties"] = []
            continue
        if line.startswith("confidence:"):
            current_list = None
            try:
                parsed["confidence"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                parsed["confidence"] = 0.0
            continue
        if line.startswith("-") and current_list in {"claims", "uncertainties"}:
            value = line[1:].strip()
            parsed[current_list] = [*parsed[current_list], value]  # type: ignore[index]

    return parsed


def _is_clarified_intent(claim: str) -> bool:
    lowered = claim.lower()
    return any(token in lowered for token in ("intent", "wants to", "goal is", "asking for"))


def _is_definition_or_domain_context(claim: str) -> bool:
    lowered = claim.lower()
    return any(token in lowered for token in ("definition", "means", "refers to", "domain context"))


def _is_uncertain_or_conflicting(claim: str) -> bool:
    lowered = claim.lower()
    return any(token in lowered for token in ("maybe", "might", "unsure", "conflict", "contradict"))


def _contains_internal_debug(claim: str) -> bool:
    lowered = claim.lower()
    return any(token in lowered for token in ("debug", "internal", "trace", "stack"))


def evaluate_promotion_policy(
    *,
    reflection_yaml: str,
    min_confidence: float = 0.75,
) -> PromotionDecision:
    parsed = _parse_reflection_yaml(reflection_yaml)
    claims = [str(c).strip() for c in parsed.get("claims", []) if str(c).strip()]
    uncertainties = [str(c).strip() for c in parsed.get("uncertainties", []) if str(c).strip()]
    confidence = float(parsed.get("confidence", 0.0) or 0.0)

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
        if _is_uncertain_or_conflicting(claim):
            rejected.append("claim_uncertain_or_conflicting")
            continue

        if _is_clarified_intent(claim):
            items.append(PromotionItem(text=claim, category="clarified_intent", confidence=confidence))
            continue
        if _is_definition_or_domain_context(claim):
            items.append(PromotionItem(text=claim, category="accepted_context", confidence=confidence))

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
