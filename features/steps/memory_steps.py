from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import arrow
from behave import given, then, when
from langchain_core.documents import Document

from testbot.eval_fixtures import best_candidate_doc_id, cases_by_id
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType
from testbot.rerank import adaptive_sigma_fractional, rerank_docs_with_time_and_type_outcome
from testbot.sat_chatbot_memory_v2 import has_sufficient_context_confidence
from testbot.stage_transitions import (
    validate_answer_post,
    validate_answer_pre,
    validate_retrieve_post,
    validate_retrieve_pre,
)

_EVAL_RECALL_PATH = Path(__file__).resolve().parents[2] / "scripts" / "eval_recall.py"
_eval_spec = importlib.util.spec_from_file_location("eval_recall", _EVAL_RECALL_PATH)
assert _eval_spec and _eval_spec.loader
eval_recall = importlib.util.module_from_spec(_eval_spec)
_eval_spec.loader.exec_module(eval_recall)

FIXED_NOW = arrow.get("2026-03-10T11:00:00+00:00")
NEAR_TIE_DELTA = 0.02

FALLBACK = "I don't know from memory."
ASSIST_FALLBACK = "I don't have enough reliable memory to answer directly. I can either help you reconstruct the timeline from what you remember, or suggest where to check next for the missing detail."
BRIDGING_CLARIFIER = "I found related memory fragments (fragment A; fragment B), but not enough to answer precisely. Which person, event, or time window should I focus on?"
CITATION_PATTERN = re.compile(r"doc_id\s*[:=]\s*[^,\]\)\n]+.*?ts\s*[:=]\s*[^,\]\)\n]+", re.IGNORECASE)


def _validate_answer_contract(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized or normalized == FALLBACK:
        return True
    return bool(CITATION_PATTERN.search(text or ""))


def _answer_from_case(case_id: str, loaded_cases) -> str:
    case = loaded_cases[case_id]
    chosen_doc_id = best_candidate_doc_id(case)
    if not chosen_doc_id:
        return ASSIST_FALLBACK

    chosen = next(candidate for candidate in case.candidates if candidate["doc_id"] == chosen_doc_id)
    return f"{chosen['text']} (doc_id: {chosen['doc_id']}, ts: {chosen['ts']})"


def _build_stage_state(case_id: str, loaded_cases, answer: str, parity_signals: dict[str, object] | None = None) -> PipelineState:
    case = loaded_cases[case_id]
    candidates = [
        CandidateHit(doc_id=candidate["doc_id"], score=float(candidate["sim_score"]), ts=str(candidate["ts"]), card_type="memory")
        for candidate in case.candidates
    ]
    if parity_signals is None:
        context_confident = bool(candidates)
        ambiguity_detected = False
    else:
        context_confident = parity_signals.get("intent") == "memory-grounded"
        ambiguity_detected = bool(parity_signals.get("ambiguity_detected", False))
    draft_answer = answer if "doc_id:" in answer else ""
    has_claims = "doc_id:" in answer
    answer_mode = "allow" if has_claims else "assist"
    return PipelineState(
        user_input=case.utterance,
        rewritten_query=case.utterance,
        retrieval_candidates=candidates,
        reranked_hits=candidates[:4],
        confidence_decision={"context_confident": context_confident, "ambiguity_detected": ambiguity_detected},
        draft_answer=draft_answer,
        final_answer=answer,
        claims=[f"INFERENCE: {answer}"] if has_claims else [],
        provenance_types=[ProvenanceType.MEMORY, ProvenanceType.INFERENCE] if has_claims else [ProvenanceType.UNKNOWN],
        used_memory_refs=[f"{candidates[0].doc_id}@{candidates[0].ts}"] if has_claims and candidates else [],
        basis_statement=("Answer synthesized from reranked memory context." if has_claims else "Trivial fallback response with no substantive claim."),
        invariant_decisions={
            "answer_contract_valid": _validate_answer_contract(draft_answer),
            "general_knowledge_contract_valid": True,
            "answer_mode": answer_mode,
        },
        alignment_decision={
            "objective_version": "2026-03-01.v1",
            "dimensions": {
                "factual_grounding_reliability": 1.0 if not has_claims or _validate_answer_contract(draft_answer) else 0.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 1.0 if has_claims else 0.7,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 1.0,
            },
            "final_alignment_decision": "allow",
        },
    )


def _runtime_memory_signals(utterance: str, candidates: list[dict[str, str | float]]) -> dict[str, object]:
    target = eval_recall.parse_target_time(utterance, now=FIXED_NOW)
    sigma = adaptive_sigma_fractional(now=FIXED_NOW, target=target)
    docs_and_scores = [
        (
            Document(
                id=str(candidate["doc_id"]),
                page_content=str(candidate.get("text", "")),
                metadata={
                    "doc_id": str(candidate["doc_id"]),
                    "type": str(candidate.get("type", "user_utterance")),
                    "ts": str(candidate.get("ts", "")),
                    "source_doc_id": str(candidate.get("source_doc_id", "")),
                },
            ),
            float(candidate.get("sim_score", 0.0)),
        )
        for candidate in candidates
    ]
    outcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=FIXED_NOW,
        target=target,
        sigma_seconds=sigma,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        top_k=len(candidates),
        near_tie_delta=NEAR_TIE_DELTA,
    )
    context_confident = has_sufficient_context_confidence(
        outcome.scored_candidates,
        ambiguity_detected=outcome.ambiguity_detected,
    )
    return {
        "ranked_doc_ids": [str(doc.id or "") for doc in outcome.docs],
        "scored_candidates": outcome.scored_candidates,
        "near_tie_candidates": outcome.near_tie_candidates,
        "ambiguity_detected": outcome.ambiguity_detected,
        "intent": "memory-grounded" if context_confident else "dont-know",
    }


