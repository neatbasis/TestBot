from __future__ import annotations

from dataclasses import dataclass

from testbot.pipeline_state import PipelineState


@dataclass(frozen=True)
class TurnObservation:
    turn_id: str
    utterance: str
    observed_at: str
    speaker: str
    channel: str
    classified_intent: str
    resolved_intent: str


def observe_turn(
    state: PipelineState,
    *,
    turn_id: str,
    observed_at: str,
    speaker: str,
    channel: str,
) -> TurnObservation:
    """Capture a lossless typed observation boundary before inference/routing."""

    return TurnObservation(
        turn_id=turn_id,
        utterance=state.user_input,
        observed_at=observed_at,
        speaker=speaker,
        channel=channel,
        classified_intent=state.classified_intent,
        resolved_intent=state.resolved_intent,
    )
