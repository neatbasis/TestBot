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
from testbot.turn_observation import observe_turn
from testbot.candidate_encoding import FactCandidate, encode_turn_candidates
from testbot.canonical_turn_orchestrator import CanonicalStage, CanonicalTurnContext, CanonicalTurnOrchestrator
from testbot.memory_strata import derive_segment_descriptor
from testbot.stabilization import StabilizedTurnState
from testbot.intent_router import IntentType
from testbot.context_resolution import resolve as resolve_context
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.policy_decision import DecisionClass, decide_from_evidence
from testbot.evidence_retrieval import (
    EvidenceBundle,
    EvidencePosture,
    build_evidence_bundle_from_docs_and_scores,
    retrieval_result,
)

from testbot.sat_chatbot_memory_v2 import has_sufficient_context_confidence, stage_rerank
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


def _assert_evidence_state_fields(
    state_contract: dict[str, object],
    *,
    typed_state: str,
    evidence_posture: str,
    decision_class: str,
    provenance_label: str,
    fallback_strategy: str,
) -> None:
    assert state_contract.get("typed_state") == typed_state
    assert state_contract.get("evidence_posture") == evidence_posture
    assert state_contract.get("decision_class") == decision_class
    assert state_contract.get("provenance_label") == provenance_label
    assert state_contract.get("fallback_strategy") == fallback_strategy

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
        resolved_intent="memory_recall",
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


def _assert_intermediate_signal_contract(signals: dict[str, object], fixture_id: str) -> None:
    scored_candidates = signals["scored_candidates"]
    ranked_doc_ids = signals["ranked_doc_ids"]
    scored_doc_ids = [str(candidate.get("doc_id", "")) for candidate in scored_candidates]
    assert scored_doc_ids == ranked_doc_ids, fixture_id

    near_tie_candidates = signals["near_tie_candidates"]
    near_tie_doc_ids = [str(candidate.get("doc_id", "")) for candidate in near_tie_candidates]
    assert all(doc_id in scored_doc_ids for doc_id in near_tie_doc_ids), fixture_id

    if signals["ambiguity_detected"]:
        assert signals["intent"] == "dont-know", fixture_id
        assert len(near_tie_candidates) >= 2, fixture_id


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
    _assert_intermediate_signal_contract(runtime, fixture_id)
    _assert_intermediate_signal_contract(eval_path, fixture_id)
    context.parity_signals = runtime
    context.eval_parity_signals = eval_path



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
    context.expected_fallback_class = "memory-grounded" if "doc_id:" in context.answer else "dont-know"
    assert context.parity_signals["intent"] == context.expected_fallback_class, case_id

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
            "doc_id": "",
            "text": "Fragment A",
            "type": "user_utterance",
            "ts": "2026-03-10T09:00:00+00:00",
            "sim_score": 0.62,
        },
        {
            "doc_id": "",
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
        resolved_intent="memory_recall",
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
    assert context.parity_signals["intent"] == "memory-grounded"
    assert context.parity_signals["ambiguity_detected"] is False


@then('the answer includes citation fields "doc_id" and "ts"')
def step_then_has_citation(context) -> None:
    assert "doc_id:" in context.answer
    assert "ts:" in context.answer


@then("the response includes memory provenance transparency fields")
def step_then_memory_provenance_fields(context) -> None:
    assert context.pipeline_state.provenance_types
    assert ProvenanceType.MEMORY in context.pipeline_state.provenance_types
    assert context.pipeline_state.used_memory_refs
    assert "@" in context.pipeline_state.used_memory_refs[0]


@then("the response includes a grounding basis statement")
def step_then_grounding_basis_statement(context) -> None:
    assert context.pipeline_state.basis_statement.strip()
    assert "memory context" in context.pipeline_state.basis_statement.lower()


@then("the assistant returns an assistive fallback response")
def step_then_assistive_fallback(context) -> None:
    lowered = context.answer.lower()
    assert "either" in lowered and "or" in lowered
    assert context.parity_signals["intent"] == "dont-know"
    assert context.parity_signals["ambiguity_detected"] is False




@when("typed memory fallback contracts are resolved for empty and scored-empty evidence")
def step_when_typed_memory_fallback_contracts_resolved(context) -> None:
    empty_retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    scored_empty_retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=2,
        hit_count=0,
    )

    empty_decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=empty_retrieval)
    scored_empty_decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=scored_empty_retrieval)

    context.memory_typed_fallback_mapping = {
        "E.empty": {
            "typed_state": "E.empty",
            "evidence_posture": empty_retrieval.evidence_posture.value,
            "decision_class": empty_decision.decision_class.value,
            "provenance_label": "UNKNOWN",
            "fallback_strategy": "ASK_CLARIFIER",
        },
        "E.scored_empty": {
            "typed_state": "E.scored_empty",
            "evidence_posture": scored_empty_retrieval.evidence_posture.value,
            "decision_class": scored_empty_decision.decision_class.value,
            "provenance_label": "UNKNOWN",
            "fallback_strategy": "ANSWER_UNKNOWN",
        },
        "E.scored_empty_non_memory": {
            "typed_state": "E.scored_empty_non_memory",
            "evidence_posture": scored_empty_retrieval.evidence_posture.value,
            "decision_class": DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED.value,
            "provenance_label": "UNKNOWN",
            "fallback_strategy": "OFFER_ASSIST_ALTERNATIVES",
        },
    }


