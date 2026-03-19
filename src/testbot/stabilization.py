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
class PendingClarification:
    obligation_id: str
    question: str
    source_anchor: str
    focus: str = ""
    carry_forward: bool = True


@dataclass(frozen=True)
class PendingRepair:
    obligation_id: str
    reason: str
    followup_route: str
    source_anchor: str
    carry_forward: bool = True


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
    pending_clarification: PendingClarification | None = None
    pending_repair: PendingRepair | None = None


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
    def _carried_pending_clarification() -> PendingClarification | None:
        prior = state.pending_clarification
        if not prior.required:
            return None
        question = str(prior.question or "")
        source_anchor = str(prior.get("source_anchor") or "commit.pending_clarification")
        focus = str(prior.get("focus") or "")
        durable_id = str(prior.get("obligation_id") or f"{source_anchor}:{observation.turn_id}")
        return PendingClarification(
            obligation_id=durable_id,
            question=question,
            source_anchor=source_anchor,
            focus=focus,
            carry_forward=True,
        )

    def _carried_pending_repair() -> PendingRepair | None:
        prior = state.commit_receipt.pending_repair_state
        if not (isinstance(prior, dict) and bool(prior.get("repair_offered_to_user"))):
            return None
        reason = str(prior.get("reason") or "repair_offer_rendered")
        route = str(prior.get("followup_route") or "")
        source_anchor = "commit.pending_repair_state:repair_offered_to_user"
        durable_id = str(prior.get("obligation_id") or f"{source_anchor}:{observation.turn_id}")
        return PendingRepair(
            obligation_id=durable_id,
            reason=reason,
            followup_route=route,
            source_anchor=source_anchor,
            carry_forward=True,
        )

    def _fact_with_durable_id(candidate: FactCandidate, index: int) -> FactCandidate:
        if candidate.candidate_id:
            return candidate
        return FactCandidate(
            key=candidate.key,
            value=candidate.value,
            confidence=candidate.confidence,
            candidate_id=f"{observation.turn_id}:fact:{candidate.key}:{index}",
            provenance=candidate.provenance,
        )

    def _speech_with_durable_id(candidate: SpeechActCandidate, index: int) -> SpeechActCandidate:
        if candidate.candidate_id:
            return candidate
        return SpeechActCandidate(
            label=candidate.label,
            confidence=candidate.confidence,
            rationale=candidate.rationale,
            candidate_id=f"{observation.turn_id}:speech_act:{candidate.label}:{index}",
            provenance=candidate.provenance,
        )

    def _dialogue_state_with_durable_id(candidate: DialogueStateCandidate, index: int) -> DialogueStateCandidate:
        if candidate.candidate_id:
            return candidate
        return DialogueStateCandidate(
            label=candidate.label,
            confidence=candidate.confidence,
            candidate_id=f"{observation.turn_id}:dialogue_state:{candidate.label}:{index}",
            provenance=candidate.provenance,
        )

    def _repair_with_durable_id(candidate: RepairCandidate, index: int) -> RepairCandidate:
        if candidate.candidate_id:
            return candidate
        return RepairCandidate(
            label=candidate.label,
            confidence=candidate.confidence,
            rationale=candidate.rationale,
            candidate_id=f"{observation.turn_id}:repair:{candidate.label}:{index}",
            provenance=candidate.provenance,
        )

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
        FactCandidate(
            key="utterance_raw",
            value=observation.utterance,
            confidence=1.0,
            candidate_id=f"{observation.turn_id}:fact:utterance_raw:0",
            provenance="stabilize.pre_route",
        ),
        *[_fact_with_durable_id(candidate, index) for index, candidate in enumerate(encoded.facts, start=1)],
    ]
    stabilized_speech_acts = [_speech_with_durable_id(candidate, index) for index, candidate in enumerate(encoded.speech_acts)]
    stabilized_dialogue_state = [
        _dialogue_state_with_durable_id(candidate, index) for index, candidate in enumerate(encoded.dialogue_state)
    ]
    stabilized_repairs = [_repair_with_durable_id(candidate, index) for index, candidate in enumerate(encoded.repairs)]
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
        candidate_speech_acts=stabilized_speech_acts,
        candidate_dialogue_state=stabilized_dialogue_state,
        candidate_repairs=stabilized_repairs,
        pending_clarification=_carried_pending_clarification(),
        pending_repair=_carried_pending_repair(),
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
            "pending_clarification": {
                "required": stabilized.pending_clarification is not None,
                "question": stabilized.pending_clarification.question if stabilized.pending_clarification else "",
                "obligation_id": stabilized.pending_clarification.obligation_id if stabilized.pending_clarification else "",
                "source_anchor": stabilized.pending_clarification.source_anchor if stabilized.pending_clarification else "",
                "focus": stabilized.pending_clarification.focus if stabilized.pending_clarification else "",
                "carry_forward": bool(stabilized.pending_clarification and stabilized.pending_clarification.carry_forward),
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
    def _fact_with_durable_id(candidate: FactCandidate, index: int) -> FactCandidate:
        if candidate.candidate_id:
            return candidate
        return FactCandidate(
            key=candidate.key,
            value=candidate.value,
            confidence=candidate.confidence,
            candidate_id=f"{observation.turn_id}:fact:{candidate.key}:{index}",
            provenance=candidate.provenance,
        )

    def _speech_with_durable_id(candidate: SpeechActCandidate, index: int) -> SpeechActCandidate:
        if candidate.candidate_id:
            return candidate
        return SpeechActCandidate(
            label=candidate.label,
            confidence=candidate.confidence,
            rationale=candidate.rationale,
            candidate_id=f"{observation.turn_id}:speech_act:{candidate.label}:{index}",
            provenance=candidate.provenance,
        )

    def _dialogue_state_with_durable_id(candidate: DialogueStateCandidate, index: int) -> DialogueStateCandidate:
        if candidate.candidate_id:
            return candidate
        return DialogueStateCandidate(
            label=candidate.label,
            confidence=candidate.confidence,
            candidate_id=f"{observation.turn_id}:dialogue_state:{candidate.label}:{index}",
            provenance=candidate.provenance,
        )

    def _repair_with_durable_id(candidate: RepairCandidate, index: int) -> RepairCandidate:
        if candidate.candidate_id:
            return candidate
        return RepairCandidate(
            label=candidate.label,
            confidence=candidate.confidence,
            rationale=candidate.rationale,
            candidate_id=f"{observation.turn_id}:repair:{candidate.label}:{index}",
            provenance=candidate.provenance,
        )
