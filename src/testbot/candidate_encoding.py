from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from testbot.pipeline_state import PipelineState
from testbot.turn_observation import TurnObservation


@dataclass(frozen=True)
class SpeechActCandidate:
    label: str
    confidence: float
    rationale: str


@dataclass(frozen=True)
class FactCandidate:
    key: str
    value: str
    confidence: float
    provenance: str = "user_utterance"


@dataclass(frozen=True)
class DialogueStateCandidate:
    label: str
    confidence: float


@dataclass(frozen=True)
class RepairCandidate:
    label: str
    confidence: float
    rationale: str


@dataclass(frozen=True)
class EncodedTurnCandidates:
    rewritten_query: str
    speech_acts: list[SpeechActCandidate] = field(default_factory=list)
    facts: list[FactCandidate] = field(default_factory=list)
    dialogue_state: list[DialogueStateCandidate] = field(default_factory=list)
    repairs: list[RepairCandidate] = field(default_factory=list)

    def as_artifact_payload(self) -> dict[str, object]:
        return {
            "facts": [asdict(fact) for fact in self.facts],
            "speech_acts": [asdict(candidate) for candidate in self.speech_acts],
            "dialogue_state": [asdict(candidate) for candidate in self.dialogue_state],
            "repairs": [asdict(candidate) for candidate in self.repairs],
        }


_NAME_PATTERN = re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z\-']*)", re.IGNORECASE)


def encode_turn_candidates(
    state: PipelineState,
    *,
    observation: TurnObservation,
    rewritten_query: str,
) -> EncodedTurnCandidates:
    utterance = observation.utterance.strip()
    speech_acts: list[SpeechActCandidate] = []
    facts: list[FactCandidate] = []
    dialogue_state: list[DialogueStateCandidate] = []

    if utterance.endswith("?"):
        speech_acts.append(SpeechActCandidate(label="query", confidence=0.9, rationale="question_mark"))
    else:
        speech_acts.append(SpeechActCandidate(label="inform", confidence=0.6, rationale="declarative_default"))

    name_match = _NAME_PATTERN.search(utterance)
    if name_match:
        facts.append(FactCandidate(key="user_name", value=name_match.group(1), confidence=0.95))
        dialogue_state.append(DialogueStateCandidate(label="self_identification", confidence=0.9))

    return EncodedTurnCandidates(
        rewritten_query=rewritten_query or state.user_input,
        speech_acts=speech_acts,
        facts=facts,
        dialogue_state=dialogue_state,
    )
