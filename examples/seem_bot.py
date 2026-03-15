from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Annotated, Any, Literal, TypedDict
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages


# =============================================================================
# Types
# =============================================================================

class PassageRecord(TypedDict):
    passage_id: str
    kind: Literal["observation", "response"]
    observed_at: str
    sequence_index: int
    source_message_ids: list[str]
    canonical_text: str
    metadata: dict[str, Any]


class FactRecord(TypedDict):
    fact_id: str
    passage_id: str
    fact_type: str
    key: str
    value: str


class ContextRecord(TypedDict, total=False):
    thread_id: str
    now_utc: str
    latest_user_passage_id: str
    latest_passage_text: str
    latest_user_text: str
    user_intent_hint: str
    conversation_turn: int


class SelfAssessment(TypedDict, total=False):
    current_goal: str
    chosen_strategy: str
    confidence: float
    uncertainty_reason: str
    missing_information: list[str]
    risk_flags: list[str]
    last_updated_at: str


class SelfReflectionRecord(TypedDict):
    reflection_id: str
    timestamp: str
    turn_index: int
    trigger: Literal[
        "post_response",
        "validation_failure",
        "tool_failure",
        "user_correction",
        "periodic_review",
    ]
    summary: str
    what_worked: list[str]
    what_failed: list[str]
    adjustment: str
    confidence_delta: float


class ValidationRecord(TypedDict, total=False):
    passed: bool
    issues: list[str]
    checked_at: str


class PendingFocus(TypedDict, total=False):
    kind: Literal["assistant_question", "topic_under_discussion"]
    subject: str
    assistant_question: str
    created_at: str
    source_passage_id: str


class State(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    passages: list[PassageRecord]
    facts: list[FactRecord]
    context: ContextRecord
    response_plan: dict[str, Any]
    self_model: SelfAssessment
    self_history: list[SelfReflectionRecord]
    validation: ValidationRecord
    pending_focus: PendingFocus
    iteration: int


# =============================================================================
# Config
# =============================================================================

load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", os.getenv("SEEM_BOT_MODEL", "llama3.2:3b"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
X_OLLAMA_KEY = os.getenv("X_OLLAMA_KEY", "").strip()


def _ollama_client_kwargs() -> dict[str, object]:
    if X_OLLAMA_KEY:
        return {"client_kwargs": {"headers": {"X-Ollama-Key": X_OLLAMA_KEY}}}
    return {}


model = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0,
    **_ollama_client_kwargs(),
)


# =============================================================================
# Helpers
# =============================================================================

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _message_id(msg: AnyMessage, index_hint: int) -> str:
    existing = getattr(msg, "id", None)
    return str(existing) if existing else f"msg-{index_hint}-{uuid4().hex[:12]}"


def _message_text(msg: AnyMessage) -> str:
    content = msg.content
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def _next_passage_index(state: State) -> int:
    return len(state.get("passages", []))


def _latest_passage_of_kind(state: State, kind: str) -> PassageRecord | None:
    for passage in reversed(state.get("passages", [])):
        if passage["kind"] == kind:
            return passage
    return None


def _recent_user_texts(state: State, *, limit: int = 5, exclude_latest: bool = False) -> list[str]:
    observations = [
        _strip_role_prefix(p["canonical_text"], "human")
        for p in state.get("passages", [])
        if p["kind"] == "observation"
    ]
    if exclude_latest and observations:
        observations = observations[:-1]
    return [text for text in observations if text][-limit:]


def _make_passage(
    *,
    state: State,
    msg: AnyMessage,
    kind: Literal["observation", "response"],
    role_prefix: str,
    metadata: dict[str, Any] | None = None,
) -> PassageRecord:
    idx = _next_passage_index(state)
    return {
        "passage_id": f"passage-{uuid4().hex}",
        "kind": kind,
        "observed_at": _now_utc(),
        "sequence_index": idx,
        "source_message_ids": [_message_id(msg, idx)],
        "canonical_text": f"{role_prefix}: {_message_text(msg)}",
        "metadata": metadata or {},
    }


