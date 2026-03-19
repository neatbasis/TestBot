from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field

from testbot.candidate_encoding import DialogueStateCandidate, EncodedTurnCandidates, FactCandidate, RepairCandidate, SpeechActCandidate
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
    candidate_facts: list[FactCandidate]
    candidate_speech_acts: list[SpeechActCandidate]
    candidate_dialogue_state: list[DialogueStateCandidate]
    candidate_repairs: list[RepairCandidate] = field(default_factory=list)


@dataclass(frozen=True)
class PersistenceRecord:
    doc_id: str
    content: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class StabilizationPlan:
    stabilized: StabilizedTurnState
    persistence_records: tuple[PersistenceRecord, ...]
    next_state: PipelineState


def build_stabilization_plan(
    *,
    state: PipelineState,
    observation: TurnObservation,
    encoded: EncodedTurnCandidates,
    response_plan: dict[str, object],
    reflection_yaml: str,
    segment: SegmentDescriptor,
    reflection_doc_id: str | None = None,
    dialogue_state_doc_id: str | None = None,
) -> StabilizationPlan:
    """Build pure stabilization decisions without touching storage adapters."""
    generated_reflection_doc_id = reflection_doc_id or str(uuid.uuid4())
    generated_dialogue_state_doc_id = dialogue_state_doc_id or str(uuid.uuid4())
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

    reflection_card = make_reflection_card(
        ts_iso=observation.observed_at,
        about=observation.speaker,
        source_doc_id=utterance_doc_id,
        doc_id=generated_reflection_doc_id,
        reflection_yaml=reflection_yaml,
    )
    reflection_metadata = apply_persistence_metadata(
        metadata={
            "ts": observation.observed_at,
            "type": "reflection",
            "about": observation.speaker,
            "source_doc_id": utterance_doc_id,
            "doc_id": generated_reflection_doc_id,
            "turn_id": observation.turn_id,
        },
        stratum=MemoryStratum.SEMANTIC,
        segment=segment,
        member_doc_id=generated_reflection_doc_id,
    )

    dialogue_state_payload = {
        "turn_id": observation.turn_id,
        "dialogue_state": [asdict(candidate) for candidate in encoded.dialogue_state],
        "response_plan": response_plan,
    }
    dialogue_state_metadata = apply_persistence_metadata(
        metadata={
            "ts": observation.observed_at,
            "type": "dialogue_state_snapshot",
            "doc_id": generated_dialogue_state_doc_id,
            "turn_id": observation.turn_id,
        },
        stratum=MemoryStratum.PROCEDURAL_DIALOGUE_STATE,
        segment=segment,
        member_doc_id=generated_dialogue_state_doc_id,
    )
    same_turn_exclusion_doc_ids = [utterance_doc_id, generated_reflection_doc_id, generated_dialogue_state_doc_id]
    segment_membership_edge_refs = (
        list(utterance_metadata.get("segment_membership_edge_refs") or [])
        + list(reflection_metadata.get("segment_membership_edge_refs") or [])
        + list(dialogue_state_metadata.get("segment_membership_edge_refs") or [])
    )
    stabilized_candidate_facts = [
        FactCandidate(key="utterance_raw", value=observation.utterance, confidence=1.0, provenance="stabilize.pre_route"),
        *encoded.facts,
    ]
    stabilized = StabilizedTurnState(
        turn_id=observation.turn_id,
        utterance_card=utterance_card,
        utterance_doc_id=utterance_doc_id,
        reflection_doc_id=generated_reflection_doc_id,
        dialogue_state_doc_id=generated_dialogue_state_doc_id,
        segment_type=segment.segment_type.value,
        segment_id=segment.segment_id,
        segment_membership_edge_refs=segment_membership_edge_refs,
        same_turn_exclusion_doc_ids=same_turn_exclusion_doc_ids,
        candidate_facts=stabilized_candidate_facts,
        candidate_speech_acts=list(encoded.speech_acts),
        candidate_dialogue_state=list(encoded.dialogue_state),
        candidate_repairs=list(encoded.repairs),
    )
    next_state = PipelineState(
        **{
            **state.__dict__,
            "rewritten_query": encoded.rewritten_query,
            "response_plan": response_plan,
            "candidate_facts": {
                "facts": [asdict(candidate) for candidate in stabilized.candidate_facts],
                "speech_acts": [asdict(candidate) for candidate in stabilized.candidate_speech_acts],
                "dialogue_state": [asdict(candidate) for candidate in stabilized.candidate_dialogue_state],
                "repairs": [asdict(candidate) for candidate in stabilized.candidate_repairs],
                "turn_id": observation.turn_id,
                "utterance_card": utterance_card,
                "utterance_doc_id": utterance_doc_id,
                "reflection_doc_id": generated_reflection_doc_id,
                "dialogue_state_doc_id": generated_dialogue_state_doc_id,
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
    return StabilizationPlan(
        stabilized=stabilized,
        next_state=next_state,
        persistence_records=(
            PersistenceRecord(doc_id=utterance_doc_id, content=utterance_card, metadata=utterance_metadata),
            PersistenceRecord(doc_id=generated_reflection_doc_id, content=reflection_card, metadata=reflection_metadata),
            PersistenceRecord(
                doc_id=generated_dialogue_state_doc_id,
                content=str(dialogue_state_payload),
                metadata=dialogue_state_metadata,
            ),
        ),
    )


def persist_stabilization_records(
    *,
    store: MemoryStore,
    persistence_records: tuple[PersistenceRecord, ...],
    store_doc_fn: Callable[..., None],
) -> None:
    for record in persistence_records:
        store_doc_fn(
            store,
            doc_id=record.doc_id,
            content=record.content,
            metadata=record.metadata,
        )


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
    plan = build_stabilization_plan(
        state=state,
        observation=observation,
        encoded=encoded,
        response_plan=response_plan,
        reflection_yaml=reflection_yaml,
        segment=segment,
    )
    persist_stabilization_records(store=store, persistence_records=plan.persistence_records, store_doc_fn=store_doc_fn)
    return plan.next_state, plan.stabilized
