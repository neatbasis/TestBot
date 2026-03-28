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
