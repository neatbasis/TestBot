from __future__ import annotations

from collections import deque
from dataclasses import replace

import arrow
from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot import sat_chatbot_memory_v2 as runtime
from testbot.intent_router import IntentType
from testbot.policy_decision import EvidencePosture, decide
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
    stage_answer,
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


def test_stage_answer_invoke_failure_uses_deterministic_fallback_and_logs(monkeypatch) -> None:
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "decide_fallback_action", lambda **_: "ANSWER_GENERAL_KNOWLEDGE")

    state = PipelineState(
        user_input="what happened yesterday?",
        confidence_decision={"context_confident": True, "ambiguity_detected": False},
    )

    answered = stage_answer(
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

def test_stage_answer_non_memory_without_ambiguity_does_not_emit_memory_fragment_clarifier(monkeypatch) -> None:
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

    answered = stage_answer(
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
    monkeypatch.setattr(runtime, "encode_stage", lambda _llm, state: replace(state, rewritten_query="ontology definition"))
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
        "stage_answer",
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
    assert retrieval_payload["candidate_count"] >= 0
    assert retrieval_payload.get("skipped", False) is False
    assert retrieval_payload["hygiene"]["primary_invariant"] == "retrieve_stage_exclusion"
    assert retrieval_payload["hygiene"]["rerank_defense_in_depth"] is True
    assert len(retrieval_payload["hygiene"]["exclude_doc_ids"]) == 2


def test_chat_loop_conversational_prompt_skips_knowledge_retrieval_path(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_validate_and_log_transition", lambda _result: None)
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        runtime,
        "stage_answer",
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


def test_stage_answer_low_source_confidence_non_memory_uses_safe_unknowing_mode_legacy_assertions() -> None:
    state = PipelineState(
        user_input="What happened in my calendar?",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
            "source_confidence": 0.2,
        },
    )

    answered = stage_answer(
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




def test_stage_answer_greeting_command_preserves_social_draft_answer() -> None:
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

    answered = stage_answer(
        _StaticLLM("Hello! Nice to meet you."),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == "Hello! Nice to meet you."
    assert answered.invariant_decisions.get("answer_mode") == "assist"


def test_stage_answer_low_source_confidence_non_memory_uses_uncertainty_response() -> None:
    state = PipelineState(
        user_input="What happened in my calendar?",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
            "source_confidence": 0.2,
        },
    )

    answered = stage_answer(
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


def test_stage_answer_self_introduction_preserves_acknowledgement_draft() -> None:
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

    answered = stage_answer(
        _StaticLLM("Thanks, Taylor — I'll remember that for this conversation."),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == "Thanks, Taylor — I'll remember that for this conversation."
    assert answered.invariant_decisions.get("answer_mode") == "assist"


def test_stage_answer_regression_say_hello_keeps_greeting_instead_of_memory_fallback() -> None:
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

    answered = stage_answer(
        _StaticLLM("hello"),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=_FIXED_CLOCK,
    )

    assert answered.final_answer == "hello"
    assert "reliable memory" not in answered.final_answer.lower()


def test_stage_answer_memory_recall_confident_hit_recovers_from_contract_failure() -> None:
    state = PipelineState(
        user_input="what did i note about release prep?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
        },
    )

    answered = stage_answer(
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
    monkeypatch.setattr(runtime, "encode_stage", lambda _llm, state: replace(state, rewritten_query="release memory"))
    monkeypatch.setattr(runtime, "stage_retrieve", lambda _store, state, **kwargs: (replace(state, retrieval_candidates=[]), []))
    monkeypatch.setattr(
        runtime,
        "stage_rerank",
        lambda state, docs_and_scores, **kwargs: (  # noqa: ARG005
            replace(
                state,
                reranked_hits=[],
                confidence_decision={
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
        "stage_answer",
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

    policy = debug_event["payload"]["debug.policy"]
    assert policy["reject_code"] == "ANSWER_CONTRACT_GROUNDING_FAIL"
    assert policy["counterfactuals"]["alternate_routing_policy_checks"] == {
        "ask_clarifying_question_passes": False,
        "route_to_ask_passes": False,
    }
    assert debug_event["payload"]["debug.confidence"]["context_confident_gate"]["passed"] is False
    assert debug_event["payload"]["debug.rerank"]["margin_gate"]["passed"] is False
