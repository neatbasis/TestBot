from __future__ import annotations

from collections import deque
import json
from dataclasses import replace

import arrow
import pytest
from langchain_core.documents import Document

from testbot import sat_chatbot_memory_v2 as runtime
from testbot.entrypoints import runtime_background_ingestion, runtime_loop
from testbot.intent_router import IntentType
from testbot.pipeline_state import AlignmentDecision, PipelineState
from testbot.sat_chatbot_memory_v2 import (
    CapabilitySnapshot,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    RuntimeCapabilityStatus,
    run_canonical_answer_stage_flow,
)


class _FixedClock:
    def now(self) -> arrow.Arrow:
        return arrow.get("2026-03-10T11:00:00+00:00")


_FIXED_CLOCK = _FixedClock()


class _StaticLLM:
    def __init__(self, content: str) -> None:
        self.content = content

    def invoke(self, _msgs):
        return type("_Resp", (), {"content": self.content})()


class _HarnessStore:
    def __init__(self) -> None:
        self._docs: list[object] = []
        self._records: list[object] = []

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
        del query, k, kwargs
        return []

    def add_documents(self, docs) -> None:
        self._docs.extend(list(docs))

    def add_memory_records(self, records) -> None:
        self._records.extend(list(records))


def _compat_runtime_replay_deps(
    *,
    append_session_log,
    answer_commit_persistence,
) -> runtime_background_ingestion.RuntimeBackgroundIngestionDependencies:
    def _replay(request):
        replay_state, _hits = runtime._run_canonical_turn_pipeline(
            runtime=request.runtime,
            llm=request.llm,
            store=request.store,
            state=PipelineState(
                user_input=request.utterance,
                last_user_message_ts=request.last_user_message_ts,
                classified_intent=IntentType.KNOWLEDGE_QUESTION.value,
                resolved_intent="",
                prior_unresolved_intent=(
                    request.prior_pipeline_state.prior_unresolved_intent
                    if isinstance(request.prior_pipeline_state, PipelineState)
                    else ""
                ),
                confidence_decision={},
            ),
            utterance=request.utterance,
            prior_pipeline_state=request.prior_pipeline_state,
            turn_id=request.turn_id,
            near_tie_delta=request.near_tie_delta,
            chat_history=request.chat_history,
            capability_status=request.capability_status,
            capability_snapshot=request.capability_snapshot,
            clock=request.clock,
            io_channel=request.io_channel,
        )
        return replay_state

    return runtime_background_ingestion.RuntimeBackgroundIngestionDependencies(
        append_session_log=append_session_log,
        build_source_connector=lambda _runtime: None,
        source_ingestor_cls=object,
        answer_commit_persistence=answer_commit_persistence,
        replay_background_completion_turn=_replay,
    )


def test_stage_retrieve_passes_hygiene_exclusions_and_blocks_same_turn_candidates() -> None:
    class _FilteringStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k
            docs = [
                Document(id="turn-user", page_content="latest", metadata={"doc_id": "turn-user"}),
                Document(id="turn-reflection", page_content="reflection", metadata={"doc_id": "turn-reflection", "source_doc_id": "turn-user"}),
                Document(id="older-memory", page_content="older", metadata={"doc_id": "older-memory"}),
            ]
            excluded_docs = set(kwargs.get("exclude_doc_ids") or set())
            excluded_sources = set(kwargs.get("exclude_source_ids") or set())
            excluded_turn = set(kwargs.get("exclude_turn_scoped_ids") or set())
            kept = []
            for doc in docs:
                source = str(doc.metadata.get("source_doc_id") or "")
                if doc.id in excluded_docs:
                    continue
                if source and source in excluded_sources:
                    continue
                if doc.id in excluded_turn or source in excluded_turn:
                    continue
                kept.append((doc, 0.9))
            return kept

    state = PipelineState(user_input="what did i just say", rewritten_query="latest memory")
    updated_state, docs_and_scores = runtime.stage_retrieve(
        _FilteringStore(),
        state,
        exclude_doc_ids={"turn-user", "turn-reflection"},
        exclude_source_ids={"turn-user"},
        exclude_turn_scoped_ids={"turn-user", "turn-reflection"},
    )

    assert [doc.id for doc, _score in docs_and_scores] == ["older-memory"]
    assert [candidate.doc_id for candidate in updated_state.retrieval_candidates] == ["older-memory"]
    assert updated_state.confidence_decision["retrieval_exclude_doc_ids"] == ["turn-reflection", "turn-user"]
    assert updated_state.confidence_decision["retrieval_exclusion_invariant"] == "retrieve_stage_primary"


