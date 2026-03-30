from __future__ import annotations

from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable
import uuid

import arrow

from testbot.continuity_read_model import ContinuityReadModel, continuity_read_model_from_pipeline_state


_BACKGROUND_SOURCE_INGEST_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="source-ingest")
_BACKGROUND_SOURCE_INGEST_LOCK = Lock()


@dataclass(frozen=True)
class BackgroundIngestionReplayRequest:
    runtime: dict[str, object]
    llm: Any
    store: Any
    utterance: str
    last_user_message_ts: str
    prior_pipeline_state: Any
    near_tie_delta: float
    chat_history: deque[dict[str, str]]
    capability_status: Any
    capability_snapshot: Any
    clock: Any
    io_channel: str
    turn_id: str
    prior_continuity: ContinuityReadModel | None = None


def emit_obligation_transition(
    *,
    append_session_log: Callable[[str, dict[str, object]], None],
    ingestion_request_id: str,
    status: str,
    created_at: str,
    last_polled_at: str,
    attempt_count: int,
    deadline_at: str,
) -> None:
    append_session_log(
        "source_ingest_obligation_transition",
        {
            "ingestion_request_id": ingestion_request_id,
            "status": status,
            "created_at": created_at,
            "last_polled_at": last_polled_at,
            "attempt_count": attempt_count,
            "deadline_at": deadline_at,
        },
    )


def poll_pending_ingestion_obligations(
    *,
    runtime: dict[str, object],
    append_session_log: Callable[[str, dict[str, object]], None],
    obligation_timeout_seconds: int,
    utcnow: Callable[[], arrow.Arrow],
) -> None:
    pending_registry = runtime.get("pending_ingestion_registry")
    if not isinstance(pending_registry, dict):
        return

    now = utcnow()
    now_iso = now.isoformat()
    for request_id, raw_record in list(pending_registry.items()):
        if not isinstance(raw_record, dict):
            continue

        created_at = str(raw_record.get("created_at") or now_iso)
        deadline_at = str(raw_record.get("deadline_at") or "")
        attempt_count = int(raw_record.get("attempt_count") or 0) + 1
        raw_record["created_at"] = created_at
        raw_record["last_polled_at"] = now_iso
        raw_record["attempt_count"] = attempt_count

        if not deadline_at:
            deadline_at = now.shift(seconds=obligation_timeout_seconds).isoformat()
            raw_record["deadline_at"] = deadline_at

        timed_out = False
        try:
            timed_out = now >= arrow.get(deadline_at)
        except (arrow.parser.ParserError, ValueError):
            deadline_at = now.shift(seconds=obligation_timeout_seconds).isoformat()
            raw_record["deadline_at"] = deadline_at

        if timed_out:
            raw_record["status"] = "timed_out"
            raw_record["last_polled_at"] = now_iso
            dead_letter_registry = runtime.setdefault("dead_letter_ingestion_registry", {})
            if isinstance(dead_letter_registry, dict):
                dead_letter_registry[str(request_id)] = dict(raw_record)
            emit_obligation_transition(
                append_session_log=append_session_log,
                ingestion_request_id=str(request_id),
                status="timed_out",
                created_at=created_at,
                last_polled_at=now_iso,
                attempt_count=attempt_count,
                deadline_at=deadline_at,
            )
            pending_registry.pop(request_id, None)
            continue

        raw_record["status"] = "pending"
        emit_obligation_transition(
            append_session_log=append_session_log,
            ingestion_request_id=str(request_id),
            status="polled_pending",
            created_at=created_at,
            last_polled_at=now_iso,
            attempt_count=attempt_count,
            deadline_at=deadline_at,
        )


