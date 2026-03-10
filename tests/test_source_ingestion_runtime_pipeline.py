from __future__ import annotations

from collections import deque
import json

from testbot.clock import SystemClock
from testbot.sat_chatbot_memory_v2 import (
    CapabilitySnapshot,
    RuntimeCapabilityStatus,
    _run_chat_loop,
    _run_source_ingestion,
)


class _FakeStore:
    def __init__(self) -> None:
        self._docs = []

    def add_documents(self, documents):
        self._docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
        del query, kwargs
        return [(doc, 0.9) for doc in self._docs[:k]]


class _StaticLLM:
    def __init__(self, content: str) -> None:
        self._content = content

    def invoke(self, _msgs):
        return type("_Resp", (), {"content": self._content})()


def test_fixture_source_ingestion_pipeline_emits_completion_and_provenance(monkeypatch, tmp_path) -> None:
    fixture_path = tmp_path / "source_fixture.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "item_id": "src-1",
                    "content": "A Hilbert space is a complete inner-product vector space.",
                    "source_uri": "fixture://wiki/hilbert-space",
                    "retrieved_at": "2026-03-10T09:00:00Z",
                    "trust_tier": "verified",
                    "metadata": {"ts": "2026-03-10T09:00:00Z", "topic": "Hilbert space"},
                }
            ]
        ),
        encoding="utf-8",
    )

    runtime = {
        "source_ingest_enabled": True,
        "source_connector_type": "fixture",
        "source_fixture_path": str(fixture_path),
        "source_ingest_limit": 10,
        "source_ingest_cursor": None,
    }

    store = _FakeStore()
    events: list[dict[str, object]] = []

    def _capture_session_log(event: str, payload: dict, *, log_path=None) -> None:  # noqa: ARG001
        events.append({"event": event, "payload": payload})

    monkeypatch.setattr("testbot.sat_chatbot_memory_v2.append_session_log", _capture_session_log)

    _run_source_ingestion(runtime=runtime, store=store)

    replies: list[str] = []
    prompts = iter(["What is a Hilbert space?", "stop"])
    _run_chat_loop(
        runtime=runtime,
        llm=_StaticLLM("A Hilbert space is a complete inner-product vector space."),
        store=store,
        chat_history=deque(maxlen=10),
        near_tie_delta=0.02,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime=runtime,
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error="not_configured",
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="in_memory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=SystemClock(),
    )

    ingest_payload = next((item["payload"] for item in events if item["event"] == "source_ingest_completed"), None)
    assert isinstance(ingest_payload, dict)
    assert ingest_payload["stored_count"] == 2

    non_stop_replies = [text.strip() for text in replies if text.strip() and text.strip() != "Stopping. Bye."]
    assert non_stop_replies

    final_answer_mode_payload = next((item["payload"] for item in events if item["event"] == "final_answer_mode"), None)
    assert isinstance(final_answer_mode_payload, dict)
    for required_key in (
        "provenance_types",
        "claims",
        "used_memory_refs",
        "used_source_evidence_refs",
        "source_evidence_attribution",
        "basis_statement",
    ):
        assert required_key in final_answer_mode_payload
    assert isinstance(final_answer_mode_payload["used_source_evidence_refs"], list)
