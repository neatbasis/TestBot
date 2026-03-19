from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from typing import Any, Callable

from langchain_core.documents import Document

from testbot.answer_assembly import assemble_answer_contract
from testbot.answer_commit import AnswerCommitService, build_commit_stage_inputs
from testbot.answer_rendering import render_answer
from testbot.answer_validation import validate_answer_assembly_boundary
from testbot.canonical_turn_orchestrator import CanonicalStage, CanonicalTurnContext, CanonicalTurnOrchestrator
from testbot.clock import Clock
from testbot.evidence_retrieval import (
    EvidenceBundle,
    build_evidence_bundle_from_docs_and_scores,
    build_evidence_bundle_from_hits,
    continuity_evidence_from_prior_state,
    retrieval_result,
)
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.intent_router import IntentType, extract_intent_facets, planning_pathway_for_intent
from testbot.memory_strata import SegmentDescriptor, SegmentType, derive_segment_descriptor
from testbot.logic import StageArtifacts
from testbot.pipeline_state import PipelineState, append_pipeline_snapshot
from testbot.policy_decision import DecisionClass, decide as decide_policy, decide_from_evidence
from testbot.reflection_policy import CapabilityStatus
from testbot.response_planner import build_response_plan, plan_to_dict
from testbot.retrieval_routing import decide_retrieval_routing
from testbot.stabilization import StabilizedTurnState, stabilize_pre_route
from testbot.stage_transitions import (
    validate_answer_assemble_pre,
    validate_answer_commit_post,
    validate_answer_commit_pre,
    validate_answer_render_post,
    validate_answer_render_pre,
    validate_answer_validate_post,
    validate_answer_validate_pre,
    validate_context_resolve_post,
    validate_context_resolve_pre,
    validate_encode_candidates_post,
    validate_encode_candidates_pre,
    validate_intent_resolve_post,
    validate_intent_resolve_pre,
    validate_observe_turn_post,
    validate_observe_turn_pre,
    validate_policy_decide_post,
    validate_policy_decide_pre,
    validate_retrieve_evidence_post,
    validate_retrieve_evidence_pre,
    validate_stabilize_pre_route_post,
    validate_stabilize_pre_route_pre,
)
from testbot.turn_observation import observe_turn
from testbot.vector_store import MemoryStore
from testbot.ports import LanguageModel


@dataclass(frozen=True)
class TurnPipelineDependencies:
    append_session_log: Callable[[str, dict[str, object]], None]
    validate_and_log_transition: Callable[[object], None]
    stage_rewrite_query: Callable[[LanguageModel, PipelineState], PipelineState]
    generate_reflection_yaml: Callable[..., str]
    intent_classifier_confidence: Callable[..., float]
    optional_string: Callable[[object], str | None]
    should_force_memory_retrieval_for_identity_recall: Callable[..., bool]
    resolve_context_fn: Callable[..., Any]
    intent_telemetry_payload: Callable[..., dict[str, object]]
    poll_background_source_ingestion: Callable[..., dict[str, object] | None]
    start_background_source_ingestion: Callable[..., dict[str, object]]
    stage_retrieve: Callable[..., tuple[PipelineState, list[tuple[Document, float]]]]
    stage_rerank: Callable[..., tuple[PipelineState, list[Document]]]
    selected_decision_from_confidence: Callable[..., Any]
    minimal_confidence_decision_for_direct_answer: Callable[..., dict[str, object]]
    resolve_answer_routing_for_stage: Callable[..., tuple[PipelineState, Any]]
    answer_assemble: Callable[..., Any]
    answer_validate: Callable[..., Any]
    detect_capability_offer: Callable[[str], str]
    ambiguity_score: Callable[[dict[str, object]], float]
    store_doc_fn: Callable[..., None]
    intent_classifier_confidence_threshold: float


@dataclass(frozen=True)
class _ClockSnapshotTimeProvider:
    clock: Clock

    def now_iso(self) -> str:
        return self.clock.now().isoformat()


@dataclass(frozen=True)
class TurnPipelineStageRuntime:
    runtime: dict[str, object]
    llm: LanguageModel
    store: MemoryStore
    utterance: str
    prior_pipeline_state: PipelineState | None
    near_tie_delta: float
    chat_history: deque[dict[str, str]]
    capability_status: CapabilityStatus
    capability_snapshot: Any
    clock: Clock
    io_channel: str
    deps: TurnPipelineDependencies
    snapshot_time_provider: _ClockSnapshotTimeProvider