def _strip_role_prefix(text: str, prefix: str) -> str:
    wanted = f"{prefix}:"
    if text.lower().startswith(wanted.lower()):
        return text[len(wanted):].strip()
    return text.strip()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _dialogue_act_features(text: str) -> dict[str, bool]:
    tokens = _tokenize(text)
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

    looks_summary_request = (
        bool(token_set.intersection(summary_tokens))
        and bool(token_set.intersection({"i", "me", "my"}))
        and bool(token_set.intersection(recall_tokens))
    )

    is_bare_confirmation = is_short and bool(token_set.intersection(affirmation_tokens))
    is_bare_rejection = is_short and bool(token_set.intersection(rejection_tokens))
    is_bare_clarifier = is_short and has_question_mark and bool(token_set.intersection(clarification_tokens))

    return {
        "is_short": is_short,
        "has_question_mark": has_question_mark,
        "is_greeting": bool(token_set.intersection(greeting_tokens)) and is_short,
        "is_confirmation": is_bare_confirmation,
        "is_rejection": is_bare_rejection,
        "is_clarification": is_bare_clarifier,
        "is_summary_request": looks_summary_request,
        "starts_generation": bool(tokens) and tokens[0] in generation_verbs,
        "starts_analysis": bool(tokens) and tokens[0] in analysis_verbs,
    }


def _intent_hint(text: str) -> str:
    features = _dialogue_act_features(text)

    if features["is_greeting"]:
        return "casual_greeting"
    if features["is_clarification"]:
        return "clarification_request"
    if features["is_confirmation"]:
        return "confirmation"
    if features["is_rejection"]:
        return "rejection"
    if features["is_summary_request"]:
        return "request_user_query_summary"
    if features["has_question_mark"]:
        return "question"
    if features["starts_generation"]:
        return "generation_request"
    if features["starts_analysis"]:
        return "analysis_request"
    return "statement"


def _format_user_query_summary(items: list[str]) -> str:
    if not items:
        return "I don't have enough prior messages to summarize yet."
    bullets = "\n".join(f"- {item}" for item in items)
    return f"You asked about:\n{bullets}"


def _extract_simple_facts(passage: PassageRecord) -> list[FactRecord]:
    text = passage["canonical_text"]
    facts: list[FactRecord] = []

    mentions = re.findall(r"https?://\S+|[A-Za-z_][A-Za-z0-9_\-.:/]{2,}", text)
    for match in mentions:
        facts.append(
            {
                "fact_id": f"fact-{uuid4().hex}",
                "passage_id": passage["passage_id"],
                "fact_type": "token_mention",
                "key": "mention",
                "value": match,
            }
        )

    if "?" in text:
        facts.append(
            {
                "fact_id": f"fact-{uuid4().hex}",
                "passage_id": passage["passage_id"],
                "fact_type": "speech_act",
                "key": "kind",
                "value": "question",
            }
        )

    return facts


def _format_recent_passages(state: State, limit: int = 4) -> str:
    recent = state.get("passages", [])[-limit:]
    if not recent:
        return "(none)"
    return "\n".join(
        f"- [{p['sequence_index']}:{p['kind']}] {p['canonical_text']}"
        for p in recent
    )


def _format_recent_facts(state: State, limit: int = 8) -> str:
    recent = state.get("facts", [])[-limit:]
    if not recent:
        return "(none)"
    return "\n".join(f"- ({f['fact_type']}) {f['key']} = {f['value']}" for f in recent)


def _recent_self_reflections(state: State, limit: int = 3) -> str:
    reflections = state.get("self_history", [])[-limit:]
    if not reflections:
        return "(none)"
    return "\n".join(
        f"- {r['trigger']}: {r['summary']} (delta={r['confidence_delta']})"
        for r in reflections
    )


