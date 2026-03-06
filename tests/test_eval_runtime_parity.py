from __future__ import annotations

import json
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
from testbot.rerank import adaptive_sigma_fractional, rerank_docs_with_time_and_type_outcome
from testbot.sat_chatbot_memory_v2 import has_sufficient_context_confidence

FIXED_NOW = arrow.get("2026-03-10T11:00:00+00:00")
NEAR_TIE_DELTA = 0.02


def _load_candidate_set_fixture(fixture_id: str) -> dict[str, Any]:
    fixtures_path = Path("tests/fixtures/candidate_sets.jsonl")
    with fixtures_path.open("r", encoding="utf-8") as fixture_file:
        for line in fixture_file:
            fixture = json.loads(line)
            if fixture["fixture_id"] == fixture_id:
                return fixture
    raise AssertionError(f"Missing fixture_id: {fixture_id}")


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
    intent = "memory-grounded" if eval_signals["context_confident"] and not eval_signals["ambiguity_detected"] else "dont-know"

    return {
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


def _assert_runtime_eval_signal_parity(runtime: dict[str, Any], eval_path: dict[str, Any], fixture_id: str) -> None:
    assert runtime["ranked_doc_ids"] == eval_path["ranked_doc_ids"], fixture_id
    assert runtime["top_doc_id"] == eval_path["top_doc_id"], fixture_id
    assert runtime["intent"] == eval_path["intent"], fixture_id
    assert runtime["ambiguity_detected"] == eval_path["ambiguity_detected"], fixture_id

    runtime_scored = [_candidate_signal_signature(c) for c in runtime["scored_candidates"]]
    eval_scored = [_candidate_signal_signature(c) for c in eval_path["scored_candidates"]]
    assert runtime_scored == eval_scored, fixture_id

    runtime_near_tie = [_near_tie_signature(c) for c in runtime["near_tie_candidates"]]
    eval_near_tie = [_near_tie_signature(c) for c in eval_path["near_tie_candidates"]]
    assert runtime_near_tie == eval_near_tie, fixture_id

    assert abs(runtime["top_score"] - eval_path["top_score"]) <= 1e-12, fixture_id


def test_eval_runtime_parity_clear_winner_case() -> None:
    case = cases_by_id()["sleep-followup"]

    runtime = _runtime_path_result(case.utterance, list(case.candidates))
    eval_path = _eval_path_result(case.utterance, list(case.candidates))

    _assert_runtime_eval_signal_parity(runtime, eval_path, fixture_id="sleep-followup")
    assert runtime["top_doc_id"] == case.expected_doc_id
    assert runtime["intent"] == "memory-grounded"


def test_eval_runtime_parity_near_tie_fixture_case() -> None:
    fixture = _load_candidate_set_fixture("candidate-set-no-memory-match")
    candidates = [dict(candidate, type="user_utterance") for candidate in fixture["candidates"]]
    candidates[1]["sim_score"] = 0.27

    runtime = _runtime_path_result(fixture["query"], candidates)
    eval_path = _eval_path_result(fixture["query"], candidates)

    _assert_runtime_eval_signal_parity(runtime, eval_path, fixture_id=fixture["fixture_id"])
    assert runtime["intent"] == "dont-know"
    assert len(runtime["near_tie_candidates"]) >= 2
    top_scores = [candidate["score"] for candidate in runtime["near_tie_candidates"]]
    assert max(top_scores) - min(top_scores) <= NEAR_TIE_DELTA


def _load_runtime_parity_fixtures(file_name: str) -> list[dict[str, Any]]:
    fixtures_path = Path("tests/fixtures") / file_name
    loaded: list[dict[str, Any]] = []
    with fixtures_path.open("r", encoding="utf-8") as fixture_file:
        for line in fixture_file:
            loaded.append(json.loads(line))
    return loaded


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
    assert runtime["top_score"] == 0.2
    assert runtime["intent"] == "memory-grounded"

def test_eval_runtime_parity_fixture_families() -> None:
    fixture_files = [
        "eval_runtime_parity_ordering_topx_fallback_confidence.jsonl",
        "eval_runtime_parity_edge_time.jsonl",
        "eval_runtime_parity_ambiguous_intent.jsonl",
        "eval_runtime_parity_observation_making_processes.jsonl",
        "eval_runtime_parity_temporal_uncertainty.jsonl",
    ]

    fixtures: list[dict[str, Any]] = []
    for file_name in fixture_files:
        fixtures.extend(_load_runtime_parity_fixtures(file_name))

    for fixture in fixtures:
        candidates = [dict(candidate) for candidate in fixture["candidates"]]
        runtime = _runtime_path_result(fixture["utterance"], candidates)
        eval_path = _eval_path_result(fixture["utterance"], candidates)

        _assert_runtime_eval_signal_parity(runtime, eval_path, fixture_id=fixture["fixture_id"])

        expected = fixture["expected"]
        top_k = int(expected.get("top_k", 1))
        assert runtime["ranked_doc_ids"][:top_k] == expected["ranked_doc_ids_top_k"], fixture["fixture_id"]
        assert runtime["intent"] == expected["intent"], fixture["fixture_id"]
        if "near_tie_min_count" in expected:
            assert len(runtime["near_tie_candidates"]) >= int(expected["near_tie_min_count"]), fixture["fixture_id"]
