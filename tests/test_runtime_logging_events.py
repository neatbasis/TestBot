from __future__ import annotations

from collections import deque
import json
from dataclasses import replace

import arrow
import pytest
from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot.pipeline_state import AlignmentDecision
from testbot.pipeline_state import CandidateHit
from testbot import sat_chatbot_memory_v2 as runtime
from testbot.context_resolution import ContinuityPosture, ResolvedContext
from testbot.intent_router import IntentType, classify_intent
from testbot.policy_decision import DecisionClass, DecisionObject, EvidencePosture, decide
from testbot.sat_chatbot_memory_v2 import (
    ASSIST_ALTERNATIVES_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    CapabilitySnapshot,
    RuntimeCapabilityStatus,
    _derive_response_blocker_reason,
    _ambiguity_score,
    _intent_label,
    _run_chat_loop,
    _user_followup_signal_proxy,
    build_provenance_metadata,
    generate_reflection_yaml,
    run_canonical_answer_stage_flow,
    stage_rewrite_query,
)


class _FixedClock:
    def now(self) -> arrow.Arrow:
        return arrow.get("2026-03-10T11:00:00+00:00")


_FIXED_CLOCK = _FixedClock()


class _ExplodingLLM:
    def __init__(self, message: str = "boom") -> None:
        self._message = message

    def invoke(self, _msgs):
        raise RuntimeError(self._message)


class _StaticLLM:
    def __init__(self, content: str) -> None:
        self.content = content

    def invoke(self, _msgs):
        return type("_Resp", (), {"content": self.content})()




def test_stage_retrieve_passes_hygiene_exclusions_and_blocks_same_turn_candidates() -> None:
    class _FilteringStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k
            docs = [
                Document(id="turn-user", page_content="latest", metadata={"doc_id": "turn-user"}),
                Document(id="turn-reflection", page_content="reflection", metadata={"doc_id": "turn-reflection", "source_doc_id": "turn-user"}),
                Document(id="older-memory", page_content="older", metadata={"doc_id": "older-memory"}),
            ]
            excluded_docs = set(kwargs.get("exclude_doc_ids") or set())
            excluded_sources = set(kwargs.get("exclude_source_ids") or set())
            excluded_turn = set(kwargs.get("exclude_turn_scoped_ids") or set())
            kept = []
            for doc in docs:
                source = str(doc.metadata.get("source_doc_id") or "")
                if doc.id in excluded_docs:
                    continue
                if source and source in excluded_sources:
                    continue
                if doc.id in excluded_turn or source in excluded_turn:
                    continue
                kept.append((doc, 0.9))
            return kept

    state = PipelineState(user_input="what did i just say", rewritten_query="latest memory")
    updated_state, docs_and_scores = runtime.stage_retrieve(
        _FilteringStore(),
        state,
        exclude_doc_ids={"turn-user", "turn-reflection"},
        exclude_source_ids={"turn-user"},
        exclude_turn_scoped_ids={"turn-user", "turn-reflection"},
    )

    assert [doc.id for doc, _score in docs_and_scores] == ["older-memory"]
    assert [candidate.doc_id for candidate in updated_state.retrieval_candidates] == ["older-memory"]
    assert updated_state.confidence_decision["retrieval_exclude_doc_ids"] == ["turn-reflection", "turn-user"]
    assert updated_state.confidence_decision["retrieval_exclusion_invariant"] == "retrieve_stage_primary"

def test_stage_rewrite_query_invoke_failure_falls_back_and_logs(monkeypatch) -> None:
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)

    state = PipelineState(user_input="what did i say last week?")

    rewritten = stage_rewrite_query(_ExplodingLLM("rewrite down"), state)

    assert rewritten.rewritten_query == state.user_input
    assert events
    assert events[0][0] == "query_rewrite_failed"
    assert events[0][1]["error_class"] == "RuntimeError"
    assert "rewrite down" in events[0][1]["error_message"]




def test_stage_rewrite_query_self_identification_preserves_original_user_declaration() -> None:
    class _AssistantFocusedRewriteLLM:
        def invoke(self, _msgs):
            return type("_Resp", (), {"content": "What is your name?"})()

    state = PipelineState(user_input="I'm Taylor")

    rewritten = stage_rewrite_query(_AssistantFocusedRewriteLLM(), state)

    assert rewritten.rewritten_query == "I'm Taylor"


def test_stage_rewrite_query_self_identification_guard_skips_llm_invoke() -> None:
    class _FailIfInvokedLLM:
        def invoke(self, _msgs):
            raise AssertionError("rewrite LLM should not be invoked for self-identification declarations")

    state = PipelineState(user_input="My name is Jordan")

    rewritten = stage_rewrite_query(_FailIfInvokedLLM(), state)

    assert rewritten.rewritten_query == "My name is Jordan"

def test_run_canonical_answer_stage_flow_invoke_failure_uses_deterministic_fallback_and_logs(monkeypatch) -> None:
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "decide_fallback_action", lambda **_: "ANSWER_GENERAL_KNOWLEDGE")

    state = PipelineState(
        user_input="what happened yesterday?",
        confidence_decision={"context_confident": True, "ambiguity_detected": False},
    )

    answered = run_canonical_answer_stage_flow(
        _ExplodingLLM("answer down"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.draft_answer == ""
    assert answered.final_answer == ASSIST_ALTERNATIVES_ANSWER
    assert events
    assert events[0][0] == "answer_generation_failed"
    assert events[0][1]["error_class"] == "RuntimeError"
    assert events[0][1]["fallback_action"] == "ANSWER_GENERAL_KNOWLEDGE"


def test_run_canonical_answer_stage_flow_seeded_store_honors_retrieval_exclusions_for_same_turn_and_synthetic_hits(monkeypatch) -> None:
    captured_doc_ids: list[str] = []

    def _stub_pipeline(**kwargs):
        docs_and_scores = kwargs["store"].similarity_search_with_score(
            "q",
            k=18,
            exclude_doc_ids={"turn-user"},
            exclude_source_ids={"turn-user"},
            exclude_turn_scoped_ids={"turn-user"},
        )
        captured_doc_ids.extend(str(doc.id or "") for doc, _score in docs_and_scores)
        return kwargs["state"], []

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _stub_pipeline)
    state = PipelineState(
        user_input="what did i just say?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={"context_confident": True, "ambiguity_detected": False},
    )
    hits = [
        Document(
            id="turn-user",
            page_content="turn-local utterance snapshot",
            metadata={"doc_id": "turn-user", "turn_doc_id": "turn-user"},
        ),
        Document(
            id="seeded-snapshot",
            page_content="serialized pipeline snapshot artifact",
            metadata={"doc_id": "seeded-snapshot", "pipeline_state_snapshot": True},
        ),
        Document(
            id="older-memory",
            page_content="Earlier memory: you asked about release notes.",
            metadata={"doc_id": "older-memory", "ts": "2026-03-09T12:00:00Z"},
        ),
    ]

    _ = run_canonical_answer_stage_flow(
        _StaticLLM("ignored"),
        state,
        chat_history=deque(),
        hits=hits,
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert captured_doc_ids == ["older-memory"]


def test_generate_reflection_yaml_invoke_failure_returns_minimal_yaml_and_logs(monkeypatch) -> None:
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))

    reflection = generate_reflection_yaml(_ExplodingLLM("reflect down"), speaker="user", text="i might be wrong")

    assert reflection == (
        "claims: []\ncommitments: []\npreferences: []\nuncertainties: []\nfollowups: []\nconfidence: 0.2"
    )
    assert events
    assert events[0][0] == "reflection_generation_failed"
    assert events[0][1]["error_class"] == "RuntimeError"
    assert "reflect down" in events[0][1]["error_message"]


def test_intent_classified_log_contains_bandit_fields() -> None:
    intent = _intent_label(IntentType.MEMORY_RECALL)
    ambiguity_score = _ambiguity_score(
        {
            "scored_candidates": [
                {"doc_id": "d1", "final_score": 0.8},
                {"doc_id": "d2", "final_score": 0.76},
            ]
        }
    )

    row = {
        "intent": intent,
        "ambiguity_score": ambiguity_score,
        "user_followup_signal_proxy": round(ambiguity_score, 4),
    }

    assert row["intent"] == "memory_recall"
    assert row["ambiguity_score"] == 0.95
    assert 0.0 <= row["user_followup_signal_proxy"] <= 1.0


