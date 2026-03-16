from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from .state_types import State


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


def _format_summary(state: State) -> str:
    items = []
    for passage in state.get("passages", []):
        if passage["kind"] == "observation":
            text = passage["canonical_text"]
            if text.lower().startswith("human:"):
                items.append(text[len("human:") :].strip())
    items = items[:-1] if items else []
    if not items:
        return "I don't have enough prior messages to summarize yet."
    return "You asked about:\n" + "\n".join(f"- {item}" for item in items[-5:])


def render_reply(state: State) -> dict[str, Any]:
    plan = state.get("response_plan", {})
    render_context = state.get("render_context", {})
    resolution = state.get("referent_resolution", {})

    mode = plan.get("mode", "respond")

    if mode == "summarize_user_queries":
        return {"messages": [AIMessage(content=_format_summary(state))]}

    if mode == "clarify_missing_referent":
        return {
            "messages": [
                AIMessage(content="What are you referring to exactly?")
            ]
        }

    if mode == "advance_current_topic" and resolution.get("resolved"):
        subject = resolution.get("referent_subject", "")
        if subject:
            return {
                "messages": [
                    AIMessage(content=f"Got it — you mean yes regarding {subject}. Go on.")
                ]
            }
        return {
            "messages": [
                AIMessage(content="Got it. Go on.")
            ]
        }

    if mode == "repair_direction" and resolution.get("resolved"):
        subject = resolution.get("referent_subject", "")
        if subject:
            return {
                "messages": [
                    AIMessage(content=f"Understood — you mean no regarding {subject}. What direction should we take instead?")
                ]
            }
        return {
            "messages": [
                AIMessage(content="Understood. What direction should we take instead?")
            ]
        }

    system_prompt = (
        "You are a helpful assistant.\n"
        "Reply directly to the user.\n"
        "Do not mention internal state, routing, metadata, plans, or hidden context.\n"
        "Return only the final user-facing reply.\n"
    )

    supporting = "\n".join(render_context.get("supporting_passages", []))

    human_prompt = (
        f"LATEST USER MESSAGE\n{render_context.get('latest_user_text', '')}\n\n"
        f"RESPONSE MODE\n{render_context.get('response_mode', 'respond')}\n\n"
        f"RESOLVED REFERENT\n"
        f"kind={render_context.get('referent_kind', 'none')}\n"
        f"subject={render_context.get('referent_subject', '')}\n\n"
        f"SUPPORTING PASSAGES\n{supporting}\n\n"
        f"Write the best direct reply."
    )

    prompt_messages: list[AnyMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        answer = model.invoke(prompt_messages)
    except Exception as exc:
        answer = AIMessage(content=f"[offline fallback] Could not reach Ollama: {exc}")

    return {"messages": [answer]}
