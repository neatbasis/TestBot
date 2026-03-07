from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass

from testbot.candidate_encoding import EncodedTurnCandidates
from typing import Callable

from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc
from testbot.pipeline_state import PipelineState
from testbot.turn_observation import TurnObservation
from testbot.vector_store import MemoryStore


@dataclass(frozen=True)
class StabilizedTurnState:
    turn_id: str
    utterance_doc_id: str
    reflection_doc_id: str
    same_turn_exclusion_doc_ids: list[str]
    candidate_facts: list[dict[str, object]]
    candidate_speech_acts: list[dict[str, object]]
    candidate_dialogue_state: list[dict[str, object]]


def stabilize_pre_route(
    *,
    store: MemoryStore,
    state: PipelineState,
    observation: TurnObservation,
    encoded: EncodedTurnCandidates,
    response_plan: dict[str, object],
    reflection_yaml: str,
    store_doc_fn: Callable[..., None] = store_doc,
) -> tuple[PipelineState, StabilizedTurnState]:
    utterance_doc_id = observation.turn_id
    utterance_card = make_utterance_card(
        ts_iso=observation.observed_at,
        speaker=observation.speaker,
        text=observation.utterance,
        doc_id=utterance_doc_id,
        channel=observation.channel,
    )
    store_doc_fn(
        store,
        doc_id=utterance_doc_id,
        content=utterance_card,
        metadata={
            "ts": observation.observed_at,
            "type": "user_utterance",
            "speaker": observation.speaker,
            "channel": observation.channel,
            "doc_id": utterance_doc_id,
            "turn_id": observation.turn_id,
            "raw": observation.utterance,
        },
    )

    reflection_doc_id = str(uuid.uuid4())
    reflection_card = make_reflection_card(
        ts_iso=observation.observed_at,
        about=observation.speaker,
        source_doc_id=utterance_doc_id,
        doc_id=reflection_doc_id,
        reflection_yaml=reflection_yaml,
    )
    store_doc_fn(
        store,
        doc_id=reflection_doc_id,
        content=reflection_card,
        metadata={
            "ts": observation.observed_at,
            "type": "reflection",
            "about": observation.speaker,
            "source_doc_id": utterance_doc_id,
            "doc_id": reflection_doc_id,
            "turn_id": observation.turn_id,
        },
    )

    same_turn_exclusion_doc_ids = [utterance_doc_id, reflection_doc_id]
    stabilized = StabilizedTurnState(
        turn_id=observation.turn_id,
        utterance_doc_id=utterance_doc_id,
        reflection_doc_id=reflection_doc_id,
        same_turn_exclusion_doc_ids=same_turn_exclusion_doc_ids,
        candidate_facts=[asdict(candidate) for candidate in encoded.facts],
        candidate_speech_acts=[asdict(candidate) for candidate in encoded.speech_acts],
        candidate_dialogue_state=[asdict(candidate) for candidate in encoded.dialogue_state],
    )

    next_state = PipelineState(
        **{
            **state.__dict__,
            "rewritten_query": encoded.rewritten_query,
            "response_plan": response_plan,
            "candidate_facts": {
                "facts": stabilized.candidate_facts,
                "speech_acts": stabilized.candidate_speech_acts,
                "dialogue_state": stabilized.candidate_dialogue_state,
                "turn_id": observation.turn_id,
                "utterance_doc_id": utterance_doc_id,
                "reflection_doc_id": reflection_doc_id,
            },
            "same_turn_exclusion": {
                "excluded_doc_ids": same_turn_exclusion_doc_ids,
                "reason": "stabilize.pre_route",
            },
        }
    )
    return next_state, stabilized
