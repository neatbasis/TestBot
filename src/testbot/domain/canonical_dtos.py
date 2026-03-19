from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from testbot.answer_commit import CommittedTurnState as LegacyCommittedTurnState
from testbot.answer_commit import PendingRepairState as LegacyPendingRepairState
from testbot.answer_assembly import AnswerCandidate as LegacyAnswerCandidate
from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import ValidatedAnswer
from testbot.candidate_encoding import DialogueStateCandidate, EncodedTurnCandidates, FactCandidate, RepairCandidate, SpeechActCandidate
from testbot.context_resolution import ContinuityPosture, ResolvedContext
from testbot.evidence_retrieval import EvidenceBundle, EvidenceRecord
from testbot.intent_resolution import ResolvedIntent
from testbot.intent_router import IntentType
from testbot.pipeline_state import AlignmentDecision, InvariantDecision, ProvenanceType
from testbot.policy_decision import DecisionClass, DecisionObject
from testbot.stabilization import StabilizedTurnState
from testbot.turn_observation import TurnObservation as LegacyTurnObservation


@dataclass(frozen=True)
class CandidateEncodingSet:
    rewritten_query: str
    speech_acts: tuple[SpeechActCandidate, ...] = ()
    facts: tuple[FactCandidate, ...] = ()
    dialogue_state: tuple[DialogueStateCandidate, ...] = ()
    repairs: tuple[RepairCandidate, ...] = ()

    @classmethod
    def from_encoded_turn_candidates(cls, encoded: EncodedTurnCandidates) -> CandidateEncodingSet:
        return cls(
            rewritten_query=encoded.rewritten_query,
            speech_acts=tuple(encoded.speech_acts),
            facts=tuple(encoded.facts),
            dialogue_state=tuple(encoded.dialogue_state),
            repairs=tuple(encoded.repairs),
        )

    def to_encoded_turn_candidates(self) -> EncodedTurnCandidates:
        return EncodedTurnCandidates(
            rewritten_query=self.rewritten_query,
            speech_acts=list(self.speech_acts),
            facts=list(self.facts),
            dialogue_state=list(self.dialogue_state),
            repairs=list(self.repairs),
        )


@dataclass(frozen=True)
class PreRouteState:
    turn_id: str
    utterance_card: str
    utterance_doc_id: str
    reflection_doc_id: str
    dialogue_state_doc_id: str
    segment_type: str
    segment_id: str
    segment_membership_edge_refs: tuple[str, ...] = ()
    same_turn_exclusion_doc_ids: tuple[str, ...] = ()
    candidate_facts: tuple[FactCandidate, ...] = ()
    candidate_speech_acts: tuple[SpeechActCandidate, ...] = ()
    candidate_dialogue_state: tuple[DialogueStateCandidate, ...] = ()
    candidate_repairs: tuple[RepairCandidate, ...] = ()

    @classmethod
    def from_stabilized_turn_state(cls, stabilized: StabilizedTurnState) -> PreRouteState:
        return cls(
            turn_id=stabilized.turn_id,
            utterance_card=stabilized.utterance_card,
            utterance_doc_id=stabilized.utterance_doc_id,
            reflection_doc_id=stabilized.reflection_doc_id,
            dialogue_state_doc_id=stabilized.dialogue_state_doc_id,
            segment_type=stabilized.segment_type,
            segment_id=stabilized.segment_id,
            segment_membership_edge_refs=tuple(stabilized.segment_membership_edge_refs),
            same_turn_exclusion_doc_ids=tuple(stabilized.same_turn_exclusion_doc_ids),
            candidate_facts=tuple(stabilized.candidate_facts),
            candidate_speech_acts=tuple(stabilized.candidate_speech_acts),
            candidate_dialogue_state=tuple(stabilized.candidate_dialogue_state),
            candidate_repairs=tuple(stabilized.candidate_repairs),
        )

    def to_stabilized_turn_state(self) -> StabilizedTurnState:
        return StabilizedTurnState(
            turn_id=self.turn_id,
            utterance_card=self.utterance_card,
            utterance_doc_id=self.utterance_doc_id,
            reflection_doc_id=self.reflection_doc_id,
            dialogue_state_doc_id=self.dialogue_state_doc_id,
            segment_type=self.segment_type,
            segment_id=self.segment_id,
            segment_membership_edge_refs=list(self.segment_membership_edge_refs),
            same_turn_exclusion_doc_ids=list(self.same_turn_exclusion_doc_ids),
            candidate_facts=list(self.candidate_facts),
            candidate_speech_acts=list(self.candidate_speech_acts),
            candidate_dialogue_state=list(self.candidate_dialogue_state),
            candidate_repairs=list(self.candidate_repairs),
        )