def _infer_pending_focus_from_ai(text: str) -> PendingFocus | None:
    stripped = text.strip()
    lower = stripped.lower()

    if not stripped:
        return None

    if stripped.endswith("?"):
        subject = "latest assistant question"

        patterns = [
            (r"what specific features.*structured memory", "features of structured memory"),
            (r"what kind of challenges.*grounded memory", "challenges in grounded memory development"),
            (r"what specific steps.*make it happen", "steps to make the project happen"),
            (r"what are you planning", "planned next steps"),
            (r"can you clarify", "the user's last point"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, lower):
                subject = label
                break

        return {
            "kind": "assistant_question",
            "subject": subject,
            "assistant_question": stripped,
            "created_at": _now_utc(),
        }

    topic_patterns = [
        (r"seem", "SEEM as a memory architecture"),
        (r"structured memory", "structured memory"),
        (r"grounded memory", "grounded memory for AI agents"),
        (r"non-grounded ai agents", "non-grounded AI agents"),
    ]
    for pattern, label in topic_patterns:
        if re.search(pattern, lower):
            return {
                "kind": "topic_under_discussion",
                "subject": label,
                "assistant_question": "",
                "created_at": _now_utc(),
            }

    return None


# =============================================================================
# Nodes
# =============================================================================

def stabilize_observation(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, HumanMessage):
        return {}

    passage = _make_passage(
        state=state,
        msg=last_msg,
        kind="observation",
        role_prefix="human",
    )
    return {
        "passages": state.get("passages", []) + [passage],
        "iteration": state.get("iteration", 0) + 1,
    }


def resolve_context(state: State, config) -> dict[str, Any]:
    latest = _latest_passage_of_kind(state, "observation")
    if not latest:
        return {}

    latest_user_text = _strip_role_prefix(latest["canonical_text"], "human")
    thread_id = config.get("configurable", {}).get("thread_id", "default-thread")

    context: ContextRecord = {
        "thread_id": thread_id,
        "now_utc": _now_utc(),
        "latest_user_passage_id": latest["passage_id"],
        "latest_passage_text": latest["canonical_text"],
        "latest_user_text": latest_user_text,
        "user_intent_hint": _intent_hint(latest_user_text),
        "conversation_turn": state.get("iteration", 0),
    }
    return {"context": context}


def extract_facts(state: State) -> dict[str, Any]:
    latest = _latest_passage_of_kind(state, "observation")
    if not latest:
        return {}

    new_facts = _extract_simple_facts(latest)
    return {"facts": state.get("facts", []) + new_facts}


def decide_response_plan(state: State) -> dict[str, Any]:
    ctx = state.get("context", {})
    pending_focus = state.get("pending_focus", {})
    intent = ctx.get("user_intent_hint", "statement")
    latest = ctx.get("latest_user_text", "")

    if intent == "clarification_request":
        mode = "clarify_prior_question"
    elif intent == "confirmation":
        mode = "advance_current_topic"
    elif intent == "rejection":
        mode = "repair_reference"
    elif intent == "casual_greeting":
        mode = "casual_reply"
    elif "help me" in latest.lower() or intent == "analysis_request":
        mode = "structured_help"
    elif intent == "generation_request":
        mode = "generate"
    elif intent == "question":
        mode = "answer"
    elif intent == "request_user_query_summary":
        mode = "summarize_user_queries"
    else:
        mode = "respond"

    return {
        "response_plan": {
            "mode": mode,
            "ground_on_passages": True,
            "ground_on_context": True,
            "ground_on_facts": True,
            "ground_on_pending_focus": bool(pending_focus),
            "render_directly_to_user": True,
        }
    }


def update_self_model(state: State) -> dict[str, Any]:
    ctx = state.get("context", {})
    plan = state.get("response_plan", {})
    latest_text = ctx.get("latest_user_text", "")
    intent = ctx.get("user_intent_hint", "unknown")
    pending_focus = state.get("pending_focus", {})

    missing: list[str] = []
    confidence = 0.8
    uncertainty_reason = ""
    risk_flags: list[str] = []

    if not latest_text:
        missing.append("latest_user_message")
        confidence = 0.2
        uncertainty_reason = "no latest user message available"
    elif intent == "casual_greeting":
        confidence = 0.95
    elif intent == "clarification_request":
        if pending_focus:
            confidence = 0.88
        else:
            confidence = 0.4
            uncertainty_reason = "clarification request without active referent"
            missing.append("pending_focus")
    elif intent == "confirmation":
        if pending_focus:
            confidence = 0.85
        else:
            confidence = 0.45
            uncertainty_reason = "confirmation without active topic"
            missing.append("pending_focus")
    elif intent == "statement":
        confidence = 0.55
        uncertainty_reason = "statement may not imply a concrete request"
    elif intent == "question":
        confidence = 0.75
    elif intent == "analysis_request":
        confidence = 0.72
    elif intent == "generation_request":
        confidence = 0.78

    if plan.get("mode") in {"respond", "answer", "structured_help", "clarify_prior_question"}:
        risk_flags.append("meta_leak_risk")

    self_model: SelfAssessment = {
        "current_goal": "Respond helpfully to the latest user turn",
        "chosen_strategy": plan.get("mode", "respond"),
        "confidence": confidence,
        "uncertainty_reason": uncertainty_reason,
        "missing_information": missing,
        "risk_flags": risk_flags,
        "last_updated_at": _now_utc(),
    }
    return {"self_model": self_model}


def answer_from_state(state: State) -> dict[str, Any]:
    ctx = state.get("context", {})
    plan = state.get("response_plan", {})
    self_model = state.get("self_model", {})
    pending_focus = state.get("pending_focus", {})
    latest_user_text = ctx.get("latest_user_text", "")
    intent = ctx.get("user_intent_hint", "statement")
    act = _dialogue_act_features(latest_user_text)

    if intent == "request_user_query_summary":
        summary_items = _recent_user_texts(state, exclude_latest=True)
        return {"messages": [AIMessage(content=_format_user_query_summary(summary_items))]}

    if act["is_confirmation"] and not pending_focus:
        recent = _recent_user_texts(state, limit=1, exclude_latest=True)
        if recent:
            content = (
                "Got it — it sounds like you're confirming this: "
                f"\"{recent[0]}\". If that's not right, tell me what you're saying yes to."
            )
        else:
            content = "Got it. What would you like to confirm exactly?"
        return {"messages": [AIMessage(content=content)]}

    if act["is_confirmation"] and pending_focus.get("kind") == "assistant_question":
        question = pending_focus.get("assistant_question", "")
        content = "Thanks for confirming."
        if question:
            content += f" You answered yes to: \"{question}\""
        content += " If you'd like, tell me the next detail and I'll build on it."
        return {"messages": [AIMessage(content=content)]}

    if act["is_rejection"] and not pending_focus:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Thanks — I may be missing what you're rejecting. "
                        "Could you say what part you want to change?"
                    )
                )
            ]
        }

    if act["is_rejection"] and pending_focus.get("kind") == "assistant_question":
        question = pending_focus.get("assistant_question", "")
        content = "Understood — thanks for clarifying."
        if question:
            content += f" You meant no to: \"{question}\""
        content += " What direction should we take instead?"
        return {"messages": [AIMessage(content=content)]}

    if act["is_clarification"] and not pending_focus:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Happy to clarify. Could you point to the specific sentence or topic you mean?"
                    )
                )
            ]
        }

    system_prompt = (
        "You are a helpful assistant.\n"
        "Use the provided structured state as hidden grounding.\n"
        "Answer the user directly.\n"
        "If the user asks for clarification like 'what do you mean?' or 'what?', "
        "first resolve it against PENDING FOCUS and the latest assistant question.\n"
        "If the user says 'yes', treat it as confirmation of the active topic when possible.\n"
        "Do not ask for clarification if the active referent is already available in the state.\n"
        "Do not mention THREAD CONTEXT, RESPONSE PLAN, RECENT PASSAGES, RECENT FACTS, "
        "SELF MODEL, or PENDING FOCUS.\n"
        "Do not say things like 'Based on the provided context' or "
        "'I will respond accordingly'.\n"
        "Return only the final assistant reply intended for the user.\n"
        "If the latest user message is casual, reply naturally and briefly.\n"
    )

    grounded_prompt = (
        f"LATEST USER MESSAGE\n"
        f"{latest_user_text}\n\n"
        f"THREAD CONTEXT\n"
        f"- thread_id: {ctx.get('thread_id', 'unknown')}\n"
        f"- now_utc: {ctx.get('now_utc', 'unknown')}\n"
        f"- turn: {ctx.get('conversation_turn', 'unknown')}\n"
        f"- intent_hint: {ctx.get('user_intent_hint', 'unknown')}\n\n"
        f"RESPONSE PLAN\n"
        f"{plan}\n\n"
        f"SELF MODEL\n"
        f"- chosen_strategy: {self_model.get('chosen_strategy', 'unknown')}\n"
        f"- confidence: {self_model.get('confidence', 'unknown')}\n"
        f"- uncertainty_reason: {self_model.get('uncertainty_reason', '')}\n"
        f"- missing_information: {self_model.get('missing_information', [])}\n"
        f"- risk_flags: {self_model.get('risk_flags', [])}\n\n"
        f"PENDING FOCUS\n"
        f"- kind: {pending_focus.get('kind', 'none')}\n"
        f"- subject: {pending_focus.get('subject', 'none')}\n"
        f"- assistant_question: {pending_focus.get('assistant_question', 'none')}\n\n"
        f"RECENT PASSAGES\n"
        f"{_format_recent_passages(state)}\n\n"
        f"RECENT FACTS\n"
        f"{_format_recent_facts(state)}\n\n"
        f"RECENT SELF REFLECTIONS\n"
        f"{_recent_self_reflections(state)}\n\n"
        f"Write the best direct reply to the user's latest message."
    )

    prompt_messages: list[AnyMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=grounded_prompt),
    ]

    try:
        answer = model.invoke(prompt_messages)
    except Exception as exc:
        answer = AIMessage(content=f"[offline fallback] Could not reach Ollama: {exc}")

    return {"messages": [answer]}


