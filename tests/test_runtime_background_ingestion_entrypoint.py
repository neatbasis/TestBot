from __future__ import annotations

from types import SimpleNamespace

from testbot.continuity_read_model import CommittedTurnContinuity, ContinuityReadModel
from testbot.entrypoints import runtime_background_ingestion as entrypoint


def test_register_pending_ingestion_obligation_uses_canonical_now_iso_and_emits_created_transition(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(entrypoint.arrow, "utcnow", lambda: entrypoint.arrow.get("2026-03-10T11:00:00+00:00"))

    deps = entrypoint.RuntimeBackgroundIngestionDependencies(
        append_session_log=lambda event, payload: events.append((event, payload)),
        build_source_connector=lambda _runtime: None,
        source_ingestor_cls=object,
        answer_commit_persistence=lambda **_kwargs: None,
        replay_background_completion_turn=lambda _request: None,
    )

    runtime: dict[str, object] = {}
    state = SimpleNamespace(
        candidate_facts=SimpleNamespace(turn_id="turn-doc-123"),
        same_turn_exclusion={"excluded_doc_ids": ["turn-doc-123", "reflection-doc-123"]},
    )

    created = entrypoint.register_pending_ingestion_obligation(
        runtime=runtime,
        pending_request_id="ingest-req-123",
        utterance="What changed?",
        turn_id="turn-123",
        state=state,
        prior_pipeline_state=None,
        deps=deps,
        obligation_timeout_seconds=60,
    )

    assert created is True
    pending = runtime["pending_ingestion_registry"]["ingest-req-123"]
    assert pending["created_at"] == "2026-03-10T11:00:00+00:00"
    assert pending["last_polled_at"] == "2026-03-10T11:00:00+00:00"
    assert pending["deadline_at"] == "2026-03-10T11:01:00+00:00"
    assert pending["source_context"] == {
        "utterance_doc_id": "turn-doc-123",
        "same_turn_exclusion_doc_ids": ["turn-doc-123", "reflection-doc-123"],
    }
    assert pending["prior_continuity"] is None
    assert events == [
        (
            "source_ingest_obligation_transition",
            {
                "ingestion_request_id": "ingest-req-123",
                "status": "created",
                "created_at": "2026-03-10T11:00:00+00:00",
                "last_polled_at": "2026-03-10T11:00:00+00:00",
                "attempt_count": 0,
                "deadline_at": "2026-03-10T11:01:00+00:00",
            },
        )
    ]


def test_register_pending_ingestion_obligation_keeps_explicit_prior_continuity_for_runtime_replay(monkeypatch) -> None:
    monkeypatch.setattr(entrypoint.arrow, "utcnow", lambda: entrypoint.arrow.get("2026-03-10T11:00:00+00:00"))
    deps = entrypoint.RuntimeBackgroundIngestionDependencies(
        append_session_log=lambda *_args: None,
        build_source_connector=lambda _runtime: None,
        source_ingestor_cls=object,
        answer_commit_persistence=lambda **_kwargs: None,
        replay_background_completion_turn=lambda _request: None,
    )
    runtime: dict[str, object] = {}
    state = SimpleNamespace(
        candidate_facts=SimpleNamespace(turn_id="turn-doc-123"),
        same_turn_exclusion={"excluded_doc_ids": []},
    )
    prior_continuity = ContinuityReadModel(
        committed_turn=CommittedTurnContinuity(
            turn_id="turn-123",
            commit_stage="answer.commit",
            pending_ingestion_request_id="ingest-req-123",
        )
    )

    created = entrypoint.register_pending_ingestion_obligation(
        runtime=runtime,
        pending_request_id="ingest-req-123",
        utterance="What changed?",
        turn_id="turn-123",
        state=state,
        prior_pipeline_state=None,
        deps=deps,
        prior_continuity=prior_continuity,
    )

    assert created is True
    assert runtime["pending_ingestion_registry"]["ingest-req-123"]["prior_continuity"] is prior_continuity
