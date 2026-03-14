from __future__ import annotations

from pathlib import Path
from typing import Any

import arrow
from langchain_core.documents import Document

import importlib.util

_EVAL_RECALL_PATH = Path(__file__).resolve().parents[1] / "scripts" / "eval_recall.py"
_eval_spec = importlib.util.spec_from_file_location("eval_recall", _EVAL_RECALL_PATH)
assert _eval_spec and _eval_spec.loader
eval_recall = importlib.util.module_from_spec(_eval_spec)
_eval_spec.loader.exec_module(eval_recall)
from testbot.eval_fixtures import cases_by_id
from tests.helpers.eval_case_builders import build_eval_case_candidate_sets_by_id
from tests.helpers.eval_runtime_parity_scenarios import runtime_parity_scenarios
from testbot.context_resolution import ContinuityPosture, resolve as resolve_context
from testbot import sat_chatbot_memory_v2 as runtime
from testbot.candidate_encoding import FactCandidate
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.intent_router import IntentType
from testbot.pipeline_state import PipelineState
from testbot.evidence_retrieval import continuity_evidence_from_prior_state
from testbot.rerank import adaptive_sigma_fractional, rerank_docs_with_time_and_type_outcome
from testbot.sat_chatbot_memory_v2 import has_sufficient_context_confidence

FIXED_NOW = arrow.get("2026-03-10T11:00:00+00:00")
NEAR_TIE_DELTA = 0.02


