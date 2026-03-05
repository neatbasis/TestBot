from __future__ import annotations

import re

from behave import given, then, when

from testbot.eval_fixtures import best_candidate_doc_id, cases_by_id
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType
from testbot.stage_transitions import (
    validate_answer_post,
    validate_answer_pre,
    validate_retrieve_post,
    validate_retrieve_pre,
)

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


def _build_stage_state(case_id: str, loaded_cases, answer: str) -> PipelineState:
    case = loaded_cases[case_id]
    candidates = [
        CandidateHit(doc_id=candidate["doc_id"], score=float(candidate["sim_score"]), ts=str(candidate["ts"]), card_type="memory")
        for candidate in case.candidates
    ]
    context_confident = bool(candidates)
    draft_answer = answer if "doc_id:" in answer else ""
    has_claims = "doc_id:" in answer
    return PipelineState(
        user_input=case.utterance,
        rewritten_query=case.utterance,
        retrieval_candidates=candidates,
        reranked_hits=candidates[:4],
        confidence_decision={"context_confident": context_confident},
        draft_answer=draft_answer,
        final_answer=answer,
        claims=[f"INFERENCE: {answer}"] if has_claims else [],
        provenance_types=[ProvenanceType.MEMORY, ProvenanceType.INFERENCE] if has_claims else [ProvenanceType.UNKNOWN],
        used_memory_refs=[f"{candidates[0].doc_id}@{candidates[0].ts}"] if has_claims and candidates else [],
        basis_statement=("Answer synthesized from reranked memory context." if has_claims else "Trivial fallback response with no substantive claim."),
        invariant_decisions={
            "answer_contract_valid": _validate_answer_contract(draft_answer),
            "general_knowledge_contract_valid": True,
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
    context.answer = _answer_from_case(case_id, context.eval_cases)
    context.pipeline_state = _build_stage_state(case_id, context.eval_cases, context.answer)

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
