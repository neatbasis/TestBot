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
IDK_THRESHOLD = 0.2
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

    context_confident = has_sufficient_context_confidence(docs_and_scores) and not outcome.ambiguity_detected
    intent = "memory-grounded" if context_confident else "dont-know"

    return {
        "ranked_doc_ids": [str(doc.id or "") for doc in outcome.docs],
        "top_doc_id": str(outcome.docs[0].id or "") if outcome.docs else "",
        "intent": intent,
        "near_tie_candidates": outcome.near_tie_candidates,
        "top_score": float(outcome.scored_candidates[0]["final_score"]) if outcome.scored_candidates else 0.0,
    }


def _eval_path_result(utterance: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    target = eval_recall.parse_target_time(utterance, now=FIXED_NOW)
    sigma = adaptive_sigma_fractional(now=FIXED_NOW, target=target)

    ranked = eval_recall.rank_candidates(
        candidates,
        now=FIXED_NOW,
        target=target,
        sigma_seconds=sigma,
    )
    top_score = (
        float(eval_recall.candidate_objective_components(ranked[0], target=target, sigma_seconds=sigma)["final_score"])
        if ranked
        else 0.0
    )
    intent = "memory-grounded" if top_score >= IDK_THRESHOLD else "dont-know"

    return {
        "ranked_doc_ids": [candidate.get("doc_id", "") for candidate in ranked],
        "top_doc_id": ranked[0].get("doc_id", "") if ranked else "",
        "intent": intent,
        "top_score": top_score,
    }


def test_eval_runtime_parity_clear_winner_case() -> None:
    case = cases_by_id()["sleep-followup"]

    runtime = _runtime_path_result(case.utterance, list(case.candidates))
    eval_path = _eval_path_result(case.utterance, list(case.candidates))

    assert runtime["ranked_doc_ids"] == eval_path["ranked_doc_ids"]
    assert runtime["top_doc_id"] == eval_path["top_doc_id"] == case.expected_doc_id
    assert runtime["intent"] == eval_path["intent"] == "memory-grounded"
    assert abs(runtime["top_score"] - eval_path["top_score"]) <= 1e-12


def test_eval_runtime_parity_near_tie_fixture_case() -> None:
    fixture = _load_candidate_set_fixture("candidate-set-no-memory-match")
    candidates = [dict(candidate, type="user_utterance") for candidate in fixture["candidates"]]
    candidates[1]["sim_score"] = 0.27

    runtime = _runtime_path_result(fixture["query"], candidates)
    eval_path = _eval_path_result(fixture["query"], candidates)

    assert runtime["ranked_doc_ids"] == eval_path["ranked_doc_ids"]
    assert runtime["top_doc_id"] == eval_path["top_doc_id"]
    assert runtime["intent"] == eval_path["intent"] == "dont-know"
    assert len(runtime["near_tie_candidates"]) >= 2
    top_scores = [candidate["score"] for candidate in runtime["near_tie_candidates"]]
    assert max(top_scores) - min(top_scores) <= NEAR_TIE_DELTA
