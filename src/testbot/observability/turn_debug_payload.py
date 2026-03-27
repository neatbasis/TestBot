from __future__ import annotations

import json

from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot.reflection_policy import fallback_reason as derive_fallback_reason
from testbot.reject_taxonomy import RejectSignal, derive_reject_signal

_DEBUG_TOP_LEVEL_FIELDS = {
    "debug.intent",
    "debug.rewrite",
    "debug.retrieval",
    "debug.rerank",
    "debug.confidence",
    "debug.observation",
    "debug.contract",
    "debug.policy",
}


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    as_string = str(value).strip()
    if not as_string:
        return None
    return as_string


def _derive_reject_signal(
    *,
    intent_label: str,
    answer_mode: str,
    fallback_action: str,
    context_confident: bool,
    context_score: float,
    hit_count: int,
    ambiguity_detected: bool,
    answer_contract_valid: bool,
    general_knowledge_contract_valid: bool,
    general_knowledge_contract_applicability: str,
) -> RejectSignal:
    return derive_reject_signal(
        intent_label=intent_label,
        answer_mode=answer_mode,
        fallback_action=fallback_action,
        context_confident=context_confident,
        context_score=context_score,
        hit_count=hit_count,
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
        general_knowledge_contract_applicability=general_knowledge_contract_applicability,
    )


def _gate_metrics(*, passed: bool, score: float, threshold: float) -> dict[str, float | bool]:
    margin = round(score - threshold, 4)
    return {
        "passed": passed,
        "score": round(score, 4),
        "threshold": round(threshold, 4),
        "margin": margin,
    }


def _nearest_failure_gate(*, gates: dict[str, dict[str, float | bool]]) -> dict[str, float | str] | None:
    failed: list[tuple[str, float, float]] = []
    for name, gate in gates.items():
        passed = bool(gate.get("passed", False))
        if passed:
            continue
        score = float(gate.get("score", 0.0) or 0.0)
        threshold = float(gate.get("threshold", 0.0) or 0.0)
        failed.append((name, score, threshold))
    if not failed:
        return None
    nearest_name, nearest_score, nearest_threshold = min(
        failed,
        key=lambda item: max(0.0, item[2] - item[1]),
    )
    return {
        "gate": nearest_name,
        "current": round(nearest_score, 4),
        "required": round(nearest_threshold, 4),
        "margin_to_pass": round(max(0.0, nearest_threshold - nearest_score), 4),
    }


def _gate_delta_entry(*, family: str, gate_name: str, gate: dict[str, float | bool]) -> dict[str, float | str]:
    score = float(gate.get("score", 0.0) or 0.0)
    threshold = float(gate.get("threshold", 0.0) or 0.0)
    return {
        "family": family,
        "gate": gate_name,
        "current": round(score, 4),
        "required": round(threshold, 4),
        "delta_to_pass": round(max(0.0, threshold - score), 4),
    }


def _dominant_score_contributors(*, score_decomposition: list[dict[str, object]], max_items: int = 2) -> list[dict[str, float | str]]:
    if not score_decomposition:
        return []
    top_candidate = score_decomposition[0] if isinstance(score_decomposition[0], dict) else {}
    contributor_pairs: list[tuple[str, float]] = [
        ("time_decay_freshness", float(top_candidate.get("time_decay_freshness", 0.0) or 0.0)),
        ("semantic_similarity", float(top_candidate.get("semantic_similarity", 0.0) or 0.0)),
        ("type_prior", float(top_candidate.get("type_prior", 0.0) or 0.0)),
        ("provenance_citation_factor", float(top_candidate.get("provenance_citation_factor", 0.0) or 0.0)),
    ]
    ordered = sorted(contributor_pairs, key=lambda item: (-abs(1.0 - item[1]), item[0]))
    dominant: list[dict[str, float | str]] = []
    for component, value in ordered[:max_items]:
        dominant.append(
            {
                "component": component,
                "current": round(value, 4),
                "delta_to_ideal": round(max(0.0, 1.0 - value), 4),
            }
        )
    return dominant


