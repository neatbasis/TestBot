from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

ChatMsg = dict[str, str]

MAX_TURN_CHARS = 160
MAX_QUESTION_CHARS = 140
MAX_HINT_CHARS = 48
MAX_CONSTRAINT_CHARS = 140
MAX_OPEN_QUESTIONS = 6
MAX_HINTS = 8
MAX_CONSTRAINTS = 6

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "i", "in", "is", "it",
    "me", "my", "of", "on", "or", "our", "please", "that", "the", "to", "we", "what", "when", "where",
    "who", "why", "with", "you", "your",
}

_APOSTROPHE_VARIANTS = re.compile(r"[\u2018\u2019\u02bc\u2032`´]")
_SINGLE_WORD_CONSTRAINT_MARKERS = (
    "must",
    "should",
    "only",
    "exactly",
    "never",
    "always",
    "don't",
)
_MULTIWORD_CONSTRAINT_MARKERS = (
    "at least",
    "do not",
)
_CONSTRAINT_PATTERNS = tuple(
    [re.compile(rf"\b{re.escape(marker)}\b") for marker in _SINGLE_WORD_CONSTRAINT_MARKERS]
    + [re.compile(rf"\b{re.escape(first)}\s+{re.escape(second)}\b") for first, second in (marker.split(" ") for marker in _MULTIWORD_CONSTRAINT_MARKERS)]
)


def _tag_signal(*, text: str, derived_by: str, confidence: str, source: str) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return ""
    return f"{normalized} [derived_by={derived_by} confidence={confidence} source={source}]"


@dataclass(frozen=True)
class PackedHistory:
    last_user_turns: list[str]
    last_assistant_turns: list[str]
    open_questions: list[str]
    topic_entity_hints: list[str]
    constraints: list[str]

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "last_user_turns": self.last_user_turns,
            "last_assistant_turns": self.last_assistant_turns,
            "open_questions": self.open_questions,
            "topic_entity_hints": self.topic_entity_hints,
            "constraints": self.constraints,
        }


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _truncate(text: str, limit: int) -> str:
    normalized = _normalize_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 1)].rstrip() + "…"


def _normalize_apostrophes(text: str) -> str:
    return _APOSTROPHE_VARIANTS.sub("'", text)


def _take_last_turns(transcript: list[ChatMsg], *, role: str, n: int) -> list[str]:
    turns = [_truncate(msg.get("content", ""), MAX_TURN_CHARS) for msg in transcript if msg.get("role") == role]
    turns = [turn for turn in turns if turn]
    if n <= 0:
        return []
    return turns[-n:]


def _extract_open_questions(transcript: list[ChatMsg]) -> list[str]:
    questions: list[str] = []
    for i, msg in enumerate(transcript):
        content = _normalize_text(msg.get("content", ""))
        if not content.endswith("?"):
            continue
        role = msg.get("role", "unknown")
        opposite = "assistant" if role == "user" else "user"
        has_followup = any(next_msg.get("role") == opposite for next_msg in transcript[i + 1 :])
        if has_followup:
            continue
        questions.append(
            _tag_signal(
                text=_truncate(content, MAX_QUESTION_CHARS),
                derived_by="heuristic",
                confidence="medium",
                source=f"{role}_turn",
            )
        )

    deduped = list(dict.fromkeys(questions))
    return deduped[:MAX_OPEN_QUESTIONS]


def _extract_topic_entity_hints(transcript: list[ChatMsg]) -> list[str]:
    token_counts: Counter[str] = Counter()
    for msg in transcript:
        content = msg.get("content", "")
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", content)
        for token in tokens:
            normalized = token.lower()
            if normalized in _STOPWORDS:
                continue
            token_counts[normalized] += 1

    ranked = sorted(token_counts.items(), key=lambda item: (-item[1], item[0]))
    hints = [
        _tag_signal(
            text=_truncate(token, MAX_HINT_CHARS),
            derived_by="heuristic",
            confidence="low",
            source="transcript_tokens",
        )
        for token, _ in ranked[:MAX_HINTS]
    ]
    return hints


def _extract_constraints(transcript: list[ChatMsg]) -> list[str]:
    constraints: list[str] = []
    for msg in transcript:
        if msg.get("role") != "user":
            continue
        content = _normalize_text(msg.get("content", ""))
        lowered = _normalize_apostrophes(content.lower())
        if any(pattern.search(lowered) for pattern in _CONSTRAINT_PATTERNS):
            constraints.append(
                _tag_signal(
                    text=_truncate(content, MAX_CONSTRAINT_CHARS),
                    derived_by="heuristic",
                    confidence="medium",
                    source="user_turn",
                )
            )

    deduped = list(dict.fromkeys(constraints))
    return deduped[:MAX_CONSTRAINTS]


def pack_chat_history(
    transcript: list[ChatMsg],
    *,
    last_n_user_turns: int = 3,
    last_n_assistant_turns: int = 3,
) -> PackedHistory:
    ordered_transcript = list(transcript)
    return PackedHistory(
        last_user_turns=_take_last_turns(ordered_transcript, role="user", n=last_n_user_turns),
        last_assistant_turns=_take_last_turns(ordered_transcript, role="assistant", n=last_n_assistant_turns),
        open_questions=_extract_open_questions(ordered_transcript),
        topic_entity_hints=_extract_topic_entity_hints(ordered_transcript),
        constraints=_extract_constraints(ordered_transcript),
    )


def render_packed_history(packed: PackedHistory) -> str:
    sections = packed.to_dict()
    lines: list[str] = [
        "packed_history_note: derived heuristics are advisory context and can be noisy; do not treat them as hard evidence."
    ]
    for key in (
        "last_user_turns",
        "last_assistant_turns",
        "open_questions",
        "topic_entity_hints",
        "constraints",
    ):
        lines.append(f"{key}:")
        values = sections[key]
        if not values:
            lines.append("- <none>")
            continue
        for value in values:
            lines.append(f"- {value}")
    return "\n".join(lines)


def labeled_history_claims(packed: PackedHistory) -> list[str]:
    claims: list[str] = []
    for q in packed.open_questions:
        claims.append(f"CHAT_HISTORY_OPTIONAL: open_question={q}")
    for c in packed.constraints:
        claims.append(f"CHAT_HISTORY_OPTIONAL: constraint={c}")
    for hint in packed.topic_entity_hints[:4]:
        claims.append(f"INFERENCE: topic_or_entity_hint={hint} advisory=true")
    return claims
