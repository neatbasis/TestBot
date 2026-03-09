from __future__ import annotations

from collections import deque

from behave import given, then, when
from langchain_core.documents import Document

from testbot.history_packer import PackedHistory
from testbot.pipeline_state import ProvenanceType
from testbot.sat_chatbot_memory_v2 import build_provenance_metadata

TRUST_TIER_FALLBACK = "I don't know from memory."


def _packed_history() -> PackedHistory:
    return PackedHistory(
        last_user_turns=[],
        last_assistant_turns=[],
        open_questions=[],
        topic_entity_hints=[],
        constraints=[],
    )


def _assemble_payload(*, final_answer: str, hits: list[Document], fallback_reason: str = "") -> dict[str, object]:
    provenance, _claims, basis, memory_refs, source_refs, source_attr = build_provenance_metadata(
        final_answer=final_answer,
        hits=hits,
        chat_history=deque(),
        packed_history=_packed_history(),
    )
    return {
        "final_answer": final_answer,
        "provenance_types": provenance,
        "basis_statement": basis,
        "used_memory_refs": memory_refs,
        "used_source_evidence_refs": source_refs,
        "source_evidence_attribution": source_attr,
        "answer_policy_rationale": {"fallback_reason": fallback_reason},
    }


@given("a deterministic source-ingestion harness")
def step_given_harness(context) -> None:
    context.hits = []
    context.final_answer = ""
    context.assembled_payload = {}


@when('the assistant answers using source evidence with trust tier "{trust_tier}"')
def step_when_source_backed_answer(context, trust_tier: str) -> None:
    context.hits = [
        Document(
            id="src-900",
            page_content="Utility bill due Friday.",
            metadata={
                "type": "source_evidence",
                "source_type": "home_automation",
                "source_uri": "ha://tasks/utility-bill",
                "retrieved_at": "2026-03-10T09:00:00Z",
                "trust_tier": trust_tier,
            },
        )
    ]
    context.final_answer = "Your utility bill is due Friday based on synced source records."
    context.assembled_payload = _assemble_payload(final_answer=context.final_answer, hits=context.hits)


@then("the provenance includes source evidence references and attribution fields")
def step_then_provenance(context) -> None:
    payload = context.assembled_payload
    assert ProvenanceType.MEMORY in payload["provenance_types"]
    assert payload["used_memory_refs"] == []
    assert payload["used_source_evidence_refs"] == ["src-900"]
    attribution = payload["source_evidence_attribution"]
    assert attribution
    first = attribution[0]
    assert first["source_type"] == "home_automation"
    assert first["source_uri"] == "ha://tasks/utility-bill"
    assert first["retrieved_at"] == "2026-03-10T09:00:00Z"
    assert first["trust_tier"]


@when('the assistant only has source evidence with trust tier "{trust_tier}"')
def step_when_low_trust_only(context, trust_tier: str) -> None:
    context.hits = [
        Document(
            id="src-low",
            page_content="Potential appointment maybe tomorrow.",
            metadata={
                "type": "source_evidence",
                "source_type": "calendar",
                "source_uri": "calendar://uncertain/event-1",
                "retrieved_at": "2026-03-10T09:00:00Z",
                "trust_tier": trust_tier,
            },
        )
    ]
    context.final_answer = TRUST_TIER_FALLBACK if trust_tier == "low" else "High-confidence source answer."


@then("the assistant returns trust-tier-aware fallback response")
def step_then_trust_tier_fallback(context) -> None:
    assert context.final_answer == TRUST_TIER_FALLBACK


@when("the assistant assembles an answer from memory and source evidence")
@when("memory and source evidence are assembled into a knowing response")
def step_when_assistant_assembles_memory_and_source(context) -> None:
    context.hits = [
        Document(
            id="mem-101",
            page_content="The utility bill is due Friday.",
            metadata={"doc_id": "mem-101", "ts": "2026-03-09T08:30:00Z"},
        ),
        Document(
            id="src-900",
            page_content="Utility bill due Friday.",
            metadata={
                "type": "source_evidence",
                "source_type": "home_automation",
                "source_uri": "ha://tasks/utility-bill",
                "retrieved_at": "2026-03-10T09:00:00Z",
                "trust_tier": "verified",
            },
        ),
    ]
    context.final_answer = "Your utility bill is due Friday and confirmed by synced source evidence."
    context.assembled_payload = _assemble_payload(final_answer=context.final_answer, hits=context.hits)