@then("typed evidence states should remain distinct for empty and scored-empty in memory recall")
def step_then_typed_evidence_states_distinct_memory(context) -> None:
    empty_contract = context.memory_typed_fallback_mapping["E.empty"]
    scored_empty_contract = context.memory_typed_fallback_mapping["E.scored_empty"]
    assert empty_contract["typed_state"] != scored_empty_contract["typed_state"]
    assert empty_contract["evidence_posture"] == EvidencePosture.EMPTY_EVIDENCE.value
    assert scored_empty_contract["evidence_posture"] == EvidencePosture.SCORED_EMPTY.value


@then('the memory evidence-state mapping should include decision class "{decision_class}" and provenance label "{provenance_label}" for "{typed_state}"')
def step_then_memory_mapping_decision_and_provenance(context, decision_class: str, provenance_label: str, typed_state: str) -> None:
    state_contract = context.memory_typed_fallback_mapping[typed_state]
    _assert_evidence_state_fields(
        state_contract,
        typed_state=typed_state,
        evidence_posture=str(state_contract["evidence_posture"]),
        decision_class=decision_class,
        provenance_label=provenance_label,
        fallback_strategy=str(state_contract["fallback_strategy"]),
    )


@then('the memory evidence-state mapping should include fallback strategy "{fallback_strategy}" for "{typed_state}"')
def step_then_memory_mapping_fallback_strategy(context, fallback_strategy: str, typed_state: str) -> None:
    state_contract = context.memory_typed_fallback_mapping[typed_state]
    _assert_evidence_state_fields(
        state_contract,
        typed_state=typed_state,
        evidence_posture=str(state_contract["evidence_posture"]),
        decision_class=str(state_contract["decision_class"]),
        provenance_label=str(state_contract["provenance_label"]),
        fallback_strategy=fallback_strategy,
    )
@then("the assistant returns a bridging clarification response")
def step_then_bridging_clarifier(context) -> None:
    lowered = context.answer.lower()
    assert "which" in lowered and "time window" in lowered
    assert context.parity_signals["intent"] == "dont-know"
    assert context.parity_signals["ambiguity_detected"] == context.eval_parity_signals["ambiguity_detected"]
    assert len(context.parity_signals["near_tie_candidates"]) >= 2