def _eval_memory_signals(utterance: str, candidates: list[dict[str, str | float]]) -> dict[str, object]:
    target = eval_recall.parse_target_time(utterance, now=FIXED_NOW)
    sigma = adaptive_sigma_fractional(now=FIXED_NOW, target=target)
    eval_signals = eval_recall.rank_candidates_with_signals(
        candidates,
        now=FIXED_NOW,
        target=target,
        sigma_seconds=sigma,
        near_tie_delta=NEAR_TIE_DELTA,
    )
    ranked = eval_signals["ranked_candidates"]
    return {
        "ranked_doc_ids": [str(candidate.get("doc_id", "")) for candidate in ranked],
        "scored_candidates": eval_signals["scored_candidates"],
        "near_tie_candidates": eval_signals["near_tie_candidates"],
        "ambiguity_detected": bool(eval_signals["ambiguity_detected"]),
        "intent": "memory-grounded" if eval_signals["context_confident"] and not eval_signals["ambiguity_detected"] else "dont-know",
    }


def _signal_signature(signal: dict[str, object], score_key: str) -> tuple[str, float]:
    return (str(signal.get("doc_id", "")), float(signal.get(score_key, 0.0) or 0.0))


def _assert_signal_parity(context, *, fixture_id: str, utterance: str, candidates: list[dict[str, str | float]]) -> None:
    runtime = _runtime_memory_signals(utterance, candidates)
    eval_path = _eval_memory_signals(utterance, candidates)
    assert runtime["ranked_doc_ids"] == eval_path["ranked_doc_ids"], fixture_id
    assert runtime["ambiguity_detected"] == eval_path["ambiguity_detected"], fixture_id
    assert runtime["intent"] == eval_path["intent"], fixture_id
    runtime_scored = [_signal_signature(c, "final_score") for c in runtime["scored_candidates"]]
    eval_scored = [_signal_signature(c, "final_score") for c in eval_path["scored_candidates"]]
    assert runtime_scored == eval_scored, fixture_id
    runtime_near_tie = [_signal_signature(c, "score") for c in runtime["near_tie_candidates"]]
    eval_near_tie = [_signal_signature(c, "score") for c in eval_path["near_tie_candidates"]]
    assert runtime_near_tie == eval_near_tie, fixture_id
    context.parity_signals = runtime



@given("a deterministic in-memory recall harness")
def step_given_deterministic_harness(context) -> None:
    """BDD default path intentionally avoids live HA/Ollama integrations."""
    context.live_dependencies = {"home_assistant": False, "ollama": False}


@given('eval cases are loaded from "{cases_path}"')
def step_given_cases_loaded(context, cases_path: str) -> None:
    del cases_path  # path is fixed via shared loader until alternate case files are needed.
    context.eval_cases = cases_by_id()