def test_fallback_action_selected_log_contains_bandit_fields() -> None:
    ambiguity_score = _ambiguity_score(
        {
            "scored_candidates": [
                {"doc_id": "d1", "final_score": 0.7},
                {"doc_id": "d2", "final_score": 0.1},
            ]
        }
    )

    row = {
        "intent": "memory_recall",
        "ambiguity_score": ambiguity_score,
        "chosen_action": "ASK_CLARIFYING_QUESTION",
        "user_followup_signal_proxy": _user_followup_signal_proxy(
            final_answer="Can you clarify which memory and time window you mean?",
            fallback_action="ASK_CLARIFYING_QUESTION",
            ambiguity_score=ambiguity_score,
        ),
    }

    assert row["chosen_action"] == "ASK_CLARIFYING_QUESTION"
    assert 0.0 <= row["ambiguity_score"] <= 1.0
    assert row["user_followup_signal_proxy"] == 1.0


def test_provenance_summary_log_contains_bandit_and_provenance_fields() -> None:
    ambiguity_score = _ambiguity_score({"scored_candidates": []})
    row = {
        "intent": "knowledge_question",
        "ambiguity_score": ambiguity_score,
        "chosen_action": "NONE",
        "user_followup_signal_proxy": _user_followup_signal_proxy(
            final_answer="A grounded answer with citation doc_id: abc, ts: 2026-01-01T00:00:00Z",
            fallback_action="NONE",
            ambiguity_score=ambiguity_score,
        ),
        "provenance_types": ["memory"],
        "used_memory_refs": [{"doc_id": "abc", "ts": "2026-01-01T00:00:00Z"}],
        "used_source_evidence_refs": ["src-1"],
        "source_evidence_attribution": [
            {
                "doc_id": "src-1",
                "source_type": "calendar",
                "source_uri": "calendar://work/event-1",
                "retrieved_at": "2026-01-01T00:00:00Z",
                "trust_tier": "high",
            }
        ],
    }

    assert row["ambiguity_score"] == 0.0
    assert row["provenance_types"] == ["memory"]
    assert row["used_memory_refs"][0]["doc_id"] == "abc"
    assert row["used_source_evidence_refs"] == ["src-1"]
    assert row["source_evidence_attribution"][0]["source_uri"] == "calendar://work/event-1"




def test_build_provenance_metadata_mixed_memory_and_source_mentions_both_in_basis() -> None:
    hits = [
        Document(
            id="mem-1",
            page_content="memory fragment",
            metadata={"doc_id": "mem-1", "ts": "2026-03-10T09:00:00Z", "type": "user_utterance"},
        ),
        Document(
            id="src-1",
            page_content="source evidence",
            metadata={
                "doc_id": "src-1",
                "type": "source_evidence",
                "source_type": "calendar",
                "source_uri": "calendar://work/event-1",
                "retrieved_at": "2026-03-10T09:05:00Z",
                "trust_tier": "high",
            },
        ),
    ]

    provenance_types, _claims, basis_statement, used_memory_refs, used_source_refs, source_attr = build_provenance_metadata(
        final_answer="Memory-backed answer (doc_id: mem-1, ts: 2026-03-10T09:00:00Z)",
        hits=hits,
        chat_history=deque([{"role": "user", "content": "what about the meeting?"}]),
        packed_history=runtime.pack_chat_history([{"role": "user", "content": "what about the meeting?"}]),
    )

    assert used_memory_refs == ["mem-1@2026-03-10T09:00:00Z"]
    assert used_source_refs == ["src-1"]
    assert source_attr and source_attr[0]["source_uri"] == "calendar://work/event-1"
    assert any(p.value == "MEMORY" for p in provenance_types)
    assert "memory context and source evidence documents" in basis_statement.lower()