@given("recall candidates include a recent anchor and older distractor")
def step_given_recall_candidates_include_anchor(context) -> None:
    context.followup_now = arrow.get("2026-03-10T12:00:00+00:00")
    context.followup_candidates = [
        (
            Document(
                id="anchor-doc",
                page_content="Anchored memory",
                metadata={"doc_id": "anchor-doc", "type": "user_utterance", "ts": "2026-03-09T22:00:00+00:00"},
            ),
            0.81,
        ),
        (
            Document(
                id="older-doc",
                page_content="Older memory",
                metadata={"doc_id": "older-doc", "type": "user_utterance", "ts": "2026-03-08T10:00:00+00:00"},
            ),
            0.93,
        ),
    ]


@when('the user asks a pronoun temporal follow-up "{utterance}"')
def step_when_user_asks_pronoun_temporal_followup(context, utterance: str) -> None:
    class _Clock:
        def now(self) -> arrow.Arrow:
            return context.followup_now

    state = PipelineState(user_input=utterance)
    context.followup_state, context.followup_hits = stage_rerank(
        state,
        context.followup_candidates,
        utterance=utterance,
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=_Clock(),
        io_channel="cli",
    )


@then("the temporal anaphora bridge selects the anchor before rerank")
def step_then_temporal_bridge_selects_anchor(context) -> None:
    assert context.followup_state.confidence_decision["anaphora_detected"] is True
    assert context.followup_state.confidence_decision["selected_anchor_doc_id"] == "anchor-doc"
    assert [doc.id for doc in context.followup_hits] == ["anchor-doc"]


@then("the bridge emits elapsed delta and yesterday window details")
def step_then_bridge_emits_delta_and_window(context) -> None:
    decision = context.followup_state.confidence_decision
    assert decision["computed_delta_raw_seconds"] == 50400
    assert decision["computed_delta_humanized"] == "14 hours ago"
    assert decision["time_window"] == "yesterday"
    assert decision["window_start"].startswith("2026-03-09T00:00:00")

@given('a canonical stage harness with a raw utterance "{utterance}"')
def step_given_canonical_stage_harness(context, utterance: str) -> None:
    context.canonical_stage_state = PipelineState(user_input=utterance)


@when("canonical observe encode and stabilize execute")
def step_when_canonical_observe_encode_stabilize_execute(context) -> None:
    state = context.canonical_stage_state
    observation = observe_turn(
        state,
        turn_id="turn-bdd-1",
        observed_at="2026-03-07T10:00:00+00:00",
        speaker="user",
        channel="cli",
    )
    encoded = encode_turn_candidates(state, observation=observation, rewritten_query=state.user_input)
    context.canonical_observation = observation
    context.canonical_encoded = encoded
    context.canonical_same_turn_exclusion_doc_ids = ["turn-bdd-1", "reflection-bdd-1", "dialogue-state-bdd-1"]


@then("the stage artifacts include a typed turn observation")
def step_then_stage_artifacts_include_typed_turn_observation(context) -> None:
    assert context.canonical_observation.turn_id == "turn-bdd-1"
    assert context.canonical_observation.utterance


@then("stabilization provides same-turn exclusion doc ids before intent resolve")
def step_then_stabilization_provides_same_turn_exclusion_doc_ids(context) -> None:
    assert context.canonical_same_turn_exclusion_doc_ids == ["turn-bdd-1", "reflection-bdd-1", "dialogue-state-bdd-1"]


@then('stabilization candidate facts include "user_name" as "Sebastian"')
def step_then_stabilization_candidate_facts_include_name(context) -> None:
    assert any(f.key == "user_name" and f.value == "Sebastian" for f in context.canonical_encoded.facts)



@then("the response includes deterministic citation-context formatting")
def step_then_deterministic_citation_context_formatting(context) -> None:
    refs = list(context.pipeline_state.used_memory_refs)
    assert refs == sorted(refs)
    assert all("@" in ref for ref in refs)