@dataclass(frozen=True)
class ContextResolvedState:
    history_anchors: tuple[str, ...] = ()
    ambiguity_flags: tuple[str, ...] = ()
    continuity_posture: ContinuityPosture = ContinuityPosture.REEVALUATE
    prior_intent: IntentType | None = None

    @classmethod
    def from_resolved_context(cls, resolved: ResolvedContext) -> ContextResolvedState:
        return cls(
            history_anchors=tuple(resolved.history_anchors),
            ambiguity_flags=tuple(resolved.ambiguity_flags),
            continuity_posture=resolved.continuity_posture,
            prior_intent=resolved.prior_intent,
        )

    def to_resolved_context(self) -> ResolvedContext:
        return ResolvedContext(
            history_anchors=self.history_anchors,
            ambiguity_flags=self.ambiguity_flags,
            continuity_posture=self.continuity_posture,
            prior_intent=self.prior_intent,
        )


@dataclass(frozen=True)
class EvidenceSet:
    structured_facts: tuple[EvidenceRecord, ...] = ()
    episodic_utterances: tuple[EvidenceRecord, ...] = ()
    repair_anchors_offers: tuple[EvidenceRecord, ...] = ()
    reflections_hypotheses: tuple[EvidenceRecord, ...] = ()
    source_evidence: tuple[EvidenceRecord, ...] = ()

    @classmethod
    def from_evidence_bundle(cls, bundle: EvidenceBundle) -> EvidenceSet:
        return cls(
            structured_facts=bundle.structured_facts,
            episodic_utterances=bundle.episodic_utterances,
            repair_anchors_offers=bundle.repair_anchors_offers,
            reflections_hypotheses=bundle.reflections_hypotheses,
            source_evidence=bundle.source_evidence,
        )

    def to_evidence_bundle(self) -> EvidenceBundle:
        return EvidenceBundle(
            structured_facts=self.structured_facts,
            episodic_utterances=self.episodic_utterances,
            repair_anchors_offers=self.repair_anchors_offers,
            reflections_hypotheses=self.reflections_hypotheses,
            source_evidence=self.source_evidence,
        )


@dataclass(frozen=True)
class PolicyDecision:
    decision_class: DecisionClass
    retrieval_branch: str
    rationale: str
    reasoning: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_decision_object(cls, decision: DecisionObject) -> PolicyDecision:
        return cls(
            decision_class=decision.decision_class,
            retrieval_branch=decision.retrieval_branch,
            rationale=decision.rationale,
            reasoning=dict(decision.reasoning),
        )

    def to_decision_object(self) -> DecisionObject:
        return DecisionObject(
            decision_class=self.decision_class,
            retrieval_branch=self.retrieval_branch,
            rationale=self.rationale,
            reasoning=dict(self.reasoning),
        )


@dataclass(frozen=True)
class PendingRepairState:
    repair_required_by_policy: bool = False
    repair_offered_to_user: bool = False
    offer_type: str = ""
    reason: str = "none"
    followup_route: str = ""
    obligation_id: str = ""

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> PendingRepairState:
        return cls(
            repair_required_by_policy=bool(raw.get("repair_required_by_policy", False)),
            repair_offered_to_user=bool(raw.get("repair_offered_to_user", False)),
            offer_type=str(raw.get("offer_type") or ""),
            reason=str(raw.get("reason") or "none"),
            followup_route=str(raw.get("followup_route") or ""),
            obligation_id=str(raw.get("obligation_id") or ""),
        )

    @classmethod
    def from_legacy(cls, state: LegacyPendingRepairState) -> PendingRepairState:
        return cls(
            repair_required_by_policy=state.repair_required_by_policy,
            repair_offered_to_user=state.repair_offered_to_user,
            offer_type=state.offer_type,
            reason=state.reason,
            followup_route=state.followup_route,
            obligation_id=getattr(state, "obligation_id", ""),
        )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "repair_required_by_policy": self.repair_required_by_policy,
            "repair_offered_to_user": self.repair_offered_to_user,
            "reason": self.reason,
        }
        if self.offer_type:
            payload["offer_type"] = self.offer_type
        if self.followup_route:
            payload["followup_route"] = self.followup_route
        if self.obligation_id:
            payload["obligation_id"] = self.obligation_id
        return payload

    def to_legacy(self) -> LegacyPendingRepairState:
        return LegacyPendingRepairState(
            repair_required_by_policy=self.repair_required_by_policy,
            repair_offered_to_user=self.repair_offered_to_user,
            offer_type=self.offer_type,
            reason=self.reason,
            followup_route=self.followup_route,
            obligation_id=self.obligation_id,
        )


