"""Canonical runtime-owned background ingestion helper assembly.

Ownership:
- This module is the canonical owner for runtime background-ingestion helper
  wiring used by runtime loop + turn-pipeline entrypoints.
- Compatibility façades may delegate here during retirement windows.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

import arrow
from langchain_ollama import ChatOllama

from testbot.application.services import background_ingestion_runtime as background_ingestion_runtime_service
from testbot.application.services import continuity_runtime as continuity_runtime_service
from testbot.application.services.background_ingestion_runtime import BackgroundIngestionReplayRequest
from testbot.continuity_read_model import ContinuityReadModel
from testbot.pipeline_state import PipelineState
from testbot.ports import MemoryStorePort


BACKGROUND_INGESTION_COMPLETION_MESSAGE_TEMPLATE = (
    "Background ingestion completed for request {correlation_id}. "
    "Here is the newly grounded answer:"
)
BACKGROUND_INGESTION_OBLIGATION_TIMEOUT_SECONDS = 900

ChatMsg = dict[str, str]


@dataclass(frozen=True)
class RuntimeBackgroundIngestionDependencies:
    append_session_log: Callable[[str, dict[str, object]], None]
    build_source_connector: Callable[[dict[str, object]], object | None]
    source_ingestor_cls: object
    answer_commit_persistence: Callable[..., None]
    replay_background_completion_turn: Callable[[BackgroundIngestionReplayRequest], PipelineState]


def execute_source_ingestion(
    *,
    runtime: dict[str, object],
    store: MemoryStorePort,
    deps: RuntimeBackgroundIngestionDependencies,
    background: bool = False,
    ingestion_request_id: str = "",
) -> dict[str, object]:
    return background_ingestion_runtime_service.execute_source_ingestion(
        runtime=runtime,
        store=store,
        build_source_connector=deps.build_source_connector,
        source_ingestor_cls=deps.source_ingestor_cls,
        append_session_log=deps.append_session_log,
        background=background,
        ingestion_request_id=ingestion_request_id,
    )


def start_background_source_ingestion(
    *,
    runtime: dict[str, object],
    store: MemoryStorePort,
    deps: RuntimeBackgroundIngestionDependencies,
    ingestion_request_id: str = "",
) -> dict[str, object]:
    return background_ingestion_runtime_service.start_background_source_ingestion(
        runtime=runtime,
        store=store,
        execute_source_ingestion=lambda **kwargs: execute_source_ingestion(
            deps=deps,
            **kwargs,
        ),
        append_session_log=deps.append_session_log,
        ingestion_request_id=ingestion_request_id,
    )


def poll_background_source_ingestion(
    *,
    runtime: dict[str, object],
    deps: RuntimeBackgroundIngestionDependencies,
) -> dict[str, object] | None:
    return background_ingestion_runtime_service.poll_background_source_ingestion(
        runtime=runtime,
        append_session_log=deps.append_session_log,
    )


def emit_obligation_transition(
    *,
    ingestion_request_id: str,
    status: str,
    created_at: str,
    last_polled_at: str,
    attempt_count: int,
    deadline_at: str,
    deps: RuntimeBackgroundIngestionDependencies,
) -> None:
    background_ingestion_runtime_service.emit_obligation_transition(
        append_session_log=deps.append_session_log,
        ingestion_request_id=ingestion_request_id,
        status=status,
        created_at=created_at,
        last_polled_at=last_polled_at,
        attempt_count=attempt_count,
        deadline_at=deadline_at,
    )


def register_pending_ingestion_obligation(
    *,
    runtime: dict[str, object],
    pending_request_id: str,
    utterance: str,
    turn_id: str,
    state: PipelineState,
    prior_pipeline_state: PipelineState | None,
    deps: RuntimeBackgroundIngestionDependencies,
    obligation_timeout_seconds: int = BACKGROUND_INGESTION_OBLIGATION_TIMEOUT_SECONDS,
    prior_continuity: ContinuityReadModel | None = None,
) -> bool:
    pending_registry = runtime.setdefault("pending_ingestion_registry", {})
    if not isinstance(pending_registry, dict):
        return False

    now_iso = arrow.utcnow().isoformat()
    deadline_at = arrow.get(now_iso).shift(seconds=obligation_timeout_seconds).isoformat()
    pending_registry[pending_request_id] = {
        "ingestion_request_id": pending_request_id,
        "utterance": utterance,
        "turn_id": turn_id,
        "source_context": {
            "utterance_doc_id": str(state.candidate_facts.turn_id or ""),
            "same_turn_exclusion_doc_ids": list(state.same_turn_exclusion.get("excluded_doc_ids", [])),
        },
        "prior_pipeline_state": prior_pipeline_state,
        "prior_continuity": prior_continuity,
        "created_at": now_iso,
        "last_polled_at": now_iso,
        "attempt_count": 0,
        "deadline_at": deadline_at,
        "status": "pending",
    }
    emit_obligation_transition(
        deps=deps,
        ingestion_request_id=pending_request_id,
        status="created",
        created_at=now_iso,
        last_polled_at=now_iso,
        attempt_count=0,
        deadline_at=deadline_at,
    )
    return True


def poll_pending_ingestion_obligations(
    *,
    runtime: dict[str, object],
    deps: RuntimeBackgroundIngestionDependencies,
    obligation_timeout_seconds: int = BACKGROUND_INGESTION_OBLIGATION_TIMEOUT_SECONDS,
) -> None:
    background_ingestion_runtime_service.poll_pending_ingestion_obligations(
        runtime=runtime,
        append_session_log=deps.append_session_log,
        obligation_timeout_seconds=obligation_timeout_seconds,
        utcnow=arrow.utcnow,
    )


def format_background_ingestion_completion_message(*, correlation_id: str) -> str:
    return background_ingestion_runtime_service.format_background_ingestion_completion_message(
        correlation_id=correlation_id,
        template=BACKGROUND_INGESTION_COMPLETION_MESSAGE_TEMPLATE,
    )


def process_background_ingestion_completion(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    capability_status: object,
    capability_snapshot: object,
    clock: object,
    io_channel: str,
    send_assistant_text: Callable[[str], None],
    last_user_message_ts: str,
    prior_pipeline_state: PipelineState | None,
    deps: RuntimeBackgroundIngestionDependencies,
) -> tuple[str, PipelineState | None, bool]:
    return background_ingestion_runtime_service.process_background_ingestion_completion(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        clock=clock,
        io_channel=io_channel,
        send_assistant_text=send_assistant_text,
        last_user_message_ts=last_user_message_ts,
        prior_pipeline_state=prior_pipeline_state,
        poll_background_source_ingestion=lambda **kwargs: poll_background_source_ingestion(deps=deps, **kwargs),
        emit_obligation_transition=lambda **kwargs: emit_obligation_transition(deps=deps, **kwargs),
        utc_now_iso=lambda: arrow.utcnow().isoformat(),
        append_session_log=deps.append_session_log,
        format_background_ingestion_completion_message=format_background_ingestion_completion_message,
        replay_background_completion_turn=deps.replay_background_completion_turn,
        apply_unresolved_intent_carryover=continuity_runtime_service.apply_unresolved_intent_carryover,
        answer_commit_persistence=deps.answer_commit_persistence,
    )


__all__ = [
    "RuntimeBackgroundIngestionDependencies",
    "emit_obligation_transition",
    "execute_source_ingestion",
    "format_background_ingestion_completion_message",
    "poll_background_source_ingestion",
    "poll_pending_ingestion_obligations",
    "process_background_ingestion_completion",
    "register_pending_ingestion_obligation",
    "start_background_source_ingestion",
]
