"""Deterministic intent routing for incoming user utterances."""

from __future__ import annotations

import re
from enum import Enum


class IntentType(str, Enum):
    """Top-level intent classes used by the pipeline router."""

    KNOWLEDGE_QUESTION = "knowledge_question"
    META_CONVERSATION = "meta_conversation"
    CAPABILITIES_HELP = "capabilities_help"
    MEMORY_RECALL = "memory_recall"
    TIME_QUERY = "time_query"
    CONTROL = "control"


_CONTROL_PATTERNS = (
    r"\b(cancel|stop|abort|nevermind|never mind)\b",
    r"\b(reset|restart)\b",
    r"\b(quit|exit|shutdown)\b",
)

_MEMORY_RECALL_PATTERNS = (
    r"\bwhat did (i|we|you)\b",
    r"\bdo you remember\b",
    r"\b(remind me|recall|remember)\b",
    r"\b(last time|earlier|before|yesterday)\b",
    r"\bwhat (was|were) (my|our)\b",
)

_META_CONVERSATION_PATTERNS = (
    r"\b(about this chat|our conversation|this conversation|this chat)\b",
    r"\bwhat('?s| is) relevant\b",
    r"\bsummarize (this|our) (chat|conversation)\b",
    r"\bhow are we doing\b",
)

_CAPABILITIES_HELP_PATTERNS = (
    r"^\s*help\s*$",
    r"\bwhat can you do\b",
    r"\bcapabilities\b",
    r"\byour capabilities\b",
    r"\bhelp options\b",
)

_TIME_QUERY_PATTERNS = (
    r"\bhow many (seconds?|minutes?|hours?|days?) ago\b",
    r"\bwhat is (today|tomorrow|yesterday)\b",
)

_KNOWLEDGE_CUES = (
    r"^\s*what is\b",
    r"^\s*who is\b",
    r"^\s*when (is|was)\b",
    r"^\s*define\b",
    r"^\s*explain\b",
    r"\bhow does\b",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_intent(user_input: str) -> IntentType:
    """Classify user intent using deterministic rule precedence.

    Precedence is intentional:
    1. Control commands override all other categories.
    2. Memory recall requests win over conversation-meta language.
    3. Time queries use a dedicated path.
    4. Capabilities/help requests use a stable responder path.
    5. Meta-conversation requests are routed separately from factual Q&A.
    6. Knowledge questions and the fallback default are KNOWLEDGE_QUESTION.
    """

    normalized = user_input.strip().lower()
    if not normalized:
        return IntentType.KNOWLEDGE_QUESTION

    if _matches_any(normalized, _CONTROL_PATTERNS):
        return IntentType.CONTROL
    if _matches_any(normalized, _MEMORY_RECALL_PATTERNS):
        return IntentType.MEMORY_RECALL
    if _matches_any(normalized, _TIME_QUERY_PATTERNS):
        return IntentType.TIME_QUERY
    if _matches_any(normalized, _CAPABILITIES_HELP_PATTERNS):
        return IntentType.CAPABILITIES_HELP
    if _matches_any(normalized, _META_CONVERSATION_PATTERNS):
        return IntentType.META_CONVERSATION
    if _matches_any(normalized, _KNOWLEDGE_CUES):
        return IntentType.KNOWLEDGE_QUESTION
    return IntentType.KNOWLEDGE_QUESTION