def _counterfactual_policy_passes(
    *,
    intent_label: str,
    action: str,
    context_confident: bool,
    context_score: float,
    hit_count: int,
    ambiguity_detected: bool,
    answer_contract_valid: bool,
    general_knowledge_contract_valid: bool,
    general_knowledge_contract_applicability: str,
) -> bool:
    action_to_mode = {
        "ROUTE_TO_ASK": "clarify",
        "ASK_CLARIFYING_QUESTION": "clarify",
        "ANSWER_UNKNOWN": "dont-know",
        "ANSWER_TIME": "assist",
        "OFFER_CAPABILITY_ALTERNATIVES": "assist",
        "ANSWER_FROM_MEMORY": "memory-grounded",
        "ANSWER_GENERAL_KNOWLEDGE": "assist",
    }
    mapped_mode = action_to_mode.get(action, "assist")
    signal = _derive_reject_signal(
        intent_label=intent_label,
        answer_mode=mapped_mode,
        fallback_action=action,
        context_confident=context_confident,
        context_score=context_score,
        hit_count=hit_count,
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
        general_knowledge_contract_applicability=general_knowledge_contract_applicability,
    )
    return signal.reject_code == "NONE"


def _policy_action_universe(*, intent_label: str) -> list[str]:
    if intent_label == "memory_recall":
        return [
            "ROUTE_TO_ASK",
            "ASK_CLARIFYING_QUESTION",
            "OFFER_CAPABILITY_ALTERNATIVES",
            "ANSWER_FROM_MEMORY",
            "ANSWER_GENERAL_KNOWLEDGE",
            "ANSWER_UNKNOWN",
        ]
    if intent_label == "time_query":
        return ["ANSWER_TIME", "ANSWER_UNKNOWN", "ANSWER_GENERAL_KNOWLEDGE"]
    return ["ANSWER_GENERAL_KNOWLEDGE", "ANSWER_UNKNOWN", "OFFER_CAPABILITY_ALTERNATIVES"]


def _policy_alternative_rejection_reason(
    *,
    action: str,
    chosen_action: str,
    context_confident: bool,
    ambiguity_detected: bool,
    hit_count: int,
) -> str:
    if action == chosen_action:
        return "selected"
    if action == "ROUTE_TO_ASK":
        return "ask route rejected: ambiguity or ask-capability requirements were not met"
    if action == "ASK_CLARIFYING_QUESTION":
        return "clarifier rejected: policy preferred either ask route or capability alternatives"
    if action == "OFFER_CAPABILITY_ALTERNATIVES":
        if context_confident and hit_count > 0:
            return "alternatives rejected: confident retrieval context supported direct handling"
        return "alternatives rejected: policy chose a stricter uncertainty handling path"
    if action == "ANSWER_TIME":
        return "time answer rejected: intent was not a time query"
    if action == "ANSWER_UNKNOWN":
        if context_confident and not ambiguity_detected:
            return "unknown fallback rejected: confidence gates passed"
        return "unknown fallback rejected: policy preferred a more specific fallback path"
    if action == "ANSWER_FROM_MEMORY":
        return "memory-grounded path rejected: retrieval confidence or ambiguity policy did not permit direct answer"
    if action == "ANSWER_GENERAL_KNOWLEDGE":
        return "general-knowledge path rejected: retrieval/policy gates required fallback behavior"
    return "alternative rejected by deterministic fallback policy"


def _build_policy_alternatives(
    *,
    intent_label: str,
    chosen_action: str,
    context_confident: bool,
    ambiguity_detected: bool,
    hit_count: int,
) -> list[dict[str, str]]:
    alternatives: list[dict[str, str]] = []
    for action in _policy_action_universe(intent_label=intent_label):
        alternatives.append(
            {
                "action": action,
                "status": "selected" if action == chosen_action else "rejected",
                "reason": _policy_alternative_rejection_reason(
                    action=action,
                    chosen_action=chosen_action,
                    context_confident=context_confident,
                    ambiguity_detected=ambiguity_detected,
                    hit_count=hit_count,
                ),
            }
        )
    return alternatives


