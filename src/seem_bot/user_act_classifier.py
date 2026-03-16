from __future__ import annotations

import re
from typing import Any

from .passage_log import latest_passage_of_kind
from .state_types import State, UserAct
from .utils import strip_role_prefix


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def classify_text(text: str) -> UserAct:
    tokens = tokenize(text)
    token_set = set(tokens)
    is_short = len(tokens) <= 3
    has_question_mark = "?" in text

    greeting_tokens = {"hi", "hello", "hey", "yo", "sup"}
    affirmation_tokens = {"yes", "yep", "yeah", "sure", "ok", "okay", "correct", "right", "exactly"}
    rejection_tokens = {"no", "nope", "nah", "wrong", "incorrect"}
    clarification_tokens = {"what", "mean", "clarify", "confused"}
    summary_tokens = {"summarize", "summarise", "summary", "recap"}
    recall_tokens = {"asked", "ask", "said", "tell", "told"}
    generation_verbs = {"write", "generate", "draft", "create", "compose", "build"}
    analysis_verbs = {"fix", "debug", "explain", "review", "analyze", "analyse", "inspect"}

    if is_short and token_set.intersection(greeting_tokens):
        return {"act_type": "greeting", "confidence": 0.98}

    if is_short and token_set.intersection(affirmation_tokens):
        return {"act_type": "confirmation", "confidence": 0.95}

    if is_short and token_set.intersection(rejection_tokens):
        return {"act_type": "rejection", "confidence": 0.95}

    if is_short and has_question_mark and token_set.intersection(clarification_tokens):
        return {"act_type": "clarification", "confidence": 0.9}

    if token_set.intersection(summary_tokens) and token_set.intersection({"i", "me", "my"}) and token_set.intersection(recall_tokens):
        return {"act_type": "summary_request", "confidence": 0.9}

    if tokens and tokens[0] in generation_verbs:
        return {"act_type": "generation_request", "confidence": 0.85}

    if tokens and tokens[0] in analysis_verbs:
        return {"act_type": "analysis_request", "confidence": 0.85}

    if has_question_mark:
        return {"act_type": "question", "confidence": 0.8}

    return {"act_type": "statement", "confidence": 0.65}


def classify_user_act(state: State) -> dict[str, Any]:
    latest = latest_passage_of_kind(state, "observation")
    if not latest:
        return {}

    latest_user_text = strip_role_prefix(latest["canonical_text"], "human")
    return {"user_act": classify_text(latest_user_text)}
