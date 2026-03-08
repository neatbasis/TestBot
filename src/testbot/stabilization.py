from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass

from testbot.candidate_encoding import EncodedTurnCandidates
from typing import Callable

from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc
from testbot.memory_strata import MemoryStratum, SegmentDescriptor, apply_persistence_metadata
from testbot.pipeline_state import PipelineState
from testbot.turn_observation import TurnObservation
from testbot.vector_store import MemoryStore


@dataclass(frozen=True)
class StabilizedTurnState:
    turn_id: str
    utterance_card: str
    utterance_doc_id: str
    reflection_doc_id: str
    dialogue_state_doc_id: str
    segment_type: str
    segment_id: str
    segment_membership_edge_refs: list[str]
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
    segment: SegmentDescriptor,
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
    utterance_metadata = apply_persistence_metadata(
        metadata={
            "ts": observation.observed_at,
            "type": "user_utterance",
            "speaker": observation.speaker,
            "channel": observation.channel,
            "doc_id": utterance_doc_id,
            "turn_id": observation.turn_id,
            "raw": observation.utterance,
        },
        stratum=MemoryStratum.EPISODIC,
        segment=segment,
        member_doc_id=utterance_doc_id,
    )
    store_doc_fn(
        store,
        doc_id=utterance_doc_id,
        content=utterance_card,
        metadata=utterance_metadata,
    )

    reflection_doc_id = str(uuid.uuid4())
    reflection_card = make_reflection_card(
        ts_iso=observation.observed_at,
        about=observation.speaker,
        source_doc_id=utterance_doc_id,
        doc_id=reflection_doc_id,
        reflection_yaml=reflection_yaml,
    )
    reflection_metadata = apply_persistence_metadata(
        metadata={
            "ts": observation.observed_at,
            "type": "reflection",
            "about": observation.speaker,
            "source_doc_id": utterance_doc_id,
            "doc_id": reflection_doc_id,
            "turn_id": observation.turn_id,
        },
        stratum=MemoryStratum.SEMANTIC,
        segment=segment,
        member_doc_id=reflection_doc_id,
    )
    store_doc_fn(
        store,
        doc_id=reflection_doc_id,
        content=reflection_card,
        metadata=reflection_metadata,
    )

    dialogue_state_doc_id = str(uuid.uuid4())
    dialogue_state_payload = {
        "turn_id": observation.turn_id,
        "dialogue_state": [asdict(candidate) for candidate in encoded.dialogue_state],
        "response_plan": response_plan,
    }
    dialogue_state_metadata = apply_persistence_metadata(
        metadata={
            "ts": observation.observed_at,
            "type": "dialogue_state_snapshot",
            "doc_id": dialogue_state_doc_id,
            "turn_id": observation.turn_id,
        },
        stratum=MemoryStratum.PROCEDURAL_DIALOGUE_STATE,
        segment=segment,
        member_doc_id=dialogue_state_doc_id,
    )
    store_doc_fn(
        store,
        doc_id=dialogue_state_doc_id,
        content=str(dialogue_state_payload),
        metadata=dialogue_state_metadata,
    )

    same_turn_exclusion_doc_ids = [utterance_doc_id, reflection_doc_id, dialogue_state_doc_id]
    segment_membership_edge_refs = (
        list(utterance_metadata.get("segment_membership_edge_refs") or [])
        + list(reflection_metadata.get("segment_membership_edge_refs") or [])
        + list(dialogue_state_metadata.get("segment_membership_edge_refs") or [])
    )
    stabilized_candidate_facts = [
        {"key": "utterance_raw", "value": observation.utterance, "confidence": 1.0, "provenance": "stabilize.pre_route"},
        *[asdict(candidate) for candidate in encoded.facts],
    ]

    stabilized = StabilizedTurnState(
        turn_id=observation.turn_id,
        utterance_card=utterance_card,
        utterance_doc_id=utterance_doc_id,
        reflection_doc_id=reflection_doc_id,
        dialogue_state_doc_id=dialogue_state_doc_id,
        segment_type=segment.segment_type.value,
        segment_id=segment.segment_id,
        segment_membership_edge_refs=segment_membership_edge_refs,
        same_turn_exclusion_doc_ids=same_turn_exclusion_doc_ids,
        candidate_facts=stabilized_candidate_facts,
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
                "utterance_card": utterance_card,
                "utterance_doc_id": utterance_doc_id,
                "reflection_doc_id": reflection_doc_id,
                "dialogue_state_doc_id": dialogue_state_doc_id,
                "segment_type": segment.segment_type.value,
                "segment_id": segment.segment_id,
                "segment_membership_edge_refs": segment_membership_edge_refs,
                "retrieval_constraints": {
                    "segment_ids": [segment.segment_id],
                    "segment_types": [segment.segment_type.value],
                    "memory_strata": [
                        MemoryStratum.SEMANTIC.value,
                        MemoryStratum.EPISODIC.value,
                        MemoryStratum.PROCEDURAL_DIALOGUE_STATE.value,
                    ],
                },
            },
            "same_turn_exclusion": {
                "excluded_doc_ids": same_turn_exclusion_doc_ids,
                "reason": "stabilize.pre_route",
            },
        }
    )
    return next_state, stabilized
