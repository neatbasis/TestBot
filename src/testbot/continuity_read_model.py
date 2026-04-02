from __future__ import annotations

from dataclasses import dataclass, field

from testbot.pipeline_state import PipelineState


@dataclass(frozen=True)
class ContinuityPendingRepairState:
    repair_required_by_policy: bool = False
    repair_offered_to_user: bool = False
    offer_type: str = ""
    reason: str = "none"
    followup_route: str = ""
    obligation_id: str = ""


@dataclass(frozen=True)
class CommittedTurnContinuity:
    turn_id: str = ""
    commit_stage: str = ""
    pending_ingestion_request_id: str = ""
    pending_repair_state: ContinuityPendingRepairState = field(default_factory=ContinuityPendingRepairState)
    resolved_obligations: tuple[str, ...] = ()
    remaining_obligations: tuple[str, ...] = ()
    confirmed_user_facts: tuple[str, ...] = ()


@dataclass(frozen=True)
class PendingClarificationContinuity:
    obligation_id: str
    question: str
    source_anchor: str
    focus: str = ""


@dataclass(frozen=True)
class ContinuityInterpretation:
    prior_unresolved_intent: str = ""
    resolved_intent_fallback: str = ""

    def prior_intent_hint(self) -> str:
        return self.prior_unresolved_intent or self.resolved_intent_fallback


@dataclass(frozen=True)
class ContinuityReadModel:
    committed_turn: CommittedTurnContinuity | None = None
    pending_clarification: PendingClarificationContinuity | None = None
    interpretation: ContinuityInterpretation = field(default_factory=ContinuityInterpretation)


def continuity_read_model_from_pipeline_state(prior_pipeline_state: PipelineState | None) -> ContinuityReadModel | None:
    if prior_pipeline_state is None:
        return None

    commit_receipt = prior_pipeline_state.commit_receipt
    pending_repair_payload = commit_receipt.pending_repair_state
    committed_turn = None
    if any(
        (
            commit_receipt.committed,
            commit_receipt.turn_id,
            commit_receipt.commit_stage,
            commit_receipt.pending_ingestion_request_id,
            pending_repair_payload,
            commit_receipt.resolved_obligations,
            commit_receipt.remaining_obligations,
            commit_receipt.confirmed_user_facts,
        )
    ):
        committed_turn = CommittedTurnContinuity(
            turn_id=commit_receipt.turn_id,
            commit_stage=commit_receipt.commit_stage,
            pending_ingestion_request_id=commit_receipt.pending_ingestion_request_id,
            pending_repair_state=ContinuityPendingRepairState(
                repair_required_by_policy=bool(pending_repair_payload.get("repair_required_by_policy", False)),
                repair_offered_to_user=bool(pending_repair_payload.get("repair_offered_to_user", False)),
                offer_type=str(pending_repair_payload.get("offer_type") or ""),
                reason=str(pending_repair_payload.get("reason") or "none"),
                followup_route=str(pending_repair_payload.get("followup_route") or ""),
                obligation_id=str(pending_repair_payload.get("obligation_id") or ""),
            ),
            resolved_obligations=tuple(str(value).strip() for value in commit_receipt.resolved_obligations if str(value).strip()),
            remaining_obligations=tuple(str(value).strip() for value in commit_receipt.remaining_obligations if str(value).strip()),
            confirmed_user_facts=tuple(str(value).strip() for value in commit_receipt.confirmed_user_facts if str(value).strip()),
        )

    pending_clarification_payload = prior_pipeline_state.pending_clarification
    pending_clarification = None
    if pending_clarification_payload.required:
        pending_clarification = PendingClarificationContinuity(
            obligation_id=str(pending_clarification_payload.get("obligation_id") or ""),
            question=str(pending_clarification_payload.question or ""),
            source_anchor=str(pending_clarification_payload.get("source_anchor") or "commit.pending_clarification"),
            focus=str(pending_clarification_payload.get("focus") or ""),
        )

    return ContinuityReadModel(
        committed_turn=committed_turn,
        pending_clarification=pending_clarification,
        interpretation=ContinuityInterpretation(
            prior_unresolved_intent=str(prior_pipeline_state.prior_unresolved_intent or "").strip(),
            resolved_intent_fallback=str(prior_pipeline_state.resolved_intent or "").strip(),
        ),
    )


