"""Runtime mode runners.

Interaction/profile selection remains planner-owned via
``testbot.interaction_planner.select_interaction_policy_request``.
This module intentionally avoids direct monolith imports.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
import re

from homeassistant_api import Client
from langchain_ollama import ChatOllama

from testbot.adapters.ask_gateway import AskGateway, STOP_DECISION_ID
from testbot.domain import Clock
from testbot.interaction_planner import COLLECT_TURN_INPUT_INTENT, select_interaction_policy_request
from testbot.interaction_policy import ChannelContext
from testbot.ports import MemoryStorePort

_TERMINAL_STOP_DECISION_IDS = frozenset(
    {
        STOP_DECISION_ID,
        "cancel",
        "cancelled",
        "user_cancelled",
        "user_aborted",
        "abort",
        "aborted",
        "interrupted",
        "interrupt",
        "eof",
    }
)
_TERMINAL_STOP_SENTENCES = frozenset({"stop", "quit", "exit", "cancel", "abort"})
_RETRYABLE_ERROR_MARKERS = (
    "timeout",
    "temporar",
    "unavailable",
    "try again",
    "connection",
    "network",
    "reset",
)
_LAST_SUCCESSFUL_ASK_CHANNEL_CONTEXT_KEY = "last_successful_ask_channel_context"
_KNOWN_ARTIFACT_EXACT_PHRASES = frozenset(
    {
        "thanks for watching",
        "thank you for watching",
        "see you next time",
        "thanks for listening",
        "thank you for listening",
    }
)
_KNOWN_ARTIFACT_FRAGMENT_PHRASES = frozenset(
    {
        "subtitles by",
        "captions by",
        "translated by",
        "amara.org community",
    }
)
_CONTEXT_TOKEN_PATTERN = re.compile(r"[a-z0-9']+")
_CONTEXT_TOKEN_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "ask",
        "for",
        "one",
        "please",
        "the",
        "to",
    }
)


@dataclass(frozen=True)
class ArtifactAcceptanceDecision:
    likely_artifact: bool
    context_consistent: bool
    artifact_reasons: tuple[str, ...]

    @property
    def should_reject(self) -> bool:
        return self.likely_artifact and not self.context_consistent


def _as_channel_context(resolved_channel: str | None) -> ChannelContext | None:
    if resolved_channel == "satellite":
        return "satellite"
    if resolved_channel == "terminal":
        return "cli"
    return None


def _read_recent_successful_channel_context(runtime: dict[str, object]) -> ChannelContext | None:
    value = runtime.get(_LAST_SUCCESSFUL_ASK_CHANNEL_CONTEXT_KEY)
    if value == "satellite":
        return "satellite"
    if value == "cli":
        return "cli"
    return None


def _persist_recent_successful_channel_context(*, runtime: dict[str, object], ask_result_channel: str | None) -> None:
    channel_context = _as_channel_context(ask_result_channel)
    if channel_context is None:
        return
    runtime[_LAST_SUCCESSFUL_ASK_CHANNEL_CONTEXT_KEY] = channel_context


def _is_terminal_stop_signal(*, decision_id: str | None, sentence: str) -> bool:
    normalized_decision = str(decision_id or "").strip().lower()
    if normalized_decision in _TERMINAL_STOP_DECISION_IDS:
        return True
    normalized_sentence = sentence.strip().lower()
    return normalized_sentence in _TERMINAL_STOP_SENTENCES


def _is_retryable_ask_error(error: str) -> bool:
    normalized_error = error.strip().lower()
    return any(marker in normalized_error for marker in _RETRYABLE_ERROR_MARKERS)


def _normalize_transcript_artifact_phrase(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _looks_like_repeated_low_information_loop(normalized_sentence: str) -> bool:
    words = normalized_sentence.split()
    if len(words) < 4:
        return False
    if len(set(words)) == 1:
        return True
    if len(words) % 2 != 0:
        return False
    two_word_chunk = words[:2]
    return two_word_chunk * (len(words) // 2) == words


def _artifact_evidence_reasons(sentence: str) -> tuple[str, ...]:
    normalized_sentence = _normalize_transcript_artifact_phrase(sentence)
    if not normalized_sentence:
        return ()
    reasons: list[str] = []
    if _looks_like_repeated_low_information_loop(normalized_sentence):
        reasons.append("repeated_low_information_loop")
    if normalized_sentence in _KNOWN_ARTIFACT_EXACT_PHRASES:
        reasons.append("exact_known_phrase")
    if any(
        phrase in normalized_sentence and normalized_sentence != phrase for phrase in _KNOWN_ARTIFACT_EXACT_PHRASES
    ):
        reasons.append("contains_known_artifact_fragment")
    if any(phrase in normalized_sentence for phrase in _KNOWN_ARTIFACT_FRAGMENT_PHRASES):
        reasons.append("contains_known_artifact_fragment")
    return tuple(reasons)


def _extract_context_tokens(text: str) -> set[str]:
    tokens = {token for token in _CONTEXT_TOKEN_PATTERN.findall(text.lower()) if len(token) > 2}
    return {token for token in tokens if token not in _CONTEXT_TOKEN_STOPWORDS}


def _contains_meaningful_content_beyond_artifact_phrase(sentence: str) -> bool:
    normalized_sentence = _normalize_transcript_artifact_phrase(sentence)
    residual = normalized_sentence
    for phrase in _KNOWN_ARTIFACT_EXACT_PHRASES.union(_KNOWN_ARTIFACT_FRAGMENT_PHRASES):
        residual = residual.replace(phrase, " ")
    residual_tokens = _extract_context_tokens(residual)
    if len(residual_tokens) < 3:
        return False
    filler_tokens = {
        "thank",
        "thanks",
        "watching",
        "listening",
        "next",
        "time",
        "community",
    }
    return any(token not in filler_tokens for token in residual_tokens)


def _is_context_consistent_with_invited_response(*, sentence: str, question: str) -> bool:
    sentence_tokens = _extract_context_tokens(sentence)
    if not sentence_tokens:
        return False
    prompt_tokens = _extract_context_tokens(question)
    if sentence_tokens.intersection(prompt_tokens):
        return True
    return _contains_meaningful_content_beyond_artifact_phrase(sentence)


def _classify_artifact_vs_context(
    *, sentence: str, question: str
) -> ArtifactAcceptanceDecision:
    artifact_reasons = _artifact_evidence_reasons(sentence)
    return ArtifactAcceptanceDecision(
        likely_artifact=bool(artifact_reasons),
        context_consistent=_is_context_consistent_with_invited_response(
            sentence=sentence,
            question=question,
        ),
        artifact_reasons=artifact_reasons,
    )


def run_cli_mode(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[dict[str, str]],
    near_tie_delta: float,
    capability_snapshot: object,
    clock: Clock,
    ask_gateway: AskGateway,
    run_chat_loop: Callable[..., None],
) -> None:
    print("CLI chat ready. Ask memory-grounded questions; type 'stop' to exit.")
    # Input collection is Ask-backed in CLI mode; output remains direct print() for now.
    # This split is intentional until output-channel unification is explicitly scheduled.

    interaction_plan = select_interaction_policy_request(
        interaction_intent=COLLECT_TURN_INPUT_INTENT,
        channel_context="cli",
        task_flow_context="memory_chat_loop",
    )

    def _read() -> str | None:
        recent_successful_channel_context = _read_recent_successful_channel_context(runtime)
        ask_result = ask_gateway.request_turn_input_for_policy(
            interaction_policy=interaction_plan.request,
            question="Ask one memory-grounded question.",
            timeout_s=60.0,
            recent_successful_channel_context=recent_successful_channel_context,
        )
        if _is_terminal_stop_signal(decision_id=ask_result.decision_id, sentence=ask_result.sentence):
            return "stop"
        if ask_result.error:
            if _is_retryable_ask_error(ask_result.error):
                print(f"bot> I didn't get that yet ({ask_result.error}). Please try again.")
                return ""
            print(f"bot> Ask input is unavailable ({ask_result.error}). Stopping.")
            return "stop"
        if not ask_result.sentence.strip():
            print("bot> I heard silence. Try again.")
            return ""
        _persist_recent_successful_channel_context(runtime=runtime, ask_result_channel=ask_result.resolved_channel)
        return ask_result.sentence

    def _send(text: str) -> None:
        print(f"bot> {text}")

    run_chat_loop(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel="cli",
        capability_status="ask_available",
        capability_snapshot=capability_snapshot,
        read_user_utterance=_read,
        send_assistant_text=_send,
        clock=clock,
    )


def run_satellite_mode(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[dict[str, str]],
    near_tie_delta: float,
    capability_snapshot: object,
    clock: Clock,
    ask_gateway: AskGateway,
    run_chat_loop: Callable[..., None],
    satellite_say: Callable[[Client, str, str], None],
) -> None:
    with Client(ask_gateway.normalized_ha_rest_url(), ask_gateway.ha_api_token) as client:
        entity_id = ask_gateway.satellite_entity_id
        satellite_say(client, entity_id, "v0 memory loop online. Say 'stop' to exit.")

        interaction_plan = select_interaction_policy_request(
            interaction_intent=COLLECT_TURN_INPUT_INTENT,
            channel_context="satellite",
            task_flow_context="memory_chat_loop",
        )

        def _read() -> str | None:
            question = "Ask one memory-grounded question."
            recent_successful_channel_context = _read_recent_successful_channel_context(runtime)
            ask_result = ask_gateway.request_turn_input_for_policy(
                interaction_policy=interaction_plan.request,
                question=question,
                timeout_s=60.0,
                recent_successful_channel_context=recent_successful_channel_context,
            )
            if ask_result.error:
                satellite_say(client, entity_id, f"I didn't get that. Error: {ask_result.error}")
                return ""
            if ask_result.decision_id == STOP_DECISION_ID:
                return "stop"
            if not ask_result.sentence.strip():
                satellite_say(client, entity_id, "I heard silence. Please try again.")
                return ""
            # Downstream runtime rejection only; upstream ASR/VAD and decode mitigations stay deferred.
            artifact_decision = _classify_artifact_vs_context(
                sentence=ask_result.sentence,
                question=question,
            )
            if artifact_decision.should_reject:
                satellite_say(client, entity_id, "I heard a low-information transcript artifact. Please try again.")
                return ""
            _persist_recent_successful_channel_context(runtime=runtime, ask_result_channel=ask_result.resolved_channel)
            return ask_result.sentence

        def _send(text: str) -> None:
            satellite_say(client, entity_id, text)

        run_chat_loop(
            runtime=runtime,
            llm=llm,
            store=store,
            chat_history=chat_history,
            near_tie_delta=near_tie_delta,
            io_channel="satellite",
            capability_status="ask_available",
            capability_snapshot=capability_snapshot,
            read_user_utterance=_read,
            send_assistant_text=_send,
            clock=clock,
        )
