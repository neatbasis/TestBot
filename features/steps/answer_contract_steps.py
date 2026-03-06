from __future__ import annotations

from behave import given, then, when

from testbot.eval_fixtures import cases_by_id
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType
from testbot.sat_chatbot_memory_v2 import RuntimeCapabilityStatus, stage_answer, validate_answer_contract, validate_general_knowledge_contract
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
        resolved_intent="memory_recall",
        retrieval_candidates=[CandidateHit(doc_id="doc-1", score=0.8, ts="2024-01-01T00:00:00Z", card_type="memory")],
        reranked_hits=[CandidateHit(doc_id="doc-1", score=0.8, ts="2024-01-01T00:00:00Z", card_type="memory")],
        confidence_decision={"context_confident": True},
        draft_answer=context.candidate,
        final_answer="Can you clarify which memory and time window you mean?",
        invariant_decisions={
            "answer_contract_valid": context.contract_passed,
            "general_knowledge_contract_valid": True,
            "answer_mode": "clarify",
        },
        alignment_decision={
            "objective_version": "2026-03-01.v1",
            "dimensions": {
                "factual_grounding_reliability": 0.0,
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


class _BDDUnlabeledGeneralKnowledgeLLM:
    class _Response:
        content = "Ontology is the study of being and existence."

    def invoke(self, _msgs):
        return self._Response()


@given('a non-memory knowledge question "{question}"')
def step_given_non_memory_knowledge_question(context, question: str) -> None:
    context.user_question = question


@given("an unlabeled general-knowledge draft answer with failed confidence gate")
def step_given_unlabeled_general_knowledge_with_failed_gate(context) -> None:
    context.answer_state_input = PipelineState(
        user_input=context.user_question,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": True,
            "general_knowledge_confidence": 0.1,
            "general_knowledge_support": 0,
        },
        resolved_intent="knowledge_question",
    )


@when("stage answer enforces the general-knowledge contract")
def step_when_stage_answer_enforces_contract(context) -> None:
    context.stage_answer_state = stage_answer(
        _BDDUnlabeledGeneralKnowledgeLLM(),
        context.answer_state_input,
        chat_history=[],
        hits=[],
        capability_status="ask_unavailable",
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=True,
            ha_available=False,
            effective_mode="cli",
            requested_mode="cli",
            daemon_mode=False,
            fallback_reason=None,
            memory_backend="in_memory",
            debug_enabled=False,
            text_clarification_available=True,
            satellite_ask_available=False,
        ),
        clock=None,
    )


@then("the final answer should be knowledge-safe fallback")
def step_then_final_answer_is_knowledge_safe_fallback(context) -> None:
    lowered = context.stage_answer_state.final_answer.lower()
    assert "don't have enough reliable" in lowered
    assert "i can either" in lowered and " or " in lowered




@then("the final answer should include explicit uncertainty language")
def step_then_final_answer_includes_explicit_uncertainty_language(context) -> None:
    lowered = context.stage_answer_state.final_answer.lower()
    assert "don't have enough reliable" in lowered or "don't know" in lowered


@then("the final answer should include a safe action path")
def step_then_final_answer_includes_safe_action_path(context) -> None:
    lowered = context.stage_answer_state.final_answer.lower()
    assert "i can either" in lowered
    assert " or " in lowered

@then('the final answer should not ask "{message}"')
def step_then_final_answer_does_not_ask_message(context, message: str) -> None:
    assert message not in context.stage_answer_state.final_answer


@then("the response records knowledge-safe fallback provenance transparency")
def step_then_response_records_general_knowledge_provenance_and_basis(context) -> None:
    provenance_names = {p.name for p in context.stage_answer_state.provenance_types}
    assert provenance_names == {"UNKNOWN"}
    assert context.stage_answer_state.basis_statement.strip()
    assert "no substantive claim" in context.stage_answer_state.basis_statement.lower()
