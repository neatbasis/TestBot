from __future__ import annotations

import arrow
from langchain_core.documents import Document

from testbot.rerank import rerank_docs_with_time_and_type_outcome


def _doc(doc_id: str, *, ts: str, card_type: str) -> Document:
    return Document(page_content=doc_id, id=doc_id, metadata={"doc_id": doc_id, "ts": ts, "type": card_type})


def test_rerank_uses_deterministic_tie_break_priority() -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    docs_and_scores = [
        (_doc("older", ts="2026-03-10T11:00:00+00:00", card_type="user_utterance"), 0.9),
        (_doc("newer", ts="2026-03-10T11:05:00+00:00", card_type="user_utterance"), 0.9),
    ]

    outcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        near_tie_delta=0.05,
    )

    assert outcome.docs[0].id == "newer"
    assert not outcome.ambiguity_detected


def test_rerank_marks_unresolved_ambiguity_when_tie_break_cannot_decide() -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    docs_and_scores = [
        (Document(page_content="a", id="", metadata={"doc_id": "", "type": "memory", "ts": ""}), 0.8),
        (Document(page_content="b", id="", metadata={"doc_id": "", "type": "memory", "ts": ""}), 0.79),
    ]

    outcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        near_tie_delta=0.05,
    )

    assert outcome.ambiguity_detected
    assert len(outcome.near_tie_candidates) == 2


def test_rerank_near_tie_delta_controls_ambiguity_window() -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    docs_and_scores = [
        (_doc("a", ts="", card_type="memory"), 0.8),
        (_doc("b", ts="", card_type="memory"), 0.79),
    ]

    strict = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        near_tie_delta=0.001,
    )
    relaxed = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=now,
        sigma_seconds=3600,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        near_tie_delta=0.05,
    )

    assert len(strict.near_tie_candidates) == 1
    assert len(relaxed.near_tie_candidates) == 2