@dataclass(frozen=True)
class TurnObservation:
    turn_id: str
    utterance: str
    observed_at: str
    speaker: str
    channel: str
    classified_intent: str
    resolved_intent: str

    @classmethod
    def from_legacy(cls, legacy: LegacyTurnObservation) -> TurnObservation:
        return cls(
            turn_id=legacy.turn_id,
            utterance=legacy.utterance,
            observed_at=legacy.observed_at,
            speaker=legacy.speaker,
            channel=legacy.channel,
            classified_intent=legacy.classified_intent,
            resolved_intent=legacy.resolved_intent,
        )

    def to_legacy(self) -> LegacyTurnObservation:
        return LegacyTurnObservation(
            turn_id=self.turn_id,
            utterance=self.utterance,
            observed_at=self.observed_at,
            speaker=self.speaker,
            channel=self.channel,
            classified_intent=self.classified_intent,
            resolved_intent=self.resolved_intent,
        )


@dataclass(frozen=True)
class IntentResolution:
    classified_intent: IntentType
    resolved_intent: IntentType
    rationale: str

    @classmethod
    def from_legacy(cls, legacy: ResolvedIntent) -> IntentResolution:
        return cls(
            classified_intent=legacy.classified_intent,
            resolved_intent=legacy.resolved_intent,
            rationale=legacy.rationale,
        )

    def to_legacy(self) -> ResolvedIntent:
        return ResolvedIntent(
            classified_intent=self.classified_intent,
            resolved_intent=self.resolved_intent,
            rationale=self.rationale,
        )


@dataclass(frozen=True)
class ReasoningTrace:
    values: tuple[tuple[str, object], ...] = ()

    @classmethod
    def from_mapping(cls, mapping: dict[str, object]) -> ReasoningTrace:
        return cls(values=tuple((str(k), v) for k, v in mapping.items()))

    def to_mapping(self) -> dict[str, object]:
        return {k: v for k, v in self.values}


@dataclass(frozen=True)
class AssistantOfferAnchor:
    offer_type: str
    followup_route: str
    offered_to_user: bool
    reason: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, object]) -> AssistantOfferAnchor:
        return cls(
            offer_type=str(payload.get("offer_type") or ""),
            followup_route=str(payload.get("followup_route") or ""),
            offered_to_user=bool(payload.get("repair_offered_to_user", payload.get("offered_to_user", False))),
            reason=str(payload.get("reason") or ""),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "offer_type": self.offer_type,
            "followup_route": self.followup_route,
            "offered_to_user": self.offered_to_user,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FocusAnchor:
    anchor_key: str
    anchor_value: str
    provenance: str = ""

    @classmethod
    def from_fact_candidate(cls, candidate: FactCandidate) -> FocusAnchor:
        return cls(
            anchor_key=candidate.key,
            anchor_value=candidate.value,
            provenance=candidate.provenance,
        )


@dataclass(frozen=True)
class UnresolvedObligation:
    obligation: str
    source: str = "commit.remaining_obligations"

    @classmethod
    def from_raw(cls, value: object) -> UnresolvedObligation:
        return cls(obligation=str(value).strip())


@dataclass(frozen=True)
class PendingClarification:
    obligation_id: str
    question: str
    source_anchor: str
    focus: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, object]) -> PendingClarification | None:
        if not bool(payload.get("required", False)):
            return None
        return cls(
            obligation_id=str(payload.get("obligation_id") or ""),
            question=str(payload.get("question") or ""),
            source_anchor=str(payload.get("source_anchor") or "commit.pending_clarification"),
            focus=str(payload.get("focus") or ""),
        )


