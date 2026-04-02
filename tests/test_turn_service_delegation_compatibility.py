from __future__ import annotations

from collections import deque

from testbot import sat_chatbot_memory_v2 as runtime
from testbot.entrypoints.runtime_turn_pipeline import RuntimeTurnPipelineHooks


class _CapabilitySnapshotStub:
    runtime_capability_status = None


def test_run_canonical_turn_pipeline_delegates_to_runtime_turn_pipeline_helper(monkeypatch):
    captured: dict[str, object] = {}

    def _service_stub(**kwargs):
        captured.update(kwargs)
        return "state-result", []

    monkeypatch.setattr(runtime, "run_runtime_turn_pipeline", _service_stub)

    result = runtime._run_canonical_turn_pipeline(
        runtime={"test": True},
        llm=object(),
        store=object(),
        state=object(),
        utterance="hello",
        prior_pipeline_state=None,
        turn_id="turn-1",
        near_tie_delta=0.05,
        chat_history=deque(),
        capability_status=object(),
        capability_snapshot=_CapabilitySnapshotStub(),
        clock=object(),
    )

    assert result[0] == "state-result"
    assert result[1] == []
    assert captured["utterance"] == "hello"
    assert captured["io_channel"] == "cli"
    hooks = captured["hooks"]
    assert isinstance(hooks, RuntimeTurnPipelineHooks)
    assert hooks.append_session_log is runtime.append_session_log
    assert hooks.intent_classifier_confidence_threshold == runtime.INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD


def test_legacy_intent_classifier_confidence_delegates_to_canonical_policy_owner(monkeypatch):
    from testbot.policies import turn_policy as turn_policy_policies

    captured: dict[str, object] = {}

    def _canonical_stub(**kwargs):
        captured.update(kwargs)
        return 0.88

    monkeypatch.setattr(turn_policy_policies, "intent_classifier_confidence", _canonical_stub)

    result = runtime._intent_classifier_confidence(
        utterance="what time is it",
        predicted_intent=runtime.IntentType.KNOWLEDGE_QUESTION,
    )

    assert result == 0.88
    assert captured == {
        "utterance": "what time is it",
        "predicted_intent": runtime.IntentType.KNOWLEDGE_QUESTION,
        "confidence_threshold": runtime.INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
    }


def test_legacy_minimal_confidence_decision_delegates_to_canonical_policy_owner(monkeypatch):
    from testbot.policies import turn_policy as turn_policy_policies

    captured: dict[str, object] = {}

    def _canonical_stub(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(turn_policy_policies, "minimal_confidence_decision_for_direct_answer", _canonical_stub)

    base_confidence_decision = {"x": 1}
    result = runtime._minimal_confidence_decision_for_direct_answer(
        branch="direct_answer",
        base_confidence_decision=base_confidence_decision,
    )

    assert result == {"ok": True}
    assert captured == {
        "branch": "direct_answer",
        "base_confidence_decision": base_confidence_decision,
        "retrieval_score_threshold": runtime.RETRIEVAL_SCORE_THRESHOLD,
    }


def test_legacy_selected_decision_from_confidence_delegates_to_canonical_logic_owner(monkeypatch):
    captured: dict[str, object] = {}

    def _canonical_stub(payload):
        captured["payload"] = payload
        return {"delegated": True}

    monkeypatch.setattr(runtime, "project_selected_decision_from_confidence", _canonical_stub)

    payload = {
        "allow_selected_decision_override": True,
        "selected_decision_authority_stage": "policy",
        "selected_decision_object": {
            "decision_class": "ANSWER_FROM_MEMORY",
            "retrieval_branch": "memory_retrieval",
        },
    }
    result = runtime._selected_decision_from_confidence(payload)

    assert result == {"delegated": True}
    assert captured["payload"] is payload
