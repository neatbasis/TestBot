"""Behave-facing runtime helpers.

These helpers keep feature step modules importing canonical service owners while
compatibility pipeline wiring is still transitional.
"""

from __future__ import annotations

from collections import deque

from langchain_core.documents import Document
from langchain_ollama import ChatOllama

from testbot.application.services import answer_stage_runtime as answer_stage_runtime_service
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import DecisionObject
from testbot.reflection_policy import CapabilityStatus
from testbot.runtime_capability_service import RuntimeCapabilityStatusData as RuntimeCapabilityStatus
from testbot.domain import Clock
from testbot import sat_chatbot_memory_v2 as _compat_runtime

ChatMsg = dict[str, str]


def run_answer_stage_flow(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg] | list[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None = None,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> PipelineState:
    """Canonical answer-stage entry used by behave step definitions.

    Compatibility residue is intentionally retained via the transitional
    ``_run_canonical_turn_pipeline`` dependency wiring and is addressed by a
    later runtime-hook move.
    """

    return answer_stage_runtime_service.run_canonical_answer_stage_flow(
        llm,
        state,
        chat_history=deque(chat_history),
        hits=hits,
        capability_status=capability_status,
        selected_decision=selected_decision,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        timezone=timezone,
        run_canonical_turn_pipeline=_compat_runtime._run_canonical_turn_pipeline,
    )


__all__ = ["run_answer_stage_flow"]
