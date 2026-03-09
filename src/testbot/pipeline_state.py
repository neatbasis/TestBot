from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from testbot.memory_cards import utc_now_iso

PIPELINE_SNAPSHOT_SCHEMA_VERSION = 3


@dataclass(frozen=True)
class CandidateHit:
    doc_id: str
    score: float
    ts: str = ""
    card_type: str = ""


class ProvenanceType(StrEnum):
    MEMORY = "MEMORY"
    CHAT_HISTORY = "CHAT_HISTORY"
    SYSTEM_STATE = "SYSTEM_STATE"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class StageArtifact:
    """Typed wrapper for stage contracts with an explicit extra-metadata channel."""

    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> StageArtifact:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        return cls(extra=dict(payload))

    def _raw_dict(self) -> dict[str, Any]:
        return self.extra

    def to_dict(self) -> dict[str, Any]:
        return _stable_json_value(dict(self._raw_dict()))

    def __getitem__(self, key: str) -> Any:
        return self._raw_dict()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.extra[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._raw_dict().get(key, default)

    def __iter__(self):
        return iter(self._raw_dict())

    def __len__(self) -> int:
        return len(self._raw_dict())

    def keys(self):
        return self._raw_dict().keys()

    def items(self):
        return self._raw_dict().items()

    def values(self):
        return self._raw_dict().values()


@dataclass(frozen=True)
class ConfidenceDecision(StageArtifact):
    context_confident: bool | None = None
    ambiguity_detected: bool | None = None
    retrieval_branch: str = ""

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> ConfidenceDecision:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        known = {
            "context_confident": payload.get("context_confident"),
            "ambiguity_detected": payload.get("ambiguity_detected"),
            "retrieval_branch": str(payload.get("retrieval_branch", "") or ""),
        }
        extra = {k: v for k, v in payload.items() if k not in known}
        return cls(extra=extra, **known)

    def _raw_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.context_confident is not None:
            data["context_confident"] = self.context_confident
        if self.ambiguity_detected is not None:
            data["ambiguity_detected"] = self.ambiguity_detected
        if self.retrieval_branch:
            data["retrieval_branch"] = self.retrieval_branch
        data.update(self.extra)
        return data


@dataclass(frozen=True)
class InvariantDecision(StageArtifact):
    answer_mode: str = ""
    fallback_action: str = ""
    answer_contract_valid: bool | None = None
    general_knowledge_contract_valid: bool | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> InvariantDecision:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        known = {
            "answer_mode": str(payload.get("answer_mode", "") or ""),
            "fallback_action": str(payload.get("fallback_action", "") or ""),
            "answer_contract_valid": payload.get("answer_contract_valid"),
            "general_knowledge_contract_valid": payload.get("general_knowledge_contract_valid"),
        }
        extra = {k: v for k, v in payload.items() if k not in known}
        return cls(extra=extra, **known)

    def _raw_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.answer_mode:
            data["answer_mode"] = self.answer_mode
        if self.fallback_action:
            data["fallback_action"] = self.fallback_action
        if self.answer_contract_valid is not None:
            data["answer_contract_valid"] = self.answer_contract_valid
        if self.general_knowledge_contract_valid is not None:
            data["general_knowledge_contract_valid"] = self.general_knowledge_contract_valid
        data.update(self.extra)
        return data


@dataclass(frozen=True)
class AlignmentDecision(StageArtifact):
    final_alignment_decision: str = ""
    dimensions: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> AlignmentDecision:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        known_keys = {"final_alignment_decision", "dimensions"}
        return cls(
            final_alignment_decision=str(payload.get("final_alignment_decision", "") or ""),
            dimensions=dict(payload.get("dimensions") or {}),
            extra={k: v for k, v in payload.items() if k not in known_keys},
        )

    def _raw_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.dimensions:
            data["dimensions"] = self.dimensions
        if self.final_alignment_decision:
            data["final_alignment_decision"] = self.final_alignment_decision
        data.update(self.extra)
        return data


@dataclass(frozen=True)
class ResponsePlanArtifact(StageArtifact):
    pathway: str = ""
    top_level_intent: str = ""
    facets: dict[str, bool] = field(default_factory=dict)
    stages: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> ResponsePlanArtifact:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        known_keys = {"pathway", "top_level_intent", "facets", "stages"}
        return cls(
            pathway=str(payload.get("pathway", "") or ""),
            top_level_intent=str(payload.get("top_level_intent", "") or ""),
            facets=dict(payload.get("facets") or {}),
            stages=[dict(stage) for stage in payload.get("stages", [])],
            extra={k: v for k, v in payload.items() if k not in known_keys},
        )

    def _raw_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.pathway:
            data["pathway"] = self.pathway
        if self.top_level_intent:
            data["top_level_intent"] = self.top_level_intent
        if self.facets:
            data["facets"] = self.facets
        if self.stages:
            data["stages"] = self.stages
        data.update(self.extra)
        return data


@dataclass(frozen=True)
class CandidateFactsArtifact(StageArtifact):
    facts: list[dict[str, Any]] = field(default_factory=list)

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.facts:
            data["facts"] = self.facts
        return data


@dataclass(frozen=True)
class ResolvedContextArtifact(StageArtifact):
    entities: list[dict[str, Any]] = field(default_factory=list)
    time_window: dict[str, Any] = field(default_factory=dict)

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.entities:
            data["entities"] = self.entities
        if self.time_window:
            data["time_window"] = self.time_window
        return data


@dataclass(frozen=True)
class EvidenceBundleArtifact(StageArtifact):
    memory_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.memory_refs:
            data["memory_refs"] = self.memory_refs
        if self.source_refs:
            data["source_refs"] = self.source_refs
        return data


@dataclass(frozen=True)
class PolicyDecisionArtifact(StageArtifact):
    policy: str = ""
    decision: str = ""

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.policy:
            data["policy"] = self.policy
        if self.decision:
            data["decision"] = self.decision
        return data


@dataclass(frozen=True)
class ValidationResultArtifact(StageArtifact):
    passed: bool | None = None
    failures: list[str] = field(default_factory=list)

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.passed is not None:
            data["passed"] = self.passed
        if self.failures:
            data["failures"] = self.failures
        return data


@dataclass(frozen=True)
class RenderOutputArtifact(StageArtifact):
    rendered_text: str = ""

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.rendered_text:
            data["rendered_text"] = self.rendered_text
        return data


@dataclass(frozen=True)
class CommitReceiptArtifact(StageArtifact):
    committed: bool = False
    commit_id: str = ""
    pending_ingestion_request_id: str = ""

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> CommitReceiptArtifact:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        known = {
            "committed": bool(payload.get("committed", False)),
            "commit_id": str(payload.get("commit_id", "") or ""),
            "pending_ingestion_request_id": str(payload.get("pending_ingestion_request_id", "") or ""),
        }
        extra = {k: v for k, v in payload.items() if k not in known}
        return cls(extra=extra, **known)

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.committed:
            data["committed"] = self.committed
        if self.commit_id:
            data["commit_id"] = self.commit_id
        if self.pending_ingestion_request_id:
            data["pending_ingestion_request_id"] = self.pending_ingestion_request_id
        return data


@dataclass(frozen=True)
class SameTurnExclusionArtifact(StageArtifact):
    excluded_doc_ids: list[str] = field(default_factory=list)
    reason: str = ""

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.excluded_doc_ids:
            data["excluded_doc_ids"] = self.excluded_doc_ids
        if self.reason:
            data["reason"] = self.reason
        return data


@dataclass(frozen=True)
class PendingRepairArtifact(StageArtifact):
    required: bool = False
    reason: str = ""

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.required:
            data["required"] = self.required
        if self.reason:
            data["reason"] = self.reason
        return data


@dataclass(frozen=True)
class PendingClarificationArtifact(StageArtifact):
    required: bool = False
    question: str = ""

    def _raw_dict(self) -> dict[str, Any]:
        data = dict(self.extra)
        if self.required:
            data["required"] = self.required
        if self.question:
            data["question"] = self.question
        return data


@dataclass(frozen=True)
class PipelineState:
    user_input: str
    rewritten_query: str = ""
    retrieval_candidates: list[CandidateHit] = field(default_factory=list)
    reranked_hits: list[CandidateHit] = field(default_factory=list)
    confidence_decision: ConfidenceDecision = field(default_factory=ConfidenceDecision)
    draft_answer: str = ""
    final_answer: str = ""
    claims: list[str] = field(default_factory=list)
    provenance_types: list[ProvenanceType] = field(default_factory=list)
    used_memory_refs: list[str] = field(default_factory=list)
    used_source_evidence_refs: list[str] = field(default_factory=list)
    source_evidence_attribution: list[dict[str, str]] = field(default_factory=list)
    basis_statement: str = ""
    invariant_decisions: InvariantDecision = field(default_factory=InvariantDecision)
    alignment_decision: AlignmentDecision = field(default_factory=AlignmentDecision)
    last_user_message_ts: str = ""
    classified_intent: str = ""
    resolved_intent: str = ""
    prior_unresolved_intent: str = ""
    response_plan: ResponsePlanArtifact = field(default_factory=ResponsePlanArtifact)
    candidate_facts: CandidateFactsArtifact = field(default_factory=CandidateFactsArtifact)
    resolved_context: ResolvedContextArtifact = field(default_factory=ResolvedContextArtifact)
    evidence_bundle: EvidenceBundleArtifact = field(default_factory=EvidenceBundleArtifact)
    policy_decision: PolicyDecisionArtifact = field(default_factory=PolicyDecisionArtifact)
    validation_result: ValidationResultArtifact = field(default_factory=ValidationResultArtifact)
    render_output: RenderOutputArtifact = field(default_factory=RenderOutputArtifact)
    commit_receipt: CommitReceiptArtifact = field(default_factory=CommitReceiptArtifact)
    same_turn_exclusion: SameTurnExclusionArtifact = field(default_factory=SameTurnExclusionArtifact)
    pending_repair: PendingRepairArtifact = field(default_factory=PendingRepairArtifact)
    pending_clarification: PendingClarificationArtifact = field(default_factory=PendingClarificationArtifact)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence_decision", ConfidenceDecision.from_mapping(self.confidence_decision))
        object.__setattr__(self, "invariant_decisions", InvariantDecision.from_mapping(self.invariant_decisions))
        object.__setattr__(self, "alignment_decision", AlignmentDecision.from_mapping(self.alignment_decision))
        object.__setattr__(self, "response_plan", ResponsePlanArtifact.from_mapping(self.response_plan))
        object.__setattr__(self, "candidate_facts", CandidateFactsArtifact.from_mapping(self.candidate_facts))
        object.__setattr__(self, "resolved_context", ResolvedContextArtifact.from_mapping(self.resolved_context))
        object.__setattr__(self, "evidence_bundle", EvidenceBundleArtifact.from_mapping(self.evidence_bundle))
        object.__setattr__(self, "policy_decision", PolicyDecisionArtifact.from_mapping(self.policy_decision))
        object.__setattr__(self, "validation_result", ValidationResultArtifact.from_mapping(self.validation_result))
        object.__setattr__(self, "render_output", RenderOutputArtifact.from_mapping(self.render_output))
        object.__setattr__(self, "commit_receipt", CommitReceiptArtifact.from_mapping(self.commit_receipt))
        object.__setattr__(self, "same_turn_exclusion", SameTurnExclusionArtifact.from_mapping(self.same_turn_exclusion))
        object.__setattr__(self, "pending_repair", PendingRepairArtifact.from_mapping(self.pending_repair))
        object.__setattr__(self, "pending_clarification", PendingClarificationArtifact.from_mapping(self.pending_clarification))


def _stable_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable_json_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_stable_json_value(item) for item in value]
    return value