@dataclass(frozen=True)
class AnswerCandidate:
    decision_class: str
    rendered_class: str
    retrieval_branch: str
    rationale: str
    evidence_counts: tuple[tuple[str, int], ...]
    pending_repair_state: PendingRepairState
    pending_ingestion_request_id: str
    resolved_obligations: tuple[str, ...]
    remaining_obligations: tuple[str, ...]
    confirmed_user_facts: tuple[str, ...]

    @classmethod
    def from_legacy(cls, legacy: LegacyAnswerCandidate) -> AnswerCandidate:
        return cls(
            decision_class=legacy.decision_class,
            rendered_class=legacy.rendered_class,
            retrieval_branch=legacy.retrieval_branch,
            rationale=legacy.rationale,
            evidence_counts=tuple((str(k), int(v)) for k, v in legacy.evidence_counts.items()),
            pending_repair_state=PendingRepairState.from_legacy(legacy.pending_repair_state),
            pending_ingestion_request_id=legacy.pending_ingestion_request_id,
            resolved_obligations=tuple(legacy.resolved_obligations),
            remaining_obligations=tuple(legacy.remaining_obligations),
            confirmed_user_facts=tuple(legacy.confirmed_user_facts),
        )

    def to_legacy(self) -> LegacyAnswerCandidate:
        return LegacyAnswerCandidate(
            decision_class=self.decision_class,
            rendered_class=self.rendered_class,
            retrieval_branch=self.retrieval_branch,
            rationale=self.rationale,
            evidence_counts={k: v for k, v in self.evidence_counts},
            pending_repair_state=self.pending_repair_state.to_legacy(),
            pending_ingestion_request_id=self.pending_ingestion_request_id,
            resolved_obligations=list(self.resolved_obligations),
            remaining_obligations=list(self.remaining_obligations),
            confirmed_user_facts=list(self.confirmed_user_facts),
        )


@dataclass(frozen=True)
class CommittedTurnState:
    turn_id: str
    commit_stage: str
    rendered_text: str
    pending_repair_state: PendingRepairState
    pending_ingestion_request_id: str
    resolved_obligations: tuple[str, ...]
    remaining_obligations: tuple[str, ...]
    confirmed_user_facts: tuple[str, ...]

    @classmethod
    def from_legacy(cls, legacy: LegacyCommittedTurnState) -> CommittedTurnState:
        return cls(
            turn_id=legacy.turn_id,
            commit_stage=legacy.commit_stage,
            rendered_text=legacy.rendered_text,
            pending_repair_state=PendingRepairState.from_legacy(legacy.pending_repair_state),
            pending_ingestion_request_id=legacy.pending_ingestion_request_id,
            resolved_obligations=tuple(legacy.resolved_obligations),
            remaining_obligations=tuple(legacy.remaining_obligations),
            confirmed_user_facts=tuple(legacy.confirmed_user_facts),
        )

    def to_legacy(self) -> LegacyCommittedTurnState:
        return LegacyCommittedTurnState(
            turn_id=self.turn_id,
            commit_stage=self.commit_stage,
            rendered_text=self.rendered_text,
            pending_repair_state=self.pending_repair_state.to_legacy(),
            pending_ingestion_request_id=self.pending_ingestion_request_id,
            resolved_obligations=list(self.resolved_obligations),
            remaining_obligations=list(self.remaining_obligations),
            confirmed_user_facts=list(self.confirmed_user_facts),
        )


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    failures: tuple[str, ...] = ()
    final_answer: str = ""
    claims: tuple[str, ...] | None = None
    provenance_types: tuple[ProvenanceType, ...] | None = None
    used_memory_refs: tuple[str, ...] | None = None
    used_source_evidence_refs: tuple[str, ...] | None = None
    source_evidence_attribution: tuple[dict[str, str], ...] | None = None
    basis_statement: str = ""
    invariant_decisions: InvariantDecision | None = None
    alignment_decision: AlignmentDecision | None = None

    @classmethod
    def from_validated_answer(cls, validated: ValidatedAnswer) -> ValidationResult:
        return cls(
            passed=validated.passed,
            failures=tuple(validated.failures),
            final_answer=validated.final_answer,
            claims=tuple(validated.claims) if validated.claims is not None else None,
            provenance_types=tuple(validated.provenance_types) if validated.provenance_types is not None else None,
            used_memory_refs=tuple(validated.used_memory_refs) if validated.used_memory_refs is not None else None,
            used_source_evidence_refs=(
                tuple(validated.used_source_evidence_refs) if validated.used_source_evidence_refs is not None else None
            ),
            source_evidence_attribution=(
                tuple(dict(item) for item in validated.source_evidence_attribution)
                if validated.source_evidence_attribution is not None
                else None
            ),
            basis_statement=validated.basis_statement,
            invariant_decisions=InvariantDecision.from_mapping(validated.invariant_decisions),
            alignment_decision=AlignmentDecision.from_mapping(validated.alignment_decision),
        )

    def to_validated_answer(self) -> ValidatedAnswer:
        return ValidatedAnswer(
            passed=self.passed,
            failures=list(self.failures),
            final_answer=self.final_answer,
            claims=list(self.claims) if self.claims is not None else None,
            provenance_types=list(self.provenance_types) if self.provenance_types is not None else None,
            used_memory_refs=list(self.used_memory_refs) if self.used_memory_refs is not None else None,
            used_source_evidence_refs=(
                list(self.used_source_evidence_refs) if self.used_source_evidence_refs is not None else None
            ),
            source_evidence_attribution=(
                [dict(item) for item in self.source_evidence_attribution]
                if self.source_evidence_attribution is not None
                else None
            ),
            basis_statement=self.basis_statement,
            invariant_decisions=(
                self.invariant_decisions.to_dict() if self.invariant_decisions is not None else None
            ),
            alignment_decision=self.alignment_decision.to_dict() if self.alignment_decision is not None else None,
        )