def validate_answer(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage):
        return {}

    text = _message_text(last_msg).lower()
    issues: list[str] = []

    forbidden_phrases = [
        "based on the provided context",
        "i will respond accordingly",
        "response plan",
        "recent passages",
        "recent facts",
        "thread context",
        "self model",
        "pending focus",
    ]
    for phrase in forbidden_phrases:
        if phrase in text:
            issues.append(f"meta_leak:{phrase}")

    validation: ValidationRecord = {
        "passed": not issues,
        "issues": issues,
        "checked_at": _now_utc(),
    }
    return {"validation": validation}


def reflect_on_outcome(state: State) -> dict[str, Any]:
    history = state.get("self_history", [])
    validation = state.get("validation", {})
    passed = validation.get("passed", True)
    issues = validation.get("issues", [])

    if passed:
        record: SelfReflectionRecord = {
            "reflection_id": f"refl-{uuid4().hex}",
            "timestamp": _now_utc(),
            "turn_index": state.get("iteration", 0),
            "trigger": "post_response",
            "summary": "final answer stayed user-facing",
            "what_worked": ["final answer remained direct"],
            "what_failed": [],
            "adjustment": "keep current rendering contract",
            "confidence_delta": 0.05,
        }
    else:
        record = {
            "reflection_id": f"refl-{uuid4().hex}",
            "timestamp": _now_utc(),
            "turn_index": state.get("iteration", 0),
            "trigger": "validation_failure",
            "summary": "answer leaked internal scaffolding",
            "what_worked": [],
            "what_failed": issues,
            "adjustment": "tighten render contract and avoid meta-commentary",
            "confidence_delta": -0.2,
        }

    return {"self_history": history + [record]}