def validate_debug_turn_payload_schema(payload: dict[str, object]) -> None:
    actual_top_level = set(payload.keys())
    if actual_top_level != _DEBUG_TOP_LEVEL_FIELDS:
        missing = sorted(_DEBUG_TOP_LEVEL_FIELDS - actual_top_level)
        extra = sorted(actual_top_level - _DEBUG_TOP_LEVEL_FIELDS)
        raise ValueError(f"debug payload schema drift: missing={missing}, extra={extra}")

    gate_sections = {
        "debug.rerank": ["top_final_score_gate", "margin_gate", "ambiguity_gate"],
        "debug.confidence": ["context_confident_gate"],
        "debug.contract": ["answer_contract_gate", "general_knowledge_contract_gate"],
    }
    required_gate_fields = {"passed", "score", "threshold", "margin"}

    for section_key, gate_keys in gate_sections.items():
        section = payload.get(section_key)
        if not isinstance(section, dict):
            raise ValueError(f"debug payload schema drift: {section_key} must be an object")
        for gate_key in gate_keys:
            gate = section.get(gate_key)
            if not isinstance(gate, dict):
                raise ValueError(f"debug payload schema drift: {section_key}.{gate_key} must be an object")
            if set(gate.keys()) != required_gate_fields:
                raise ValueError(
                    f"debug payload schema drift: {section_key}.{gate_key} fields changed; "
                    f"expected={sorted(required_gate_fields)}, actual={sorted(gate.keys())}"
                )

        if section_key == "debug.contract":
            applicability = section.get("general_knowledge_contract_applicability")
            if applicability not in {"applicable", "not_applicable"}:
                raise ValueError(
                    "debug payload schema drift: debug.contract.general_knowledge_contract_applicability "
                    "must be 'applicable' or 'not_applicable'"
                )
            if not isinstance(section.get("general_knowledge_contract_failed_when_applicable"), bool):
                raise ValueError(
                    "debug payload schema drift: debug.contract.general_knowledge_contract_failed_when_applicable "
                    "must be a boolean"
                )


