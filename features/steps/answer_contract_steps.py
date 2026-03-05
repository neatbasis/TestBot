from __future__ import annotations

from behave import given, then, when

from testbot.eval_fixtures import cases_by_id
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType
from testbot.sat_chatbot_memory_v2 import (
    build_provenance_metadata,
    validate_answer_contract,
    validate_general_knowledge_contract,
)
from testbot.stage_transitions import validate_answer_post, validate_answer_pre


@given('an uncited factual candidate from eval case "{case_id}"')
def step_given_uncited_candidate_from_eval_case(context, case_id: str) -> None:
    case = cases_by_id()[case_id]
    top_candidate = max(case.candidates, key=lambda candidate: candidate["sim_score"])
    context.candidate = top_candidate["text"]


@when("the answer contract validator checks the candidate")
def step_when_validate(context) -> None:
    context.contract_passed = validate_answer_contract(context.candidate)
    context.pipeline_state = PipelineState(
        user_input="test question",
        rewritten_query="test question",
        retrieval_candidates=[CandidateHit(doc_id="doc-1", score=0.8, ts="2024-01-01T00:00:00Z", card_type="memory")],
        reranked_hits=[CandidateHit(doc_id="doc-1", score=0.8, ts="2024-01-01T00:00:00Z", card_type="memory")],
        confidence_decision={"context_confident": True},
        draft_answer=context.candidate,
        final_answer="I don't know from memory.",
        invariant_decisions={"answer_contract_valid": context.contract_passed},
        alignment_decision={
            "objective_version": "2026-03-01.v1",
            "dimensions": {
                "factual_grounding_reliability": 0.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 0.4,
                "cost_latency_budget": 1.0,
            },
            "final_alignment_decision": "fallback",
        },
    )
    context.answer_pre_check = validate_answer_pre(context.pipeline_state)
    context.answer_post_check = validate_answer_post(context.pipeline_state)


@then("the candidate is rejected")
def step_then_rejected(context) -> None:
    assert context.contract_passed is False
    assert context.answer_pre_check.passed, f"answer.pre failed: {context.answer_pre_check.failures}"
    assert context.answer_post_check.passed, f"answer.post failed: {context.answer_post_check.failures}"


@given("a general-knowledge factual candidate without marker text")
def step_given_general_knowledge_candidate_without_marker(context) -> None:
    context.gk_candidate = "Earth orbits the Sun once every year."
    context.gk_provenance = [ProvenanceType.GENERAL_KNOWLEDGE, ProvenanceType.INFERENCE]


@given("the general-knowledge confidence gate does not pass")
def step_given_general_knowledge_gate_fail(context) -> None:
    context.gk_confidence_decision = {"general_knowledge_confidence": 0.42, "general_knowledge_support": 1}


@given("a general-knowledge factual candidate with marker text")
def step_given_general_knowledge_candidate_with_marker(context) -> None:
    context.gk_candidate = "General definition (not from your memory): Earth orbits the Sun once every year."
    context.gk_provenance = [ProvenanceType.GENERAL_KNOWLEDGE, ProvenanceType.INFERENCE]


@given("the general-knowledge confidence gate passes")
def step_given_general_knowledge_gate_pass(context) -> None:
    context.gk_confidence_decision = {"general_knowledge_confidence": 0.93, "general_knowledge_support": 3}


@when("the general-knowledge contract validator checks the candidate")
def step_when_validate_general_knowledge_contract(context) -> None:
    context.gk_contract_passed = validate_general_knowledge_contract(
        context.gk_candidate,
        provenance_types=context.gk_provenance,
        confidence_decision=context.gk_confidence_decision,
    )


@then("the general-knowledge candidate is rejected")
def step_then_general_knowledge_rejected(context) -> None:
    assert context.gk_contract_passed is False


@then("the general-knowledge candidate is accepted")
def step_then_general_knowledge_accepted(context) -> None:
    assert context.gk_contract_passed is True


@given("a memory-grounded answer rendered in normal mode")
def step_given_normal_mode_render(context) -> None:
    from collections import deque
    from langchain_core.documents import Document
    from testbot.history_packer import pack_chat_history

    _, _, _, _, rendered = build_provenance_metadata(
        final_answer="You usually sleep around 11pm.",
        hits=[Document(page_content="x", metadata={"doc_id": "abc", "ts": "2026-01-01T00:00:00Z"}, id="abc")],
        chat_history=deque(),
        packed_history=pack_chat_history([]),
        debug_mode=False,
    )
    context.rendered_answer = rendered


@then("the user-facing answer omits raw citation markers")
def step_then_normal_omits_markers(context) -> None:
    assert "doc_id" not in context.rendered_answer.lower()
    assert "ts=" not in context.rendered_answer.lower()


@given("a memory-grounded answer rendered in debug mode")
def step_given_debug_mode_render(context) -> None:
    from collections import deque
    from langchain_core.documents import Document
    from testbot.history_packer import pack_chat_history

    _, _, _, _, rendered = build_provenance_metadata(
        final_answer="You usually sleep around 11pm.",
        hits=[Document(page_content="x", metadata={"doc_id": "abc", "ts": "2026-01-01T00:00:00Z"}, id="abc")],
        chat_history=deque(),
        packed_history=pack_chat_history([]),
        debug_mode=True,
    )
    context.rendered_answer = rendered


@then("the user-facing answer includes internal citation diagnostics")
def step_then_debug_has_diagnostics(context) -> None:
    assert "debug provenance" in context.rendered_answer.lower()
    assert "doc_id=" in context.rendered_answer
    assert "ts=" in context.rendered_answer