def stabilize_response(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage):
        return {}

    passage = _make_passage(
        state=state,
        msg=last_msg,
        kind="response",
        role_prefix="ai",
        metadata={
            "source": "answer_from_state",
            "validation_passed": state.get("validation", {}).get("passed", True),
        },
    )
    return {"passages": state.get("passages", []) + [passage]}


def update_pending_focus(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage):
        return {}

    focus = _infer_pending_focus_from_ai(_message_text(last_msg))
    if not focus:
        return {}

    latest_response = _latest_passage_of_kind(state, "response")
    if latest_response:
        focus["source_passage_id"] = latest_response["passage_id"]

    return {"pending_focus": focus}


# =============================================================================
# Graph
# =============================================================================

graph = StateGraph(State)

graph.add_node("stabilize_observation", stabilize_observation)
graph.add_node("resolve_context", resolve_context)
graph.add_node("extract_facts", extract_facts)
graph.add_node("decide_response_plan", decide_response_plan)
graph.add_node("update_self_model", update_self_model)
graph.add_node("answer_from_state", answer_from_state)
graph.add_node("validate_answer", validate_answer)
graph.add_node("reflect_on_outcome", reflect_on_outcome)
graph.add_node("stabilize_response", stabilize_response)
graph.add_node("update_pending_focus", update_pending_focus)

graph.add_edge(START, "stabilize_observation")
graph.add_edge("stabilize_observation", "resolve_context")
graph.add_edge("resolve_context", "extract_facts")
graph.add_edge("extract_facts", "decide_response_plan")
graph.add_edge("decide_response_plan", "update_self_model")
graph.add_edge("update_self_model", "answer_from_state")
graph.add_edge("answer_from_state", "validate_answer")
graph.add_edge("validate_answer", "reflect_on_outcome")
graph.add_edge("reflect_on_outcome", "stabilize_response")
graph.add_edge("stabilize_response", "update_pending_focus")
graph.add_edge("update_pending_focus", END)

checkpointer = InMemorySaver()
workflow = graph.compile(checkpointer=checkpointer)


# =============================================================================
# CLI loop outside the graph
# =============================================================================

def main() -> None:
    config = {
        "configurable": {"thread_id": "demo-cli-thread"},
        "recursion_limit": 100,
    }

    bootstrap_state: State = {
        "passages": [],
        "facts": [],
        "self_history": [],
        "iteration": 0,
    }

    print("Type 'exit' or press Enter on an empty line to quit.")
    first_turn = True

    while True:
        try:
            user_query = input("query: ").strip()
        except EOFError:
            print()
            break

        if not user_query or user_query.lower() in {"exit", "quit"}:
            break

        turn_input: State = {"messages": [HumanMessage(content=user_query)]}
        if first_turn:
            turn_input = {**bootstrap_state, **turn_input}
            first_turn = False

        result = workflow.invoke(turn_input, config=config)

        messages = result.get("messages", [])
        if messages and isinstance(messages[-1], AIMessage):
            print("answer:", messages[-1].content)
        else:
            print("answer: [no AI message produced]")


if __name__ == "__main__":
    main()
