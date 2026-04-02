from __future__ import annotations

from collections import deque
from types import SimpleNamespace

from testbot.entrypoints import runtime_turn_pipeline
from testbot.entrypoints.runtime_turn_pipeline import RuntimeTurnPipelineHooks
from testbot.evidence_retrieval import RetrievalInputRecord
from testbot.logic import decision_helpers
from testbot.pipeline_state import PipelineState
from testbot.policies import turn_policy as turn_policy_policies


def _hooks() -> RuntimeTurnPipelineHooks:
    return RuntimeTurnPipelineHooks(
        append_session_log=lambda *_args, **_kwargs: None,
        validate_and_log_transition=lambda *_args, **_kwargs: None,
        stage_rewrite_query=lambda *_args, **_kwargs: "",
        generate_reflection_yaml=lambda *_args, **_kwargs: "",
        intent_classifier_confidence=lambda *_args, **_kwargs: 0.9,
        optional_string=lambda value: value if isinstance(value, str) else None,
        should_force_memory_retrieval_for_identity_recall=lambda *_args, **_kwargs: False,
        resolve_context_fn=lambda *_args, **_kwargs: ("", [], []),
        intent_telemetry_payload=lambda *_args, **_kwargs: {},
        poll_background_source_ingestion=lambda *_args, **_kwargs: None,
        start_background_source_ingestion=lambda *_args, **_kwargs: None,
        stage_retrieve=lambda *_args, **_kwargs: (PipelineState(user_input=""), []),
        stage_rerank=lambda *_args, **_kwargs: (PipelineState(user_input=""), []),
        selected_decision_from_confidence=lambda *_args, **_kwargs: None,
        minimal_confidence_decision_for_direct_answer=lambda *_args, **_kwargs: {},
        resolve_answer_routing_for_stage=lambda state, **_kwargs: (state, None),
        answer_assemble=lambda *_args, **_kwargs: {},
        answer_validate=lambda *_args, **_kwargs: {},
        detect_capability_offer=lambda *_args, **_kwargs: False,
        ambiguity_score=lambda *_args, **_kwargs: 0.0,
        store_doc_fn=lambda *_args, **_kwargs: None,
        intent_classifier_confidence_threshold=turn_policy_policies.INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
        document_from_retrieval_input=lambda record: SimpleNamespace(id=record.ref_id, page_content=record.content),
    )


def test_runtime_turn_pipeline_delegates_to_canonical_turn_runtime(monkeypatch) -> None:
    captured: dict[str, object] = {}
    state = PipelineState(user_input="hello")

    def _canonical_stub(**kwargs):
        captured.update(kwargs)
        return state, [RetrievalInputRecord(ref_id="doc-1", score=0.9, content="candidate", metadata={})]

    monkeypatch.setattr(runtime_turn_pipeline, "run_canonical_turn_pipeline", _canonical_stub)

    next_state, docs = runtime_turn_pipeline.run_runtime_turn_pipeline(
        runtime={"test": True},
        llm=object(),
        store=object(),
        state=state,
        utterance="hello",
        prior_pipeline_state=None,
        turn_id="turn-1",
        near_tie_delta=0.05,
        chat_history=deque(),
        capability_status=object(),
        capability_snapshot=SimpleNamespace(runtime_capability_status=None),
        clock=object(),
        hooks=_hooks(),
    )

    assert next_state is state
    assert len(docs) == 1
    assert docs[0].id == "doc-1"
    assert captured["utterance"] == "hello"
    assert captured["io_channel"] == "cli"
    assert captured["deps"].intent_classifier_confidence_threshold == (
        turn_policy_policies.INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD
    )


def test_decision_helpers_selected_decision_from_confidence_delegates_to_logic_turn_policy_owner(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _canonical_stub(payload):
        captured["payload"] = payload
        return {"delegated": True}

    monkeypatch.setattr(decision_helpers, "project_selected_decision_from_confidence", _canonical_stub)

    payload = {
        "allow_selected_decision_override": True,
        "selected_decision_authority_stage": "policy",
        "selected_decision_object": {
            "decision_class": "ANSWER_FROM_MEMORY",
            "retrieval_branch": "memory_retrieval",
        },
    }
    result = decision_helpers.selected_decision_from_confidence(payload)

    assert result == {"delegated": True}
    assert captured["payload"] is payload
