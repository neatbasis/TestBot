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

_PROFILE_UPDATE_PATTERNS = (
    r"^\s*i am\s+[\w'-]+(?:\s+[\w'-]+)*\s*[.!?]*\s*$",
    r"^\s*i'm\s+[\w'-]+(?:\s+[\w'-]+)*\s*[.!?]*\s*$",
    r"^\s*my name is\s+[\w'-]+(?:\s+[\w'-]+)*\s*[.!?]*\s*$",
)

_SOCIAL_CHAT_PATTERNS = (
    r"^\s*(hi|hello|hey|hiya)\s*[.!?]*\s*$",
)

_GREETING_COMMAND_PATTERNS = (
    r"^\s*say\s+hello\b",
)

_CAPABILITIES_HELP_PATTERNS = (
    r"^\s*help\s*$",
    r"\bwhat can you do\b",
    r"\bcapabilities\b",
    r"\byour capabilities\b",
    r"\bhelp options\b",
)

_SATELLITE_ACTION_PATTERNS = (
    r"\bask (?:something\s+)?(?:via|through) satellite\b",
    r"\buse satellite\b",
    r"\bstart satellite conversation\b",
    r"\bsatellite (?:ask|conversation|mode)\b",
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


def is_satellite_action_request(user_input: str) -> bool:
    """Return whether an utterance is a direct request for satellite interaction actions."""

    normalized = (user_input or "").strip().lower()
    if not normalized:
        return False
    return _matches_any(normalized, _SATELLITE_ACTION_PATTERNS)


def classify_intent(user_input: str | None) -> IntentType:
    """Classify user intent using deterministic rule precedence.

    Precedence is intentional:
    1. Control commands override all other categories.
    2. Time queries use a dedicated path (even when memory language is present).
    3. Memory recall requests win over conversation-meta language.
    4. Capabilities/help requests use a stable responder path.
    5. Explicit profile updates are routed as non-knowledge conversation.
    6. Greeting/social prompts are routed as non-knowledge conversation.
    7. Greeting commands are routed as control actions.
    8. Meta-conversation requests are routed separately from factual Q&A.
    9. Knowledge questions and the fallback default are KNOWLEDGE_QUESTION.
    """

    normalized = (user_input or "").strip().lower()
    if not normalized:
        return IntentType.KNOWLEDGE_QUESTION

    if _matches_any(normalized, _CONTROL_PATTERNS):
        return IntentType.CONTROL
    if _matches_any(normalized, _TIME_QUERY_PATTERNS):
        return IntentType.TIME_QUERY
    if _matches_any(normalized, _MEMORY_RECALL_PATTERNS):
        return IntentType.MEMORY_RECALL
    if _matches_any(normalized, _PROFILE_UPDATE_PATTERNS):
        return IntentType.META_CONVERSATION
    if _matches_any(normalized, _SOCIAL_CHAT_PATTERNS):
        return IntentType.META_CONVERSATION
    if _matches_any(normalized, _GREETING_COMMAND_PATTERNS):
        return IntentType.CONTROL
    if is_satellite_action_request(normalized):
        return IntentType.CAPABILITIES_HELP
    if _matches_any(normalized, _CAPABILITIES_HELP_PATTERNS):
        return IntentType.CAPABILITIES_HELP
    if _matches_any(normalized, _META_CONVERSATION_PATTERNS):
        return IntentType.META_CONVERSATION
    if _matches_any(normalized, _KNOWLEDGE_CUES):
        return IntentType.KNOWLEDGE_QUESTION
    return IntentType.KNOWLEDGE_QUESTION
