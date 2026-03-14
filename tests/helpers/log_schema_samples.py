from __future__ import annotations

from typing import Any


def _base_row(*, ts: str, event: str, schema_version: int) -> dict[str, Any]:
    return {
        "ts": ts,
        "event": event,
        "schema_version": schema_version,
    }


def build_valid_event_rows(*, schema_version: int) -> list[dict[str, Any]]:
    return [
        {
            **_base_row(
                ts="2026-03-03T00:00:00Z",
                event="user_utterance_ingest",
                schema_version=schema_version,
            ),
            "utterance": "hello",
        },
        {
            **_base_row(
                ts="2026-03-03T00:00:01Z",
                event="pipeline_state_snapshot",
                schema_version=schema_version,
            ),
            "stage": "answer",
            "state": {
                "user_input": "hello",
                "rewritten_query": "hello",
                "retrieval_candidates": [],
                "reranked_hits": [],
                "confidence_decision": {"context_confident": False},
                "draft_answer": "",
                "final_answer": "I don't know from memory.",
                "invariant_decisions": {"answer_contract_valid": False},
                "alignment_decision": {
                    "dimensions": {},
                    "final_alignment_decision": "fallback",
                },
            },
        },
        {
            **_base_row(
                ts="2026-03-03T00:00:02Z",
                event="provenance_summary",
                schema_version=schema_version,
            ),
            "provenance_types": ["memory"],
            "used_memory_refs": [{"doc_id": "d1", "ts": "2026-03-01T00:00:00Z"}],
            "used_source_evidence_refs": ["src-1"],
            "source_evidence_attribution": [
                {
                    "doc_id": "src-1",
                    "source_type": "calendar",
                    "source_uri": "calendar://work/event-1",
                    "retrieved_at": "2026-03-03T00:00:00Z",
                    "trust_tier": "high",
                }
            ],
            "basis_statement": "Answer synthesized from reranked source evidence documents.",
        },
        {
            **_base_row(
                ts="2026-03-03T00:00:03Z",
                event="stage_transition_validation",
                schema_version=schema_version,
            ),
            "stage": "answer",
            "boundary": "post",
            "invariant_refs": ["PINV-001", "PINV-002"],
            "passed": True,
            "failures": [],
        },
        {
            **_base_row(
                ts="2026-03-03T00:00:04Z",
                event="debug_turn_trace",
                schema_version=schema_version,
            ),
            "utterance": "what did I say",
            "payload": {
                "debug.policy": {"reject_code": "CONTEXT_CONF_BELOW_THRESHOLD"},
                "debug.confidence": {
                    "context_confident_gate": {
                        "passed": False,
                        "score": 0.7,
                        "threshold": 0.8,
                        "margin": -0.1,
                    }
                },
                "debug.rerank": {
                    "margin_gate": {
                        "passed": False,
                        "score": 0.01,
                        "threshold": 0.05,
                        "margin": -0.04,
                    },
                    "top_final_score_gate": {
                        "passed": False,
                        "score": 0.7,
                        "threshold": 0.9,
                        "margin": -0.2,
                    },
                    "ambiguity_gate": {
                        "passed": True,
                        "score": 1.0,
                        "threshold": 0.5,
                        "margin": 0.5,
                    },
                },
                "debug.observation": {"candidate_evidence": {}},
                "debug.intent": {},
                "debug.rewrite": {},
                "debug.retrieval": {},
                "debug.contract": {},
            },
            "trace": "[debug] intent=memory_recall",
        },
    ]


def build_valid_rows_by_schema_version() -> dict[int, list[dict[str, Any]]]:
    return {version: build_valid_event_rows(schema_version=version) for version in (1, 2, 3, 4)}