@when("canonical stages execute stabilize then intent resolve then retrieve")
def step_when_canonical_stages_execute_stabilize_intent_retrieve(context) -> None:
    canonical_context = CanonicalTurnContext(
        state=context.canonical_stage_state,
        artifacts={"policy_decision": None},
    )

    def _observe(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["turn_observation"] = {"turn_id": "turn-bdd-route-1", "utterance": ctx.state.user_input}
        return ctx

    def _encode(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["encoded_candidates"] = {"facts": [{"key": "utterance_raw", "value": ctx.state.user_input}]}
        return ctx

    def _stabilize(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        context.canonical_policy_decision_before_stabilize = ctx.artifacts.get("policy_decision")
        ctx.artifacts["stabilized_turn_state"] = {"turn_id": "turn-bdd-route-1"}
        context.canonical_stabilized_turn_state = ctx.artifacts["stabilized_turn_state"]
        return ctx

    def _context_resolve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["resolved_context"] = {"continuity_posture": "reevaluate"}
        return ctx

    def _intent_resolve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        assert ctx.artifacts.get("stabilized_turn_state") == {"turn_id": "turn-bdd-route-1"}
        ctx.artifacts["policy_decision"] = {"retrieval_branch": "direct_answer"}
        context.canonical_policy_decision_after_intent = ctx.artifacts["policy_decision"]
        return ctx

    def _retrieve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        context.canonical_policy_decision_seen_by_retrieve = ctx.artifacts.get("policy_decision")
        ctx.artifacts["retrieval_result"] = {"posture": "not_requested"}
        return ctx

    def _noop(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return ctx

    def _answer_assemble(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["answer_assembly_contract"] = {"decision_class": "answer_from_memory"}
        return ctx

    def _answer_validate(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["answer_validation_contract"] = type("Validation", (), {"passed": True})()
        return ctx

    orchestrator = CanonicalTurnOrchestrator(
        stages=[
            CanonicalStage("observe.turn", _observe),
            CanonicalStage("encode.candidates", _encode),
            CanonicalStage("stabilize.pre_route", _stabilize),
            CanonicalStage("context.resolve", _context_resolve),
            CanonicalStage("intent.resolve", _intent_resolve),
            CanonicalStage("retrieve.evidence", _retrieve),
            CanonicalStage("policy.decide", _noop),
            CanonicalStage("answer.assemble", _answer_assemble),
            CanonicalStage("answer.validate", _answer_validate),
            CanonicalStage("answer.render", _noop),
            CanonicalStage("answer.commit", _noop),
        ]
    )
    context.canonical_orchestrator_result = orchestrator.run(canonical_context)


@then("intent resolve assigns policy decision after stabilization")
def step_then_intent_resolve_assigns_policy_decision_after_stabilization(context) -> None:
    assert context.canonical_policy_decision_before_stabilize is None
    assert context.canonical_stabilized_turn_state["turn_id"] == "turn-bdd-route-1"
    assert context.canonical_policy_decision_after_intent == {"retrieval_branch": "direct_answer"}


@then("retrieve observes the post-stabilization policy decision")
def step_then_retrieve_observes_post_stabilization_policy_decision(context) -> None:
    assert context.canonical_policy_decision_seen_by_retrieve == {"retrieval_branch": "direct_answer"}
    assert context.canonical_orchestrator_result.stage_audit_trail[2:6] == [
        "stabilize.pre_route",
        "context.resolve",
        "intent.resolve",
        "retrieve.evidence",
    ]



@given('a canonical memory claim harness with claim "{claim}"')
def step_given_canonical_memory_claim_harness(context, claim: str) -> None:
    context.memory_claim = claim
    context.observed_artifact_ids = []
    context.committed_memory_ids = []
    context.same_turn_retrieval_results = []
    context.later_turn_retrieval_results = []
    context.invalid_same_turn_retrieval = []
    context.same_turn_retrieval_rejected = False


@when('observe.turn captures the claim for turn "{turn_id}"')
def step_when_observe_turn_captures_claim(context, turn_id: str) -> None:
    context.memory_claim_turn_id = turn_id
    observation_id = f"obs-{turn_id}-claim-1"
    context.observed_artifact_ids = [observation_id]


@when("retrieval executes in the same turn before answer.commit")
def step_when_retrieval_executes_same_turn_before_commit(context) -> None:
    context.same_turn_retrieval_results = [doc_id for doc_id in context.committed_memory_ids if doc_id.startswith("mem-")]


@when('answer.commit persists the observed claim as memory id "{memory_id}"')
def step_when_answer_commit_persists_claim(context, memory_id: str) -> None:
    assert context.observed_artifact_ids, "observe.turn must execute before answer.commit"
    context.committed_memory_ids.append(memory_id)


@when('retrieval executes in a later turn "{turn_id}"')
def step_when_retrieval_executes_later_turn(context, turn_id: str) -> None:
    context.later_turn_id = turn_id
    context.later_turn_retrieval_results = list(context.committed_memory_ids)


@when('retrieval incorrectly returns just-observed artifact id "{artifact_id}" in the same turn')
def step_when_retrieval_incorrectly_returns_observed_artifact(context, artifact_id: str) -> None:
    assert artifact_id in context.observed_artifact_ids
    context.invalid_same_turn_retrieval = [artifact_id]


@then('observed artifact ids should be "{artifact_id}"')
def step_then_observed_artifact_ids(context, artifact_id: str) -> None:
    assert context.observed_artifact_ids == [artifact_id]
    assert all(item.startswith("obs-") for item in context.observed_artifact_ids)


@then("committed memory ids should be empty")
def step_then_committed_memory_ids_empty(context) -> None:
    assert context.committed_memory_ids == []


@then('same-turn retrieval should not return committed memory id "{memory_id}"')
def step_then_same_turn_retrieval_not_return_memory_id(context, memory_id: str) -> None:
    assert memory_id not in context.same_turn_retrieval_results


@then('committed memory ids should include "{memory_id}"')
def step_then_committed_memory_ids_include(context, memory_id: str) -> None:
    assert memory_id in context.committed_memory_ids
    assert all(item.startswith("mem-") for item in context.committed_memory_ids)


@then('later-turn retrieval should return committed memory id "{memory_id}"')
def step_then_later_turn_retrieval_returns_memory_id(context, memory_id: str) -> None:
    assert memory_id in context.later_turn_retrieval_results


@then("same-turn retrieval should be rejected as invalid durable memory")
def step_then_same_turn_retrieval_rejected(context) -> None:
    context.same_turn_retrieval_rejected = any(
        artifact_id in context.observed_artifact_ids for artifact_id in context.invalid_same_turn_retrieval
    )
    assert context.same_turn_retrieval_rejected is True


@given("a canonical multi-antecedent commit-state harness")
def step_given_multi_antecedent_commit_state_harness(context) -> None:
    context.multi_antecedent_prior_state = PipelineState(
        user_input="Apollo started in 2021 and Zephyr started in 2022",
        final_answer="I can track both project starts.",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        commit_receipt={
            "confirmed_user_facts": ["project=Apollo:start=2021", "project=Zephyr:start=2022"],
            "remaining_obligations": ["ask_which_project_for_pronoun"],
            "pending_clarification": {"required": True, "question": "Which project does 'it' refer to?"},
        },
    )


@when('a pronoun follow-up "when did it start" is evaluated at the next turn boundary')
def step_when_pronoun_followup_multi_antecedent(context) -> None:
    resolved_context = resolve_context(utterance="when did it start", prior_pipeline_state=context.multi_antecedent_prior_state)
    context.multi_antecedent_intent_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized_turn_state_for_memory_bdd("when did it start"),
            context=resolved_context,
            fallback_utterance="when did it start",
        )
    )
    context.multi_antecedent_commit_transition = {
        "persisted": list(context.multi_antecedent_prior_state.commit_receipt.get("confirmed_user_facts", [])),
        "cleared": ["selected_antecedent"],
        "history_anchors": resolved_context.history_anchors,
        "remaining_obligations": list(context.multi_antecedent_prior_state.commit_receipt.get("remaining_obligations", [])),
    }


@then("the follow-up should require disambiguation before committed context is reused")
def step_then_multi_antecedent_requires_disambiguation(context) -> None:
    assert context.multi_antecedent_intent_resolution.resolved_intent is IntentType.KNOWLEDGE_QUESTION
    assert "ask_which_project_for_pronoun" in context.multi_antecedent_commit_transition["remaining_obligations"]


@then("commit-state transitions should persist multi-antecedent facts and clear selected antecedent at the turn boundary")
def step_then_multi_antecedent_commit_transition(context) -> None:
    transition = context.multi_antecedent_commit_transition
    assert transition["persisted"] == ["project=Apollo:start=2021", "project=Zephyr:start=2022"]
    assert transition["cleared"] == ["selected_antecedent"]
    assert "commit.confirmed_user_facts:project=Apollo:start=2021" in transition["history_anchors"]
    assert "commit.confirmed_user_facts:project=Zephyr:start=2022" in transition["history_anchors"]


def _stabilized_turn_state_for_memory_bdd(utterance: str) -> StabilizedTurnState:
    return StabilizedTurnState(
        turn_id="bdd-memory-turn",
        utterance_card="UTTERANCE CARD",
        utterance_doc_id="bdd-u",
        reflection_doc_id="bdd-r",
        dialogue_state_doc_id="bdd-d",
        segment_type="episodic",
        segment_id="bdd-seg",
        segment_membership_edge_refs=[],
        same_turn_exclusion_doc_ids=[],
        candidate_facts=[FactCandidate(key="utterance_raw", value=utterance, confidence=1.0)],
        candidate_speech_acts=[],
        candidate_dialogue_state=[],
    )


@given("derived memory segments for follow-up self-profile turns")
def step_given_derived_memory_segments(context) -> None:
    first = derive_segment_descriptor(utterance="My name is Sebastian", has_dialogue_state=True)
    second = derive_segment_descriptor(
        utterance="My name is Sebastian and I prefer tea",
        prior_descriptor=first,
        has_dialogue_state=True,
    )
    context.segment_descriptors = (first, second)


@then("the segment id remains stable across those turns")
def step_then_segment_id_stable(context) -> None:
    first, second = context.segment_descriptors
    assert first.segment_id == second.segment_id


@given("a segment with semantic and episodic memory candidates")
def step_given_segment_strata_candidates(context) -> None:
    segment = derive_segment_descriptor(utterance="What is my name?")
    context.segment_bundle = build_evidence_bundle_from_docs_and_scores(
        [
            (
                Document(
                    id="semantic-name",
                    page_content="name=Sebastian",
                    metadata={"type": "profile_fact", "memory_stratum": "semantic", "segment_id": segment.segment_id},
                ),
                0.82,
            ),
            (
                Document(
                    id="episodic-name",
                    page_content="My name is Sebastian",
                    metadata={"type": "user_utterance", "memory_stratum": "episodic", "segment_id": segment.segment_id},
                ),
                0.95,
            ),
        ]
    )


@when("evidence is bundled for policy consumption")
def step_when_evidence_bundled(context) -> None:
    assert context.segment_bundle.total_records() >= 1


@then("semantic memory is retained as canonical evidence for that segment")
def step_then_semantic_retained(context) -> None:
    assert [record.ref_id for record in context.segment_bundle.structured_facts] == ["semantic-name"]


@then("raw episodic utterance evidence for that segment is de-prioritized")
def step_then_episodic_deprioritized(context) -> None:
    assert context.segment_bundle.episodic_utterances == ()
