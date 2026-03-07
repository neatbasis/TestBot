from __future__ import annotations

from dataclasses import replace

import pytest

from testbot.canonical_turn_orchestrator import CanonicalStage, CanonicalTurnContext, CanonicalTurnOrchestrator
from testbot.pipeline_state import PipelineState


def _make_stage(name: str):
    def _handler(context: CanonicalTurnContext) -> CanonicalTurnContext:
        return context

    return CanonicalStage(name=name, handler=_handler)


def test_orchestrator_rejects_missing_or_reordered_stages() -> None:
    truncated = [
        _make_stage("observe.turn"),
        _make_stage("encode.candidates"),
    ]
    with pytest.raises(ValueError):
        CanonicalTurnOrchestrator(stages=truncated)

    reordered = [
        _make_stage("observe.turn"),
        _make_stage("context.resolve"),
        *[_make_stage(name) for name in CanonicalTurnOrchestrator.STAGE_ORDER[2:]],
    ]
    with pytest.raises(ValueError):
        CanonicalTurnOrchestrator(stages=reordered)


def test_orchestrator_executes_all_11_canonical_stages_in_order() -> None:
    state = PipelineState(user_input="hello")
    context = CanonicalTurnContext(state=state)

    stages: list[CanonicalStage] = []
    for stage_name in CanonicalTurnOrchestrator.STAGE_ORDER:
        def _handler(ctx: CanonicalTurnContext, name: str = stage_name) -> CanonicalTurnContext:
            if name == "stabilize.pre_route":
                ctx.artifacts["stabilized_turn"] = ctx.state.user_input
            if name == "intent.resolve":
                # Guard against regressing to a lossy early U -> I shortcut.
                assert ctx.artifacts.get("stabilized_turn") == "hello"
                ctx.state = replace(ctx.state, resolved_intent="memory_recall")
            return ctx

        stages.append(CanonicalStage(name=stage_name, handler=_handler))

    orchestrator = CanonicalTurnOrchestrator(stages=stages)
    final_context = orchestrator.run(context)

    assert final_context.stage_audit_trail == list(CanonicalTurnOrchestrator.STAGE_ORDER)
    assert final_context.state.resolved_intent == "memory_recall"