def test_run_canonical_answer_stage_flow_non_memory_without_ambiguity_does_not_emit_memory_fragment_clarifier(monkeypatch) -> None:
    monkeypatch.setattr(runtime, "decide_fallback_action", lambda **_: "ANSWER_GENERAL_KNOWLEDGE")

    state = PipelineState(
        user_input="What is ontology?",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "general_knowledge_confidence": 0.95,
            "general_knowledge_support": 3,
            "retrieval_branch": "direct_answer",
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("General definition (not from your memory): Ontology is a model of concepts and relations (doc_id: gk-1, ts: 2026-01-01T00:00:00Z)."),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer.startswith("General definition (not from your memory):")
    assert not answered.final_answer.startswith("I found related memory fragments (")
    assert answered.confidence_decision.get("ambiguity_detected") is False


def test_policy_decision_routes_definitional_knowledge_question_to_memory_retrieval() -> None:
    decision = decide(utterance="What is ontology?", intent=IntentType.KNOWLEDGE_QUESTION)

    assert decision.retrieval_branch == "memory_retrieval"
    assert decision.evidence_posture is EvidencePosture.EMPTY_EVIDENCE


def test_policy_decision_routes_conversational_prompt_to_direct_answer() -> None:
    decision = decide(utterance="hello there", intent=IntentType.META_CONVERSATION)

    assert decision.retrieval_branch == "direct_answer"
    assert decision.evidence_posture is EvidencePosture.NOT_REQUESTED


def test_policy_decision_distinguishes_empty_evidence_and_scored_empty() -> None:
    empty_evidence = decide(
        utterance="what is ontology?",
        intent=IntentType.KNOWLEDGE_QUESTION,
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    scored_empty = decide(
        utterance="what is ontology?",
        intent=IntentType.KNOWLEDGE_QUESTION,
        retrieval_candidates_considered=3,
        hit_count=0,
    )

    assert empty_evidence.evidence_posture is EvidencePosture.EMPTY_EVIDENCE
    assert scored_empty.evidence_posture is EvidencePosture.SCORED_EMPTY


def test_chat_loop_definitional_question_attempts_retrieval_and_does_not_mark_skipped(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "stage_rewrite_query", lambda _llm, state: replace(state, rewritten_query="ontology definition"))
    monkeypatch.setattr(runtime, "stage_retrieve", lambda _store, state, **kwargs: (replace(state, retrieval_candidates=[]), []))
    monkeypatch.setattr(
        runtime,
        "stage_rerank",
        lambda state, docs_and_scores, **kwargs: (  # noqa: ARG005
            replace(state, reranked_hits=[], confidence_decision={"context_confident": False, "ambiguity_detected": False}),
            [],
        ),
    )
    monkeypatch.setattr(
        runtime,
        "run_canonical_answer_stage_flow",
        lambda _llm, state, **kwargs: replace(  # noqa: ARG005
            state,
            final_answer="General definition (not from your memory): Ontology is a model of concepts and relationships.",
            invariant_decisions={"fallback_action": "ANSWER_GENERAL_KNOWLEDGE", "answer_mode": "assist"},
            provenance_types=[],
            basis_statement="General-knowledge basis",
            claims=[],
        ),
    )

    prompts = iter(["What is ontology?", "stop"])
    _run_chat_loop(
        llm=_StaticLLM("ignored"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    branch_payload = next(payload for event, payload in events if event == "retrieval_branch_selected")
    retrieval_payload = next(payload for event, payload in events if event == "retrieval_candidates")

    assert branch_payload["retrieval_branch"] == "memory_retrieval"
    assert retrieval_payload.get("skipped") is not True
    assert "retry" not in retrieval_payload


def test_chat_loop_conversational_prompt_skips_knowledge_retrieval_path(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        runtime,
        "run_canonical_answer_stage_flow",
        lambda _llm, state, **kwargs: replace(  # noqa: ARG005
            state,
            final_answer="Hi!",
            invariant_decisions={"fallback_action": "NONE", "answer_mode": "assist"},
            provenance_types=[],
            basis_statement="none",
            claims=[],
        ),
    )

    prompts = iter(["hello there", "stop"])
    _run_chat_loop(
        llm=_StaticLLM("ignored"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    branch_payload = next(payload for event, payload in events if event == "retrieval_branch_selected")
    retrieval_payload = next(payload for event, payload in events if event == "retrieval_candidates")

    assert branch_payload["retrieval_branch"] == "direct_answer"
    assert retrieval_payload.get("skipped") is True
    assert "retry" not in retrieval_payload


def test_run_canonical_answer_stage_flow_low_source_confidence_non_memory_uses_safe_unknowing_mode_legacy_assertions() -> None:
    state = PipelineState(
        user_input="What happened in my calendar?",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
            "source_confidence": 0.2,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("ignored"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    assert answered.invariant_decisions.get("fallback_action") == "ANSWER_UNKNOWN"
    assert answered.invariant_decisions.get("answer_mode") == "dont-know"




def test_run_canonical_answer_stage_flow_greeting_command_preserves_social_draft_answer() -> None:
    state = PipelineState(
        user_input="say hello",
        resolved_intent=IntentType.CONTROL.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "general_knowledge_confidence": 0.0,
            "general_knowledge_support": 0,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("Hello! Nice to meet you."),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == "Hello! Nice to meet you."
    assert answered.invariant_decisions.get("answer_mode") == "assist"


def test_run_canonical_answer_stage_flow_low_source_confidence_non_memory_uses_uncertainty_response() -> None:
    state = PipelineState(
        user_input="What happened in my calendar?",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
            "source_confidence": 0.2,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("ignored"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    assert answered.invariant_decisions.get("fallback_action") == "ANSWER_UNKNOWN"
    assert answered.invariant_decisions.get("answer_mode") == "dont-know"


def test_run_canonical_answer_stage_flow_self_introduction_preserves_acknowledgement_draft() -> None:
    state = PipelineState(
        user_input="my name is taylor",
        resolved_intent=IntentType.META_CONVERSATION.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "general_knowledge_confidence": 0.0,
            "general_knowledge_support": 0,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("Thanks, Taylor — I'll remember that for this conversation."),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == "Thanks, Taylor — I'll remember that for this conversation."
    assert answered.invariant_decisions.get("answer_mode") == "assist"


def test_run_canonical_answer_stage_flow_regression_say_hello_keeps_greeting_instead_of_memory_fallback() -> None:
    state = PipelineState(
        user_input="say hello",
        resolved_intent=IntentType.CONTROL.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "general_knowledge_confidence": 0.0,
            "general_knowledge_support": 0,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("hello"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == "hello"
    assert "reliable memory" not in answered.final_answer.lower()


def test_run_canonical_answer_stage_flow_memory_recall_confident_hit_recovers_from_contract_failure() -> None:
    state = PipelineState(
        user_input="what did i note about release prep?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("It should be fine."),
        state,
        chat_history=deque(),
        hits=[
            Document(
                page_content="You noted that release prep requires changelog review before tagging.",
                metadata={"doc_id": "mem-7", "ts": "2026-03-01T12:00:00Z"},
            )
        ],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer != ASSIST_ALTERNATIVES_ANSWER
    assert "From memory, I found:" in answered.final_answer
    assert "doc_id: mem-7" in answered.final_answer
    assert "ts: 2026-03-01T12:00:00Z" in answered.final_answer
    assert answered.invariant_decisions.get("answer_mode") == "memory-grounded"

def test_response_blocker_reason_for_answer_unknown_reports_insufficient_reliable_memory() -> None:
    assert _derive_response_blocker_reason(
        answer_mode="assist",
        fallback_action="ANSWER_UNKNOWN",
        context_confident=False,
        hit_count=0,
        ambiguity_detected=False,
        answer_contract_valid=True,
        general_knowledge_contract_valid=True,
    ) == "insufficient reliable memory to answer directly"

def test_chat_loop_debug_trace_logs_structured_payload_for_queryable_policy_fields(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "stage_rewrite_query", lambda _llm, state: replace(state, rewritten_query="release memory"))
    monkeypatch.setattr(runtime, "stage_retrieve", lambda _store, state, **kwargs: (replace(state, retrieval_candidates=[]), []))
    monkeypatch.setattr(
        runtime,
        "stage_rerank",
        lambda state, docs_and_scores, **kwargs: (  # noqa: ARG005
            replace(
                state,
                reranked_hits=[],
                confidence_decision={
                    **state.confidence_decision,
                    "context_confident": False,
                    "ambiguity_detected": False,
                    "retrieval_branch": "memory_retrieval",
                    "top_final_score_min": 0.9,
                    "min_margin_to_second": 0.05,
                    "scored_candidates": [{"final_score": 0.88}, {"final_score": 0.87}],
                },
            ),
            [],
        ),
    )
    monkeypatch.setattr(
        runtime,
        "run_canonical_answer_stage_flow",
        lambda _llm, state, **kwargs: replace(  # noqa: ARG005
            state,
            final_answer=ASSIST_ALTERNATIVES_ANSWER,
            invariant_decisions={
                "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
                "answer_mode": "assist",
                "answer_contract_valid": False,
                "general_knowledge_contract_valid": True,
            },
            provenance_types=[],
            basis_statement="none",
            claims=[],
        ),
    )

    prompts = iter(["what did I say about release prep", "stop"])
    _run_chat_loop(
        llm=_StaticLLM("ignored"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=True,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    debug_event = next(payload for event, payload in events if event == "debug_turn_trace")
    assert "trace" in debug_event
    assert isinstance(debug_event["trace"], str)
    assert "payload" in debug_event

    debug_intent = debug_event["payload"]["debug.intent"]
    assert debug_intent["classified"] == "memory_recall"
    assert debug_intent["predicted"] == "memory_recall"
    assert debug_intent["confidence"] is not None
    assert debug_intent["threshold"] is not None
    assert debug_intent["confidence"] > 0.0
    assert debug_intent["threshold"] > 0.0

    policy = debug_event["payload"]["debug.policy"]
    assert policy["reject_code"] == "NO_CITABLE_MEMORY_EVIDENCE"
    assert policy["fallback_reason"] in {
        "memory_recall_no_confident_hit",
        "ambiguous_memory_candidates_without_ask",
    }
    assert policy["counterfactuals"]["alternate_routing_policy_checks"] == {
        "ask_clarifying_question_passes": False,
        "route_to_ask_passes": False,
    }
    assert debug_event["payload"]["debug.confidence"]["context_confident_gate"]["passed"] is False
    assert debug_event["payload"]["debug.rerank"]["margin_gate"]["passed"] is False


def test_chat_loop_alignment_decision_event_writes_json_safe_session_log(tmp_path, monkeypatch) -> None:
    session_log = tmp_path / "session.jsonl"

    original_append_session_log = runtime.append_session_log

    def _append_to_tmp_log(event: str, payload: dict, *, log_path=None):  # noqa: ARG001
        original_append_session_log(event, payload, log_path=session_log)

    monkeypatch.setattr(runtime, "append_session_log", _append_to_tmp_log)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "stage_rewrite_query", lambda _llm, state: replace(state, rewritten_query="release prep notes"))
    monkeypatch.setattr(runtime, "stage_retrieve", lambda _store, state, **kwargs: (replace(state, retrieval_candidates=[]), []))
    monkeypatch.setattr(
        runtime,
        "stage_rerank",
        lambda state, docs_and_scores, **kwargs: (replace(state, reranked_hits=[]), []),  # noqa: ARG005
    )
    monkeypatch.setattr(
        runtime,
        "run_canonical_answer_stage_flow",
        lambda _llm, state, **kwargs: replace(  # noqa: ARG005
            state,
            final_answer="From memory, I found: release prep includes changelog checks.",
            invariant_decisions={"fallback_action": "NONE", "answer_mode": "memory-grounded"},
            provenance_types=[],
            basis_statement="Memory-grounded basis.",
            claims=["release prep includes changelog checks"],
        ),
    )

    prompts = iter(["what did i note about release prep?", "stop"])
    replies: list[str] = []

    _run_chat_loop(
        llm=_StaticLLM("From memory, I found: release prep includes changelog checks."),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
    )

    log_rows = [json.loads(line) for line in session_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert replies
    assert any(row.get("event") == "alignment_decision_evaluated" for row in log_rows)

    alignment_row = next(row for row in log_rows if row.get("event") == "alignment_decision_evaluated")
    assert isinstance(alignment_row["alignment_decision"], dict)
    assert isinstance(alignment_row["alignment_dimensions"], dict)



def test_chat_loop_intent_telemetry_uses_resolved_state_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])

    prompts = iter(["hello there", "stop"])

    _run_chat_loop(
        llm=_StaticLLM("hi"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    intent_rows = [
        row
        for row in rows
        if row.get("event")
        in {
            "retrieval_branch_selected",
            "intent_classified",
            "fallback_action_selected",
            "provenance_summary",
            "alignment_decision_evaluated",
            "rerank_skipped",
        }
    ]

    assert intent_rows
    for row in intent_rows:
        assert row["intent"] == row["intent_resolved"]
        assert row["intent_classified"]


def test_append_session_log_accepts_alignment_decision_artifact_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    alignment_decision = AlignmentDecision(
        final_alignment_decision="allow",
        dimensions={"safety": 0.95, "citation_validity": 0.9},
    )

    runtime.append_session_log(
        "alignment_decision_evaluated",
        {
            "alignment_decision": alignment_decision,
            "alignment_dimensions": alignment_decision.dimensions,
        },
    )

    session_log = tmp_path / "logs" / "session.jsonl"
    rows = [json.loads(line) for line in session_log.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(rows) == 1
    assert rows[0]["event"] == "alignment_decision_evaluated"
    assert rows[0]["alignment_decision"]["final_alignment_decision"] == "allow"
    assert rows[0]["alignment_decision"]["dimensions"]["safety"] == 0.95


def test_chat_loop_cli_turn_logs_jsonl_with_alignment_decision_object(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "stage_rewrite_query", lambda _llm, state: replace(state, rewritten_query="release prep notes"))
    monkeypatch.setattr(runtime, "stage_retrieve", lambda _store, state, **kwargs: (replace(state, retrieval_candidates=[]), []))
    monkeypatch.setattr(
        runtime,
        "stage_rerank",
        lambda state, docs_and_scores, **kwargs: (replace(state, reranked_hits=[]), []),  # noqa: ARG005
    )
    monkeypatch.setattr(
        runtime,
        "run_canonical_answer_stage_flow",
        lambda _llm, state, **kwargs: replace(  # noqa: ARG005
            state,
            final_answer="From memory, I found: release prep includes changelog checks.",
            invariant_decisions={"fallback_action": "NONE", "answer_mode": "memory-grounded"},
            provenance_types=[],
            basis_statement="Memory-grounded basis.",
            claims=["release prep includes changelog checks"],
            alignment_decision=AlignmentDecision(
                final_alignment_decision="allow",
                dimensions={"safety": 0.92, "factual_grounding": 0.88},
            ),
        ),
    )

    prompts = iter(["what did i note about release prep?", "stop"])
    replies: list[str] = []

    _run_chat_loop(
        llm=_StaticLLM("From memory, I found: release prep includes changelog checks."),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
    )

    session_log = tmp_path / "logs" / "session.jsonl"
    rows = [json.loads(line) for line in session_log.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert replies
    assert rows

    alignment_row = next(row for row in rows if row.get("event") == "alignment_decision_evaluated")
    assert isinstance(alignment_row["alignment_decision"], dict)
    assert set(alignment_row["alignment_decision"]).issuperset({"final_alignment_decision", "dimensions"})
    assert alignment_row["alignment_decision"]["final_alignment_decision"] == "allow"


def test_chat_loop_logs_commit_stage_record_with_durable_commit_state(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "stage_rewrite_query", lambda _llm, state: replace(state, rewritten_query="self facts"))
    monkeypatch.setattr(runtime, "stage_retrieve", lambda _store, state, **kwargs: (replace(state, retrieval_candidates=[]), []))
    monkeypatch.setattr(runtime, "stage_rerank", lambda state, docs_and_scores, **kwargs: (replace(state, reranked_hits=[]), []))
    monkeypatch.setattr(
        runtime,
        "run_canonical_answer_stage_flow",
        lambda _llm, state, **kwargs: replace(  # noqa: ARG005
            state,
            final_answer="From memory, your name is Sam.",
            invariant_decisions={"fallback_action": "NONE", "answer_mode": "memory-grounded"},
            claims=["name=Sam"],
            basis_statement="Memory-backed basis",
        ),
    )

    prompts = iter(["what did i say?", "stop"])
    replies: list[str] = []
    _run_chat_loop(
        llm=_StaticLLM("From memory, your name is Sam."),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    commit_row = next(row for row in rows if row.get("event") == "commit_stage_recorded")
    assert commit_row["stage"] == "answer.commit"
    assert commit_row["pipeline_state_snapshot"] == "recorded"
    assert isinstance(commit_row["pending_repair_state"], dict)
    assert isinstance(commit_row["resolved_obligations"], list)
    assert isinstance(commit_row["remaining_obligations"], list)
    assert isinstance(commit_row["confirmed_user_facts"], list)


def test_chat_loop_identity_recall_after_self_identification_forces_retrieval_and_rerank(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "stage_rewrite_query", lambda _llm, state: replace(state, rewritten_query=state.user_input))

    retrieve_calls: list[str] = []
    rerank_calls: list[str] = []

    def _stage_retrieve_identity(_store, state, **kwargs):
        retrieve_calls.append(state.user_input)
        del kwargs
        doc = Document(
            id="identity-sebastian",
            page_content="name=sebastian",
            metadata={"doc_id": "identity-sebastian", "type": "profile_fact"},
        )
        next_state = replace(
            state,
            retrieval_candidates=[CandidateHit(doc_id="identity-sebastian", score=0.99, card_type="profile_fact")],
            confidence_decision={
                **state.confidence_decision,
                "retrieval_candidates_considered": 1,
                "context_confident": True,
                "ambiguity_detected": False,
            },
        )
        return next_state, [(doc, 0.99)]

    def _stage_rerank_identity(state, docs_and_scores, **kwargs):
        rerank_calls.append(state.user_input)
        del kwargs
        hit_doc = docs_and_scores[0][0]
        next_state = replace(
            state,
            reranked_hits=[CandidateHit(doc_id=str(hit_doc.id), score=0.99, card_type="profile_fact")],
            confidence_decision={**state.confidence_decision, "context_confident": True, "ambiguity_detected": False},
        )
        return next_state, [hit_doc]

    monkeypatch.setattr(runtime, "stage_retrieve", _stage_retrieve_identity)
    monkeypatch.setattr(runtime, "stage_rerank", _stage_rerank_identity)
    monkeypatch.setattr(
        runtime,
        "run_canonical_answer_stage_flow",
        lambda _llm, state, **kwargs: replace(
            state,
            draft_answer="Memory answer",
            final_answer="From memory, your name is Sebastian.",
            claims=["name=sebastian"],
            basis_statement="identity continuity retrieval",
        ),
    )

    prompts = iter(["Hi! I'm sebastian", "Who am I?", "stop"])
    replies: list[str] = []
    _run_chat_loop(
        llm=_StaticLLM("From memory, your name is Sebastian."),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert replies
    assert retrieve_calls == ["Who am I?"]
    assert rerank_calls == ["Who am I?"]

    branch_rows = [row for row in rows if row.get("event") == "retrieval_branch_selected"]
    assert len(branch_rows) == 2
    assert branch_rows[0]["retrieval_branch"] == "direct_answer"
    assert branch_rows[1]["retrieval_branch"] == "memory_retrieval"
    assert branch_rows[1]["guard_forced_memory_retrieval"] is True

    retrieval_rows = [row for row in rows if row.get("event") == "retrieval_candidates"]
    assert retrieval_rows[0].get("skipped") is True
    assert retrieval_rows[1].get("skipped") is not True

    rerank_skipped_for_turn_two = [
        row
        for row in rows
        if row.get("event") == "rerank_skipped" and row.get("utterance") == "Who am I?"
    ]
    assert rerank_skipped_for_turn_two == []


def test_chat_loop_two_turn_commit_continuity_is_consumed_by_context_and_retrieval(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "stage_rewrite_query", lambda _llm, state: replace(state, rewritten_query=state.user_input))

    context_calls: list[PipelineState | None] = []
    continuity_anchor: str = ""

    def _resolve_context_with_commit_anchor(*, utterance: str, prior_pipeline_state: PipelineState | None) -> ResolvedContext:
        nonlocal continuity_anchor
        del utterance
        context_calls.append(prior_pipeline_state)
        if prior_pipeline_state is None:
            return ResolvedContext(history_anchors=(), ambiguity_flags=(), continuity_posture=ContinuityPosture.REEVALUATE, prior_intent=None)

        commit_receipt = prior_pipeline_state.commit_receipt
        prior_facts = list(commit_receipt.get("confirmed_user_facts", []))
        assert prior_facts == ["name=Sam"]
        assert commit_receipt.get("pending_repair_state") == {"repair_required_by_policy": False, "repair_offered_to_user": False, "reason": "none"}
        assert commit_receipt.get("resolved_obligations") == ["repair_state_not_required"]
        continuity_anchor = f"commit.confirmed_user_facts:{prior_facts[0]}"
        return ResolvedContext(
            history_anchors=(continuity_anchor,),
            ambiguity_flags=(),
            continuity_posture=ContinuityPosture.REEVALUATE,
            prior_intent=IntentType.MEMORY_RECALL,
        )

    monkeypatch.setattr(runtime, "resolve_context", _resolve_context_with_commit_anchor)

    def _stage_retrieve_with_continuity(_store, state, **kwargs):
        del kwargs
        if state.user_input == "what did i say my name is?":
            assert continuity_anchor == ""
            doc = Document(id="name-fact-initial", page_content="name=Sam", metadata={"doc_id": "name-fact-initial", "type": "profile_fact"})
        else:
            assert continuity_anchor == "commit.confirmed_user_facts:name=Sam"
            doc = Document(id="name-fact-continuity", page_content="name=Sam", metadata={"doc_id": "name-fact-continuity", "type": "profile_fact", "source_doc_id": "name-fact-initial"})
        next_state = replace(
            state,
            retrieval_candidates=[CandidateHit(doc_id=str(doc.id), score=0.99, card_type="profile_fact")],
            confidence_decision={**state.confidence_decision, "retrieval_candidates_considered": 1, "context_confident": True, "ambiguity_detected": False},
        )
        return next_state, [(doc, 0.99)]

    monkeypatch.setattr(runtime, "stage_retrieve", _stage_retrieve_with_continuity)
    monkeypatch.setattr(runtime, "stage_rerank", lambda state, docs_and_scores, **kwargs: (replace(state, reranked_hits=[CandidateHit(doc_id=str(docs_and_scores[0][0].id), score=0.99, card_type="profile_fact")], confidence_decision={**state.confidence_decision, "context_confident": True, "ambiguity_detected": False}), [docs_and_scores[0][0]]))
    monkeypatch.setattr(runtime, "run_canonical_answer_stage_flow", lambda _llm, state, **kwargs: replace(state, draft_answer="Memory answer", final_answer="From committed facts, your name is Sam.", claims=["name=Sam"], basis_statement="prior commit continuity"))

    prompts = iter(["what did i say my name is?", "what did i say my name is again?", "stop"])
    replies: list[str] = []
    _run_chat_loop(
        llm=_StaticLLM("From committed facts, your name is Sam."),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    commit_rows = [row for row in rows if row.get("event") == "commit_stage_recorded"]
    assert len(commit_rows) == 2
    for commit_row in commit_rows:
        assert commit_row["stage"] == "answer.commit"
        assert commit_row["pending_repair_state"] == {"repair_required_by_policy": False, "repair_offered_to_user": False, "reason": "none"}
        assert commit_row["resolved_obligations"] == ["repair_state_not_required"]
        assert commit_row["confirmed_user_facts"] == ["name=Sam"]

    assert commit_rows[0]["retrieval_continuity_evidence"] == []
    assert commit_rows[1]["retrieval_continuity_evidence"] == ["commit.confirmed_user_facts:name=Sam"]

    branch_rows = [row for row in rows if row.get("event") == "retrieval_branch_selected"]
    assert branch_rows[0]["context_history_anchors"] == []
    assert branch_rows[1]["context_history_anchors"] == ["commit.confirmed_user_facts:name=Sam"]

    retrieval_rows = [row for row in rows if row.get("event") == "retrieval_candidates"]
    assert retrieval_rows[1]["top_candidates"][0]["doc_id"] == "name-fact-continuity"
    assert context_calls[0] is None
    assert context_calls[1] is not None


def test_build_provenance_metadata_sorts_memory_and_source_references_deterministically() -> None:
    hits = [
        Document(id="mem-b", page_content="b", metadata={"doc_id": "mem-b", "ts": "2026-03-10T10:00:00Z", "type": "user_utterance"}),
        Document(id="mem-a", page_content="a", metadata={"doc_id": "mem-a", "ts": "2026-03-10T09:00:00Z", "type": "user_utterance"}),
        Document(id="src-b", page_content="s2", metadata={"doc_id": "src-b", "type": "source_evidence", "source_uri": "calendar://work/event-2", "source_type": "calendar", "retrieved_at": "2026-03-10T11:00:00Z", "trust_tier": "high"}),
        Document(id="src-a", page_content="s1", metadata={"doc_id": "src-a", "type": "source_evidence", "source_uri": "calendar://work/event-1", "source_type": "calendar", "retrieved_at": "2026-03-10T10:30:00Z", "trust_tier": "high"}),
    ]

    _types, _claims, _basis, used_memory_refs, used_source_refs, source_attr = build_provenance_metadata(
        final_answer="Memory-backed answer (doc_id: mem-a, ts: 2026-03-10T09:00:00Z)",
        hits=hits,
        chat_history=deque(),
        packed_history=runtime.pack_chat_history([]),
    )

    assert used_memory_refs == ["mem-a@2026-03-10T09:00:00Z", "mem-b@2026-03-10T10:00:00Z"]
    assert used_source_refs == ["src-a", "src-b"]
    assert [item["doc_id"] for item in source_attr] == ["src-a", "src-b"]




def test_run_canonical_answer_stage_flow_selected_decision_for_note_taking_preserves_direct_answer_contract() -> None:
    state = PipelineState(
        user_input="please make a note that i prefer tea",
        resolved_intent=IntentType.META_CONVERSATION.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("Got it — I can keep that in mind."),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        selected_decision=DecisionObject(
            decision_class=DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
            retrieval_branch="direct_answer",
            rationale="meta conversational memory-write requests stay in direct-answer assist path",
            reasoning={"evidence_posture": "not_requested"},
        ),
        clock=_FIXED_CLOCK,
    )

    assert answered.invariant_decisions.get("fallback_action") == "ANSWER_GENERAL_KNOWLEDGE"
    assert answered.invariant_decisions.get("answer_mode") == "assist"

def test_run_canonical_answer_stage_flow_uses_selected_decision_object_for_memory_action() -> None:
    state = PipelineState(
        user_input="what did i note about release prep?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": True,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("From memory, I found: release prep includes checklist review. doc_id: mem-7, ts: 2026-03-01T12:00:00Z"),
        state,
        chat_history=deque(),
        hits=[
            Document(
                page_content="release prep includes checklist review",
                metadata={"doc_id": "mem-7", "ts": "2026-03-01T12:00:00Z"},
            )
        ],
        capability_status="ask_unavailable",
        selected_decision=DecisionObject(
            decision_class=DecisionClass.ANSWER_FROM_MEMORY,
            retrieval_branch="memory_retrieval",
            rationale="confident evidence bundle supports memory-grounded answer",
            reasoning={"evidence_posture": "scored_non_empty"},
        ),
        clock=_FIXED_CLOCK,
    )

    assert answered.invariant_decisions.get("fallback_action") == "ANSWER_FROM_MEMORY"
    assert answered.final_answer.startswith("From memory, I found:")
    assert answered.invariant_decisions.get("answer_policy_rationale", {}).get("authority") == "decision_object"


def test_run_canonical_answer_stage_flow_selected_decision_clarify_keeps_policy_and_answer_aligned() -> None:
    state = PipelineState(
        user_input="what did i say?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("ignored"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        selected_decision=DecisionObject(
            decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
            retrieval_branch="direct_answer",
            rationale="insufficient evidence requires clarification",
            reasoning={"evidence_posture": "scored_empty"},
        ),
        clock=_FIXED_CLOCK,
    )

    assert answered.invariant_decisions.get("fallback_action") == "ASK_CLARIFYING_QUESTION"
    assert answered.invariant_decisions.get("answer_mode") == "clarify"




def test_run_canonical_answer_stage_flow_selected_decision_pending_lookup_uses_non_clarify_mode() -> None:
    state = PipelineState(
        user_input="what did i say?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "background_ingestion_in_progress": True,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("ignored"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        selected_decision=DecisionObject(
            decision_class=DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION,
            retrieval_branch="memory_retrieval",
            rationale="retrieval required but empty evidence while background ingestion is in progress",
            reasoning={"evidence_posture": "empty_evidence", "background_ingestion_in_progress": True},
        ),
        clock=_FIXED_CLOCK,
    )

    assert answered.invariant_decisions.get("fallback_action") == "ANSWER_UNKNOWN"
    assert answered.invariant_decisions.get("answer_mode") == "assist"




def test_run_canonical_answer_stage_flow_selected_decision_non_memory_clarify_pending_lookup_degrades_to_safe_uncertainty() -> None:
    state = PipelineState(
        user_input="what is dark matter?",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": True,
            "background_ingestion_in_progress": True,
            "allow_non_memory_clarify": False,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("ignored"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        selected_decision=DecisionObject(
            decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
            retrieval_branch="direct_answer",
            rationale="clarify candidate selected despite non-memory intent",
            reasoning={"evidence_posture": "empty_evidence"},
        ),
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    assert answered.invariant_decisions.get("answer_mode") == "assist"
    assert answered.invariant_decisions.get("invariant_degrade_reason") is None




def test_run_canonical_answer_stage_flow_canonical_commit_is_authoritative_for_answer_provenance_and_commit_receipt() -> None:
    state = PipelineState(
        user_input="what did i note about release prep?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("From memory, I found: release prep includes checklist review. doc_id: mem-7, ts: 2026-03-01T12:00:00Z"),
        state,
        chat_history=deque(),
        hits=[
            Document(
                page_content="release prep includes checklist review",
                metadata={"doc_id": "mem-7", "ts": "2026-03-01T12:00:00Z"},
            )
        ],
        capability_status="ask_unavailable",
        selected_decision=DecisionObject(
            decision_class=DecisionClass.ANSWER_FROM_MEMORY,
            retrieval_branch="memory_retrieval",
            rationale="confident evidence bundle supports memory-grounded answer",
            reasoning={"evidence_posture": "scored_non_empty"},
        ),
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer.startswith("From memory, I found:")
    assert answered.used_memory_refs == ["mem-7@2026-03-01T12:00:00Z"]
    assert answered.invariant_decisions.get("fallback_action") == "ANSWER_FROM_MEMORY"
    assert answered.commit_receipt.get("commit_stage") == "answer.commit"
    assert answered.commit_receipt.get("committed") is True

def test_run_canonical_answer_stage_flow_selected_decision_non_memory_clarify_no_clarify_mode_degrades_to_assist() -> None:
    state = PipelineState(
        user_input="tell me a joke",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": True,
            "allow_non_memory_clarify": False,
        },
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("ignored"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        selected_decision=DecisionObject(
            decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
            retrieval_branch="direct_answer",
            rationale="clarify candidate selected despite explicit no-clarify mode",
            reasoning={"evidence_posture": "empty_evidence"},
        ),
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == ASSIST_ALTERNATIVES_ANSWER
    assert answered.invariant_decisions.get("answer_mode") == "assist"
    assert answered.invariant_decisions.get("invariant_degrade_reason") == "non_memory_clarify_no_clarify_mode_degraded"

@pytest.mark.non_contract
def test_chat_loop_async_pending_lookup_commits_pending_answer_and_logs_semantics(tmp_path, monkeypatch) -> None:
    """Non-contract fast path: heavily mocked to keep chat-loop regression checks cheap."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])

    def _start_background_ingest(*, runtime: dict[str, object], store: object, ingestion_request_id: str = "") -> dict[str, object]:
        del store
        runtime["source_ingest_background_in_progress"] = True
        runtime["source_ingest_background_future"] = None
        runtime["source_ingest_background_stub"] = True
        request_id = ingestion_request_id or "stub-ingest-1"
        runtime["source_ingest_background_request_id"] = request_id
        from testbot import sat_chatbot_memory_v2 as runtime_module
        runtime_module.append_session_log("source_ingest_background_started", {"background": True, "ingestion_request_id": request_id})
        return {"started": True, "already_running": False, "ingestion_request_id": request_id}

    monkeypatch.setattr(runtime, "_start_background_source_ingestion", _start_background_ingest)

    class _EmptyStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k, kwargs
            return []

    prompts = iter(["what did i say?", "stop"])
    replies: list[str] = []
    _run_chat_loop(
        runtime={"source_ingest_async_continuation": True},
        llm=_StaticLLM("ignored"),
        store=_EmptyStore(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={"source_ingest_async_continuation": True},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
    )

    assert replies[0] == NON_KNOWLEDGE_UNCERTAINTY_ANSWER

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    events = [row.get("event") for row in rows]
    assert "source_ingest_background_started" in events

    started_row = next(row for row in rows if row.get("event") == "source_ingest_background_started")
    ingestion_request_id = started_row["ingestion_request_id"]

    commit_row = next(row for row in rows if row.get("event") == "commit_stage_recorded")
    assert commit_row["pending_repair_state"]["repair_required_by_policy"] is True
    assert commit_row["pending_repair_state"]["repair_offered_to_user"] is False
    assert commit_row["pending_ingestion_request_id"] != ""
    assert commit_row["pending_ingestion_request_id"] == ingestion_request_id

    retrieval_row = next(row for row in rows if row.get("event") == "retrieval_candidates")
    hygiene = retrieval_row.get("hygiene", {})
    assert ingestion_request_id not in hygiene.get("exclude_doc_ids", [])
    assert ingestion_request_id not in hygiene.get("exclude_source_ids", [])
    assert ingestion_request_id not in hygiene.get("exclude_turn_scoped_ids", [])

    mode_row = next(row for row in rows if row.get("event") == "final_answer_mode")
    assert mode_row["mode"] == "assist"
    assert mode_row["query"] == "ignored"
    assert mode_row["stage_audit_trail"] == list(runtime.CanonicalTurnOrchestrator.STAGE_ORDER)


def test_chat_loop_async_pending_lookup_contract_path_reaches_answer_commit_post(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])

    def _start_background_ingest(*, runtime: dict[str, object], store: object, ingestion_request_id: str = "") -> dict[str, object]:
        del store
        runtime["source_ingest_background_in_progress"] = True
        runtime["source_ingest_background_future"] = None
        runtime["source_ingest_background_stub"] = True
        request_id = ingestion_request_id or "stub-ingest-1"
        runtime["source_ingest_background_request_id"] = request_id
        from testbot import sat_chatbot_memory_v2 as runtime_module

        runtime_module.append_session_log("source_ingest_background_started", {"background": True, "ingestion_request_id": request_id})
        return {"started": True, "already_running": False, "ingestion_request_id": request_id}

    monkeypatch.setattr(runtime, "_start_background_source_ingestion", _start_background_ingest)

    class _EmptyStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k, kwargs
            return []

    prompts = iter(["what did i say?", "stop"])
    replies: list[str] = []
    _run_chat_loop(
        runtime={"source_ingest_async_continuation": True},
        llm=_StaticLLM("ignored"),
        store=_EmptyStore(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={"source_ingest_async_continuation": True},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_FIXED_CLOCK,
    )

    assert replies[0] == NON_KNOWLEDGE_UNCERTAINTY_ANSWER

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    transition_rows = [row for row in rows if row.get("event") == "stage_transition_validation"]
    commit_post_row = next(
        row for row in transition_rows if row.get("stage") == "answer.commit" and row.get("boundary") == "post"
    )
    assert commit_post_row["passed"] is True

    symptom_hits = [
        row
        for row in transition_rows
        if "inv_003_general_knowledge_contract_enforced" in (row.get("failures") or [])
    ]
    assert symptom_hits == []

    commit_row = next(row for row in rows if row.get("event") == "commit_stage_recorded")
    assert commit_row["pending_repair_state"]["repair_required_by_policy"] is True
    assert commit_row["pending_repair_state"]["repair_offered_to_user"] is False
    assert commit_row["pending_ingestion_request_id"] != ""

    mode_row = next(row for row in rows if row.get("event") == "final_answer_mode")
    assert mode_row["mode"] == "assist"
    assert mode_row["query"] == "ignored"



def test_final_answer_mode_stage_audit_trail_includes_answer_commit(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])

    def _start_background_ingest(*, runtime: dict[str, object], store: object, ingestion_request_id: str = "") -> dict[str, object]:
        del store
        runtime["source_ingest_background_in_progress"] = True
        runtime["source_ingest_background_future"] = None
        runtime["source_ingest_background_stub"] = True
        request_id = ingestion_request_id or "stub-ingest-1"
        runtime["source_ingest_background_request_id"] = request_id
        from testbot import sat_chatbot_memory_v2 as runtime_module

        runtime_module.append_session_log("source_ingest_background_started", {"background": True, "ingestion_request_id": request_id})
        return {"started": True, "already_running": False, "ingestion_request_id": request_id}

    monkeypatch.setattr(runtime, "_start_background_source_ingestion", _start_background_ingest)

    class _EmptyStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k, kwargs
            return []

    prompts = iter(["what did i say?", "stop"])
    _run_chat_loop(
        runtime={"source_ingest_async_continuation": True},
        llm=_StaticLLM("ignored"),
        store=_EmptyStore(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={"source_ingest_async_continuation": True},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    mode_row = next(row for row in rows if row.get("event") == "final_answer_mode")

    assert mode_row["stage_audit_trail"] == list(runtime.CanonicalTurnOrchestrator.STAGE_ORDER)


def test_background_ingestion_pending_lifecycle_event_order_and_payloads(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    assistant_messages: list[str] = []

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))

    from concurrent.futures import Future

    completed_future: Future = Future()
    completed_future.set_result(
        {
            "ok": True,
            "status": "completed",
            "payload": {
                "ingestion_request_id": "turn-789",
                "source_type": "calendar",
                "fetched_count": 1,
                "stored_count": 1,
            },
        }
    )

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", lambda **kwargs: (
        replace(
            kwargs["state"],
            final_answer="Your utility bill is due Friday and confirmed by synced source evidence.",
            used_source_evidence_refs=["src-900"],
        ),
        [],
    ))
    monkeypatch.setattr(runtime, "answer_commit_persistence", lambda **kwargs: None)

    runtime_state: dict[str, object] = {
        "source_ingest_background_future": completed_future,
        "source_ingest_background_in_progress": True,
        "source_ingest_background_request_id": "turn-789",
        "pending_ingestion_registry": {
            "turn-789": {
                "utterance": "What is due next?",
                "prior_pipeline_state": None,
                "created_at": "2026-03-10T10:00:00+00:00",
                "last_polled_at": "2026-03-10T10:01:00+00:00",
                "attempt_count": 4,
                "deadline_at": "2026-03-10T12:00:00+00:00",
                "status": "pending",
            }
        },
    }

    last_ts, prior_state, processed = runtime._process_background_ingestion_completion(
        runtime=runtime_state,
        llm=_StaticLLM("ignored"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        clock=_FIXED_CLOCK,
        io_channel="cli",
        send_assistant_text=lambda text: assistant_messages.append(text),
        last_user_message_ts="",
        prior_pipeline_state=None,
    )

    assert processed is True
    assert last_ts == ""
    assert prior_state is not None

    synthetic_events = [
        {
            "event": "source_ingest_background_started",
            "ingestion_request_id": "turn-789",
        },
        {
            "event": "source_ingest_user_start_notified",
            "ingestion_request_id": "turn-789",
            "message_text": runtime.BACKGROUND_INGESTION_PROGRESS_ANSWER,
        },
        {
            "event": "pending_ingestion_persisted",
            "ingestion_request_id": "turn-789",
            "correlation_id": "turn-789",
        },
    ]
    synthetic_events.extend(
        {"event": event_name, **payload}
        for event_name, payload in events
        if event_name in {"source_ingest_completion_event_emitted", "source_ingest_completion_answer_emitted"}
    )

    assert [event["event"] for event in synthetic_events] == [
        "source_ingest_background_started",
        "source_ingest_user_start_notified",
        "pending_ingestion_persisted",
        "source_ingest_completion_event_emitted",
        "source_ingest_completion_answer_emitted",
    ]

    completion_event = synthetic_events[3]
    assert completion_event["ingestion_request_id"] == "turn-789"
    assert completion_event["linked_pending_ingestion_request_id"] == "turn-789"
    assert completion_event["event_type"] == "source_ingestion_completion"

    completion_answer = synthetic_events[4]
    assert completion_answer["ingestion_request_id"] == "turn-789"
    assert completion_answer["linked_pending_ingestion_request_id"] == "turn-789"
    assert "synced source evidence" in completion_answer["final_answer"]

    completion_user_notice = next(payload for name, payload in events if name == "source_ingest_completion_user_message_emitted")
    assert completion_user_notice["ingestion_request_id"] == "turn-789"
    assert completion_user_notice["linked_pending_ingestion_request_id"] == "turn-789"
    assert assistant_messages[0] == completion_user_notice["message_text"]

    obligation_events = [payload for name, payload in events if name == "source_ingest_obligation_transition"]
    assert obligation_events
    assert obligation_events[-1]["ingestion_request_id"] == "turn-789"
    assert obligation_events[-1]["status"] == "resolved"

def test_chat_loop_does_not_use_pre_pipeline_intent_classifier_route_authority(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        runtime,
        "classify_intent",
        lambda _utterance: (_ for _ in ()).throw(AssertionError("early classify_intent call is forbidden in chat loop")),
    )

    def _stub_pipeline(**kwargs):
        state = kwargs["state"]
        return (
            replace(
                state,
                classified_intent=IntentType.META_CONVERSATION.value,
                resolved_intent=IntentType.META_CONVERSATION.value,
                final_answer="Hi!",
                invariant_decisions={"fallback_action": "NONE", "answer_mode": "assist"},
                confidence_decision={"stage_audit_trail": list(runtime.CanonicalTurnOrchestrator.STAGE_ORDER)},
                provenance_types=[],
                basis_statement="none",
                claims=[],
            ),
            [],
        )

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _stub_pipeline)

    prompts = iter(["hello there", "stop"])
    _run_chat_loop(
        llm=_StaticLLM("ignored"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    ingest_payload = next(payload for event, payload in events if event == "user_utterance_ingest")
    assert ingest_payload["utterance"] == "hello there"


@pytest.mark.parametrize(
    "utterance",
    [
        "Hi! I'm Sebastian",
        "The memory today",
        "How log ago did I ask you something?",
    ],
)
def test_chat_loop_routes_issue_0013_regression_utterances_through_canonical_pipeline(monkeypatch, utterance: str) -> None:
    pipeline_calls: list[str] = []

    monkeypatch.setattr(runtime, "append_session_log", lambda _event, _payload: None)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        runtime,
        "classify_intent",
        lambda _utterance: (_ for _ in ()).throw(AssertionError("raw U->I classify_intent path is forbidden")),
    )

    def _stub_pipeline(**kwargs):
        state = kwargs["state"]
        pipeline_calls.append(state.user_input)
        return (
            replace(
                state,
                classified_intent=IntentType.META_CONVERSATION.value,
                resolved_intent=IntentType.META_CONVERSATION.value,
                final_answer="Acknowledged.",
                invariant_decisions={"fallback_action": "NONE", "answer_mode": "assist"},
                confidence_decision={"stage_audit_trail": list(runtime.CanonicalTurnOrchestrator.STAGE_ORDER)},
                provenance_types=[],
                basis_statement="none",
                claims=[],
            ),
            [],
        )

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _stub_pipeline)

    prompts = iter([utterance, "stop"])
    _run_chat_loop(
        llm=_StaticLLM("ignored"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    assert pipeline_calls == [utterance]


def test_resolve_context_consumes_commit_receipt_continuity_deterministically() -> None:
    prior_state = PipelineState(
        user_input="turn one",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        commit_receipt={
            "commit_stage": "answer.commit",
            "pending_repair_state": {"repair_required_by_policy": True, "repair_offered_to_user": True, "reason": "repair_offer_rendered", "followup_route": "repair_offer_followup"},
            "remaining_obligations": ["continue_repair_reconstruction"],
            "pending_ingestion_request_id": "ingest-42",
            "confirmed_user_facts": ["name=Sam", "timezone=PST"],
        },
    )

    resolved = runtime.resolve_context(utterance="continue", prior_pipeline_state=prior_state)

    assert resolved.history_anchors == (
        "prior_intent:memory_recall",
        "commit.confirmed_user_facts:name=Sam",
        "commit.confirmed_user_facts:timezone=PST",
        "commit.pending_repair_state:repair_offered_to_user",
        "commit.pending_ingestion_request_id:ingest-42",
        "commit.remaining_obligations:continue_repair_reconstruction",
    )


def test_run_canonical_answer_stage_flow_distinguishes_knowing_success_and_unknowing_rejection_paths() -> None:
    knowing_state = PipelineState(
        user_input="what did i note about release prep?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={"context_confident": True, "ambiguity_detected": False},
    )
    knowing = run_canonical_answer_stage_flow(
        _StaticLLM("From memory, I found: release prep requires changelog review."),
        knowing_state,
        chat_history=deque(),
        hits=[
            Document(
                page_content="release prep requires changelog review",
                metadata={"doc_id": "mem-11", "ts": "2026-03-02T10:00:00Z"},
            )
        ],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    rejecting_state = PipelineState(
        user_input="what is ontology?",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "general_knowledge_confidence": 0.1,
            "general_knowledge_support": 0,
        },
    )
    rejecting = run_canonical_answer_stage_flow(
        _StaticLLM("Ontology is the study of being and existence."),
        rejecting_state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert knowing.invariant_decisions.get("answer_mode") == "memory-grounded"
    assert knowing.invariant_decisions.get("fallback_action") == "ANSWER_FROM_MEMORY"
    assert rejecting.invariant_decisions.get("fallback_action") in {"ANSWER_UNKNOWN", "ANSWER_GENERAL_KNOWLEDGE"}
    assert "reliable memory" in rejecting.final_answer.lower()


def test_chat_loop_emits_completion_event_user_message_and_linked_answer(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "answer_commit_persistence", lambda **kwargs: None)

    poll_calls = {"count": 0}

    def _poll(*, runtime: dict[str, object]):
        poll_calls["count"] += 1
        if poll_calls["count"] == 1:
            return {
                "ok": True,
                "status": "completed",
                "payload": {"ingestion_request_id": "turn-123", "background": True, "stored_count": 2},
            }
        return None

    monkeypatch.setattr(runtime, "_poll_background_source_ingestion", _poll)

    def _pipeline(**kwargs):
        state = kwargs["state"]
        return (
            replace(
                state,
                final_answer="Grounded answer after ingestion.",
                commit_receipt={"pending_ingestion_request_id": ""},
                invariant_decisions={"fallback_action": "NONE", "answer_mode": "knowing"},
                confidence_decision={"stage_audit_trail": []},
                provenance_types=[],
                claims=[],
                used_memory_refs=[],
                used_source_evidence_refs=["src-900"],
                source_evidence_attribution=[],
                basis_statement="source evidence",
                alignment_decision=AlignmentDecision(),
            ),
            [],
        )

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _pipeline)

    prompts = iter(["stop"])
    runtime._run_chat_loop(
        runtime={
            "pending_ingestion_registry": {
                "turn-123": {"utterance": "What is due Friday?", "prior_pipeline_state": None}
            }
        },
        llm=_StaticLLM("ignored"),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    completion_event = next(row for row in rows if row.get("event") == "source_ingest_completion_event_emitted")
    assert completion_event["ingestion_request_id"] == "turn-123"
    assert completion_event["linked_pending_ingestion_request_id"] == "turn-123"

    completion_message = next(row for row in rows if row.get("event") == "source_ingest_completion_user_message_emitted")
    assert completion_message["linked_pending_ingestion_request_id"] == "turn-123"
    assert completion_message["message_text"].startswith("Background ingestion completed for request turn-123")

    completion_answer = next(row for row in rows if row.get("event") == "source_ingest_completion_answer_emitted")
    assert completion_answer["linked_pending_ingestion_request_id"] == "turn-123"
    assert completion_answer["final_answer"] == "Grounded answer after ingestion."



def test_capabilities_help_followup_yes_please_look_it_up_matches_existing_decision_branch() -> None:
    expected_intent = classify_intent("please look up the definition")
    actual_intent = classify_intent("yes please look it up")

    assert expected_intent is IntentType.CAPABILITIES_HELP
    assert actual_intent is expected_intent

    baseline = run_canonical_answer_stage_flow(
        _StaticLLM("unused"),
        PipelineState(
            user_input="please look up the definition",
            resolved_intent=expected_intent.value,
            confidence_decision={"context_confident": False, "ambiguity_detected": False},
        ),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    edge_case = run_canonical_answer_stage_flow(
        _StaticLLM("unused"),
        PipelineState(
            user_input="yes please look it up",
            resolved_intent=actual_intent.value,
            confidence_decision={"context_confident": False, "ambiguity_detected": False},
        ),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert edge_case.invariant_decisions.get("fallback_action") == baseline.invariant_decisions.get("fallback_action")
    assert edge_case.invariant_decisions.get("answer_mode") == baseline.invariant_decisions.get("answer_mode")

def test_capabilities_help_followup_debug_policy_never_reports_general_knowledge_action() -> None:
    state = PipelineState(
        user_input="define the term",
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
    )

    answered = run_canonical_answer_stage_flow(
        _StaticLLM("unused"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=True,
            ha_available=False,
            effective_mode="cli",
            requested_mode="cli",
            daemon_mode=False,
            fallback_reason=None,
            memory_backend="in_memory",
            debug_enabled=True,
            debug_verbose=False,
            text_clarification_available=True,
            satellite_ask_available=False,
        ),
        clock=_FIXED_CLOCK,
    )

    debug_payload = runtime._build_debug_turn_payload(
        state=answered,
        intent_label=answered.resolved_intent,
        hits=[],
    )

    assert answered.invariant_decisions.get("fallback_action") != "ANSWER_GENERAL_KNOWLEDGE"
    assert debug_payload["debug.policy"]["fallback_action"] != "ANSWER_GENERAL_KNOWLEDGE"


@pytest.mark.non_contract
def test_chat_loop_prescribed_four_turn_replay_sets_commit_stage_recorded_only_on_turn_three(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])

    canned_answers = {
        "turn 1": "Acknowledged.",
        "turn 2": "I can share a grounded summary.",
        "turn 3": (
            "I can either help you reconstruct the timeline from what you remember, "
            "or suggest where to check next for the missing detail."
        ),
        "turn 4": "Okay, continuing.",
    }

    def _stub_answer_assemble(llm, state, **kwargs):
        del llm, kwargs
        return runtime.AnswerAssembleResult(
            draft_answer="",
            final_answer=canned_answers[state.user_input],
            fallback_action="NONE",
            intent_class="non_memory",
            social_or_non_knowledge_intent=False,
            answer_policy_rationale={},
            capability_help_short_circuit=False,
        )

    monkeypatch.setattr(runtime, "answer_assemble", _stub_answer_assemble)

    class _EmptyStore:
        def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
            del query, k, kwargs
            return []

    prompts = iter(["turn 1", "turn 2", "turn 3", "turn 4", "stop"])
    _run_chat_loop(
        llm=_StaticLLM("ignored"),
        store=_EmptyStore(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=_FIXED_CLOCK,
    )

    rows = [json.loads(line) for line in (tmp_path / "logs" / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    commit_rows = [row for row in rows if row.get("event") == "commit_stage_recorded"]

    assert len(commit_rows) == 4
    commit_stage_recorded = [
        bool(row["pending_repair_state"].get("repair_offered_to_user"))
        for row in commit_rows
    ]
    assert commit_stage_recorded == [False, False, True, False]
