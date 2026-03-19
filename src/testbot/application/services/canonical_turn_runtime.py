from __future__ import annotations

from collections import deque

from testbot.application.services.turn_service import TurnPipelineDependencies, run_canonical_turn_pipeline_service
from testbot.clock import Clock
from testbot.evidence_retrieval import RetrievalInputRecord
from testbot.memory_cards import store_doc
from testbot.pipeline_state import PipelineState
from testbot.reflection_policy import CapabilityStatus
from testbot.ports import MemoryStorePort


def run_canonical_turn_pipeline(
    *,
    runtime: dict[str, object] | None,
    llm,
    store: MemoryStorePort,
    state: PipelineState,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    turn_id: str,
    near_tie_delta: float,
    chat_history: deque[dict[str, str]],
    capability_status: CapabilityStatus,
    capability_snapshot,
    clock: Clock,
    io_channel: str,
    deps: TurnPipelineDependencies,
) -> tuple[PipelineState, list[RetrievalInputRecord]]:
    return run_canonical_turn_pipeline_service(
        runtime=runtime,
        llm=llm,
        store=store,
        state=state,
        utterance=utterance,
        prior_pipeline_state=prior_pipeline_state,
        turn_id=turn_id,
        near_tie_delta=near_tie_delta,
        chat_history=chat_history,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        clock=clock,
        io_channel=io_channel,
        deps=deps,
    )


__all__ = ["run_canonical_turn_pipeline", "store_doc"]