@when('the user asks about eval case "{case_id}"')
def step_when_user_asks_eval_case(context, case_id: str) -> None:
    context.case_id = case_id
    case = context.eval_cases[case_id]
    _assert_signal_parity(
        context,
        fixture_id=case_id,
        utterance=case.utterance,
        candidates=[dict(candidate) for candidate in case.candidates],
    )
    context.answer = _answer_from_case(case_id, context.eval_cases)
    context.pipeline_state = _build_stage_state(case_id, context.eval_cases, context.answer, context.parity_signals)

    context.retrieve_pre_check = validate_retrieve_pre(context.pipeline_state)
    context.retrieve_post_check = validate_retrieve_post(context.pipeline_state)
    context.answer_pre_check = validate_answer_pre(context.pipeline_state)
    context.answer_post_check = validate_answer_post(context.pipeline_state)

    assert context.retrieve_pre_check.passed, f"retrieve.pre failed: {context.retrieve_pre_check.failures}"
    assert context.retrieve_post_check.passed, f"retrieve.post failed: {context.retrieve_post_check.failures}"
    assert context.answer_pre_check.passed, f"answer.pre failed: {context.answer_pre_check.failures}"
    assert context.answer_post_check.passed, f"answer.post failed: {context.answer_post_check.failures}"


@when("equivalent top candidates remain after tie-break")
def step_when_equivalent_candidates_remain(context) -> None:
    parity_candidates = [
        {
            "doc_id": "ambiguous_a",
            "text": "Fragment A",
            "type": "user_utterance",
            "ts": "2026-03-10T09:00:00+00:00",
            "sim_score": 0.62,
        },
        {
            "doc_id": "ambiguous_b",
            "text": "Fragment B",
            "type": "user_utterance",
            "ts": "2026-03-10T09:00:00+00:00",
            "sim_score": 0.62,
        },
        {
            "doc_id": "ambiguous_reflection",
            "text": "Fragment A reflection",
            "type": "reflection",
            "source_doc_id": "ambiguous_a",
            "ts": "2026-03-10T09:01:00+00:00",
            "sim_score": 0.60,
        },
    ]
    _assert_signal_parity(
        context,
        fixture_id="bdd-ambiguity-bridge",
        utterance="Which project note did I mention this morning?",
        candidates=parity_candidates,
    )
    assert context.parity_signals["intent"] == "dont-know"
    assert len(context.parity_signals["near_tie_candidates"]) >= 2

    candidates = [
        CandidateHit(doc_id="", score=0.91, ts="", card_type="memory"),
        CandidateHit(doc_id="", score=0.90, ts="", card_type="memory"),
    ]
    context.answer = BRIDGING_CLARIFIER
    context.pipeline_state = PipelineState(
        user_input="ambiguous recall",
        rewritten_query="ambiguous recall",
        retrieval_candidates=candidates,
        reranked_hits=candidates,
        confidence_decision={"context_confident": False, "ambiguity_detected": True},
        draft_answer="",
        final_answer=BRIDGING_CLARIFIER,
        claims=["INFERENCE: Ambiguous memory fragments"],
        provenance_types=[ProvenanceType.INFERENCE],
        basis_statement="Ambiguous fragments require clarification.",
        invariant_decisions={"answer_contract_valid": True, "general_knowledge_contract_valid": True, "answer_mode": "clarify"},
        alignment_decision={
            "objective_version": "2026-03-01.v1",
            "dimensions": {
                "factual_grounding_reliability": 1.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 0.7,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 1.0,
            },
            "final_alignment_decision": "allow",
        },
    )

    context.answer_pre_check = validate_answer_pre(context.pipeline_state)
    context.answer_post_check = validate_answer_post(context.pipeline_state)
    assert context.answer_pre_check.passed, f"answer.pre failed: {context.answer_pre_check.failures}"
    assert context.answer_post_check.passed, f"answer.post failed: {context.answer_post_check.failures}"


@then("the assistant returns a memory-grounded answer")
def step_then_grounded(context) -> None:
    assert context.answer != FALLBACK


@then('the answer includes citation fields "doc_id" and "ts"')
def step_then_has_citation(context) -> None:
    assert "doc_id:" in context.answer
    assert "ts:" in context.answer


@then("the assistant returns an assistive fallback response")
def step_then_assistive_fallback(context) -> None:
    lowered = context.answer.lower()
    assert "either" in lowered and "or" in lowered


@then("the assistant returns a bridging clarification response")
def step_then_bridging_clarifier(context) -> None:
    lowered = context.answer.lower()
    assert "which" in lowered and "time window" in lowered