def execute_source_ingestion(
    *,
    runtime: dict[str, object],
    store: Any,
    build_source_connector: Callable[[dict[str, object]], Any | None],
    source_ingestor_cls: Any,
    append_session_log: Callable[[str, dict[str, object]], None],
    background: bool = False,
    ingestion_request_id: str = "",
) -> dict[str, object]:
    connector = build_source_connector(runtime)
    if connector is None:
        return {"ok": False, "status": "skipped", "background": background, "ingestion_request_id": ingestion_request_id}

    ingestor = source_ingestor_cls(connector=connector, memory_store=store)
    cursor = str(runtime.get("source_ingest_cursor")) if runtime.get("source_ingest_cursor") is not None else None
    limit = int(runtime.get("source_ingest_limit", 50))
    if cursor is not None and not cursor.isdigit():
        append_session_log(
            "source_ingest_cursor_invalid",
            {
                "cursor": cursor,
                "fallback_cursor": None,
                "background": background,
            },
        )
        cursor = None

    try:
        result = ingestor.ingest_once(
            cursor=cursor,
            limit=limit,
        )
    except Exception as exc:
        payload = {
            "connector_type": str(runtime.get("source_connector_type", "")).strip().lower(),
            "source_type": connector.source_type,
            "cursor": cursor,
            "limit": limit,
            "exception_class": exc.__class__.__name__,
            "exception_message": str(exc),
            "background": background,
            "ingestion_request_id": ingestion_request_id,
        }
        return {"ok": False, "status": "failed", "payload": payload}

    payload = {
        "source_type": connector.source_type,
        "fetched_count": result.fetched_count,
        "stored_count": result.stored_count,
        "next_cursor": result.next_cursor,
        "memory_doc_ids": [str(doc.doc_id or "") for doc in result.memory_documents],
        "evidence_doc_ids": [str(doc.doc_id or "") for doc in result.evidence_documents],
        "background": background,
        "ingestion_request_id": ingestion_request_id,
    }
    return {"ok": True, "status": "completed", "payload": payload}


def start_background_source_ingestion(
    *,
    runtime: dict[str, object],
    store: Any,
    execute_source_ingestion: Callable[..., dict[str, object]],
    append_session_log: Callable[[str, dict[str, object]], None],
    ingestion_request_id: str = "",
) -> dict[str, object]:
    with _BACKGROUND_SOURCE_INGEST_LOCK:
        existing_future = runtime.get("source_ingest_background_future")
        if isinstance(existing_future, Future) and not existing_future.done():
            existing_request_id = str(runtime.get("source_ingest_background_request_id") or "")
            return {"started": False, "already_running": True, "ingestion_request_id": existing_request_id}

        request_id = str(ingestion_request_id or f"ingest-req-{uuid.uuid4()}")
        runtime["source_ingest_background_request_id"] = request_id

        future = _BACKGROUND_SOURCE_INGEST_EXECUTOR.submit(
            execute_source_ingestion,
            runtime=runtime,
            store=store,
            background=True,
            ingestion_request_id=request_id,
        )
        runtime["source_ingest_background_future"] = future
        runtime["source_ingest_background_in_progress"] = True
        append_session_log("source_ingest_background_started", {"background": True, "ingestion_request_id": request_id})
        return {"started": True, "already_running": False, "ingestion_request_id": request_id}


def poll_background_source_ingestion(
    *,
    runtime: dict[str, object],
    append_session_log: Callable[[str, dict[str, object]], None],
) -> dict[str, object] | None:
    with _BACKGROUND_SOURCE_INGEST_LOCK:
        future = runtime.get("source_ingest_background_future")
        if not isinstance(future, Future):
            runtime["source_ingest_background_in_progress"] = False
            return None
        if not future.done():
            runtime["source_ingest_background_in_progress"] = True
            return {"status": "running", "ingestion_request_id": str(runtime.get("source_ingest_background_request_id") or "")}

        runtime["source_ingest_background_in_progress"] = False
        runtime["source_ingest_background_future"] = None
        request_id = str(runtime.get("source_ingest_background_request_id") or "")
        runtime["source_ingest_background_request_id"] = ""

    result = future.result()
    if request_id and "payload" in result and isinstance(result["payload"], dict) and not result["payload"].get("ingestion_request_id"):
        result["payload"]["ingestion_request_id"] = request_id
    if result.get("ok"):
        append_session_log("source_ingest_completed", dict(result["payload"]))
    elif result.get("status") == "failed":
        append_session_log("source_ingest_failed", dict(result["payload"]))
    return result


def format_background_ingestion_completion_message(*, correlation_id: str, template: str) -> str:
    return template.format(correlation_id=correlation_id or "unknown")