def pipeline_state_to_dict(state: PipelineState) -> dict[str, Any]:
    payload = asdict(state)
    payload["provenance_types"] = [p.value for p in state.provenance_types]
    payload["confidence_decision"] = state.confidence_decision.to_dict()
    payload["invariant_decisions"] = state.invariant_decisions.to_dict()
    payload["alignment_decision"] = state.alignment_decision.to_dict()
    payload["response_plan"] = state.response_plan.to_dict()
    payload["candidate_facts"] = state.candidate_facts.to_dict()
    payload["resolved_context"] = state.resolved_context.to_dict()
    payload["evidence_bundle"] = state.evidence_bundle.to_dict()
    payload["policy_decision"] = state.policy_decision.to_dict()
    payload["validation_result"] = state.validation_result.to_dict()
    payload["render_output"] = state.render_output.to_dict()
    payload["commit_receipt"] = state.commit_receipt.to_dict()
    payload["same_turn_exclusion"] = state.same_turn_exclusion.to_dict()
    payload["pending_repair"] = state.pending_repair.to_dict()
    payload["pending_clarification"] = state.pending_clarification.to_dict()
    return _stable_json_value(payload)


def append_pipeline_snapshot(
    stage: str,
    state: PipelineState,
    *,
    log_path: Path = Path("./logs/session.jsonl"),
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utc_now_iso(),
        "event": "pipeline_state_snapshot",
        "schema_version": PIPELINE_SNAPSHOT_SCHEMA_VERSION,
        "stage": stage,
        "state": pipeline_state_to_dict(state),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