@dataclass(frozen=True)
class RenderedResponse:
    rendered_text: str
    repair_offer_rendered: bool = False
    repair_followup_route: str = ""
    response_contract: str = "validated_normal"
    degraded_response: bool = False

    @classmethod
    def from_rendered_answer(cls, rendered: RenderedAnswer) -> RenderedResponse:
        return cls(
            rendered_text=rendered.rendered_text,
            repair_offer_rendered=rendered.repair_offer_rendered,
            repair_followup_route=rendered.repair_followup_route,
            response_contract=rendered.response_contract,
            degraded_response=rendered.degraded_response,
        )

    def to_rendered_answer(self) -> RenderedAnswer:
        return RenderedAnswer(
            rendered_text=self.rendered_text,
            repair_offer_rendered=self.repair_offer_rendered,
            repair_followup_route=self.repair_followup_route,
            response_contract=self.response_contract,
            degraded_response=self.degraded_response,
        )


def candidate_encoding_set_from_encoded_turn_candidates(encoded: EncodedTurnCandidates) -> CandidateEncodingSet:
    return CandidateEncodingSet.from_encoded_turn_candidates(encoded)


def pre_route_state_from_stabilized_turn_state(stabilized: StabilizedTurnState) -> PreRouteState:
    return PreRouteState.from_stabilized_turn_state(stabilized)


def context_resolved_state_from_resolved_context(resolved: ResolvedContext) -> ContextResolvedState:
    return ContextResolvedState.from_resolved_context(resolved)


def evidence_set_from_evidence_bundle(bundle: EvidenceBundle) -> EvidenceSet:
    return EvidenceSet.from_evidence_bundle(bundle)


def policy_decision_from_decision_object(decision: DecisionObject) -> PolicyDecision:
    return PolicyDecision.from_decision_object(decision)


def validation_result_from_validated_answer(validated: ValidatedAnswer) -> ValidationResult:
    return ValidationResult.from_validated_answer(validated)


def rendered_response_from_rendered_answer(rendered: RenderedAnswer) -> RenderedResponse:
    return RenderedResponse.from_rendered_answer(rendered)


def turn_observation_from_legacy(observation: LegacyTurnObservation) -> TurnObservation:
    return TurnObservation.from_legacy(observation)


def intent_resolution_from_legacy(resolution: ResolvedIntent) -> IntentResolution:
    return IntentResolution.from_legacy(resolution)


def answer_candidate_from_legacy(candidate: LegacyAnswerCandidate) -> AnswerCandidate:
    return AnswerCandidate.from_legacy(candidate)


def committed_turn_state_from_legacy(committed: LegacyCommittedTurnState) -> CommittedTurnState:
    return CommittedTurnState.from_legacy(committed)


__all__ = [
    "AssistantOfferAnchor",
    "AnswerCandidate",
    "CandidateEncodingSet",
    "CommittedTurnState",
    "ContextResolvedState",
    "EvidenceSet",
    "FocusAnchor",
    "IntentResolution",
    "PendingRepairState",
    "PendingClarification",
    "PolicyDecision",
    "PreRouteState",
    "ReasoningTrace",
    "RenderedResponse",
    "TurnObservation",
    "UnresolvedObligation",
    "ValidationResult",
    "answer_candidate_from_legacy",
    "candidate_encoding_set_from_encoded_turn_candidates",
    "committed_turn_state_from_legacy",
    "context_resolved_state_from_resolved_context",
    "evidence_set_from_evidence_bundle",
    "intent_resolution_from_legacy",
    "policy_decision_from_decision_object",
    "pre_route_state_from_stabilized_turn_state",
    "rendered_response_from_rendered_answer",
    "turn_observation_from_legacy",
    "validation_result_from_validated_answer",
]
