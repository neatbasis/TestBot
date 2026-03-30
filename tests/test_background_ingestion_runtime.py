from __future__ import annotations

from collections import deque
from concurrent.futures import Future
from dataclasses import dataclass

import arrow

from testbot.application.services import background_ingestion_runtime as runtime


@dataclass
class _DummyState:
    user_input: str
    last_user_message_ts: str
    classified_intent: str
    resolved_intent: str
    prior_unresolved_intent: str
    confidence_decision: dict[str, object]
    final_answer: str = ""
    used_source_evidence_refs: list[str] | None = None

    def __post_init__(self) -> None:
        if self.used_source_evidence_refs is None:
            self.used_source_evidence_refs = []


def test_start_background_source_ingestion_reports_already_running() -> None:
    rt = {
        "source_ingest_background_future": Future(),
        "source_ingest_background_request_id": "ingest-existing",
    }

    started = runtime.start_background_source_ingestion(
        runtime=rt,
        store=object(),
        execute_source_ingestion=lambda **_: {"ok": True, "status": "completed", "payload": {}},
        append_session_log=lambda *_: None,
    )

    assert started == {"started": False, "already_running": True, "ingestion_request_id": "ingest-existing"}


def test_poll_pending_ingestion_obligations_marks_pending_and_times_out() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    rt = {
        "pending_ingestion_registry": {
            "ingest-pending": {
                "ingestion_request_id": "ingest-pending",
                "created_at": "2026-03-10T10:00:00+00:00",
                "deadline_at": "2099-03-10T10:30:00+00:00",
                "attempt_count": 0,
                "status": "pending",
            },
            "ingest-timeout": {
                "ingestion_request_id": "ingest-timeout",
                "created_at": "2026-03-10T10:00:00+00:00",
                "deadline_at": "2026-03-10T10:30:00+00:00",
                "attempt_count": 0,
                "status": "pending",
            },
        },
        "dead_letter_ingestion_registry": {},
    }

    runtime.poll_pending_ingestion_obligations(
        runtime=rt,
        append_session_log=lambda event, payload: events.append((event, payload)),
        obligation_timeout_seconds=900,
        utcnow=lambda: arrow.get("2026-03-10T11:00:00+00:00"),
    )

    assert "ingest-timeout" not in rt["pending_ingestion_registry"]
    assert rt["pending_ingestion_registry"]["ingest-pending"]["status"] == "pending"
    assert rt["dead_letter_ingestion_registry"]["ingest-timeout"]["status"] == "timed_out"
    statuses = [payload["status"] for event, payload in events if event == "source_ingest_obligation_transition"]
    assert "polled_pending" in statuses
    assert "timed_out" in statuses


def test_process_background_ingestion_completion_regenerates_answer() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    sent_text: list[str] = []
    persisted: list[str] = []
    rt = {
        "pending_ingestion_registry": {
            "req-1": {
                "utterance": "What changed?",
                "prior_pipeline_state": None,
                "attempt_count": 2,
                "created_at": "2026-03-10T10:00:00+00:00",
                "deadline_at": "2026-03-10T10:30:00+00:00",
            }
        }
    }

    replay_requests: list[runtime.BackgroundIngestionReplayRequest] = []

    def _replay(request: runtime.BackgroundIngestionReplayRequest) -> _DummyState:
        replay_requests.append(request)
        return _DummyState(
            user_input=request.utterance,
            last_user_message_ts=request.last_user_message_ts,
            classified_intent="knowledge_question",
            resolved_intent="",
            prior_unresolved_intent="",
            confidence_decision={},
            final_answer="Grounded answer.",
            used_source_evidence_refs=["src-1"],
        )

    _last_ts, state, processed = runtime.process_background_ingestion_completion(
        runtime=rt,
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_status="ask_unavailable",
        capability_snapshot={},
        clock=object(),
        io_channel="cli",
        send_assistant_text=lambda text: sent_text.append(text),
        last_user_message_ts="2026-03-10T11:00:00+00:00",
        prior_pipeline_state=None,
        poll_background_source_ingestion=lambda **_: {
            "ok": True,
            "status": "completed",
            "payload": {"ingestion_request_id": "req-1"},
        },
        emit_obligation_transition=lambda **kwargs: events.append(("transition", kwargs)),
        utc_now_iso=lambda: "2026-03-10T11:00:00+00:00",
        append_session_log=lambda event, payload: events.append((event, payload)),
        format_background_ingestion_completion_message=lambda **_: "Background done",
        replay_background_completion_turn=_replay,
        answer_commit_persistence=lambda **_: persisted.append("yes"),
    )

    assert processed is True
    assert state is not None
    assert sent_text == ["Background done", "Grounded answer."]
    assert persisted == ["yes"]
    assert replay_requests and replay_requests[0].utterance == "What changed?"
    assert any(event == "transition" and payload["status"] == "resolved" for event, payload in events)


def test_poll_background_source_ingestion_running_state() -> None:
    rt = {
        "source_ingest_background_future": Future(),
        "source_ingest_background_request_id": "req-5",
        "source_ingest_background_in_progress": False,
    }

    result = runtime.poll_background_source_ingestion(
        runtime=rt,
        append_session_log=lambda *_: None,
    )

    assert result == {"status": "running", "ingestion_request_id": "req-5"}
    assert rt["source_ingest_background_in_progress"] is True