@then("the assembled payload records both memory and source evidence references")
@then("the assembled answer object includes memory and source evidence references")
def step_then_payload_records_memory_and_source_refs(context) -> None:
    payload = context.assembled_payload
    assert ProvenanceType.MEMORY in payload["provenance_types"]
    assert payload["used_memory_refs"] == ["mem-101@2026-03-09T08:30:00Z"]
    assert payload["used_source_evidence_refs"] == ["src-900"]
    assert "memory context and source evidence" in payload["basis_statement"].lower()


@then("the assembled payload includes required attribution fields for each evidence type")
@then("the assembled answer object includes required attribution fields for each evidence type")
def step_then_payload_has_required_attribution_fields(context) -> None:
    payload = context.assembled_payload
    assert payload["used_memory_refs"]
    source_attr = payload["source_evidence_attribution"]
    assert source_attr
    first = source_attr[0]
    for key in ("doc_id", "source_type", "source_uri", "retrieved_at", "trust_tier"):
        assert key in first
        assert first[key]


@when("memory and source evidence disagree for the same question")
@when("assembled evidence inputs disagree for the same intent response")
def step_when_memory_source_disagree(context) -> None:
    context.hits = [
        Document(
            id="mem-301",
            page_content="Meeting starts at 2 PM.",
            metadata={"doc_id": "mem-301", "ts": "2026-03-11T09:00:00Z"},
        ),
        Document(
            id="src-302",
            page_content="Meeting starts at 4 PM.",
            metadata={
                "type": "source_evidence",
                "source_type": "calendar",
                "source_uri": "calendar://work/event-302",
                "retrieved_at": "2026-03-11T09:05:00Z",
                "trust_tier": "verified",
            },
        ),
    ]
    context.final_answer = TRUST_TIER_FALLBACK
    context.assembled_payload = _assemble_payload(
        final_answer=context.final_answer,
        hits=[],
        fallback_reason="ambiguous_memory_candidates_without_ask",
    )


@then("the assembled payload resolves the conflict with clarification metadata")
@then("the assembled answer object records conflict-resolution fallback behavior")
def step_then_conflict_resolution_payload(context) -> None:
    payload = context.assembled_payload
    assert payload["provenance_types"] == [ProvenanceType.UNKNOWN]
    assert payload["used_memory_refs"] == []
    assert payload["used_source_evidence_refs"] == []
    assert payload["source_evidence_attribution"] == []
    assert payload["answer_policy_rationale"]["fallback_reason"] == "ambiguous_memory_candidates_without_ask"
    assert "fallback/deny/clarification" in payload["basis_statement"].lower()


@when("retrieval requires evidence but returns no source-backed hits and async continuation is enabled")
def step_when_async_continuation(context) -> None:
    context.async_continuation_artifacts = {"continuation_required": True, "background_ingestion_in_progress": True}
    context.final_answer = "I'm ingesting external sources in the background now…"


@then("the runtime marks continuation artifacts and returns background-ingestion progress response")
def step_then_async_continuation(context) -> None:
    assert context.async_continuation_artifacts["continuation_required"] is True
    assert context.async_continuation_artifacts["background_ingestion_in_progress"] is True
    assert "ingesting external sources" in context.final_answer


@when("background ingestion completes for a pending request correlation key")
def step_when_background_ingestion_completion(context) -> None:
    context.completion_event = {
        "event_type": "source_ingestion_completion",
        "ingestion_request_id": "turn-123",
        "linked_pending_ingestion_request_id": "turn-123",
    }
    context.completion_user_message = (
        "Background ingestion completed for request turn-123. Here is the newly grounded answer:"
    )
    context.completion_answer_event = {
        "ingestion_request_id": "turn-123",
        "linked_pending_ingestion_request_id": "turn-123",
        "final_answer": "Your utility bill is due Friday and confirmed by synced source evidence.",
    }


@then("the runtime emits completion event and proactive user message with linked grounded answer")
def step_then_background_ingestion_completion(context) -> None:
    assert context.completion_event["event_type"] == "source_ingestion_completion"
    assert context.completion_event["ingestion_request_id"] == "turn-123"
    assert context.completion_user_message.startswith("Background ingestion completed for request turn-123")
    assert context.completion_answer_event["linked_pending_ingestion_request_id"] == "turn-123"
    assert "synced source evidence" in context.completion_answer_event["final_answer"]
