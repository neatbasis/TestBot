from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import StrEnum


class MemoryStratum(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL_DIALOGUE_STATE = "procedural_dialogue_state"


class SegmentType(StrEnum):
    CONTIGUOUS_TOPIC = "contiguous_topic"
    REPAIR = "repair"
    TASK = "task"
    SELF_PROFILE = "self_profile"
    TEMPORAL_EPISODE = "temporal_episode"


@dataclass(frozen=True)
class SegmentDescriptor:
    segment_type: SegmentType
    segment_id: str
    continuity_key: str


def derive_segment_descriptor(
    *,
    utterance: str,
    prior_descriptor: SegmentDescriptor | None = None,
    has_dialogue_state: bool = False,
) -> SegmentDescriptor:
    lowered = (utterance or "").strip().lower()
    if "my name is" in lowered or has_dialogue_state:
        segment_type = SegmentType.SELF_PROFILE
        continuity_key = "self_profile:user_identity"
    elif any(token in lowered for token in ("sorry", "didn't mean", "clarify", "what do you need")):
        segment_type = SegmentType.REPAIR
        continuity_key = "repair:continuation"
    elif any(token in lowered for token in ("yesterday", "today", "tomorrow", "ago")):
        segment_type = SegmentType.TEMPORAL_EPISODE
        continuity_key = "temporal:episode"
    elif "?" in lowered:
        segment_type = SegmentType.TASK
        continuity_key = "task:query"
    else:
        segment_type = SegmentType.CONTIGUOUS_TOPIC
        words = re.findall(r"[a-z0-9]+", lowered)
        continuity_key = "topic:" + "-".join(words[:6] or ["generic"])

    if (
        prior_descriptor is not None
        and prior_descriptor.segment_type == segment_type
        and prior_descriptor.continuity_key == continuity_key
    ):
        return prior_descriptor

    segment_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{segment_type.value}:{continuity_key}"))
    return SegmentDescriptor(segment_type=segment_type, segment_id=segment_id, continuity_key=continuity_key)


def make_membership_edge_ref(*, segment_id: str, doc_id: str) -> str:
    return f"edge:{segment_id}:{doc_id}"


def apply_persistence_metadata(
    *,
    metadata: dict[str, object],
    stratum: MemoryStratum,
    segment: SegmentDescriptor,
    member_doc_id: str,
) -> dict[str, object]:
    edge_ref = make_membership_edge_ref(segment_id=segment.segment_id, doc_id=member_doc_id)
    return {
        **metadata,
        "memory_stratum": stratum.value,
        "segment_type": segment.segment_type.value,
        "segment_id": segment.segment_id,
        "segment_membership_edge_refs": [edge_ref],
    }
