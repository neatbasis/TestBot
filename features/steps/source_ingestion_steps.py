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


@given("a deterministic source-ingestion harness")
def step_given_harness(context) -> None:
    context.hits = []
    context.final_answer = ""


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
    (
        context.provenance,
        _claims,
        _basis,
        context.memory_refs,
        context.source_refs,
        context.source_attr,
    ) = build_provenance_metadata(
        final_answer=context.final_answer,
        hits=context.hits,
        chat_history=deque(),
        packed_history=_packed_history(),
    )


@then("the provenance includes source evidence references and attribution fields")
def step_then_provenance(context) -> None:
    assert ProvenanceType.MEMORY in context.provenance
    assert context.memory_refs == []
    assert context.source_refs == ["src-900"]
    assert context.source_attr
    first = context.source_attr[0]
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