@dataclass(frozen=True)
class _TurnPipelineStageHandlers:
    runtime: TurnPipelineStageRuntime

    def observe_turn(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return observe_turn_stage(ctx, self.runtime)

    def encode_candidates(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return encode_candidates_stage(ctx, self.runtime)

    def stabilize_pre_route(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return stabilize_pre_route_stage(ctx, self.runtime)

    def context_resolve(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return context_resolve_stage(ctx, self.runtime)

    def intent_resolve(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return intent_resolve_stage(ctx, self.runtime)

    def retrieve_evidence(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return retrieve_evidence_stage(ctx, self.runtime)

    def policy_decide(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return policy_decide_stage(ctx, self.runtime)

    def answer_assemble(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return answer_assemble_stage(ctx, self.runtime)

    def answer_validate(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return answer_validate_stage(ctx, self.runtime)

    def answer_render(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return answer_render_stage(ctx, self.runtime)

    def answer_commit(self, ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return answer_commit_stage(ctx, self.runtime)

    def canonical_stages(self) -> list[CanonicalStage]:
        return [
            CanonicalStage("observe.turn", self.observe_turn),
            CanonicalStage("encode.candidates", self.encode_candidates),
            CanonicalStage("stabilize.pre_route", self.stabilize_pre_route),
            CanonicalStage("context.resolve", self.context_resolve),
            CanonicalStage("intent.resolve", self.intent_resolve),
            CanonicalStage("retrieve.evidence", self.retrieve_evidence),
            CanonicalStage("policy.decide", self.policy_decide),
            CanonicalStage("answer.assemble", self.answer_assemble),
            CanonicalStage("answer.validate", self.answer_validate),
            CanonicalStage("answer.render", self.answer_render),
            CanonicalStage("answer.commit", self.answer_commit),
        ]


def observe_turn_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    artifacts = StageArtifacts(ctx.artifacts)
    stage.deps.validate_and_log_transition(validate_observe_turn_pre(ctx.state))
    observed_at = stage.clock.now().isoformat()
    observation = observe_turn(
        ctx.state,
        turn_id=artifacts.turn_id,
        observed_at=observed_at,
        speaker="user",
        channel=stage.io_channel,
    )
    ctx.artifacts["turn_observation"] = observation
    ctx.state = replace(ctx.state, last_user_message_ts=observed_at)
    stage.deps.validate_and_log_transition(validate_observe_turn_post(ctx.state))
    append_pipeline_snapshot("observe", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def encode_candidates_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    stage.deps.validate_and_log_transition(validate_encode_candidates_pre(ctx.state))
    rewritten_state = stage.deps.stage_rewrite_query(stage.llm, ctx.state)
    stage.deps.validate_and_log_transition(validate_encode_candidates_post(rewritten_state))
    rewritten_query = rewritten_state.rewritten_query
    stage.deps.append_session_log("query_rewrite_output", {"utterance": stage.utterance, "query": rewritten_query})

    from testbot.candidate_encoding import encode_turn_candidates

    encoded = encode_turn_candidates(
        ctx.state,
        observation=ctx.artifacts["turn_observation"],
        rewritten_query=rewritten_query,
    )
    ctx.artifacts["encoded_candidates"] = encoded
    ctx.state = replace(
        ctx.state,
        rewritten_query=encoded.rewritten_query,
        candidate_facts=encoded.as_artifact_payload(),
    )
    append_pipeline_snapshot("rewrite", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def stabilize_pre_route_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    stage.deps.validate_and_log_transition(validate_stabilize_pre_route_pre(ctx.state))
    planning_descriptor = planning_pathway_for_intent(IntentType(ctx.state.classified_intent), extract_intent_facets(stage.utterance))
    response_plan = build_response_plan(descriptor=planning_descriptor, user_input=stage.utterance)
    reflection_yaml = stage.deps.generate_reflection_yaml(stage.llm, speaker="user", text=stage.utterance)
    prior_candidate_facts = ctx.state.candidate_facts if isinstance(ctx.state.candidate_facts, dict) else {}
    prior_segment_id = str(prior_candidate_facts.get("segment_id") or "")
    prior_segment_type = str(prior_candidate_facts.get("segment_type") or "")
    prior_segment = None
    if prior_segment_id and prior_segment_type:
        continuity_probe = derive_segment_descriptor(
            utterance=stage.utterance,
            has_dialogue_state=bool(ctx.artifacts["encoded_candidates"].dialogue_state),
        )
        try:
            prior_segment = SegmentDescriptor(
                segment_type=SegmentType(prior_segment_type),
                segment_id=prior_segment_id,
                continuity_key=continuity_probe.continuity_key,
            )
        except ValueError:
            prior_segment = None
    segment = derive_segment_descriptor(
        utterance=stage.utterance,
        prior_descriptor=prior_segment,
        has_dialogue_state=bool(ctx.artifacts["encoded_candidates"].dialogue_state),
    )
    ctx.state, stabilized = stabilize_pre_route(
        store=stage.store,
        state=ctx.state,
        observation=ctx.artifacts["turn_observation"],
        encoded=ctx.artifacts["encoded_candidates"],
        response_plan=plan_to_dict(response_plan),
        reflection_yaml=reflection_yaml,
        segment=segment,
        store_doc_fn=stage.deps.store_doc_fn,
    )
    ctx.artifacts["stabilized_turn_state"] = stabilized
    stage.deps.validate_and_log_transition(validate_stabilize_pre_route_post(ctx.state))
    append_pipeline_snapshot("stabilize", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def context_resolve_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    stage.deps.validate_and_log_transition(validate_context_resolve_pre(ctx.state))
    stabilized: StabilizedTurnState = ctx.artifacts["stabilized_turn_state"]
    stabilized_utterance = next((fact.value for fact in stabilized.candidate_facts if fact.key == "utterance_raw"), "")
    context_resolution = stage.deps.resolve_context_fn(
        utterance=stabilized_utterance or stage.utterance,
        prior_pipeline_state=stage.prior_pipeline_state,
    )
    continuity_evidence = continuity_evidence_from_prior_state(stage.prior_pipeline_state)
    ctx.artifacts["resolved_context"] = context_resolution
    ctx.artifacts["retrieval_continuity_evidence"] = continuity_evidence
    ctx.state = replace(
        ctx.state,
        resolved_context={
            "history_anchors": list(context_resolution.history_anchors),
            "ambiguity_flags": list(context_resolution.ambiguity_flags),
            "continuity_posture": context_resolution.continuity_posture.value,
            "prior_intent": context_resolution.prior_intent.value if context_resolution.prior_intent is not None else "",
        },
        confidence_decision={
            **ctx.state.confidence_decision,
            "retrieval_continuity_evidence": list(continuity_evidence),
        },
    )
    stage.deps.validate_and_log_transition(validate_context_resolve_post(ctx.state))
    append_pipeline_snapshot("context", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def intent_resolve_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    stage.deps.validate_and_log_transition(validate_intent_resolve_pre(ctx.state))
    stabilized: StabilizedTurnState = ctx.artifacts["stabilized_turn_state"]
    stabilized_utterance = next((fact.value for fact in stabilized.candidate_facts if fact.key == "utterance_raw"), "")
    context_resolution = ctx.artifacts["resolved_context"]
    intent_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=stabilized,
            context=context_resolution,
            fallback_utterance=stage.utterance,
        )
    )
    classifier_confidence = stage.deps.intent_classifier_confidence(
        utterance=stabilized_utterance or stage.utterance,
        predicted_intent=intent_resolution.classified_intent,
    )
    intent_classifier_metadata: dict[str, object] = {}
    classifier_model = stage.deps.optional_string(stage.runtime.get("intent_classifier_model"))
    classifier_version = stage.deps.optional_string(stage.runtime.get("intent_classifier_version"))
    if classifier_model is not None:
        intent_classifier_metadata["intent_classifier_model"] = classifier_model
    if classifier_version is not None:
        intent_classifier_metadata["intent_classifier_version"] = classifier_version
    recall_query = stabilized_utterance or stage.utterance
    continuity_evidence = tuple(ctx.artifacts.get("retrieval_continuity_evidence", ()))
    context_history_anchors = tuple(getattr(context_resolution, "history_anchors", ()))
    guard_forced_memory_retrieval = stage.deps.should_force_memory_retrieval_for_identity_recall(
        utterance=recall_query,
        prior_state=stage.prior_pipeline_state,
        continuity_evidence=continuity_evidence,
        context_history_anchors=context_history_anchors,
    )
    retrieval_routing = decide_retrieval_routing(
        utterance=recall_query,
        intent=intent_resolution.resolved_intent,
        guard_forced_memory_retrieval=guard_forced_memory_retrieval,
    )
    ctx.artifacts["retrieval_requirement"] = {
        "requires_retrieval": retrieval_routing.requires_retrieval,
        "reason": retrieval_routing.reason,
        "retrieval_branch": retrieval_routing.retrieval_branch,
    }
    ctx.artifacts["guard_forced_memory_retrieval"] = guard_forced_memory_retrieval
    ctx.state = replace(
        ctx.state,
        classified_intent=intent_resolution.classified_intent.value,
        resolved_intent=intent_resolution.resolved_intent.value,
        confidence_decision={
            **ctx.state.confidence_decision,
            "intent_predicted": intent_resolution.classified_intent.value,
            "intent_classifier_confidence": classifier_confidence,
            "intent_classifier_threshold": stage.deps.intent_classifier_confidence_threshold,
            **intent_classifier_metadata,
        },
        policy_decision={
            "policy": "intent_retrieval_requirement",
            "decision": "retrieval_requirement_only",
            "intent_classified": intent_resolution.classified_intent.value,
            "intent_resolved": intent_resolution.resolved_intent.value,
            "requires_retrieval": retrieval_routing.requires_retrieval,
            "reason": retrieval_routing.reason,
            "retrieval_branch": retrieval_routing.retrieval_branch,
        },
    )
    stage.deps.append_session_log(
        "retrieval_branch_selected",
        stage.deps.intent_telemetry_payload(
            state=ctx.state,
            utterance=stage.utterance,
            extra={
                "retrieval_branch": retrieval_routing.retrieval_branch,
                "retrieval_requirement": dict(ctx.artifacts["retrieval_requirement"]),
                "stabilized_turn_id": stabilized.turn_id,
                "stabilized_candidate_fact_count": len(stabilized.candidate_facts),
                "stabilized_dialogue_state_count": len(stabilized.candidate_dialogue_state),
                "context_continuity_posture": context_resolution.continuity_posture.value,
                "context_history_anchors": list(context_resolution.history_anchors),
                "guard_forced_memory_retrieval": bool(ctx.artifacts.get("guard_forced_memory_retrieval", False)),
            },
        ),
    )
    stage.deps.validate_and_log_transition(validate_intent_resolve_post(ctx.state))
    append_pipeline_snapshot("intent", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def retrieve_evidence_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    artifacts = StageArtifacts(ctx.artifacts)
    background_poll = stage.deps.poll_background_source_ingestion(runtime=stage.runtime)
    background_in_progress = bool(stage.runtime.get("source_ingest_background_in_progress", False))
    if background_in_progress and not artifacts.pending_ingestion_request_id:
        live_request_id = str(stage.runtime.get("source_ingest_background_request_id") or "")
        if live_request_id:
            artifacts.pending_ingestion_request_id = live_request_id
    ctx.artifacts["background_ingestion_in_progress"] = background_in_progress
    if background_poll is not None:
        ctx.artifacts["background_ingestion_poll"] = background_poll
        poll_payload = background_poll.get("payload") if isinstance(background_poll, dict) else None
        if isinstance(poll_payload, dict):
            polled_request_id = str(poll_payload.get("ingestion_request_id") or "")
            if polled_request_id:
                artifacts.pending_ingestion_request_id = polled_request_id

    retrieval_requirement = artifacts.retrieval_requirement
    if bool(retrieval_requirement.get("requires_retrieval", False)):
        stage.deps.validate_and_log_transition(validate_retrieve_evidence_pre(ctx.state))
        same_turn_exclusion_doc_ids = set(ctx.state.same_turn_exclusion.get("excluded_doc_ids", []))
        retrieval_exclude_doc_ids = same_turn_exclusion_doc_ids
        retrieval_exclude_source_ids = {ctx.artifacts["stabilized_turn_state"].utterance_doc_id}
        retrieval_exclude_turn_scoped_ids = same_turn_exclusion_doc_ids
        segment_constraints = ctx.state.candidate_facts.get("retrieval_constraints", {})
        retrieval_segment_ids = set(segment_constraints.get("segment_ids", []))
        retrieval_segment_types = set(segment_constraints.get("segment_types", []))

        ctx.state, docs_and_scores = stage.deps.stage_retrieve(
            stage.store,
            ctx.state,
            exclude_doc_ids=retrieval_exclude_doc_ids,
            exclude_source_ids=retrieval_exclude_source_ids,
            exclude_turn_scoped_ids=retrieval_exclude_turn_scoped_ids,
            segment_ids=retrieval_segment_ids,
            segment_types=retrieval_segment_types,
        )
        stage.deps.validate_and_log_transition(validate_retrieve_evidence_post(ctx.state))
        if not docs_and_scores and bool(stage.runtime.get("source_ingest_async_continuation", False)):
            start_result = stage.deps.start_background_source_ingestion(runtime=stage.runtime, store=stage.store)
            start_request_id = str(start_result.get("ingestion_request_id") or "")
            if start_request_id:
                artifacts.pending_ingestion_request_id = start_request_id
            background_in_progress = bool(stage.runtime.get("source_ingest_background_in_progress", False))
        ctx.state = replace(
            ctx.state,
            confidence_decision={**ctx.state.confidence_decision, "background_ingestion_in_progress": background_in_progress},
        )
        ctx.artifacts["background_ingestion_in_progress"] = background_in_progress
        if background_in_progress:
            ctx.artifacts["continuation_required"] = True

        ctx.artifacts["docs_and_scores"] = docs_and_scores
        considered = int(ctx.state.confidence_decision.get("retrieval_candidates_considered", len(docs_and_scores)) or 0)
        prerank_bundle = build_evidence_bundle_from_docs_and_scores(docs_and_scores)
        ctx.artifacts["pre_rerank_evidence_bundle"] = prerank_bundle
        ctx.artifacts["retrieval_result"] = retrieval_result(evidence_bundle=prerank_bundle, retrieval_candidates_considered=considered, hit_count=0)
        stage.deps.append_session_log(
            "retrieval_candidates",
            {
                "query": ctx.state.rewritten_query,
                "candidate_count": len(docs_and_scores),
                "top_candidates": [{"doc_id": (doc.id or doc.metadata.get("doc_id") or ""), "score": float(score)} for doc, score in docs_and_scores[:4]],
                "hygiene": {
                    "exclude_doc_ids": sorted(retrieval_exclude_doc_ids),
                    "exclude_source_ids": sorted(retrieval_exclude_source_ids),
                    "exclude_turn_scoped_ids": sorted(retrieval_exclude_turn_scoped_ids),
                    "primary_invariant": "retrieve_stage_exclusion",
                    "rerank_defense_in_depth": True,
                    "segment_ids": sorted(retrieval_segment_ids),
                    "segment_types": sorted(retrieval_segment_types),
                },
            },
        )
    else:
        ctx.artifacts["pre_rerank_evidence_bundle"] = EvidenceBundle()
        ctx.artifacts["retrieval_result"] = retrieval_result(
            evidence_bundle=EvidenceBundle(),
            retrieval_candidates_considered=0,
            hit_count=0,
        )
        stage.deps.append_session_log(
            "retrieval_candidates",
            {"query": ctx.state.rewritten_query, "candidate_count": 0, "top_candidates": [], "skipped": True},
        )
    append_pipeline_snapshot("retrieve", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def policy_decide_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    artifacts = StageArtifacts(ctx.artifacts)
    resolved_intent = IntentType(ctx.state.resolved_intent)
    retrieval_requirement = artifacts.retrieval_requirement
    requires_retrieval = bool(retrieval_requirement.get("requires_retrieval", False))
    repair_required = artifacts.get_bool("background_ingestion_in_progress", default=False)
    if requires_retrieval:
        stage.deps.validate_and_log_transition(validate_policy_decide_pre(ctx.state))
        stabilized: StabilizedTurnState = ctx.artifacts["stabilized_turn_state"]
        ctx.state, hits = stage.deps.stage_rerank(
            ctx.state,
            ctx.artifacts["docs_and_scores"],
            utterance=stage.utterance,
            user_doc_id=stabilized.utterance_doc_id,
            user_reflection_doc_id=stabilized.reflection_doc_id,
            near_tie_delta=stage.near_tie_delta,
            clock=stage.clock,
        )
        if repair_required:
            ctx.state = replace(
                ctx.state,
                confidence_decision={**ctx.state.confidence_decision, "background_ingestion_in_progress": True},
            )
        stage.deps.validate_and_log_transition(validate_policy_decide_post(ctx.state))
        ctx.artifacts["hits"] = hits
        considered = int(ctx.state.confidence_decision.get("retrieval_candidates_considered", len(ctx.artifacts["docs_and_scores"])) or 0)
        policy_decision = decide_policy(
            utterance=stage.utterance,
            intent=resolved_intent,
            retrieval_candidates_considered=considered,
            hit_count=len(hits),
            guard_forced_memory_retrieval=bool(ctx.artifacts.get("guard_forced_memory_retrieval", False)),
        )
        ctx.artifacts["policy_decision"] = policy_decision
        finalized_bundle = build_evidence_bundle_from_hits(hits)
        ctx.artifacts["retrieval_result"] = retrieval_result(
            evidence_bundle=finalized_bundle,
            retrieval_candidates_considered=considered,
            hit_count=len(hits),
        )
        selected_decision = stage.deps.selected_decision_from_confidence(ctx.state.confidence_decision)
        ctx.artifacts["decision_object"] = selected_decision or decide_from_evidence(
            intent=resolved_intent,
            retrieval=ctx.artifacts["retrieval_result"],
            repair_required=repair_required,
        )
    else:
        policy_decision = decide_policy(
            utterance=stage.utterance,
            intent=resolved_intent,
            guard_forced_memory_retrieval=bool(ctx.artifacts.get("guard_forced_memory_retrieval", False)),
        )
        ctx.artifacts["policy_decision"] = policy_decision
        selected_decision = stage.deps.selected_decision_from_confidence(ctx.state.confidence_decision)
        ctx.artifacts["decision_object"] = selected_decision or decide_from_evidence(
            intent=resolved_intent,
            retrieval=ctx.artifacts["retrieval_result"],
            repair_required=repair_required,
        )
        minimal_confidence = stage.deps.minimal_confidence_decision_for_direct_answer(
            branch=ctx.artifacts["policy_decision"].retrieval_branch,
            base_confidence_decision=ctx.state.confidence_decision,
        )
        ctx.state = replace(ctx.state, retrieval_candidates=[], reranked_hits=[], confidence_decision=minimal_confidence)
        stage.deps.append_session_log(
            "rerank_skipped",
            stage.deps.intent_telemetry_payload(
                state=ctx.state,
                utterance=stage.utterance,
                extra={
                    "reason": "intent_routed_to_direct_answer",
                    "retrieval_branch": ctx.artifacts["policy_decision"].retrieval_branch,
                },
            ),
        )
    append_pipeline_snapshot("rerank", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def answer_assemble_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    artifacts = StageArtifacts(ctx.artifacts)
    stage.deps.validate_and_log_transition(validate_answer_assemble_pre(ctx.state))
    ctx.state, answer_routing = stage.deps.resolve_answer_routing_for_stage(
        ctx.state,
        capability_status=stage.capability_status,
        selected_decision=ctx.artifacts["decision_object"],
    )
    assembled = stage.deps.answer_assemble(
        stage.llm,
        ctx.state,
        chat_history=stage.chat_history,
        hits=ctx.artifacts["hits"],
        capability_status=stage.capability_status,
        answer_routing=answer_routing,
        runtime_capability_status=stage.capability_snapshot.runtime_capability_status,
        clock=stage.clock,
    )
    ctx.artifacts["assembled_answer"] = assembled
    decision_object = ctx.artifacts["decision_object"]
    retrieval_result_obj = ctx.artifacts["retrieval_result"]
    offer_type = (
        stage.deps.detect_capability_offer(assembled.final_answer)
        if decision_object.decision_class is DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED
        else ""
    )
    ctx.artifacts["answer_assembly_contract"] = assemble_answer_contract(
        decision=decision_object,
        evidence_bundle=retrieval_result_obj.evidence_bundle,
        pending_ingestion_request_id=artifacts.pending_ingestion_request_id,
        offer_bearing=bool(offer_type),
        offer_type=offer_type,
    )
    append_pipeline_snapshot("answer.assemble", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def answer_validate_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    stage.deps.validate_and_log_transition(validate_answer_validate_pre(ctx.state, ctx.artifacts))
    background_ingestion_in_progress = bool(ctx.artifacts.get("background_ingestion_in_progress", False))
    if background_ingestion_in_progress:
        ctx.state = replace(
            ctx.state,
            confidence_decision={**ctx.state.confidence_decision, "background_ingestion_in_progress": True},
        )
    validated_answer = stage.deps.answer_validate(
        ctx.state,
        assembled=ctx.artifacts["assembled_answer"],
        hits=ctx.artifacts["hits"],
        chat_history=stage.chat_history,
        pending_lookup_override=background_ingestion_in_progress,
    )
    ctx.artifacts["validated_answer"] = validated_answer
    ctx.artifacts["answer_validation_contract"] = validate_answer_assembly_boundary(
        ctx.artifacts["answer_assembly_contract"],
        final_answer=validated_answer.final_answer,
        claims=validated_answer.claims,
        provenance_types=validated_answer.provenance_types,
        used_memory_refs=validated_answer.used_memory_refs,
        used_source_evidence_refs=validated_answer.used_source_evidence_refs,
        source_evidence_attribution=validated_answer.source_evidence_attribution,
        basis_statement=validated_answer.basis_statement,
        invariant_decisions=validated_answer.invariant_decisions,
        alignment_decision=validated_answer.alignment_decision,
    )
    if not ctx.artifacts["answer_validation_contract"].passed:
        raise RuntimeError("answer assembly contract validation failed before render/commit")
    stage.deps.validate_and_log_transition(validate_answer_validate_post(ctx.state, ctx.artifacts))
    append_pipeline_snapshot("answer.validate", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def answer_render_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    stage.deps.validate_and_log_transition(validate_answer_render_pre(ctx.state, ctx.artifacts))
    ctx.artifacts["answer_render_contract"] = render_answer(
        assembly=ctx.artifacts["answer_assembly_contract"],
        validation=ctx.artifacts["answer_validation_contract"],
        preferred_text=ctx.artifacts["answer_validation_contract"].final_answer,
    )
    ctx.artifacts["answer_commit_inputs"] = build_commit_stage_inputs(
        validation=ctx.artifacts["answer_validation_contract"],
        rendered=ctx.artifacts["answer_render_contract"],
    )
    stage.deps.validate_and_log_transition(validate_answer_render_post(ctx.state, ctx.artifacts))
    append_pipeline_snapshot("answer.render", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def answer_commit_stage(ctx: CanonicalTurnContext, stage: TurnPipelineStageRuntime) -> CanonicalTurnContext:
    stage.deps.validate_and_log_transition(validate_answer_commit_pre(ctx.state, ctx.artifacts))
    ctx.state, ctx.artifacts["committed_turn_state"] = AnswerCommitService().commit(
        ctx.state,
        assembly=ctx.artifacts["answer_assembly_contract"],
        commit_inputs=ctx.artifacts["answer_commit_inputs"],
        commit_stage_id="answer.commit",
    )
    ctx.state = replace(ctx.state, draft_answer=ctx.artifacts["assembled_answer"].draft_answer)
    stage.deps.validate_and_log_transition(validate_answer_commit_post(ctx.state))
    append_pipeline_snapshot("answer", ctx.state, time_provider=stage.snapshot_time_provider)
    ambiguity_score = stage.deps.ambiguity_score(ctx.state.confidence_decision)
    ctx.artifacts["ambiguity_score"] = ambiguity_score
    stage.deps.append_session_log(
        "intent_classified",
        stage.deps.intent_telemetry_payload(
            state=ctx.state,
            utterance=stage.utterance,
            extra={"ambiguity_score": ambiguity_score, "user_followup_signal_proxy": round(ambiguity_score, 4)},
        ),
    )
    stage.deps.append_session_log(
        "commit_stage_recorded",
        {
            "stage": "answer.commit",
            "commit_stage": ctx.state.commit_receipt.commit_stage or "answer.commit",
            "pipeline_state_snapshot": ctx.state.commit_receipt.pipeline_state_snapshot or "recorded",
            "pending_repair_state": dict(ctx.state.commit_receipt.pending_repair_state),
            "resolved_obligations": list(ctx.state.commit_receipt.resolved_obligations),
            "remaining_obligations": list(ctx.state.commit_receipt.remaining_obligations),
            "confirmed_user_facts": list(ctx.state.commit_receipt.confirmed_user_facts),
            "pending_ingestion_request_id": ctx.state.commit_receipt.pending_ingestion_request_id,
            "retrieval_continuity_evidence": list(ctx.artifacts.get("retrieval_continuity_evidence", ())),
        },
    )
    stage_audit_trail = list(ctx.stage_audit_trail)
    if not stage_audit_trail or stage_audit_trail[-1] != "answer.commit":
        stage_audit_trail.append("answer.commit")
    stage.deps.append_session_log(
        "final_answer_mode",
        {
            "mode": ctx.state.invariant_decisions.get("answer_mode", "dont-know"),
            "query": ctx.state.rewritten_query,
            "context_confident": ctx.state.confidence_decision.get("context_confident", False),
            "retrieved_docs": [(d.id or d.metadata.get("doc_id") or "") for d in ctx.artifacts["hits"]],
            "claims": ctx.state.claims,
            "provenance_types": [p.value for p in ctx.state.provenance_types],
            "used_memory_refs": ctx.state.used_memory_refs,
            "used_source_evidence_refs": ctx.state.used_source_evidence_refs,
            "source_evidence_attribution": ctx.state.source_evidence_attribution,
            "basis_statement": ctx.state.basis_statement,
            "stage_audit_trail": stage_audit_trail,
            "commit_stage": ctx.state.commit_receipt.commit_stage or "answer.commit",
        },
    )
    append_pipeline_snapshot("answer.commit", ctx.state, time_provider=stage.snapshot_time_provider)
    return ctx


def run_canonical_turn_pipeline_service(
    *,
    runtime: dict[str, object] | None = None,
    llm: LanguageModel,
    store: MemoryStore,
    state: PipelineState,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    turn_id: str,
    near_tie_delta: float,
    chat_history: deque[dict[str, str]],
    capability_status: CapabilityStatus,
    capability_snapshot: Any,
    clock: Clock,
    io_channel: str,
    deps: TurnPipelineDependencies,
) -> tuple[PipelineState, list[Document]]:
    runtime = runtime or {}
    snapshot_time_provider = _ClockSnapshotTimeProvider(clock=clock)
    prior_pending_ingestion_request_id = ""
    if prior_pipeline_state is not None:
        prior_pending_ingestion_request_id = prior_pipeline_state.commit_receipt.pending_ingestion_request_id

    context = CanonicalTurnContext(
        state=state,
        artifacts={
            "utterance": utterance,
            "policy_decision": None,
            "turn_id": turn_id,
            "pending_ingestion_request_id": prior_pending_ingestion_request_id,
            "docs_and_scores": [],
            "hits": [],
            "ambiguity_score": 0.0,
        },
    )

    stage_runtime = TurnPipelineStageRuntime(
        runtime=runtime,
        llm=llm,
        store=store,
        utterance=utterance,
        prior_pipeline_state=prior_pipeline_state,
        near_tie_delta=near_tie_delta,
        chat_history=chat_history,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        clock=clock,
        io_channel=io_channel,
        deps=deps,
        snapshot_time_provider=snapshot_time_provider,
    )

    stage_handlers = _TurnPipelineStageHandlers(runtime=stage_runtime)
    orchestrator = CanonicalTurnOrchestrator(stages=stage_handlers.canonical_stages())
    final_context = orchestrator.run(context)
    final_state = replace(
        final_context.state,
        confidence_decision={
            **final_context.state.confidence_decision,
            "stage_audit_trail": list(final_context.stage_audit_trail),
        },
    )
    return final_state, list(final_context.artifacts["hits"])


__all__ = ["TurnPipelineDependencies", "run_canonical_turn_pipeline_service"]
