from __future__ import annotations

from collections import deque

from langchain_core.documents import Document

from testbot.application.services.background_ingestion_runtime import BackgroundIngestionReplayRequest
from testbot.pipeline_state import PipelineState
from testbot import sat_chatbot_memory_v2 as runtime
from testbot.application.services import answer_stage_presentation as canonical_presentation


def test_answer_assemble_wrapper_delegates_to_answer_stage_runtime(monkeypatch) -> None:
    state = PipelineState(user_input="hello", resolved_intent="knowledge_question")
    expected = runtime.AnswerAssembleResult(
        draft_answer="draft",
        final_answer="final",
        fallback_action="ANSWER_GENERAL_KNOWLEDGE",
        intent_class="non_memory",
        social_or_non_knowledge_intent=False,
        answer_policy_rationale={},
    )
    observed: dict[str, object] = {}

    def _fake_answer_assemble(*args, **kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch.setattr(runtime.answer_stage_runtime_service, "answer_assemble", _fake_answer_assemble)

    actual = runtime.answer_assemble(
        llm=object(),
        state=state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        answer_routing=runtime.AnswerRoutingDecision(
            fallback_action="ANSWER_GENERAL_KNOWLEDGE",
            clarification_allowed=False,
            canonical_response_token="GENERAL_KNOWLEDGE_ANSWER",
            route_to_ask_expected=False,
            rationale={},
        ),
    )

    assert actual is expected
    assert observed["append_session_log"] is runtime.append_session_log
    assert observed["answer_prompt"] is runtime.ANSWER_PROMPT


def test_answer_validate_wrapper_delegates_to_answer_stage_runtime(monkeypatch) -> None:
    state = PipelineState(user_input="hello")
    assembled = runtime.AnswerAssembleResult(
        draft_answer="draft",
        final_answer="final",
        fallback_action="ANSWER_GENERAL_KNOWLEDGE",
        intent_class="non_memory",
        social_or_non_knowledge_intent=False,
        answer_policy_rationale={},
    )
    expected = runtime.AnswerValidateResult(
        final_answer="final",
        claims=[],
        provenance_types=[],
        used_memory_refs=[],
        used_source_evidence_refs=[],
        source_evidence_attribution=[],
        basis_statement="basis",
        invariant_decisions={},
        alignment_decision={},
    )
    observed: dict[str, object] = {}

    def _fake_answer_validate(*args, **kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch.setattr(runtime.answer_stage_runtime_service, "answer_validate", _fake_answer_validate)

    actual = runtime.answer_validate(
        state,
        assembled=assembled,
        hits=[Document(page_content="x")],
        chat_history=deque(),
    )

    assert actual is expected
    assert observed["build_provenance_metadata"] is runtime.build_provenance_metadata_from_logic
    assert observed["evaluate_alignment_decision"] is runtime._evaluate_alignment_decision


def test_run_canonical_answer_stage_flow_wrapper_delegates_to_answer_stage_runtime(monkeypatch) -> None:
    state = PipelineState(user_input="hello")
    expected = PipelineState(user_input="hello", final_answer="ok")
    observed: dict[str, object] = {}

    def _fake_run_flow(*args, **kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch.setattr(runtime.answer_stage_runtime_service, "run_canonical_answer_stage_flow", _fake_run_flow)

    actual = runtime.run_canonical_answer_stage_flow(
        llm=object(),
        state=state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
    )

    assert actual is expected
    assert observed["run_canonical_turn_pipeline"] is runtime._run_canonical_turn_pipeline


def test_answer_assemble_for_turn_service_wrapper_delegates_to_answer_stage_runtime(monkeypatch) -> None:
    expected = runtime.AnswerAssembleResult(
        draft_answer="draft",
        final_answer="final",
        fallback_action="ANSWER_GENERAL_KNOWLEDGE",
        intent_class="non_memory",
        social_or_non_knowledge_intent=False,
        answer_policy_rationale={},
    )
    observed: dict[str, object] = {}

    def _fake_answer_assemble_for_turn_service(*args, **kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch.setattr(
        runtime.answer_stage_runtime_service,
        "answer_assemble_for_turn_service",
        _fake_answer_assemble_for_turn_service,
    )
    retrieval_hit = runtime.RetrievalInputRecord(ref_id="doc-1", score=1.0, content="x", metadata={"doc_id": "doc-1"})
    actual = runtime._answer_assemble_for_turn_service(
        llm=object(),
        state=PipelineState(user_input="hello", resolved_intent="knowledge_question"),
        chat_history=deque(),
        hits=[retrieval_hit],
        capability_status="ask_unavailable",
        answer_routing=runtime.AnswerRoutingDecision(
            fallback_action="ANSWER_GENERAL_KNOWLEDGE",
            clarification_allowed=False,
            canonical_response_token="GENERAL_KNOWLEDGE_ANSWER",
            route_to_ask_expected=False,
            rationale={},
        ),
    )

    assert actual is expected
    assert observed["document_from_retrieval_input"] is runtime._document_from_retrieval_input


def test_answer_validate_for_turn_service_wrapper_delegates_to_answer_stage_runtime(monkeypatch) -> None:
    expected = runtime.AnswerValidateResult(
        final_answer="final",
        claims=[],
        provenance_types=[],
        used_memory_refs=[],
        used_source_evidence_refs=[],
        source_evidence_attribution=[],
        basis_statement="basis",
        invariant_decisions={},
        alignment_decision={},
    )
    observed: dict[str, object] = {}

    def _fake_answer_validate_for_turn_service(*args, **kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch.setattr(
        runtime.answer_stage_runtime_service,
        "answer_validate_for_turn_service",
        _fake_answer_validate_for_turn_service,
    )
    retrieval_hit = runtime.RetrievalInputRecord(ref_id="doc-1", score=1.0, content="x", metadata={"doc_id": "doc-1"})
    actual = runtime._answer_validate_for_turn_service(
        state=PipelineState(user_input="hello"),
        assembled=runtime.AnswerAssembleResult(
            draft_answer="draft",
            final_answer="final",
            fallback_action="ANSWER_GENERAL_KNOWLEDGE",
            intent_class="non_memory",
            social_or_non_knowledge_intent=False,
            answer_policy_rationale={},
        ),
        hits=[retrieval_hit],
        chat_history=deque(),
    )

    assert actual is expected
    assert observed["document_from_retrieval_input"] is runtime._document_from_retrieval_input


def test_detect_capability_offer_wrapper_delegates_to_answer_stage_runtime(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def _fake_detect_capability_offer(text: str) -> str:
        observed["text"] = text
        return "capability_offer"

    monkeypatch.setattr(
        runtime.answer_stage_runtime_service,
        "detect_capability_offer",
        _fake_detect_capability_offer,
    )

    assert runtime._detect_capability_offer("I can look up") == "capability_offer"
    assert observed["text"] == "I can look up"


def test_answer_prompt_compat_reexport_matches_canonical_owner() -> None:
    assert runtime.ANSWER_PROMPT is canonical_presentation.ANSWER_PROMPT


def test_render_context_compat_wrapper_matches_canonical_owner() -> None:
    docs = [Document(page_content="x", metadata={"doc_id": "d1", "ts": "t1", "type": "memory"})]

    assert runtime.render_context(docs, limit_chars=5000) == canonical_presentation.render_context(docs, limit_chars=5000)


def test_background_completion_replay_compat_wrapper_delegates_to_legacy_pipeline_runner(monkeypatch) -> None:
    observed: dict[str, object] = {}
    prior_state = PipelineState(user_input="previous", prior_unresolved_intent="needs-clarification")

    def _fake_legacy_pipeline(**kwargs):
        observed.update(kwargs)
        return kwargs["state"], []

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _fake_legacy_pipeline)

    replayed_state = runtime._replay_background_completion_turn_compat(
        BackgroundIngestionReplayRequest(
            runtime={"mode": "cli"},
            llm=object(),
            store=object(),
            utterance="What changed?",
            last_user_message_ts="2026-03-10T11:00:00+00:00",
            prior_pipeline_state=prior_state,
            near_tie_delta=0.05,
            chat_history=deque(),
            capability_status="ask_unavailable",
            capability_snapshot={},
            clock=object(),
            io_channel="cli",
            turn_id="turn-123",
        )
    )

    assert replayed_state.user_input == "What changed?"
    assert replayed_state.classified_intent == runtime.IntentType.KNOWLEDGE_QUESTION.value
    assert replayed_state.prior_unresolved_intent == "needs-clarification"
    assert observed["turn_id"] == "turn-123"
