"""Canonical runtime-owned answer commit persistence helpers.

Ownership:
- This module is the canonical owner for runtime commit-persistence orchestration.
- Compatibility façades may delegate here during retirement windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import uuid

from langchain_ollama import ChatOllama

from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc
from testbot.memory_strata import MemoryStratum, apply_persistence_metadata, derive_segment_descriptor
from testbot.pipeline_state import PipelineState
from testbot.promotion_policy import persist_promoted_context
from testbot.ports import MemoryStorePort
from testbot.domain import Clock


@dataclass(frozen=True)
class RuntimeCommitPersistenceDependencies:
    append_session_log: Callable[[str, dict[str, object]], None]
    generate_reflection_yaml: Callable[..., str]


def answer_commit_persistence(
    *,
    llm: ChatOllama,
    store: MemoryStorePort,
    state: PipelineState,
    io_channel: str,
    clock: Clock,
    deps: RuntimeCommitPersistenceDependencies,
) -> None:
    a_ts = clock.now().isoformat()
    a_id = str(uuid.uuid4())
    a_card = make_utterance_card(
        ts_iso=a_ts,
        speaker="assistant",
        text=state.final_answer,
        doc_id=a_id,
        channel=io_channel,
    )
    commit_segment = derive_segment_descriptor(utterance=state.user_input, has_dialogue_state=False)
    store_doc(
        store,
        doc_id=a_id,
        content=a_card,
        metadata=apply_persistence_metadata(
            metadata={
                "ts": a_ts,
                "type": "assistant_utterance",
                "speaker": "assistant",
                "channel": io_channel,
                "doc_id": a_id,
                "raw": state.final_answer,
            },
            stratum=MemoryStratum.EPISODIC,
            segment=commit_segment,
            member_doc_id=a_id,
        ),
    )

    a_ref_yaml = deps.generate_reflection_yaml(llm, speaker="assistant", text=state.final_answer)
    a_ref_ts = clock.now().isoformat()
    a_ref_id = str(uuid.uuid4())
    a_ref_card = make_reflection_card(
        ts_iso=a_ref_ts,
        about="assistant",
        source_doc_id=a_id,
        doc_id=a_ref_id,
        reflection_yaml=a_ref_yaml,
    )
    store_doc(
        store,
        doc_id=a_ref_id,
        content=a_ref_card,
        metadata=apply_persistence_metadata(
            metadata={
                "ts": a_ref_ts,
                "type": "reflection",
                "about": "assistant",
                "source_doc_id": a_id,
                "doc_id": a_ref_id,
            },
            stratum=MemoryStratum.SEMANTIC,
            segment=commit_segment,
            member_doc_id=a_ref_id,
        ),
    )

    promoted_doc_ids = persist_promoted_context(
        store=store,
        ts_iso=a_ref_ts,
        source_doc_id=a_id,
        source_reflection_id=a_ref_id,
        reflection_yaml=a_ref_yaml,
        channel=io_channel,
    )
    if promoted_doc_ids:
        deps.append_session_log(
            "promoted_context_persisted",
            {
                "source_doc_id": a_id,
                "source_reflection_id": a_ref_id,
                "promoted_doc_ids": promoted_doc_ids,
                "count": len(promoted_doc_ids),
            },
        )


__all__ = ["RuntimeCommitPersistenceDependencies", "answer_commit_persistence"]