def _runtime_path_result(utterance: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    target = eval_recall.parse_target_time(utterance, now=FIXED_NOW)
    sigma = adaptive_sigma_fractional(now=FIXED_NOW, target=target)

    docs_and_scores = [
        (
            Document(
                id=candidate["doc_id"],
                page_content=candidate.get("text", ""),
                metadata={
                    "doc_id": candidate["doc_id"],
                    "type": candidate.get("type", "user_utterance"),
                    "ts": candidate.get("ts", ""),
                    "source_doc_id": candidate.get("source_doc_id", ""),
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
    intent = "memory-grounded" if context_confident else "dont-know"

    return {
        "context_confident": context_confident,
        "ranked_doc_ids": [str(doc.id or "") for doc in outcome.docs],
        "top_doc_id": str(outcome.docs[0].id or "") if outcome.docs else "",
        "intent": intent,
        "ambiguity_detected": outcome.ambiguity_detected,
        "near_tie_candidates": outcome.near_tie_candidates,
        "scored_candidates": outcome.scored_candidates,
        "top_score": float(outcome.scored_candidates[0]["final_score"]) if outcome.scored_candidates else 0.0,
    }


def _eval_path_result(utterance: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
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
    top_score = (
        float(eval_recall.candidate_objective_components(ranked[0], target=target, sigma_seconds=sigma)["final_score"])
        if ranked
        else 0.0
    )
    context_confident = bool(eval_signals["context_confident"])
    intent = "memory-grounded" if context_confident and not eval_signals["ambiguity_detected"] else "dont-know"

    return {
        "context_confident": context_confident,
        "ranked_doc_ids": [candidate.get("doc_id", "") for candidate in ranked],
        "top_doc_id": ranked[0].get("doc_id", "") if ranked else "",
        "intent": intent,
        "top_score": top_score,
        "near_tie_candidates": eval_signals["near_tie_candidates"],
        "ambiguity_detected": eval_signals["ambiguity_detected"],
        "scored_candidates": eval_signals["scored_candidates"],
    }


def _candidate_signal_signature(candidate: dict[str, Any]) -> tuple[str, float]:
    return (str(candidate.get("doc_id", "")), float(candidate.get("final_score", 0.0) or 0.0))


def _near_tie_signature(candidate: dict[str, Any]) -> tuple[str, float]:
    return (str(candidate.get("doc_id", "")), float(candidate.get("score", 0.0) or 0.0))


def _assert_intermediate_signal_contract(signals: dict[str, Any], fixture_id: str) -> None:
    scored_doc_ids = [str(candidate.get("doc_id", "")) for candidate in signals["scored_candidates"]]
    assert scored_doc_ids == signals["ranked_doc_ids"], fixture_id

    near_tie_doc_ids = [str(candidate.get("doc_id", "")) for candidate in signals["near_tie_candidates"]]
    assert all(doc_id in scored_doc_ids for doc_id in near_tie_doc_ids), fixture_id

    if signals["ambiguity_detected"]:
        assert signals["intent"] == "dont-know", fixture_id
        assert len(signals["near_tie_candidates"]) >= 2, fixture_id


def _assert_runtime_eval_signal_parity(runtime: dict[str, Any], eval_path: dict[str, Any], fixture_id: str) -> None:
    assert runtime["ranked_doc_ids"] == eval_path["ranked_doc_ids"], fixture_id
    assert runtime["top_doc_id"] == eval_path["top_doc_id"], fixture_id
    assert runtime["intent"] == eval_path["intent"], fixture_id
    assert runtime["context_confident"] == eval_path["context_confident"], fixture_id
    assert runtime["ambiguity_detected"] == eval_path["ambiguity_detected"], fixture_id

    runtime_scored = [_candidate_signal_signature(c) for c in runtime["scored_candidates"]]
    eval_scored = [_candidate_signal_signature(c) for c in eval_path["scored_candidates"]]
    assert runtime_scored == eval_scored, fixture_id

    runtime_near_tie = [_near_tie_signature(c) for c in runtime["near_tie_candidates"]]
    eval_near_tie = [_near_tie_signature(c) for c in eval_path["near_tie_candidates"]]
    assert runtime_near_tie == eval_near_tie, fixture_id

    assert abs(runtime["top_score"] - eval_path["top_score"]) <= 1e-12, fixture_id

    _assert_intermediate_signal_contract(runtime, fixture_id)

    if runtime["intent"] == "memory-grounded":
        assert runtime["context_confident"] is True, fixture_id
        assert runtime["ambiguity_detected"] is False, fixture_id
    _assert_intermediate_signal_contract(eval_path, fixture_id)


def _structured_mode(signals: dict[str, Any]) -> str:
    if signals["intent"] == "memory-grounded":
        return "memory-grounded"
    if signals["ambiguity_detected"]:
        return "dont-know-ambiguous"
    return "dont-know-low-confidence"


def test_eval_runtime_parity_clear_winner_case() -> None:
    case = cases_by_id()["sleep-followup"]

    runtime = _runtime_path_result(case.utterance, list(case.candidates))
    eval_path = _eval_path_result(case.utterance, list(case.candidates))

    _assert_runtime_eval_signal_parity(runtime, eval_path, fixture_id="sleep-followup")
    assert runtime["top_doc_id"] == case.expected_doc_id
    assert runtime["intent"] == "memory-grounded"


def test_eval_runtime_parity_near_tie_fixture_case() -> None:
    fixture = build_eval_case_candidate_sets_by_id()["candidate-set-no-memory-match"]
    candidates = [dict(candidate, type="user_utterance") for candidate in fixture["candidates"]]
    candidates[1]["sim_score"] = 0.27

    runtime = _runtime_path_result(fixture["query"], candidates)
    eval_path = _eval_path_result(fixture["query"], candidates)

    _assert_runtime_eval_signal_parity(runtime, eval_path, fixture_id=fixture["fixture_id"])
    assert runtime["intent"] == "dont-know"
    assert len(runtime["near_tie_candidates"]) >= 2
    top_scores = [candidate["score"] for candidate in runtime["near_tie_candidates"]]
    assert max(top_scores) - min(top_scores) <= NEAR_TIE_DELTA


def test_eval_runtime_parity_high_similarity_but_weak_objective_not_confident() -> None:
    utterance = "What was my sleep quality last night?"
    candidates = [
        {
            "doc_id": "stale-high-sim",
            "text": "I slept great three months ago.",
            "type": "reflection",
            "ts": "2025-12-01T08:00:00+00:00",
            "sim_score": 0.98,
        },
        {
            "doc_id": "recent-lower-sim",
            "text": "I slept okay last night.",
            "type": "reflection",
            "ts": "2026-03-09T23:50:00+00:00",
            "sim_score": 0.6,
        },
    ]

    runtime = _runtime_path_result(utterance, candidates)
    eval_path = _eval_path_result(utterance, candidates)

    _assert_runtime_eval_signal_parity(runtime, eval_path, fixture_id="high-sim-weak-objective")
    assert runtime["intent"] == "dont-know"
    assert runtime["top_score"] < 0.2




def test_structured_mode_distinguishes_knowing_vs_unknowing_paths() -> None:
    knowing_signals = {"intent": "memory-grounded", "ambiguity_detected": False}
    ambiguous_signals = {"intent": "dont-know", "ambiguity_detected": True}
    low_conf_signals = {"intent": "dont-know", "ambiguity_detected": False}

    assert _structured_mode(knowing_signals) == "memory-grounded"
    assert _structured_mode(ambiguous_signals) == "dont-know-ambiguous"
    assert _structured_mode(low_conf_signals) == "dont-know-low-confidence"


def test_eval_runtime_parity_confidence_boundary_exact_threshold() -> None:
    utterance = "What did I say about hydration this morning?"
    candidates = [
        {
            "doc_id": "boundary-top",
            "text": "I said to drink water after waking.",
            "type": "user_utterance",
            "ts": "2026-03-10T09:00:00+00:00",
            "sim_score": 0.8,
        },
        {
            "doc_id": "boundary-second",
            "text": "I mentioned tea later.",
            "type": "user_utterance",
            "ts": "2026-03-10T09:05:00+00:00",
            "sim_score": 0.4,
        },
    ]

    runtime = _runtime_path_result(utterance, candidates)
    eval_path = _eval_path_result(utterance, candidates)

    _assert_runtime_eval_signal_parity(runtime, eval_path, fixture_id="confidence-boundary-exact-threshold")
    assert runtime["top_score"] == 0.8
    assert runtime["intent"] == "memory-grounded"


def test_eval_runtime_parity_fixture_families() -> None:
    for scenario in runtime_parity_scenarios():
        candidates = [dict(candidate) for candidate in scenario.candidates]
        runtime = _runtime_path_result(scenario.utterance, candidates)
        eval_path = _eval_path_result(scenario.utterance, candidates)

        _assert_runtime_eval_signal_parity(runtime, eval_path, fixture_id=scenario.fixture_id)

        expected = scenario.expected
        top_k = int(expected.get("top_k", 1))
        assert runtime["ranked_doc_ids"][:top_k] == expected["ranked_doc_ids_top_k"], scenario.fixture_id
        assert runtime["intent"] == expected["intent"], scenario.fixture_id
        assert _structured_mode(runtime) == expected.get("mode", _structured_mode(runtime)), scenario.fixture_id

        if "ambiguity_detected" in expected:
            assert runtime["ambiguity_detected"] is bool(expected["ambiguity_detected"]), scenario.fixture_id
        if "context_confident" in expected:
            assert runtime["context_confident"] is bool(expected["context_confident"]), scenario.fixture_id
        if "near_tie_min_count" in expected:
            assert len(runtime["near_tie_candidates"]) >= int(expected["near_tie_min_count"]), scenario.fixture_id


def test_structured_mode_distinguishes_ambiguous_and_low_confidence_dont_know() -> None:
    assert _structured_mode({"intent": "dont-know", "ambiguity_detected": True}) == "dont-know-ambiguous"
    assert _structured_mode({"intent": "dont-know", "ambiguity_detected": False}) == "dont-know-low-confidence"


def test_canonical_continuity_parity_consumes_prior_commit_artifacts_across_turns() -> None:
    turn_one_state = PipelineState(
        user_input="who am i?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        commit_receipt={
            "commit_stage": "answer.commit",
            "pending_repair_state": {"repair_required_by_policy": False, "repair_offered_to_user": False, "reason": "none"},
            "resolved_obligations": ["repair_state_not_required"],
            "pending_ingestion_request_id": "ingest-abc",
            "confirmed_user_facts": ["name=Sam"],
        },
        final_answer="Can you clarify which prior memory you mean?",
    )

    context = resolve_context(utterance="yes", prior_pipeline_state=turn_one_state)
    runtime_stabilized = runtime.StabilizedTurnState(
        turn_id="turn-2",
        utterance_card="UTTERANCE CARD",
        utterance_doc_id="u2",
        reflection_doc_id="r2",
        dialogue_state_doc_id="d2",
        segment_type="episodic",
        segment_id="seg-2",
        segment_membership_edge_refs=[],
        same_turn_exclusion_doc_ids=[],
        candidate_facts=[FactCandidate(key="utterance_raw", value="yes", confidence=1.0)],
        candidate_speech_acts=[],
        candidate_dialogue_state=[],
        candidate_repairs=[],
    )
    intent_resolution = resolve_intent(resolution_input=IntentResolutionInput(stabilized_turn_state=runtime_stabilized, context=context, fallback_utterance="yes"))

    assert context.continuity_posture is ContinuityPosture.PRESERVE_PRIOR_INTENT
    assert context.history_anchors == (
        "prior_intent:memory_recall",
        "commit.confirmed_user_facts:name=Sam",
        "commit.pending_ingestion_request_id:ingest-abc",
        "clarification_continuity",
    )
    assert intent_resolution.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert intent_resolution.resolved_intent is IntentType.MEMORY_RECALL

    retrieval_evidence = continuity_evidence_from_prior_state(turn_one_state)
    assert retrieval_evidence == ("commit.confirmed_user_facts:name=Sam", "commit.pending_ingestion_request_id:ingest-abc")