def continuity_context_anchors(read_model: ContinuityReadModel | None) -> tuple[str, ...]:
    if read_model is None:
        return ()

    anchors: list[str] = []
    committed_turn = read_model.committed_turn
    if committed_turn is not None:
        for fact in committed_turn.confirmed_user_facts:
            anchors.append(f"commit.confirmed_user_facts:{fact}")

        pending_repair_state = committed_turn.pending_repair_state
        if pending_repair_state.repair_offered_to_user:
            anchors.append("commit.pending_repair_state:repair_offered_to_user")
            if pending_repair_state.obligation_id:
                anchors.append(f"commit.pending_repair_state:obligation_id={pending_repair_state.obligation_id}")
            if pending_repair_state.followup_route:
                anchors.append(f"commit.assistant_offer_anchor:followup_route={pending_repair_state.followup_route}")
            if pending_repair_state.offer_type:
                anchors.append(f"commit.assistant_offer_anchor:offer_type={pending_repair_state.offer_type}")

        if committed_turn.pending_ingestion_request_id:
            anchors.append(f"commit.pending_ingestion_request_id:{committed_turn.pending_ingestion_request_id}")

        for obligation in committed_turn.remaining_obligations:
            anchors.append(f"commit.remaining_obligations:{obligation}")

    pending_clarification = read_model.pending_clarification
    if pending_clarification is not None:
        anchors.append("commit.pending_clarification:required")
        if pending_clarification.obligation_id:
            anchors.append(f"commit.pending_clarification:obligation_id={pending_clarification.obligation_id}")
        if pending_clarification.focus:
            anchors.append(f"commit.pending_clarification:focus={pending_clarification.focus}")

    return tuple(dict.fromkeys(anchors))


def continuity_retrieval_anchors(read_model: ContinuityReadModel | None) -> tuple[str, ...]:
    if read_model is None:
        return ()

    anchors: list[str] = []
    committed_turn = read_model.committed_turn
    if committed_turn is not None:
        for fact in committed_turn.confirmed_user_facts:
            anchors.append(f"commit.confirmed_user_facts:{fact}")

        if committed_turn.pending_ingestion_request_id:
            anchors.append(f"commit.pending_ingestion_request_id:{committed_turn.pending_ingestion_request_id}")

        for obligation in committed_turn.remaining_obligations:
            anchors.append(f"commit.remaining_obligations:{obligation}")

        pending_repair_state = committed_turn.pending_repair_state
        if pending_repair_state.repair_offered_to_user:
            anchors.append("commit.pending_repair_state:repair_offered_to_user")
            if pending_repair_state.obligation_id:
                anchors.append(f"commit.pending_repair_state:obligation_id={pending_repair_state.obligation_id}")

    pending_clarification = read_model.pending_clarification
    if pending_clarification is not None:
        anchors.append("commit.pending_clarification:required")
        if pending_clarification.obligation_id:
            anchors.append(f"commit.pending_clarification:obligation_id={pending_clarification.obligation_id}")
        if pending_clarification.focus:
            anchors.append(f"commit.pending_clarification:focus={pending_clarification.focus}")

    return tuple(dict.fromkeys(anchors))


def continuity_prior_intent_hint(read_model: ContinuityReadModel | None) -> str:
    if read_model is None:
        return ""
    return read_model.interpretation.prior_intent_hint()


def continuity_pending_ingestion_request_id(read_model: ContinuityReadModel | None) -> str:
    if read_model is None or read_model.committed_turn is None:
        return ""
    return read_model.committed_turn.pending_ingestion_request_id