def test_run_canonical_answer_stage_flow_seeded_store_honors_retrieval_exclusions_for_same_turn_and_synthetic_hits(monkeypatch) -> None:
    captured_doc_ids: list[str] = []

    def _stub_pipeline(**kwargs):
        docs_and_scores = kwargs["store"].similarity_search_with_score(
            "q",
            k=18,
            exclude_doc_ids={"turn-user"},
            exclude_source_ids={"turn-user"},
            exclude_turn_scoped_ids={"turn-user"},
        )
        captured_doc_ids.extend(str(doc.id or "") for doc, _score in docs_and_scores)
        return kwargs["state"], []

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _stub_pipeline)
    state = PipelineState(
        user_input="what did i just say?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={"context_confident": True, "ambiguity_detected": False},
    )
    hits = [
        Document(
            id="turn-user",
            page_content="turn-local utterance snapshot",
            metadata={"doc_id": "turn-user", "turn_doc_id": "turn-user"},
        ),
        Document(
            id="seeded-snapshot",
            page_content="serialized pipeline snapshot artifact",
            metadata={"doc_id": "seeded-snapshot", "pipeline_state_snapshot": True},
        ),
        Document(
            id="older-memory",
            page_content="Earlier memory: you asked about release notes.",
            metadata={"doc_id": "older-memory", "ts": "2026-03-09T12:00:00Z"},
        ),
    ]

    _ = run_canonical_answer_stage_flow(
        _StaticLLM("ignored"),
        state,
        chat_history=deque(),
        hits=hits,
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert captured_doc_ids == ["older-memory"]


@pytest.mark.non_contract
def test_chat_loop_async_pending_lookup_commits_pending_answer_and_logs_semantics(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])

    def _start_background_ingest(
        *,
        runtime: dict[str, object],
        store: object,
        deps,
        ingestion_request_id: str = "",
    ) -> dict[str, object]:
        del store
        runtime["source_ingest_background_in_progress"] = True
        runtime["source_ingest_background_future"] = None
        runtime["source_ingest_background_stub"] = True
        request_id = ingestion_request_id or "stub-ingest-1"
        runtime["source_ingest_background_request_id"] = request_id
        runtime.append_session_log("source_ingest_background_started", {"background": True, "ingestion_request_id": request_id})
        return {"started": True, "already_running": False, "ingestion_request_id": request_id}

    monkeypatch.setattr(runtime_background_ingestion, "start_background_source_ingestion", _start_background_ingest)

    class _EmptyStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k, kwargs
            return []

        def add_documents(self, docs) -> None:
            del docs

        def add_memory_records(self, records) -> None:
            del records

    prompts = iter(["what did i say?", "stop"])
    replies: list[str] = []
    runtime_loop.run_chat_loop(
        runtime={"source_ingest_async_continuation": True},
        llm=_StaticLLM("ignored"),
        store=_EmptyStore(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={"source_ingest_async_continuation": True},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
        replay_background_completion_turn=_compat_runtime_replay_deps(
            append_session_log=runtime_loop.append_runtime_session_log,
            answer_commit_persistence=runtime_loop.persist_answer_commit,
        ).replay_background_completion_turn,
    )

    assert replies[0] == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    events = [row.get("event") for row in rows]
    assert "source_ingest_background_started" in events

    started_row = next(row for row in rows if row.get("event") == "source_ingest_background_started")
    ingestion_request_id = started_row["ingestion_request_id"]
    commit_row = next(row for row in rows if row.get("event") == "commit_stage_recorded")
    assert commit_row["pending_repair_state"]["repair_required_by_policy"] is True
    assert commit_row["pending_repair_state"]["repair_offered_to_user"] is False
    assert commit_row["pending_ingestion_request_id"] == ingestion_request_id

    retrieval_row = next(row for row in rows if row.get("event") == "retrieval_candidates")
    hygiene = retrieval_row.get("hygiene", {})
    assert ingestion_request_id not in hygiene.get("exclude_doc_ids", [])
    assert ingestion_request_id not in hygiene.get("exclude_source_ids", [])
    assert ingestion_request_id not in hygiene.get("exclude_turn_scoped_ids", [])

    mode_row = next(row for row in rows if row.get("event") == "final_answer_mode")
    assert mode_row["mode"] == "assist"
    assert mode_row["query"] == "ignored"
    assert mode_row["stage_audit_trail"] == list(runtime.CanonicalTurnOrchestrator.STAGE_ORDER)


def test_chat_loop_async_pending_lookup_contract_path_reaches_answer_commit_post(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])

    def _start_background_ingest(
        *,
        runtime: dict[str, object],
        store: object,
        deps,
        ingestion_request_id: str = "",
    ) -> dict[str, object]:
        del store
        runtime["source_ingest_background_in_progress"] = True
        runtime["source_ingest_background_future"] = None
        runtime["source_ingest_background_stub"] = True
        request_id = ingestion_request_id or "stub-ingest-1"
        runtime["source_ingest_background_request_id"] = request_id
        runtime.append_session_log("source_ingest_background_started", {"background": True, "ingestion_request_id": request_id})
        return {"started": True, "already_running": False, "ingestion_request_id": request_id}

    monkeypatch.setattr(runtime_background_ingestion, "start_background_source_ingestion", _start_background_ingest)

    class _EmptyStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k, kwargs
            return []

        def add_documents(self, docs) -> None:
            del docs

        def add_memory_records(self, records) -> None:
            del records

    prompts = iter(["what did i say?", "stop"])
    replies: list[str] = []
    runtime_loop.run_chat_loop(
        runtime={"source_ingest_async_continuation": True},
        llm=_StaticLLM("ignored"),
        store=_EmptyStore(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={"source_ingest_async_continuation": True},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
        replay_background_completion_turn=_compat_runtime_replay_deps(
            append_session_log=runtime_loop.append_runtime_session_log,
            answer_commit_persistence=runtime_loop.persist_answer_commit,
        ).replay_background_completion_turn,
    )

    assert replies[0] == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    transition_rows = [row for row in rows if row.get("event") == "stage_transition_validation"]
    commit_post_row = next(row for row in transition_rows if row.get("stage") == "answer.commit" and row.get("boundary") == "post")
    assert commit_post_row["passed"] is True
    symptom_hits = [row for row in transition_rows if "inv_003_general_knowledge_contract_enforced" in (row.get("failures") or [])]
    assert symptom_hits == []

    commit_row = next(row for row in rows if row.get("event") == "commit_stage_recorded")
    assert commit_row["pending_repair_state"]["repair_required_by_policy"] is True
    assert commit_row["pending_repair_state"]["repair_offered_to_user"] is False
    assert commit_row["pending_ingestion_request_id"] != ""

    mode_row = next(row for row in rows if row.get("event") == "final_answer_mode")
    assert mode_row["mode"] == "assist"
    assert mode_row["query"] == "ignored"


def test_final_answer_mode_stage_audit_trail_includes_answer_commit(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])

    def _start_background_ingest(
        *,
        runtime: dict[str, object],
        store: object,
        deps,
        ingestion_request_id: str = "",
    ) -> dict[str, object]:
        del store
        runtime["source_ingest_background_in_progress"] = True
        runtime["source_ingest_background_future"] = None
        runtime["source_ingest_background_stub"] = True
        request_id = ingestion_request_id or "stub-ingest-1"
        runtime["source_ingest_background_request_id"] = request_id
        runtime.append_session_log("source_ingest_background_started", {"background": True, "ingestion_request_id": request_id})
        return {"started": True, "already_running": False, "ingestion_request_id": request_id}

    monkeypatch.setattr(runtime_background_ingestion, "start_background_source_ingestion", _start_background_ingest)

    class _EmptyStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k, kwargs
            return []

        def add_documents(self, docs) -> None:
            del docs

        def add_memory_records(self, records) -> None:
            del records

    prompts = iter(["what did i say?", "stop"])
    runtime_loop.run_chat_loop(
        runtime={"source_ingest_async_continuation": True},
        llm=_StaticLLM("ignored"),
        store=_EmptyStore(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={"source_ingest_async_continuation": True},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
        replay_background_completion_turn=_compat_runtime_replay_deps(
            append_session_log=runtime_loop.append_runtime_session_log,
            answer_commit_persistence=runtime_loop.persist_answer_commit,
        ).replay_background_completion_turn,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    mode_row = next(row for row in rows if row.get("event") == "final_answer_mode")
    assert mode_row["stage_audit_trail"] == list(runtime.CanonicalTurnOrchestrator.STAGE_ORDER)


def test_background_ingestion_pending_lifecycle_event_order_and_payloads(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    assistant_messages: list[str] = []

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))

    from concurrent.futures import Future

    completed_future: Future = Future()
    completed_future.set_result(
        {
            "ok": True,
            "status": "completed",
            "payload": {
                "ingestion_request_id": "turn-789",
                "source_type": "calendar",
                "fetched_count": 1,
                "stored_count": 1,
            },
        }
    )

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", lambda **kwargs: (
        replace(
            kwargs["state"],
            final_answer="Your utility bill is due Friday and confirmed by synced source evidence.",
            used_source_evidence_refs=["src-900"],
        ),
        [],
    ))
    monkeypatch.setattr(runtime, "answer_commit_persistence", lambda **kwargs: None)

    runtime_state: dict[str, object] = {
        "source_ingest_background_future": completed_future,
        "source_ingest_background_in_progress": True,
        "source_ingest_background_request_id": "turn-789",
        "pending_ingestion_registry": {
            "turn-789": {
                "utterance": "What is due next?",
                "prior_pipeline_state": None,
                "created_at": "2026-03-10T10:00:00+00:00",
                "last_polled_at": "2026-03-10T10:01:00+00:00",
                "attempt_count": 4,
                "deadline_at": "2026-03-10T12:00:00+00:00",
                "status": "pending",
            }
        },
    }

    last_ts, prior_state, processed = runtime_background_ingestion.process_background_ingestion_completion(
        runtime=runtime_state,
        llm=_StaticLLM("ignored"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        clock=_FIXED_CLOCK,
        io_channel="cli",
        send_assistant_text=lambda text: assistant_messages.append(text),
        last_user_message_ts="",
        prior_pipeline_state=None,
        deps=_compat_runtime_replay_deps(
            append_session_log=lambda event, payload: events.append((event, payload)),
            answer_commit_persistence=lambda **kwargs: None,
        ),
    )

    assert processed is True
    assert last_ts == ""
    assert prior_state is not None

    synthetic_events = [
        {"event": "source_ingest_background_started", "ingestion_request_id": "turn-789"},
        {
            "event": "source_ingest_user_start_notified",
            "ingestion_request_id": "turn-789",
            "message_text": runtime.BACKGROUND_INGESTION_PROGRESS_ANSWER,
        },
        {
            "event": "pending_ingestion_persisted",
            "ingestion_request_id": "turn-789",
            "correlation_id": "turn-789",
        },
    ]
    synthetic_events.extend(
        {"event": event_name, **payload}
        for event_name, payload in events
        if event_name in {"source_ingest_completion_event_emitted", "source_ingest_completion_answer_emitted"}
    )

    assert [event["event"] for event in synthetic_events] == [
        "source_ingest_background_started",
        "source_ingest_user_start_notified",
        "pending_ingestion_persisted",
        "source_ingest_completion_event_emitted",
        "source_ingest_completion_answer_emitted",
    ]
    completion_event = synthetic_events[3]
    assert completion_event["ingestion_request_id"] == "turn-789"
    assert completion_event["linked_pending_ingestion_request_id"] == "turn-789"
    assert completion_event["event_type"] == "source_ingestion_completion"

    completion_answer = synthetic_events[4]
    assert completion_answer["ingestion_request_id"] == "turn-789"
    assert completion_answer["linked_pending_ingestion_request_id"] == "turn-789"
    assert "synced source evidence" in completion_answer["final_answer"]

    completion_user_notice = next(payload for name, payload in events if name == "source_ingest_completion_user_message_emitted")
    assert completion_user_notice["ingestion_request_id"] == "turn-789"
    assert completion_user_notice["linked_pending_ingestion_request_id"] == "turn-789"
    assert assistant_messages[0] == completion_user_notice["message_text"]

    obligation_events = [payload for name, payload in events if name == "source_ingest_obligation_transition"]
    assert obligation_events
    assert obligation_events[-1]["ingestion_request_id"] == "turn-789"
    assert obligation_events[-1]["status"] == "resolved"


def test_chat_loop_emits_completion_event_user_message_and_linked_answer(tmp_path, monkeypatch) -> None:
    from testbot.entrypoints import runtime_background_ingestion

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr("testbot.entrypoints.runtime_loop.persist_answer_commit", lambda **kwargs: None)

    poll_calls = {"count": 0}

    def _poll(*, runtime: dict[str, object]):
        poll_calls["count"] += 1
        if poll_calls["count"] == 1:
            return {
                "ok": True,
                "status": "completed",
                "payload": {"ingestion_request_id": "turn-123", "background": True, "stored_count": 2},
            }
        return None

    monkeypatch.setattr(runtime_background_ingestion, "poll_background_source_ingestion", lambda *, runtime, deps: _poll(runtime=runtime))

    def _pipeline(**kwargs):
        state = kwargs["state"]
        return (
            replace(
                state,
                final_answer="Grounded answer after ingestion.",
                commit_receipt={"pending_ingestion_request_id": ""},
                invariant_decisions={"fallback_action": "NONE", "answer_mode": "knowing"},
                confidence_decision={"stage_audit_trail": []},
                provenance_types=[],
                claims=[],
                used_memory_refs=[],
                used_source_evidence_refs=["src-900"],
                source_evidence_attribution=[],
                basis_statement="source evidence",
                alignment_decision=AlignmentDecision(),
            ),
            [],
        )

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _pipeline)

    prompts = iter(["stop"])
    runtime_loop.run_chat_loop(
        runtime={"pending_ingestion_registry": {"turn-123": {"utterance": "What is due Friday?", "prior_pipeline_state": None}}},
        llm=_StaticLLM("ignored"),
        store=_HarnessStore(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
        replay_background_completion_turn=_compat_runtime_replay_deps(
            append_session_log=runtime_loop.append_runtime_session_log,
            answer_commit_persistence=runtime_loop.persist_answer_commit,
        ).replay_background_completion_turn,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    completion_event = next(row for row in rows if row.get("event") == "source_ingest_completion_event_emitted")
    assert completion_event["ingestion_request_id"] == "turn-123"
    assert completion_event["linked_pending_ingestion_request_id"] == "turn-123"

    completion_message = next(row for row in rows if row.get("event") == "source_ingest_completion_user_message_emitted")
    assert completion_message["linked_pending_ingestion_request_id"] == "turn-123"
    assert completion_message["message_text"].startswith("Background ingestion completed for request turn-123")

    completion_answer = next(row for row in rows if row.get("event") == "source_ingest_completion_answer_emitted")
    assert completion_answer["linked_pending_ingestion_request_id"] == "turn-123"
    assert completion_answer["final_answer"] == "Grounded answer after ingestion."