def build_debug_turn_payload(*, state: PipelineState, intent_label: str, hits: list[Document]) -> dict[str, object]:
    confidence_payload = state.confidence_decision.to_dict()
    invariant_payload = state.invariant_decisions.to_dict()
    fallback_action = str(invariant_payload.get("fallback_action", "NONE"))
    retrieval_branch = str(confidence_payload.get("retrieval_branch", "memory_retrieval"))
    answer_mode = str(invariant_payload.get("answer_mode", "dont-know"))
    context_confident = bool(confidence_payload.get("context_confident", False))
    ambiguity_detected = bool(confidence_payload.get("ambiguity_detected", False))
    answer_contract_valid = bool(invariant_payload.get("answer_contract_valid", True))
    general_knowledge_contract_valid = bool(invariant_payload.get("general_knowledge_contract_valid", True))
    general_knowledge_contract_applicability = str(
        invariant_payload.get("general_knowledge_contract_applicability", "applicable") or "applicable"
    )
    scored_candidates = confidence_payload.get("scored_candidates", [])
    top_score = 0.0
    second_score = 0.0
    if isinstance(scored_candidates, list) and scored_candidates:
        top_candidate = scored_candidates[0] if isinstance(scored_candidates[0], dict) else {}
        top_score = float(top_candidate.get("final_score", 0.0) or 0.0)
        if len(scored_candidates) > 1 and isinstance(scored_candidates[1], dict):
            second_score = float(scored_candidates[1].get("final_score", 0.0) or 0.0)
    observed_margin = max(0.0, top_score - second_score)
    top_threshold = float(confidence_payload.get("top_final_score_min", 0.0) or 0.0)
    margin_threshold = float(confidence_payload.get("min_margin_to_second", 0.0) or 0.0)
    ambiguity_threshold = 0.5
    context_score = min(
        top_score / top_threshold if top_threshold > 0 else 1.0,
        observed_margin / margin_threshold if margin_threshold > 0 else 1.0,
    )

    reject_signal = _derive_reject_signal(
        intent_label=intent_label,
        answer_mode=answer_mode,
        fallback_action=fallback_action,
        context_confident=context_confident,
        context_score=context_score,
        hit_count=len(hits),
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
        general_knowledge_contract_applicability=general_knowledge_contract_applicability,
    )
    doc_ids = [(doc.id or doc.metadata.get("doc_id") or "") for doc in hits[:3]]
    ambiguity_score = 1.0 if not ambiguity_detected else 0.0
    observed_docs: list[dict[str, object]] = []
    for doc in hits[:3]:
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        observed_docs.append(
            {
                "doc_id": str(doc.id or metadata.get("doc_id") or ""),
                "card_type": str(metadata.get("card_type") or metadata.get("type") or ""),
                "ts": str(metadata.get("ts") or ""),
                "window_start": str(metadata.get("window_start") or confidence_payload.get("window_start") or ""),
                "window_end": str(metadata.get("window_end") or confidence_payload.get("window_end") or ""),
                "source": str(metadata.get("source") or ""),
            }
        )

    score_decomposition: list[dict[str, object]] = []
    if isinstance(scored_candidates, list):
        for candidate in scored_candidates[:3]:
            if not isinstance(candidate, dict):
                continue
            score_decomposition.append(
                {
                    "doc_id": str(candidate.get("doc_id") or ""),
                    "semantic_similarity": float(candidate.get("semantic_similarity", candidate.get("semantic_score", 0.0)) or 0.0),
                    "time_decay_freshness": float(candidate.get("time_decay_freshness", candidate.get("temporal_gaussian_weight", 0.0)) or 0.0),
                    "type_prior": float(candidate.get("type_prior", 0.0) or 0.0),
                    "provenance_citation_factor": float(candidate.get("provenance_citation_factor", 0.0) or 0.0),
                    "final_score": float(candidate.get("final_score", 0.0) or 0.0),
                    "threshold": float(candidate.get("threshold", top_threshold) or 0.0),
                    "passes_threshold": bool(candidate.get("passes_threshold", False)),
                }
            )
    policy_alternatives = _build_policy_alternatives(
        intent_label=intent_label,
        chosen_action=fallback_action,
        context_confident=context_confident,
        ambiguity_detected=ambiguity_detected,
        hit_count=len(hits),
    )
    policy_thresholds = {
        "top_final_score_min": round(top_threshold, 4),
        "min_margin_to_second": round(margin_threshold, 4),
        "ambiguity_threshold": round(ambiguity_threshold, 4),
        "context_score_target": 1.0,
    }
    policy_rationale = invariant_payload.get("answer_policy_rationale", {})
    policy_fallback_reason = ""
    if isinstance(policy_rationale, dict):
        policy_fallback_reason = str(policy_rationale.get("fallback_reason") or "")
    if not policy_fallback_reason or policy_fallback_reason == "decision_object_mapping":
        source_confidence = confidence_payload.get("source_confidence")
        policy_fallback_reason = derive_fallback_reason(
            intent=intent_label if intent_label in {"memory_recall", "time_query", "non_memory"} else "non_memory",
            fallback_action=fallback_action if fallback_action in {
                "ANSWER_FROM_MEMORY",
                "ANSWER_TIME",
                "ANSWER_GENERAL_KNOWLEDGE",
                "ANSWER_UNKNOWN",
                "ASK_CLARIFYING_QUESTION",
                "ROUTE_TO_ASK",
                "OFFER_CAPABILITY_ALTERNATIVES",
            } else "ANSWER_UNKNOWN",
            memory_hit=context_confident,
            ambiguity=ambiguity_detected,
            source_confidence=float(source_confidence) if source_confidence is not None else None,
        )

    top_final_score_gate = _gate_metrics(
        passed=top_score >= top_threshold,
        score=top_score,
        threshold=top_threshold,
    )
    margin_gate = _gate_metrics(
        passed=observed_margin >= margin_threshold,
        score=observed_margin,
        threshold=margin_threshold,
    )
    ambiguity_gate = _gate_metrics(
        passed=not ambiguity_detected,
        score=ambiguity_score,
        threshold=ambiguity_threshold,
    )
    context_confident_gate = _gate_metrics(
        passed=context_confident,
        score=context_score,
        threshold=1.0,
    )
    answer_contract_gate = _gate_metrics(
        passed=answer_contract_valid,
        score=1.0 if answer_contract_valid else 0.0,
        threshold=1.0,
    )
    general_knowledge_contract_gate = _gate_metrics(
        passed=(
            general_knowledge_contract_applicability == "not_applicable"
            or general_knowledge_contract_valid
        ),
        score=(
            1.0
            if general_knowledge_contract_applicability == "not_applicable"
            else (1.0 if general_knowledge_contract_valid else 0.0)
        ),
        threshold=1.0,
    )

    rejected_turn = reject_signal.reject_code != "NONE"
    nearest_failure_gate = _nearest_failure_gate(
        gates={
            "top_final_score_gate": top_final_score_gate,
            "margin_gate": margin_gate,
            "ambiguity_gate": ambiguity_gate,
            "context_confident_gate": context_confident_gate,
            "answer_contract_gate": answer_contract_gate,
            "general_knowledge_contract_gate": general_knowledge_contract_gate,
        }
    )

    nearest_pass_frontier: list[dict[str, float | str]] = []
    if rejected_turn:
        gate_families: tuple[tuple[str, str, dict[str, float | bool]], ...] = (
            ("rerank", "top_final_score_gate", top_final_score_gate),
            ("rerank", "margin_gate", margin_gate),
            ("rerank", "ambiguity_gate", ambiguity_gate),
            ("confidence", "context_confident_gate", context_confident_gate),
            ("contract", "answer_contract_gate", answer_contract_gate),
            ("contract", "general_knowledge_contract_gate", general_knowledge_contract_gate),
        )
        if intent_label == "time_query" or bool(confidence_payload.get("anaphora_detected", False)):
            gate_families += (("temporal", "temporal_reference_gate", _gate_metrics(
                passed=reject_signal.reject_code != "TEMPORAL_REFERENCE_UNRESOLVED",
                score=reject_signal.score if reject_signal.partition == "temporal" else 1.0,
                threshold=reject_signal.threshold if reject_signal.partition == "temporal" else 1.0,
            )),)

        closest_by_family: dict[str, dict[str, float | str]] = {}
        for family, gate_name, gate in gate_families:
            if bool(gate.get("passed", False)):
                continue
            entry = _gate_delta_entry(family=family, gate_name=gate_name, gate=gate)
            current = closest_by_family.get(family)
            if current is None:
                closest_by_family[family] = entry
                continue
            if (
                float(entry["delta_to_pass"]) < float(current["delta_to_pass"])
                or (
                    float(entry["delta_to_pass"]) == float(current["delta_to_pass"])
                    and str(entry["gate"]) < str(current["gate"])
                )
            ):
                closest_by_family[family] = entry
        nearest_pass_frontier = [closest_by_family[k] for k in sorted(closest_by_family)]

    top_candidate_pass_thresholds = {
        "top_final_score_min": round(max(top_threshold, top_score), 4),
        "min_margin_to_second": round(max(margin_threshold, observed_margin), 4),
        "context_score_target": 1.0,
    }
    clarify_policy_passes = _counterfactual_policy_passes(
        intent_label=intent_label,
        action="ASK_CLARIFYING_QUESTION",
        context_confident=context_confident,
        context_score=context_score,
        hit_count=len(hits),
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
        general_knowledge_contract_applicability=general_knowledge_contract_applicability,
    )
    route_to_ask_policy_passes = _counterfactual_policy_passes(
        intent_label=intent_label,
        action="ROUTE_TO_ASK",
        context_confident=context_confident,
        context_score=context_score,
        hit_count=len(hits),
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
        general_knowledge_contract_applicability=general_knowledge_contract_applicability,
    )

    payload = {
        "debug.intent": {
            "resolved": intent_label,
            "classified": state.classified_intent,
            "predicted": str(confidence_payload.get("intent_predicted") or state.classified_intent),
            "confidence": _optional_float(confidence_payload.get("intent_classifier_confidence")),
            "threshold": _optional_float(confidence_payload.get("intent_classifier_threshold")),
            "model": _optional_string(confidence_payload.get("intent_classifier_model")),
            "version": _optional_string(confidence_payload.get("intent_classifier_version")),
            "prior_unresolved": state.prior_unresolved_intent,
        },
        "debug.rewrite": {
            "user_input": state.user_input,
            "rewritten_query": state.rewritten_query,
            "changed": state.user_input.strip() != state.rewritten_query.strip(),
        },
        "debug.retrieval": {
            "branch": retrieval_branch,
            "hit_count": len(hits),
            "retrieved_doc_ids": doc_ids,
            "candidates_considered": float(confidence_payload.get("retrieval_candidates_considered", 0.0) or 0.0),
            "returned_top_k": float(confidence_payload.get("retrieval_returned_top_k", 0.0) or 0.0),
            "threshold": float(confidence_payload.get("retrieval_threshold", 0.0) or 0.0),
            "hygiene": {
                "exclude_doc_ids": confidence_payload.get("retrieval_exclude_doc_ids", []),
                "exclude_source_ids": confidence_payload.get("retrieval_exclude_source_ids", []),
                "exclude_turn_scoped_ids": confidence_payload.get("retrieval_exclude_turn_scoped_ids", []),
                "exclusion_invariant": str(confidence_payload.get("retrieval_exclusion_invariant") or ""),
                "rerank_defense_in_depth": True,
            },
        },
        "debug.rerank": {
            "top_final_score": round(top_score, 4),
            "second_final_score": round(second_score, 4),
            "margin": round(observed_margin, 4),
            "top_final_score_gate": top_final_score_gate,
            "margin_gate": margin_gate,
            "ambiguity_gate": ambiguity_gate,
        },
        "debug.confidence": {
            "context_confident_gate": context_confident_gate,
        },
        "debug.observation": {
            "candidate_evidence": {
                "retrieved_docs": observed_docs,
                "score_components": {
                    "top_final_score": round(top_score, 4),
                    "second_final_score": round(second_score, 4),
                    "observed_margin": round(observed_margin, 4),
                    "top_gate_threshold": round(top_threshold, 4),
                    "margin_gate_threshold": round(margin_threshold, 4),
                    "context_score": round(context_score, 4),
                    "candidate_score_decomposition": score_decomposition,
                },
                "time_windows": {
                    "query_time_window": str(confidence_payload.get("time_window") or ""),
                    "window_start": str(confidence_payload.get("window_start") or ""),
                    "window_end": str(confidence_payload.get("window_end") or ""),
                    "last_user_message_ts": state.last_user_message_ts,
                },
                "ambiguity_state": {
                    "ambiguity_detected": ambiguity_detected,
                    "ambiguous_candidates": confidence_payload.get("ambiguous_candidates", []),
                    "anaphora_detected": bool(confidence_payload.get("anaphora_detected", False)),
                    "candidate_anchors": confidence_payload.get("anchor_candidates", []),
                    "selected_anchor_doc_id": str(confidence_payload.get("selected_anchor_doc_id") or ""),
                    "selected_anchor_ts": str(confidence_payload.get("selected_anchor_ts") or ""),
                    "computed_delta_raw_seconds": confidence_payload.get("computed_delta_raw_seconds"),
                    "computed_delta_humanized": str(confidence_payload.get("computed_delta_humanized") or ""),
                },
            }
        },
        "debug.contract": {
            "answer_contract_gate": answer_contract_gate,
            "general_knowledge_contract_gate": general_knowledge_contract_gate,
            "general_knowledge_contract_applicability": general_knowledge_contract_applicability,
            "general_knowledge_contract_failed_when_applicable": (
                general_knowledge_contract_applicability == "applicable" and not general_knowledge_contract_valid
            ),
        },
        "debug.policy": {
            "chosen_action": fallback_action,
            "considered_alternatives": policy_alternatives,
            "decision_rationale": {
                "reject_signal": {
                    "reject_code": reject_signal.reject_code,
                    "partition": reject_signal.partition,
                    "reason": reject_signal.reason,
                    "score": reject_signal.score,
                    "threshold": reject_signal.threshold,
                    "margin": reject_signal.margin,
                },
                "thresholds": policy_thresholds,
                "answer_policy_inputs": policy_rationale if isinstance(policy_rationale, dict) else {},
            },
            "rejected_turn": rejected_turn,
            "nearest_failure_gate": nearest_failure_gate,
            "counterfactuals": {
                "top_candidate_pass_thresholds": top_candidate_pass_thresholds,
                "nearest_pass_frontier": nearest_pass_frontier,
                "dominant_contributors": _dominant_score_contributors(score_decomposition=score_decomposition),
                "alternate_routing_policy_checks": {
                    "ask_clarifying_question_passes": clarify_policy_passes,
                    "route_to_ask_passes": route_to_ask_policy_passes,
                },
            },
            "answer_mode": answer_mode,
            "fallback_action": fallback_action,
            "reject_code": reject_signal.reject_code,
            "partition": reject_signal.partition,
            "score": reject_signal.score,
            "threshold": reject_signal.threshold,
            "margin": reject_signal.margin,
            "reason": reject_signal.reason,
            "blocker_reason": reject_signal.reason,
            "fallback_reason": policy_fallback_reason,
        },
    }

    validate_debug_turn_payload_schema(payload)
    return payload