def process_background_ingestion_completion(
    *,
    runtime: dict[str, object],
    llm: Any,
    store: Any,
    chat_history: deque[dict[str, str]],
    near_tie_delta: float,
    capability_status: Any,
    capability_snapshot: Any,
    clock: Any,
    io_channel: str,
    send_assistant_text: Callable[[str], None],
    last_user_message_ts: str,
    prior_pipeline_state: Any,
    poll_background_source_ingestion: Callable[..., dict[str, object] | None],
    emit_obligation_transition: Callable[..., None],
    utc_now_iso: Callable[[], str],
    append_session_log: Callable[[str, dict[str, object]], None],
    format_background_ingestion_completion_message: Callable[..., str],
    replay_background_completion_turn: Callable[[BackgroundIngestionReplayRequest], Any],
    apply_unresolved_intent_carryover: Callable[[Any], Any],
    answer_commit_persistence: Callable[..., None],
) -> tuple[str, Any, bool]:
    poll_result = poll_background_source_ingestion(runtime=runtime)
    if not isinstance(poll_result, dict) or poll_result.get("status") != "completed":
        return last_user_message_ts, prior_pipeline_state, False

    payload = poll_result.get("payload") if isinstance(poll_result.get("payload"), dict) else {}
    correlation_id = str(payload.get("ingestion_request_id") or "")
    pending_registry = runtime.get("pending_ingestion_registry")
    if not isinstance(pending_registry, dict) or not correlation_id:
        return last_user_message_ts, prior_pipeline_state, False

    pending_context = pending_registry.pop(correlation_id, None)
    if not isinstance(pending_context, dict):
        return last_user_message_ts, prior_pipeline_state, False

    emit_obligation_transition(
        ingestion_request_id=correlation_id,
        status="resolved",
        created_at=str(pending_context.get("created_at") or utc_now_iso()),
        last_polled_at=utc_now_iso(),
        attempt_count=int(pending_context.get("attempt_count") or 0),
        deadline_at=str(pending_context.get("deadline_at") or ""),
    )
    pending_context["status"] = "resolved"

    original_utterance = str(pending_context.get("utterance") or "")
    original_prior_state = pending_context.get("prior_pipeline_state")
    original_prior_continuity = pending_context.get("prior_continuity")
    if original_prior_state is not None and prior_pipeline_state is not None:
        if not isinstance(original_prior_state, prior_pipeline_state.__class__):
            original_prior_state = prior_pipeline_state
    if original_prior_continuity is None:
        original_prior_continuity = continuity_read_model_from_pipeline_state(original_prior_state)

    append_session_log(
        "source_ingest_completion_event_emitted",
        {
            "event_type": "source_ingestion_completion",
            "ingestion_request_id": correlation_id,
            "linked_pending_ingestion_request_id": correlation_id,
            "original_utterance": original_utterance,
            "io_channel": io_channel,
        },
    )
    completion_message = format_background_ingestion_completion_message(correlation_id=correlation_id)
    send_assistant_text(completion_message)
    append_session_log(
        "source_ingest_completion_user_message_emitted",
        {
            "event_type": "assistant_text",
            "ingestion_request_id": correlation_id,
            "linked_pending_ingestion_request_id": correlation_id,
            "message_text": completion_message,
        },
    )

    continuation_turn_id = str(uuid.uuid4())
    regenerated_state = replay_background_completion_turn(
        BackgroundIngestionReplayRequest(
            runtime=runtime,
            llm=llm,
            store=store,
            utterance=original_utterance,
            last_user_message_ts=last_user_message_ts,
            prior_pipeline_state=original_prior_state,
            prior_continuity=original_prior_continuity,
            near_tie_delta=near_tie_delta,
            chat_history=chat_history,
            capability_status=capability_status,
            capability_snapshot=capability_snapshot,
            clock=clock,
            io_channel=io_channel,
            turn_id=continuation_turn_id,
        )
    )
    regenerated_state = apply_unresolved_intent_carryover(regenerated_state)
    send_assistant_text(regenerated_state.final_answer)
    append_session_log(
        "source_ingest_completion_answer_emitted",
        {
            "ingestion_request_id": correlation_id,
            "linked_pending_ingestion_request_id": correlation_id,
            "continuation_turn_id": continuation_turn_id,
            "final_answer": regenerated_state.final_answer,
            "used_source_evidence_refs": regenerated_state.used_source_evidence_refs,
        },
    )
    chat_history.append({"role": "assistant", "content": completion_message})
    chat_history.append({"role": "assistant", "content": regenerated_state.final_answer})
    answer_commit_persistence(
        llm=llm,
        store=store,
        state=regenerated_state,
        io_channel=io_channel,
        clock=clock,
    )
    return last_user_message_ts, regenerated_state, True