def format_debug_turn_trace_payload(*, payload: dict[str, object], verbose: bool = False) -> str:
    validate_debug_turn_payload_schema(payload)

    if verbose:
        return "[debug] " + json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def _metric_fragment(label: str, gate: dict[str, object]) -> str:
        score = float(gate.get("score", 0.0) or 0.0)
        threshold = float(gate.get("threshold", 0.0) or 0.0)
        return f"{label}={score:.3f}>{threshold:.3f}" if bool(gate.get("passed", False)) else f"{label}={score:.3f}<{threshold:.3f}"

    rerank = payload["debug.rerank"]
    confidence = payload["debug.confidence"]
    policy = payload["debug.policy"]
    top1_metric = _metric_fragment("top1", rerank["top_final_score_gate"])
    context_metric = _metric_fragment("context_conf", confidence["context_confident_gate"])
    margin_metric = _metric_fragment("margin", rerank["margin_gate"])

    nearest_failure_fragment = ""
    nearest_failure_gate = policy.get("nearest_failure_gate")
    if bool(policy.get("rejected_turn", False)) and isinstance(nearest_failure_gate, dict):
        gate_name = str(nearest_failure_gate.get("gate", ""))
        gate_margin = float(nearest_failure_gate.get("margin_to_pass", 0.0) or 0.0)
        nearest_failure_fragment = f" nearest_failure={gate_name}:+{gate_margin:.3f};"

    retrieved_doc_ids = payload["debug.retrieval"]["retrieved_doc_ids"]
    retrieved_doc_ids_compact = retrieved_doc_ids[:3] if isinstance(retrieved_doc_ids, list) else retrieved_doc_ids

    return (
        "[debug] "
        f"intent={payload['debug.intent']['resolved']}; "
        f"answer_mode={payload['debug.policy']['answer_mode']}; "
        f"fallback_action={payload['debug.policy']['fallback_action']}; "
        f"retrieval_branch={payload['debug.retrieval']['branch']}; "
        f"context_confident={payload['debug.confidence']['context_confident_gate']['passed']}; "
        f"ambiguity_detected={not payload['debug.rerank']['ambiguity_gate']['passed']}; "
        f"{top1_metric}; "
        f"{context_metric}; "
        f"{margin_metric};"
        f"{nearest_failure_fragment} "
        f"rewritten_query={payload['debug.rewrite']['rewritten_query']!r}; "
        f"retrieved_doc_ids={retrieved_doc_ids_compact}; "
        f"reject_code={payload['debug.policy']['reject_code']}; "
        f"partition={payload['debug.policy']['partition']}; "
        f"blocker_reason={payload['debug.policy']['blocker_reason']}."
    )


def format_debug_turn_trace(*, state: PipelineState, intent_label: str, hits: list[Document], verbose: bool = False) -> str:
    payload = build_debug_turn_payload(state=state, intent_label=intent_label, hits=hits)
    return format_debug_turn_trace_payload(payload=payload, verbose=verbose)


__all__ = [
    "build_debug_turn_payload",
    "format_debug_turn_trace",
    "format_debug_turn_trace_payload",
    "validate_debug_turn_payload_schema",
]
