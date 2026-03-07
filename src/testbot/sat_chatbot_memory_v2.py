# sat_chatbot_memory_v2.py
from __future__ import annotations

import json
import logging
import os
import re
import sys
import uuid
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import urlopen
from argparse import ArgumentParser, Namespace
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path

import arrow
from homeassistant_api import Client

from testbot.clock import Clock, SystemClock
from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc, utc_now_iso
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType, append_pipeline_snapshot
from testbot.promotion_policy import persist_promoted_context
from testbot.reflection_policy import CapabilityStatus, decide_fallback_action
from testbot.rerank import (
    rerank_confidence_thresholds,
    adaptive_sigma_fractional,
    has_sufficient_context_confidence_from_objective,
    is_source_evidence_doc,
    mix_source_evidence_with_memory_cards,
    rerank_docs_with_time_and_type_outcome,
)
from testbot.stage_transitions import (
    append_transition_validation_log,
    validate_answer_post,
    validate_answer_pre,
    validate_encode_post,
    validate_encode_pre,
    validate_observe_post,
    validate_observe_pre,
    validate_rerank_post,
    validate_rerank_pre,
    validate_retrieve_post,
    validate_retrieve_pre,
)
from testbot.time_parse import parse_target_time
from testbot.intent_router import IntentType, classify_intent, is_satellite_action_request
from testbot.time_reasoning import elapsed_since_last_user_message, resolve_relative_date
from testbot.source_connectors import (
    ArxivSourceConnector,
    FixtureSourceConnector,
    LocalMarkdownSourceConnector,
    SourceConnector,
    WikipediaSummarySourceConnector,
)
from testbot.source_ingest import SourceIngestor
from ha_ask import AskSpec, ask_question
from ha_ask.config import normalize_rest_api_url
from testbot.history_packer import PackedHistory, labeled_history_claims, pack_chat_history, render_packed_history

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from testbot.vector_store import MemoryStore, build_memory_store, normalize_memory_store_mode
from langchain_ollama import ChatOllama, OllamaEmbeddings


# ---------------------------
# HA satellite output
# ---------------------------
def sat_say(client: Client, entity_id: str, text: str) -> None:
    client.trigger_service(
        "assist_satellite",
        "start_conversation",
        entity_id=entity_id,
        start_message=text,
        preannounce=False,
    )


# ---------------------------
# Chat history (short-term memory)
# ---------------------------
ChatMsg = dict[str, str]

FALLBACK_ANSWER = "I don't know from memory."
DENY_ANSWER = "I can't comply with that request."
CLARIFY_ANSWER = "Can you clarify which memory and time window you mean?"
ROUTE_TO_ASK_ANSWER = "I can disambiguate this with a quick follow-up question."
ASSIST_ALTERNATIVES_ANSWER = (
    "I don't have enough reliable memory to answer directly. "
    "I can either help you reconstruct the timeline from what you remember, "
    "or suggest where to check next for the missing detail."
)
NON_KNOWLEDGE_UNCERTAINTY_ANSWER = (
    "I'm not fully confident in a reliable answer right now. "
    "I can offer a best-effort response and suggest a quick way to verify it."
)
GENERAL_KNOWLEDGE_MARKER_PREFIX = "General definition (not from your memory):"
GENERAL_KNOWLEDGE_CONFIDENCE_MIN = 0.85
GENERAL_KNOWLEDGE_SUPPORT_MIN = 2
ALIGNMENT_OBJECTIVE_VERSION = "2026-03-05.v3"
SESSION_LOG_SCHEMA_VERSION = 2
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeCapabilityStatus:
    ollama_available: bool
    ha_available: bool
    effective_mode: str
    requested_mode: str
    daemon_mode: bool
    fallback_reason: str | None
    memory_backend: str
    debug_enabled: bool
    text_clarification_available: bool
    satellite_ask_available: bool


@dataclass(frozen=True)
class CapabilitySnapshot:
    runtime: dict[str, object]
    requested_mode: str
    daemon_mode: bool
    effective_mode: str | None
    fallback_reason: str | None
    exit_reason: str | None
    ha_error: str | None
    ollama_error: str | None
    runtime_capability_status: RuntimeCapabilityStatus


def _format_capabilities_help_answer(*, status: RuntimeCapabilityStatus, capability_status: CapabilityStatus) -> str:
    ask_available = capability_status == "ask_available"

    def _derive_core_reasoning_lines() -> list[str]:
        memory_text = (
            f"- Memory recall: available. can recall stored memory cards using the '{status.memory_backend}' backend; "
            "cannot invent details that are not in memory."
        )
        general_state = "available" if status.ollama_available else "unavailable"
        general_text = (
            f"- Grounded explanations: {general_state}. can provide grounded explanations when Ollama is reachable; "
            "cannot generate model-based explanations while Ollama is unavailable."
        )
        return ["core_reasoning:", memory_text, general_text]

    def _derive_interaction_lines() -> list[str]:
        if status.effective_mode == "cli":
            if status.text_clarification_available:
                clarification_state = "available"
                clarification_text = (
                    f"- Clarification/disambiguation: {clarification_state}. text clarification still available in CLI when memory is incomplete; "
                    "interactive satellite ask flow unavailable in CLI mode."
                )
            else:
                clarification_state = "unavailable"
                clarification_text = (
                    f"- Clarification/disambiguation: {clarification_state}. no clarification path is active in the current runtime; "
                    "interactive satellite ask flow unavailable."
                )
        else:
            clarification_available = ask_available or status.text_clarification_available
            clarification_state = "available" if clarification_available else "unavailable"
            clarification_text = (
                f"- Clarification/disambiguation: {clarification_state}. can ask follow-up questions when an active clarification path exists; "
                "cannot clarify when no clarification path is active."
            )
        satellite_ask_state = "available" if status.satellite_ask_available else "unavailable"
        satellite_ask_text = (
            f"- Satellite ask loop: {satellite_ask_state}. can run interactive satellite ask follow-ups when available; "
            "cannot run satellite ask when Home Assistant satellite flow is unavailable."
        )
        return ["interaction:", clarification_text, satellite_ask_text]

    def _derive_integrations_lines() -> list[str]:
        if status.ha_available and status.effective_mode == "satellite":
            ha_state = "available"
            ha_text = (
                "- Home Assistant satellite actions: available. can use satellite speak/start-conversation actions; "
                "cannot act on entities that are missing or unauthorized."
            )
        elif status.ha_available:
            ha_state = "degraded"
            ha_text = (
                "- Home Assistant satellite actions: degraded. can connect to Home Assistant, but current mode is CLI; "
                "cannot run the satellite voice loop until satellite mode is selected."
            )
        else:
            ha_state = "unavailable"
            mode_note = "daemon mode blocks fallback" if status.daemon_mode else "CLI fallback is active"
            ha_text = (
                f"- Home Assistant satellite actions: {ha_state}. can continue in {status.effective_mode} mode ({mode_note}); "
                "cannot run satellite actions while Home Assistant is unavailable."
            )
        return ["integrations:", ha_text]

    def _derive_diagnostics_lines() -> list[str]:
        if status.debug_enabled:
            debug_text = "- Debug visibility: enabled (TESTBOT_DEBUG=1)."
        else:
            debug_text = "- Debug visibility: disabled (set TESTBOT_DEBUG=1 to enable)."
        return ["diagnostics:", debug_text]

    mode_line = (
        f"Runtime mode: requested={status.requested_mode}, effective={status.effective_mode}, "
        f"daemon={status.daemon_mode}, fallback={status.fallback_reason or 'none'}."
    )

    return "\n".join(
        [
            mode_line,
            *_derive_core_reasoning_lines(),
            *_derive_interaction_lines(),
            *_derive_integrations_lines(),
            *_derive_diagnostics_lines(),
            f"policy_hint: reflection capability status={capability_status}.",
        ]
    )


def _format_satellite_action_alternatives(*, status: RuntimeCapabilityStatus) -> str:
    mode_hint = "switch to --mode satellite" if status.ha_available else "restore Home Assistant connectivity first"
    return "\n".join(
        [
            "satellite_action_request:",
            "- Requested satellite action: detected.",
            f"- Action alternatives: continue in {status.effective_mode} mode for text Q&A right now; {mode_hint} to re-enable interactive satellite ask.",
            "- Next step: ask your question directly in this chat, or request a capability check after changing runtime mode.",
        ]
    )

def _parse_env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        _LOGGER.warning("Invalid %s=%r; using default=%s", name, raw, default)
        return default


def _parse_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        _LOGGER.warning("Invalid %s=%r; using default=%s", name, raw, default)
        return default


def _parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(description="Run TestBot with satellite or CLI chat interfaces.")
    parser.add_argument(
        "--mode",
        choices=("auto", "satellite", "cli"),
        default="auto",
        help="Input/output mode. auto prefers satellite and falls back to CLI.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Do not fall back to CLI if satellite mode is unavailable; exit instead.",
    )
    return parser.parse_args(argv)


def _read_runtime_env() -> dict[str, object]:
    memory_store_mode = os.getenv("MEMORY_STORE_MODE", "in_memory")
    return {
        "ha_api_url": os.getenv("HA_API_URL", "http://localhost:8123"),
        "ha_api_secret": os.getenv("HA_API_SECRET", ""),
        "ha_satellite_entity_id": os.getenv("HA_SATELLITE_ENTITY_ID", ""),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434",
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
        "ollama_embedding_model": os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        "memory_near_tie_delta": _parse_env_float("MEMORY_NEAR_TIE_DELTA", 0.02),
        "memory_store_mode": memory_store_mode,
        "memory_store_backend": normalize_memory_store_mode(memory_store_mode),
        "elasticsearch_url": os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        "elasticsearch_index": os.getenv("ELASTICSEARCH_INDEX", "testbot_memory_cards"),
        "source_ingest_enabled": os.getenv("SOURCE_INGEST_ENABLED", "0") == "1",
        "source_connector_type": os.getenv("SOURCE_CONNECTOR_TYPE", "fixture"),
        "source_fixture_path": os.getenv("SOURCE_FIXTURE_PATH", ""),
        "source_ingest_limit": _parse_env_int("SOURCE_INGEST_LIMIT", 50),
        "source_ingest_cursor": os.getenv("SOURCE_INGEST_CURSOR") or None,
        "source_markdown_path": os.getenv("SOURCE_MARKDOWN_PATH", ""),
        "source_wikipedia_topic": os.getenv("SOURCE_WIKIPEDIA_TOPIC", ""),
        "source_wikipedia_language": os.getenv("SOURCE_WIKIPEDIA_LANGUAGE", "en"),
        "source_arxiv_query": os.getenv("SOURCE_ARXIV_QUERY", ""),
    }


def _ha_connection_error(api_url: str, token: str, entity_id: str) -> str | None:
    if not token:
        return "Missing HA_API_SECRET"
    if not entity_id:
        return "Missing HA_SATELLITE_ENTITY_ID"
    try:
        with Client(normalize_rest_api_url(api_url), token):
            return None
    except Exception as exc:  # pragma: no cover - network/credential dependent
        return f"{type(exc).__name__}: {exc}"


def _ollama_connection_error(base_url: str, chat_model: str, embedding_model: str) -> str | None:
    tags_url = urljoin(base_url.rstrip("/") + "/", "api/tags")
    try:
        with urlopen(tags_url, timeout=3.0) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
    except URLError as exc:  # pragma: no cover - network dependent
        return f"Cannot reach Ollama endpoint {base_url}: {type(exc.reason).__name__}: {exc.reason}"
    except Exception as exc:  # pragma: no cover - network dependent
        return f"Cannot reach Ollama endpoint {base_url}: {type(exc).__name__}: {exc}"

    models = payload.get("models", []) if isinstance(payload, dict) else []
    available = {
        str(item.get("model") or item.get("name") or "")
        for item in models
        if isinstance(item, dict)
    }
    if chat_model not in available:
        return (
            f"Configured chat model '{chat_model}' is not installed on Ollama. "
            f"Run: ollama pull {chat_model}"
        )
    if embedding_model not in available:
        return (
            f"Configured embedding model '{embedding_model}' is not installed on Ollama. "
            f"Run: ollama pull {embedding_model}"
        )
    return None


def _resolve_mode(requested_mode: str, ha_error: str | None) -> str:
    if requested_mode == "auto":
        return "satellite" if ha_error is None else "cli"
    return requested_mode


def _resolve_effective_mode(
    *,
    requested_mode: str,
    daemon_mode: bool,
    ha_error: str | None,
    ollama_error: str | None,
) -> tuple[str | None, str | None, str | None]:
    if ollama_error is not None:
        return None, None, f"Ollama is unavailable: {ollama_error}"

    if requested_mode == "auto" and ha_error is not None and daemon_mode:
        return None, None, f"Home Assistant is unavailable: {ha_error}"

    selected_mode = _resolve_mode(requested_mode, ha_error)
    if selected_mode == "satellite" and ha_error is not None:
        if daemon_mode:
            return None, None, f"Home Assistant is unavailable: {ha_error}"
        return "cli", "satellite connection is unavailable", None
    return selected_mode, None, None



def _build_source_connector(runtime: dict[str, object]) -> SourceConnector | None:
    if not bool(runtime.get("source_ingest_enabled", False)):
        return None
    connector_type = str(runtime.get("source_connector_type", "fixture")).strip().lower()

    if connector_type == "fixture":
        fixture_path = str(runtime.get("source_fixture_path") or "").strip()
        if not fixture_path:
            append_session_log("source_ingest_skipped", {"reason": "missing_fixture_path", "connector_type": connector_type})
            return None
        return FixtureSourceConnector.from_json_file(source_type="fixture", fixture_path=fixture_path)

    if connector_type in {"local_markdown", "markdown"}:
        markdown_path = str(runtime.get("source_markdown_path") or "").strip()
        if not markdown_path:
            append_session_log("source_ingest_skipped", {"reason": "missing_markdown_path", "connector_type": connector_type})
            return None
        return LocalMarkdownSourceConnector(markdown_path=markdown_path)

    if connector_type in {"wikipedia", "wiki"}:
        topic = str(runtime.get("source_wikipedia_topic") or "").strip()
        language = str(runtime.get("source_wikipedia_language") or "en").strip() or "en"
        if not topic:
            append_session_log("source_ingest_skipped", {"reason": "missing_wikipedia_topic", "connector_type": connector_type})
            return None
        return WikipediaSummarySourceConnector(topic=topic, language=language)

    if connector_type == "arxiv":
        query = str(runtime.get("source_arxiv_query") or "").strip()
        if not query:
            append_session_log("source_ingest_skipped", {"reason": "missing_arxiv_query", "connector_type": connector_type})
            return None
        return ArxivSourceConnector(query=query)

    append_session_log("source_ingest_skipped", {"reason": "unsupported_connector_type", "connector_type": connector_type})
    return None


def _run_source_ingestion(*, runtime: dict[str, object], store: MemoryStore) -> None:
    connector = _build_source_connector(runtime)
    if connector is None:
        return
    ingestor = SourceIngestor(connector=connector, memory_store=store)
    cursor = str(runtime.get("source_ingest_cursor")) if runtime.get("source_ingest_cursor") is not None else None
    limit = int(runtime.get("source_ingest_limit", 50))
    if cursor is not None and not cursor.isdigit():
        append_session_log(
            "source_ingest_cursor_invalid",
            {
                "cursor": cursor,
                "fallback_cursor": None,
            },
        )
        cursor = None
    try:
        result = ingestor.ingest_once(
            cursor=cursor,
            limit=limit,
        )
    except Exception as exc:
        append_session_log(
            "source_ingest_failed",
            {
                "connector_type": str(runtime.get("source_connector_type", "")).strip().lower(),
                "source_type": connector.source_type,
                "cursor": cursor,
                "limit": limit,
                "exception_class": exc.__class__.__name__,
                "exception_message": str(exc),
            },
        )
        print(
            "Warning: source ingestion failed at startup; continuing without ingested source documents.",
            file=sys.stderr,
        )
        return
    append_session_log(
        "source_ingest_completed",
        {
            "source_type": connector.source_type,
            "fetched_count": result.fetched_count,
            "stored_count": result.stored_count,
            "next_cursor": result.next_cursor,
            "memory_doc_ids": [str(doc.id or "") for doc in result.memory_documents],
            "evidence_doc_ids": [str(doc.id or "") for doc in result.evidence_documents],
        },
    )

def _print_startup_status(*, snapshot: CapabilitySnapshot) -> None:
    runtime = snapshot.runtime
    print("=== TestBot startup status ===")
    effective_mode = snapshot.effective_mode or "unavailable"
    if snapshot.fallback_reason:
        print(
            "Selected mode: "
            f"{effective_mode} (requested={snapshot.requested_mode}, "
            f"fallback reason={snapshot.fallback_reason}, daemon={snapshot.daemon_mode})"
        )
    else:
        print(f"Selected mode: {effective_mode} (requested={snapshot.requested_mode}, daemon={snapshot.daemon_mode})")
    print(
        f"Ollama endpoint: {runtime['ollama_base_url']} "
        f"chat_model={runtime['ollama_model']} embed_model={runtime['ollama_embedding_model']}"
    )
    if snapshot.ollama_error:
        print(f"Ollama: unavailable ({snapshot.ollama_error})")
        print("Install warning [RED]: Ollama capability is unavailable; verify OLLAMA_BASE_URL and pull required models before restarting.")
        print("Developer note: runtime will exit early because model and embedding checks are required at startup.")
    else:
        print("Ollama: available (chat + embedding models verified)")
        print("Install warning [GREEN]: Ollama capability is active; keep OLLAMA_MODEL and OLLAMA_EMBEDDING_MODEL provisioned.")
    print(f"Memory backend: {runtime['memory_store_backend']}")
    if snapshot.ha_error:
        print(f"Home Assistant: unavailable ({snapshot.ha_error})")
        print("Install warning [YELLOW]: Home Assistant capability is degraded; configure HA_API_SECRET and HA_SATELLITE_ENTITY_ID to enable satellite mode.")
        print("Developer note: satellite interface disabled; CLI fallback will be used unless --daemon is set.")
    else:
        print(f"Home Assistant: available ({runtime['ha_api_url']}, entity={runtime['ha_satellite_entity_id']})")
        print("Install warning [GREEN]: Home Assistant capability is active; keep Home Assistant credentials configured when reinstalling or reprovisioning.")
        print("Developer note: satellite ask/speak loop is enabled.")
    print("Continuity: memory cards are shared across interfaces in-process via one vector store.")
    print("==============================")


def append_session_log(event: str, payload: dict, *, log_path: Path = Path("./logs/session.jsonl")) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utc_now_iso(),
        "event": event,
        "schema_version": SESSION_LOG_SCHEMA_VERSION,
        **payload,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def doc_to_candidate_hit(doc: Document, score: float) -> CandidateHit:
    return CandidateHit(
        doc_id=str(doc.id or doc.metadata.get("doc_id") or ""),
        score=float(score),
        ts=str(doc.metadata.get("ts") or ""),
        card_type=str(doc.metadata.get("type") or ""),
    )


def stage_rewrite_query(llm: ChatOllama, state: PipelineState) -> PipelineState:
    try:
        rewritten_query = llm.invoke(QUERY_REWRITE_PROMPT.format_messages(input=state.user_input)).content.strip() or state.user_input
    except Exception as exc:
        append_session_log(
            "query_rewrite_failed",
            {
                "error_class": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        rewritten_query = state.user_input
    return replace(state, rewritten_query=rewritten_query)


def observe_stage(state: PipelineState) -> PipelineState:
    return state


def encode_stage(llm: ChatOllama, state: PipelineState) -> PipelineState:
    return stage_rewrite_query(llm, state)


def stage_retrieve(store: MemoryStore, state: PipelineState) -> tuple[PipelineState, list[tuple[Document, float]]]:
    raw_docs_and_scores = store.similarity_search_with_score(state.rewritten_query, k=18)
    docs_and_scores = mix_source_evidence_with_memory_cards(raw_docs_and_scores, top_k=12, source_quota=3)
    retrieval_candidates = [doc_to_candidate_hit(doc, score) for doc, score in docs_and_scores]
    return replace(state, retrieval_candidates=retrieval_candidates), docs_and_scores


def stage_rerank(
    state: PipelineState,
    docs_and_scores: list[tuple[Document, float]],
    *,
    utterance: str,
    user_doc_id: str,
    user_reflection_doc_id: str,
    near_tie_delta: float,
    clock: Clock,
) -> tuple[PipelineState, list[Document]]:
    now = clock.now()
    target = parse_target_time(utterance, now=now)
    sigma = adaptive_sigma_fractional(now=now, target=target, frac=0.25)
    rerank_outcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=target,
        sigma_seconds=sigma,
        exclude_doc_ids={user_doc_id, user_reflection_doc_id},
        exclude_source_ids={user_doc_id},
        top_k=4,
        near_tie_delta=near_tie_delta,
    )
    hits = rerank_outcome.docs
    reranked_hits = [doc_to_candidate_hit(doc, score=0.0) for doc in hits]
    has_context = has_sufficient_context_confidence(
        rerank_outcome.scored_candidates,
        ambiguity_detected=rerank_outcome.ambiguity_detected,
    )
    confidence_decision = {
        "context_confident": has_context,
        "ambiguity_detected": rerank_outcome.ambiguity_detected,
        "ambiguous_candidates": rerank_outcome.near_tie_candidates,
        "scored_candidates": rerank_outcome.scored_candidates,
        "objective": rerank_outcome.scored_candidates[0].get("objective", "") if rerank_outcome.scored_candidates else "",
        "objective_version": rerank_outcome.scored_candidates[0].get("objective_version", "") if rerank_outcome.scored_candidates else "",
        "top_final_score_min": rerank_confidence_thresholds().top_final_score_min,
        "min_margin_to_second": rerank_confidence_thresholds().min_margin_to_second,
        "allow_ambiguity_override": rerank_confidence_thresholds().allow_ambiguity_override,
        "ambiguity_override_top_final_score_min": rerank_confidence_thresholds().ambiguity_override_top_final_score_min,
        "now_ts": now.isoformat(),
        "target_ts": target.isoformat(),
        "sigma_seconds": sigma,
    }
    return replace(state, reranked_hits=reranked_hits, confidence_decision=confidence_decision), hits



_AFFIRMATION_UTTERANCE_PATTERN = re.compile(r"^\s*(yes|yeah|yep|yup|ok|okay|sure|please|yes please|ok please|okay please)\s*[.!?]*\s*$", re.IGNORECASE)
_DEFINITIONAL_QUERY_PATTERN = re.compile(
    r"^\s*(what(?:\s+is|\s+are|'s)\b|who(?:\s+is|\s+are|'s)\b|define\b|definition\s+of\b|what\s+does\b.+\bmean\b)",
    re.IGNORECASE,
)


def _is_short_affirmation(user_input: str) -> bool:
    return bool(_AFFIRMATION_UTTERANCE_PATTERN.match((user_input or "").strip()))


def _is_clarification_or_capability_confirmation_answer(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    return is_clarification_answer(normalized) or _is_capabilities_help_answer(normalized)


def resolve_turn_intent(*, utterance: str, prior_pipeline_state: PipelineState | None) -> tuple[IntentType, IntentType]:
    classified_intent = classify_intent(utterance)
    if prior_pipeline_state is None:
        return classified_intent, classified_intent

    prior_intent_raw = (prior_pipeline_state.prior_unresolved_intent or prior_pipeline_state.resolved_intent or "").strip()
    if not prior_intent_raw:
        return classified_intent, classified_intent

    try:
        prior_intent = IntentType(prior_intent_raw)
    except ValueError:
        return classified_intent, classified_intent

    prior_answer = (prior_pipeline_state.final_answer or "").strip()
    if _is_short_affirmation(utterance) and _is_clarification_or_capability_confirmation_answer(prior_answer):
        return classified_intent, prior_intent

    return classified_intent, classified_intent


def _intent_class_for_policy(intent: IntentType) -> str:
    if intent == IntentType.MEMORY_RECALL:
        return "memory_recall"
    if intent == IntentType.TIME_QUERY:
        return "time_query"
    return "non_memory"


def _is_social_or_non_knowledge_intent(intent: IntentType) -> bool:
    return intent in {IntentType.META_CONVERSATION, IntentType.CONTROL, IntentType.CAPABILITIES_HELP}


def _is_capabilities_help_request(intent: IntentType) -> bool:
    return intent == IntentType.CAPABILITIES_HELP


def _is_capabilities_help_answer(text: str) -> bool:
    normalized = (text or "").strip().lower()
    return normalized.startswith("runtime mode:") and "memory recall:" in normalized and "home assistant" in normalized


def _intent_label(intent: IntentType) -> str:
    return intent.value


def _uses_memory_retrieval(intent: IntentType) -> bool:
    return intent == IntentType.MEMORY_RECALL


def _is_definitional_query_form(utterance: str) -> bool:
    return bool(_DEFINITIONAL_QUERY_PATTERN.match((utterance or "").strip()))


def _select_retrieval_branch(*, utterance: str, intent: IntentType) -> str:
    if _uses_memory_retrieval(intent):
        return "memory_retrieval"
    if intent == IntentType.KNOWLEDGE_QUESTION and _is_definitional_query_form(utterance):
        return "memory_retrieval"
    return "direct_answer"


def _minimal_confidence_decision_for_direct_answer(*, branch: str) -> dict[str, object]:
    return {
        "context_confident": False,
        "ambiguity_detected": False,
        "ambiguous_candidates": [],
        "scored_candidates": [],
        "objective": "",
        "objective_version": "",
        "retrieval_branch": branch,
    }


def _ambiguity_score(confidence_decision: dict[str, object]) -> float:
    scored_candidates = confidence_decision.get("scored_candidates", [])
    if not isinstance(scored_candidates, list) or len(scored_candidates) < 2:
        return 0.0
    first = scored_candidates[0] if isinstance(scored_candidates[0], dict) else {}
    second = scored_candidates[1] if isinstance(scored_candidates[1], dict) else {}
    first_score = float(first.get("final_score", 0.0) or 0.0)
    second_score = float(second.get("final_score", 0.0) or 0.0)
    if first_score <= 0.0:
        return 1.0
    separation = max(0.0, first_score - second_score) / first_score
    return round(max(0.0, min(1.0, 1.0 - separation)), 4)


def _user_followup_signal_proxy(*, final_answer: str, fallback_action: str, ambiguity_score: float) -> float:
    if final_answer in {CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER}:
        return 1.0
    if fallback_action in {"ASK_CLARIFYING_QUESTION", "ROUTE_TO_ASK"}:
        return 0.9
    if fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        return round(max(0.2, ambiguity_score), 4)
    return round(max(0.0, ambiguity_score * 0.5), 4)


def _derive_response_blocker_reason(*, answer_mode: str, fallback_action: str, context_confident: bool, hit_count: int, ambiguity_detected: bool) -> str:
    if answer_mode == "clarify" or fallback_action in {"ASK_CLARIFYING_QUESTION", "ROUTE_TO_ASK"}:
        if hit_count > 0 and (ambiguity_detected or not context_confident):
            return "retrieved memory fragments were ambiguous or low-confidence"
        if hit_count == 0:
            return "no memory fragments were retrieved for this request"
    if answer_mode == "dont-know" or fallback_action == "ANSWER_UNKNOWN":
        return "insufficient reliable memory to answer directly"
    if answer_mode == "assist" or fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        return "insufficient confidence for a direct answer; offered capability alternatives"
    if answer_mode == "deny":
        return "request blocked by safety or policy checks"
    return "none"


def _format_debug_turn_trace(*, state: PipelineState, intent_label: str, hits: list[Document]) -> str:
    fallback_action = str(state.invariant_decisions.get("fallback_action", "NONE"))
    retrieval_branch = str(state.confidence_decision.get("retrieval_branch", "memory_retrieval"))
    answer_mode = str(state.invariant_decisions.get("answer_mode", "dont-know"))
    context_confident = bool(state.confidence_decision.get("context_confident", False))
    ambiguity_detected = bool(state.confidence_decision.get("ambiguity_detected", False))
    reason = _derive_response_blocker_reason(
        answer_mode=answer_mode,
        fallback_action=fallback_action,
        context_confident=context_confident,
        hit_count=len(hits),
        ambiguity_detected=ambiguity_detected,
    )
    doc_ids = [(doc.id or doc.metadata.get("doc_id") or "") for doc in hits[:3]]
    return (
        "[debug] "
        f"intent={intent_label}; "
        f"answer_mode={answer_mode}; "
        f"fallback_action={fallback_action}; "
        f"retrieval_branch={retrieval_branch}; "
        f"context_confident={context_confident}; "
        f"ambiguity_detected={ambiguity_detected}; "
        f"rewritten_query={state.rewritten_query!r}; "
        f"retrieved_doc_ids={doc_ids}; "
        f"blocker_reason={reason}."
    )


def build_partial_memory_clarifier(hits: list[Document], *, max_items: int = 2) -> str:
    snippets: list[str] = []
    for doc in hits[:max_items]:
        snippet = (doc.page_content or "").strip()
        if snippet:
            snippets.append(snippet[:80])
    if snippets:
        joined = "; ".join(snippets)
        return (
            f"I found related memory fragments ({joined}), but not enough to answer precisely. "
            "Which person, event, or time window should I focus on?"
        )
    return CLARIFY_ANSWER


def _select_memory_recovery_hit(hits: list[Document]) -> Document | None:
    for hit in hits:
        metadata = hit.metadata if isinstance(hit.metadata, dict) else {}
        doc_id = str(metadata.get("doc_id", "")).strip()
        ts = str(metadata.get("ts", "")).strip()
        snippet = (hit.page_content or "").strip()
        if doc_id and ts and snippet:
            return hit
    return None


def _build_memory_recall_recovery_answer(hit: Document) -> str:
    metadata = hit.metadata if isinstance(hit.metadata, dict) else {}
    doc_id = str(metadata.get("doc_id", "")).strip()
    ts = str(metadata.get("ts", "")).strip()
    snippet = " ".join((hit.page_content or "").split())
    trimmed_snippet = snippet[:180].rstrip()
    return f"From memory, I found: {trimmed_snippet}. doc_id: {doc_id}, ts: {ts}"


def is_clarification_answer(text: str) -> bool:
    normalized = (text or "").strip()
    return normalized in {CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER} or normalized.startswith(
        "I found related memory fragments ("
    )


def _build_time_answer(*, user_input: str, now: arrow.Arrow, last_user_message_ts: str | None, timezone: str) -> str:
    normalized = user_input.strip().lower()

    if "ago" in normalized:
        elapsed_seconds = elapsed_since_last_user_message(last_user_message_ts, now)
        if elapsed_seconds is None:
            return "I don't have a previous user-message timestamp yet."
        minutes = elapsed_seconds // 60
        return f"Your previous user message was {minutes} minute(s) ago."

    for token in ("today", "tomorrow", "yesterday"):
        if token in normalized:
            resolved = resolve_relative_date(token, now, timezone)
            if resolved is not None:
                return f"{token.capitalize()} is {resolved} in {timezone}."

    return "I can answer relative time questions like 'how many minutes ago' or 'what is tomorrow?'."


def stage_answer(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> PipelineState:
    runtime_capability_status = runtime_capability_status or RuntimeCapabilityStatus(
        ollama_available=True,
        ha_available=False,
        effective_mode="cli",
        requested_mode="cli",
        daemon_mode=False,
        fallback_reason=None,
        memory_backend="in_memory",
        debug_enabled=False,
        text_clarification_available=True,
        satellite_ask_available=False,
    )

    def _fallback_answer_for_action(action: str, *, intent_class: str) -> str:
        if action == "ROUTE_TO_ASK":
            return ROUTE_TO_ASK_ANSWER
        if action == "ASK_CLARIFYING_QUESTION":
            if intent_class == "memory_recall":
                return build_partial_memory_clarifier(hits)
            return FALLBACK_ANSWER
        if action == "ANSWER_UNKNOWN":
            return NON_KNOWLEDGE_UNCERTAINTY_ANSWER if intent_class == "non_memory" else FALLBACK_ANSWER
        if action == "ANSWER_TIME":
            if clock is None:
                return "I can answer relative time questions like 'how many minutes ago' or 'what is tomorrow?'."
            return _build_time_answer(
                user_input=state.user_input,
                now=clock.now(),
                last_user_message_ts=state.last_user_message_ts,
                timezone=timezone,
            )
        return ASSIST_ALTERNATIVES_ANSWER

    resolved_intent = IntentType(state.resolved_intent or classify_intent(state.user_input).value)
    intent_class = _intent_class_for_policy(resolved_intent)
    social_or_non_knowledge_intent = _is_social_or_non_knowledge_intent(resolved_intent)
    satellite_action_request = is_satellite_action_request(state.user_input)

    if _is_capabilities_help_request(resolved_intent):
        final_answer = _format_capabilities_help_answer(
            status=runtime_capability_status,
            capability_status=capability_status,
        )
        if (
            satellite_action_request
            and runtime_capability_status.effective_mode == "cli"
            and not runtime_capability_status.satellite_ask_available
        ):
            final_answer = "\n".join(
                [
                    final_answer,
                    _format_satellite_action_alternatives(status=runtime_capability_status),
                ]
            )
        provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
            final_answer=final_answer,
            hits=hits,
            chat_history=chat_history,
            packed_history=pack_chat_history(list(chat_history)),
        )
        alignment_decision = evaluate_alignment_decision(
            user_input=state.user_input,
            draft_answer="",
            final_answer=final_answer,
            confidence_decision=state.confidence_decision,
            claims=claims,
            provenance_types=provenance_types,
            basis_statement=basis_statement,
        )
        return replace(
            state,
            draft_answer="",
            final_answer=final_answer,
            claims=claims,
            provenance_types=provenance_types,
            used_memory_refs=used_memory_refs,
            used_source_evidence_refs=used_source_evidence_refs,
            source_evidence_attribution=source_evidence_attribution,
            basis_statement=basis_statement,
            invariant_decisions={
                "response_contains_claims": False,
                "has_required_memory_citation": False,
                "answer_contract_valid": True,
                "general_knowledge_contract_valid": True,
                "has_general_knowledge_marker": False,
                "general_knowledge_confidence_gate_passed": True,
                "answer_mode": "assist",
                "fallback_action": "ANSWER_GENERAL_KNOWLEDGE",
                "provenance_recorded": True,
            },
            alignment_decision=alignment_decision,
        )

    context_str = render_context(hits)
    packed_history = pack_chat_history(list(chat_history))
    history_str = render_packed_history(packed_history)
    msgs = ANSWER_PROMPT.format_messages(input=state.user_input, chat_history=history_str, context=context_str)

    fallback_action = decide_fallback_action(
        intent=intent_class,
        memory_hit=bool(state.confidence_decision.get("context_confident", False)),
        ambiguity=bool(state.confidence_decision.get("ambiguity_detected", False)),
        capability_status=capability_status,
        source_confidence=(
            float(state.confidence_decision["source_confidence"])
            if "source_confidence" in state.confidence_decision
            else None
        ),
    )
    ambiguity_detected = bool(state.confidence_decision.get("ambiguity_detected", False))
    memory_hit_count = len(hits)
    route_to_ask_expected = fallback_action == "ROUTE_TO_ASK"
    clarification_allowed = (
        (intent_class == "memory_recall" or route_to_ask_expected)
        and (ambiguity_detected or (intent_class == "memory_recall" and memory_hit_count == 0))
        and (not route_to_ask_expected or capability_status == "ask_available")
    )

    def _clarifier_or_policy_alternative() -> str:
        if clarification_allowed:
            return build_partial_memory_clarifier(hits)
        if intent_class == "memory_recall":
            return ASSIST_ALTERNATIVES_ANSWER
        return ASSIST_ALTERNATIVES_ANSWER

    def _memory_recall_recovery_or_alternative() -> str:
        selected_hit = _select_memory_recovery_hit(hits)
        if selected_hit is not None:
            return _build_memory_recall_recovery_answer(selected_hit)
        return _clarifier_or_policy_alternative()

    def _knowledge_safe_fallback() -> str:
        if fallback_action in {"ANSWER_UNKNOWN", "OFFER_CAPABILITY_ALTERNATIVES", "ANSWER_TIME"}:
            return _fallback_answer_for_action(fallback_action, intent_class=intent_class)
        if intent_class == "memory_recall":
            return _clarifier_or_policy_alternative()
        return _fallback_answer_for_action(fallback_action, intent_class=intent_class)

    if is_unsafe_user_request(state.user_input):
        draft_answer = ""
        final_answer = DENY_ANSWER
    elif fallback_action == "ROUTE_TO_ASK":
        draft_answer = ""
        final_answer = ROUTE_TO_ASK_ANSWER
    elif fallback_action == "ASK_CLARIFYING_QUESTION":
        draft_answer = ""
        final_answer = _clarifier_or_policy_alternative()
    elif fallback_action == "ANSWER_UNKNOWN":
        draft_answer = FALLBACK_ANSWER
        final_answer = _fallback_answer_for_action(fallback_action, intent_class=intent_class)
    elif fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        draft_answer = ""
        final_answer = ASSIST_ALTERNATIVES_ANSWER
    elif fallback_action == "ANSWER_TIME":
        draft_answer = ""
        final_answer = _fallback_answer_for_action(fallback_action, intent_class=intent_class)
    else:
        try:
            draft_answer = (llm.invoke(msgs).content or "").strip()
        except Exception as exc:
            append_session_log(
                "answer_generation_failed",
                {
                    "error_class": type(exc).__name__,
                    "error_message": str(exc),
                    "fallback_action": fallback_action,
                },
            )
            draft_answer = ""
            final_answer = _fallback_answer_for_action(fallback_action, intent_class=intent_class)
        else:
            if not draft_answer:
                final_answer = ASSIST_ALTERNATIVES_ANSWER
            elif validate_answer_contract(draft_answer):
                final_answer = draft_answer
            elif intent_class == "memory_recall" and bool(state.confidence_decision.get("context_confident", False)):
                final_answer = _memory_recall_recovery_or_alternative()
            elif social_or_non_knowledge_intent and fallback_action == "ANSWER_GENERAL_KNOWLEDGE":
                final_answer = draft_answer
            else:
                final_answer = _clarifier_or_policy_alternative()

    provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
        final_answer=final_answer,
        hits=hits,
        chat_history=chat_history,
        packed_history=packed_history,
    )

    general_knowledge_contract_valid = (
        True
        if fallback_action == "ANSWER_TIME"
        else validate_general_knowledge_contract(
            final_answer,
            provenance_types=provenance_types,
            confidence_decision=state.confidence_decision,
        )
    )
    if final_answer != FALLBACK_ANSWER and not general_knowledge_contract_valid:
        preserve_social_draft = (
            social_or_non_knowledge_intent
            and bool(draft_answer)
            and final_answer == draft_answer
            and fallback_action == "ANSWER_GENERAL_KNOWLEDGE"
        )
        if not preserve_social_draft:
            final_answer = _knowledge_safe_fallback()
            provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
                final_answer=final_answer,
                hits=hits,
                chat_history=chat_history,
                packed_history=packed_history,
            )

    alignment_decision = evaluate_alignment_decision(
        user_input=state.user_input,
        draft_answer=draft_answer,
        final_answer=final_answer,
        confidence_decision=state.confidence_decision,
        claims=claims,
        provenance_types=provenance_types,
        basis_statement=basis_statement,
    )

    answer_mode = (
        "deny"
        if final_answer == DENY_ANSWER
        else (
            "clarify"
            if is_clarification_answer(final_answer)
            else (
                "dont-know"
                if fallback_action == "ANSWER_UNKNOWN" or final_answer in {FALLBACK_ANSWER, NON_KNOWLEDGE_UNCERTAINTY_ANSWER}
                else (
                    "assist"
                    if final_answer == ASSIST_ALTERNATIVES_ANSWER or social_or_non_knowledge_intent
                    else "memory-grounded"
                )
            )
        )
    )
    ambiguity_policy_allows_non_memory_clarify = bool(state.confidence_decision.get("allow_non_memory_clarify", False))
    if answer_mode == "clarify" and intent_class != "memory_recall" and not ambiguity_policy_allows_non_memory_clarify:
        raise AssertionError(
            "Non-memory intent produced answer_mode=clarify without explicit ambiguity policy override."
        )

    invariant_decisions = {
        "response_contains_claims": bool(claims),
        "raw_claim_like_text_detected": raw_claim_like_text_detected(draft_answer),
        "has_required_memory_citation": has_required_memory_citation(draft_answer),
        "answer_contract_valid": validate_answer_contract(draft_answer),
        "general_knowledge_contract_valid": general_knowledge_contract_valid,
        "has_general_knowledge_marker": has_general_knowledge_marker(final_answer),
        "general_knowledge_confidence_gate_passed": passes_general_knowledge_confidence_gate(state.confidence_decision),
        "answer_mode": answer_mode,
        "fallback_action": fallback_action,
        "provenance_recorded": bool(not is_non_trivial_answer(final_answer) or provenance_types),
    }
    return replace(
        state,
        draft_answer=draft_answer,
        final_answer=final_answer,
        claims=claims,
        provenance_types=provenance_types,
        used_memory_refs=used_memory_refs,
        used_source_evidence_refs=used_source_evidence_refs,
        source_evidence_attribution=source_evidence_attribution,
        basis_statement=basis_statement,
        invariant_decisions=invariant_decisions,
        alignment_decision=alignment_decision,
    )


def _validate_and_log_transition(result) -> None:
    append_transition_validation_log(result)
    if not result.passed:
        failures = ", ".join(result.failures)
        raise AssertionError(f"Stage transition validation failed at {result.stage}.{result.boundary}: {failures}")


# ---------------------------
# Reflection extraction (metacognition)
# ---------------------------
REFLECTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a metacognitive reflection extractor.\n"
            "Given an observed statement, produce compact YAML with ONLY these keys:\n"
            "claims: [..]\n"
            "commitments: [..]\n"
            "preferences: [..]\n"
            "uncertainties: [..]\n"
            "followups: [..]\n"
            "confidence: <0..1>\n"
            "Rules:\n"
            "- Keep each list item short.\n"
            "- If none, use empty list [].\n"
            "- Do NOT invent facts.\n"
            "- If uncertain, put it under uncertainties.\n"
            "- Output YAML only (no prose).\n",
        ),
        ("human", "speaker: {speaker}\ntext: {text}\n"),
    ]
)


def generate_reflection_yaml(llm: ChatOllama, *, speaker: str, text: str) -> str:
    msgs = REFLECTION_PROMPT.format_messages(speaker=speaker, text=text)
    try:
        out = llm.invoke(msgs).content
    except Exception as exc:
        append_session_log(
            "reflection_generation_failed",
            {
                "error_class": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        out = ""
    return (out or "").strip() or (
        "claims: []\ncommitments: []\npreferences: []\nuncertainties: []\nfollowups: []\nconfidence: 0.2"
    )


# ---------------------------
# RAG prompt (uses chat history + retrieved memory)
# ---------------------------
ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a careful assistant.\n"
            "Use ONLY the provided memory context and recent chat.\n"
            "If memory is empty or low-confidence, ask one targeted clarifying question or offer at least two capability-based alternatives.\n"
            "If memory is partial or ambiguous, provide a short user-facing summary and one bridging clarifier.\n"
            "Keep the exact phrase \"I don't know from memory.\" only for explicit deny/safety-policy cases.\n"
            "For any factual claim, include at least one cited memory with both doc_id and ts.\n\n"
            "Recent chat:\n{chat_history}\n\n"
            "Memory context:\n{context}\n",
        ),
        ("human", "{input}"),
    ]
)

QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "Rewrite the user's message into a short search query for retrieving relevant memory.\nReturn ONLY the query text."),
        ("human", "{input}"),
    ]
)


def render_context(docs: list[Document], *, limit_chars: int = 5000) -> str:
    chunks: list[str] = []
    total = 0
    for d in docs:
        s = (d.page_content or "").strip()
        if not s:
            continue
        add = s + "\n---\n"
        if total + len(add) > limit_chars:
            break
        chunks.append(add)
        total += len(add)
    return "".join(chunks).strip()


def has_sufficient_context_confidence(
    scored_candidates: list[dict[str, float | str]], *, ambiguity_detected: bool
) -> bool:
    return has_sufficient_context_confidence_from_objective(
        scored_candidates=scored_candidates,
        ambiguity_detected=ambiguity_detected,
    )




def is_non_trivial_answer(text: str) -> bool:
    normalized = (text or "").strip()
    return bool(normalized) and normalized not in {
        FALLBACK_ANSWER,
        DENY_ANSWER,
        CLARIFY_ANSWER,
        ROUTE_TO_ASK_ANSWER,
        ASSIST_ALTERNATIVES_ANSWER,
    }


def extract_claims(text: str) -> list[str]:
    if not is_non_trivial_answer(text):
        return []
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    return parts[:4]


def collect_used_memory_refs(hits: list[Document]) -> list[str]:
    refs: list[str] = []
    for d in hits:
        if is_source_evidence_doc(d):
            continue
        doc_id = str(d.metadata.get("doc_id") or d.id or "").strip()
        if not doc_id:
            continue
        ts = str(d.metadata.get("ts") or "").strip()
        refs.append(f"{doc_id}@{ts}" if ts else doc_id)
    return list(dict.fromkeys(refs))


def collect_used_source_evidence_refs(hits: list[Document]) -> tuple[list[str], list[dict[str, str]]]:
    refs: list[str] = []
    attributions: list[dict[str, str]] = []
    for d in hits:
        if not is_source_evidence_doc(d):
            continue
        doc_id = str(d.metadata.get("doc_id") or d.id or "").strip()
        if doc_id:
            refs.append(doc_id)
        attribution = {
            "doc_id": doc_id,
            "source_type": str(d.metadata.get("source_type") or ""),
            "source_uri": str(d.metadata.get("source_uri") or ""),
            "retrieved_at": str(d.metadata.get("retrieved_at") or ""),
            "trust_tier": str(d.metadata.get("trust_tier") or ""),
        }
        attributions.append(attribution)
    deduped_refs = list(dict.fromkeys(refs))
    deduped_attributions = list({json.dumps(item, sort_keys=True): item for item in attributions}.values())
    return deduped_refs, deduped_attributions


def build_provenance_metadata(
    *,
    final_answer: str,
    hits: list[Document],
    chat_history: deque[ChatMsg],
    packed_history: PackedHistory,
) -> tuple[list[ProvenanceType], list[str], str, list[str], list[str], list[dict[str, str]]]:
    if not is_non_trivial_answer(final_answer):
        return (
            [ProvenanceType.UNKNOWN],
            [],
            "Trivial fallback/deny/clarification response with no substantive claim.",
            [],
            [],
            [],
        )

    used_memory_refs = collect_used_memory_refs(hits)
    used_source_evidence_refs, source_evidence_attribution = collect_used_source_evidence_refs(hits)
    claims = [f"INFERENCE: {claim}" for claim in extract_claims(final_answer)]
    claims.extend(labeled_history_claims(packed_history))
    claims = claims[:8]
    provenance_types: list[ProvenanceType] = [ProvenanceType.INFERENCE]
    if used_memory_refs or used_source_evidence_refs:
        provenance_types.append(ProvenanceType.MEMORY)
    else:
        provenance_types.append(ProvenanceType.GENERAL_KNOWLEDGE)
    if chat_history:
        provenance_types.append(ProvenanceType.CHAT_HISTORY)

    if used_memory_refs and used_source_evidence_refs:
        basis_statement = (
            "Answer synthesized from reranked memory context and source evidence documents"
            + (" with recent chat history signals." if chat_history else ".")
        )
    elif used_memory_refs:
        basis_statement = (
            "Answer synthesized from reranked memory context"
            + (" and recent chat history." if chat_history else ".")
        )
    elif used_source_evidence_refs:
        basis_statement = (
            "Answer synthesized from reranked source evidence documents"
            + (" and recent chat history." if chat_history else ".")
        )
    elif chat_history:
        basis_statement = (
            "Relevance summary basis: synthesized from recent chat history signals."
            if final_answer.startswith("Relevant summary:")
            else "Answer synthesized from recent chat history."
        )
    else:
        basis_statement = "General-knowledge basis: no supporting memory references were retrieved."
    return (
        list(dict.fromkeys(provenance_types)),
        claims,
        basis_statement,
        used_memory_refs,
        used_source_evidence_refs,
        source_evidence_attribution,
    )

def response_contains_claims(text: str) -> bool:
    return bool(extract_claims(text))


def raw_claim_like_text_detected(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    if normalized in {FALLBACK_ANSWER, CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER, ASSIST_ALTERNATIVES_ANSWER}:
        return False
    # A simple heuristic: if there is sentence-like prose, treat it as factual/semantic claims.
    return bool(re.search(r"[A-Za-z0-9].{8,}", normalized))


def has_required_memory_citation(text: str) -> bool:
    citation_pattern = re.compile(r"doc_id\s*[:=]\s*[^,\]\)\n]+.*?ts\s*[:=]\s*[^,\]\)\n]+", re.IGNORECASE)
    return bool(citation_pattern.search(text or ""))


def validate_answer_contract(text: str) -> bool:
    if not raw_claim_like_text_detected(text):
        return True
    return has_required_memory_citation(text)


def has_general_knowledge_marker(text: str) -> bool:
    normalized = (text or "").strip().lower()
    return normalized.startswith(GENERAL_KNOWLEDGE_MARKER_PREFIX.lower())


def passes_general_knowledge_confidence_gate(confidence_decision: dict[str, object]) -> bool:
    confidence = float(confidence_decision.get("general_knowledge_confidence", 0.0) or 0.0)
    support_count = int(confidence_decision.get("general_knowledge_support", 0) or 0)
    return confidence >= GENERAL_KNOWLEDGE_CONFIDENCE_MIN and support_count >= GENERAL_KNOWLEDGE_SUPPORT_MIN


def validate_general_knowledge_contract(
    text: str,
    *,
    provenance_types: list[ProvenanceType],
    confidence_decision: dict[str, object],
) -> bool:
    if not response_contains_claims(text):
        return True
    if ProvenanceType.GENERAL_KNOWLEDGE not in provenance_types:
        return True
    return has_general_knowledge_marker(text) and passes_general_knowledge_confidence_gate(confidence_decision)


def is_unsafe_user_request(text: str) -> bool:
    lowered = (text or "").lower()
    return bool(re.search(r"\b(bypass|exploit|weapon|harm|poison|malware)\b", lowered))


def evaluate_alignment_decision(
    *,
    user_input: str,
    draft_answer: str,
    final_answer: str,
    confidence_decision: dict[str, object],
    claims: list[str],
    provenance_types: list[ProvenanceType],
    basis_statement: str,
) -> dict[str, object]:
    def _clamp01(value: float) -> float:
        return round(max(0.0, min(1.0, value)), 4)

    def _candidate_margin_normalized() -> tuple[float, float, float]:
        scored_candidates = confidence_decision.get("scored_candidates", [])
        if not isinstance(scored_candidates, list) or len(scored_candidates) < 2:
            return 0.0, 0.0, 0.0
        first = scored_candidates[0] if isinstance(scored_candidates[0], dict) else {}
        second = scored_candidates[1] if isinstance(scored_candidates[1], dict) else {}
        top_score = float(first.get("final_score", 0.0) or 0.0)
        second_score = float(second.get("final_score", 0.0) or 0.0)
        observed_margin = max(0.0, top_score - second_score)
        required_margin = float(confidence_decision.get("min_margin_to_second", 0.05) or 0.05)
        normalized_margin = _clamp01(observed_margin / required_margin) if required_margin > 0.0 else 1.0
        return observed_margin, required_margin, normalized_margin

    contract_exempt_response = is_clarification_answer(final_answer) or final_answer in {
        ASSIST_ALTERNATIVES_ANSWER,
    } or _is_capabilities_help_answer(final_answer)
    has_claims = response_contains_claims(draft_answer)
    raw_claim_text_detected = raw_claim_like_text_detected(draft_answer)
    has_citation = has_required_memory_citation(draft_answer)
    context_confident = bool(confidence_decision.get("context_confident", False))
    unsafe_request = is_unsafe_user_request(user_input)
    observed_margin, required_margin, confidence_margin_normalized = _candidate_margin_normalized()

    citation_required_for_mode = raw_claim_text_detected and not contract_exempt_response
    citation_check_applicable = citation_required_for_mode
    if citation_required_for_mode:
        citation_validity = 1.0 if has_citation else 0.0
    elif raw_claim_text_detected:
        citation_validity = 0.5
    else:
        citation_validity = 0.0
    factual_grounding_reliability = _clamp01((0.65 * citation_validity) + (0.35 * confidence_margin_normalized))
    safety_compliance_strictness = 0.0 if (unsafe_request and final_answer != DENY_ANSWER) else 1.0

    fallback_mode_score = 1.0
    if final_answer == DENY_ANSWER:
        fallback_mode_score = 0.0
    elif final_answer == FALLBACK_ANSWER:
        fallback_mode_score = 0.25
    elif contract_exempt_response:
        fallback_mode_score = 0.7

    intent_fulfillment_proxy = 1.0 if context_confident and final_answer not in {"", FALLBACK_ANSWER, DENY_ANSWER} else 0.45
    if contract_exempt_response:
        intent_fulfillment_proxy = 0.75
    response_utility = _clamp01((0.5 * fallback_mode_score) + (0.5 * intent_fulfillment_proxy))

    observed_latency_ms = float(confidence_decision.get("turn_latency_ms", 0.0) or 0.0)
    latency_budget_ms = float(confidence_decision.get("latency_budget_ms", 3500.0) or 3500.0)
    latency_score = 1.0 if observed_latency_ms <= 0.0 else _clamp01(1.0 - (observed_latency_ms / latency_budget_ms))
    token_budget_ratio = float(confidence_decision.get("token_budget_ratio", 0.0) or 0.0)
    token_budget_score = 1.0 if token_budget_ratio <= 0.0 else _clamp01(1.0 - token_budget_ratio)
    cost_latency_budget = _clamp01(min(latency_score, token_budget_score))

    required_provenance_checks = {
        "claims_non_empty": bool(claims),
        "provenance_types_non_empty": bool(provenance_types),
        "basis_statement_non_empty": bool((basis_statement or "").strip()),
    }
    passed_required_checks = sum(1 for passed in required_provenance_checks.values() if passed)
    provenance_transparency = 0.0 if not is_non_trivial_answer(final_answer) else _clamp01(
        passed_required_checks / float(len(required_provenance_checks))
    )

    if safety_compliance_strictness < 1.0:
        final_alignment_decision = "deny"
    elif contract_exempt_response:
        final_alignment_decision = "allow"
    elif factual_grounding_reliability < 0.6:
        final_alignment_decision = "fallback"
    elif response_utility < 0.5:
        final_alignment_decision = "fallback"
    elif provenance_transparency < 0.75:
        final_alignment_decision = "fallback"
    elif cost_latency_budget < 0.35:
        final_alignment_decision = "fallback"
    else:
        final_alignment_decision = "allow"

    return {
        "objective_version": ALIGNMENT_OBJECTIVE_VERSION,
        "dimensions": {
            "factual_grounding_reliability": factual_grounding_reliability,
            "safety_compliance_strictness": safety_compliance_strictness,
            "response_utility": response_utility,
            "cost_latency_budget": cost_latency_budget,
            "provenance_transparency": provenance_transparency,
        },
        "dimension_inputs": {
            "raw": {
                "has_claims": has_claims,
                "raw_claim_like_text_detected": raw_claim_text_detected,
                "has_required_memory_citation": has_citation,
                "citation_required_for_mode": citation_required_for_mode,
                "citation_check_applicable": citation_check_applicable,
                "context_confident": context_confident,
                "unsafe_request": unsafe_request,
                "confidence_margin_observed": round(observed_margin, 4),
                "confidence_margin_required": round(required_margin, 4),
                "fallback_mode_score": fallback_mode_score,
                "intent_fulfillment_proxy": intent_fulfillment_proxy,
                "turn_latency_ms": observed_latency_ms,
                "latency_budget_ms": latency_budget_ms,
                "token_budget_ratio": token_budget_ratio,
                "provenance_checks": required_provenance_checks,
            },
            "normalized": {
                "citation_validity": citation_validity,
                "confidence_margin_normalized": confidence_margin_normalized,
                "fallback_mode_score": fallback_mode_score,
                "intent_fulfillment_proxy": intent_fulfillment_proxy,
                "latency_score": latency_score,
                "token_budget_score": token_budget_score,
                "provenance_completeness": provenance_transparency,
            },
        },
        "final_alignment_decision": final_alignment_decision,
    }


def _run_chat_loop(
    *,
    llm: ChatOllama,
    store: MemoryStore,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    io_channel: str,
    capability_status: CapabilityStatus,
    capability_snapshot: CapabilitySnapshot,
    read_user_utterance,
    send_assistant_text,
    clock: Clock,
) -> None:
    last_user_message_ts = ""
    prior_pipeline_state: PipelineState | None = None
    while True:
        utterance = read_user_utterance()
        if utterance is None:
            return
        utterance = utterance.strip()
        if not utterance:
            send_assistant_text("I heard silence. Try again.")
            continue

        append_session_log(
            "user_utterance_ingest",
            {
                "channel": io_channel,
                "utterance": utterance,
            },
        )

        low = utterance.lower()
        if low in {"stop", "quit", "exit"}:
            send_assistant_text("Stopping. Bye.")
            break

        classified_intent, resolved_intent = resolve_turn_intent(
            utterance=utterance,
            prior_pipeline_state=prior_pipeline_state,
        )
        intent_label = _intent_label(resolved_intent)

        state = PipelineState(
            user_input=utterance,
            last_user_message_ts=last_user_message_ts,
            classified_intent=classified_intent.value,
            resolved_intent=resolved_intent.value,
            prior_unresolved_intent=(
                prior_pipeline_state.prior_unresolved_intent
                if prior_pipeline_state is not None
                else ""
            ),
        )
        append_pipeline_snapshot("ingest", state)

        _validate_and_log_transition(validate_observe_pre(state))
        state = observe_stage(state)
        _validate_and_log_transition(validate_observe_post(state))
        append_pipeline_snapshot("observe", state)

            # -----------------------
            # 1) Store user utterance card + reflection card
            # -----------------------
        now_iso = clock.now().isoformat()
        u_id = str(uuid.uuid4())

        u_card = make_utterance_card(
            ts_iso=now_iso,
            speaker="user",
            text=utterance,
            doc_id=u_id,
            channel=io_channel,
        )
        store_doc(
            store,
            doc_id=u_id,
            content=u_card,
            metadata={
                "ts": now_iso,
                "type": "user_utterance",
                "speaker": "user",
                "channel": io_channel,
                "doc_id": u_id,
                "raw": utterance,
            },
        )

        u_ref_yaml = generate_reflection_yaml(llm, speaker="user", text=utterance)
        u_ref_ts = clock.now().isoformat()
        u_ref_id = str(uuid.uuid4())

        u_ref_card = make_reflection_card(
            ts_iso=u_ref_ts,
            about="user",
            source_doc_id=u_id,
            doc_id=u_ref_id,
            reflection_yaml=u_ref_yaml,
        )
        store_doc(
            store,
            doc_id=u_ref_id,
            content=u_ref_card,
            metadata={
                "ts": u_ref_ts,
                "type": "reflection",
                "about": "user",
                "source_doc_id": u_id,
                "doc_id": u_ref_id,
            },
        )

            # -----------------------
            # 2) Retrieve + time-aware rerank (FIXED: handle tuples)
            # -----------------------
        retrieval_branch = _select_retrieval_branch(utterance=utterance, intent=resolved_intent)
        append_session_log(
            "retrieval_branch_selected",
            {
                "utterance": utterance,
                "intent": intent_label,
                "intent_classified": classified_intent.value,
                "intent_resolved": resolved_intent.value,
                "retrieval_branch": retrieval_branch,
            },
        )

        if retrieval_branch == "memory_retrieval":
            _validate_and_log_transition(validate_encode_pre(state))
            state = encode_stage(llm, state)
            _validate_and_log_transition(validate_encode_post(state))
            append_pipeline_snapshot("rewrite", state)
            append_session_log("query_rewrite_output", {"utterance": utterance, "query": state.rewritten_query})

            _validate_and_log_transition(validate_retrieve_pre(state))
            state, docs_and_scores = stage_retrieve(store, state)
            _validate_and_log_transition(validate_retrieve_post(state))
            append_pipeline_snapshot("retrieve", state)
            append_session_log(
                "retrieval_candidates",
                {
                    "query": state.rewritten_query,
                    "candidate_count": len(docs_and_scores),
                    "top_candidates": [
                        {
                            "doc_id": (doc.id or doc.metadata.get("doc_id") or ""),
                            "score": float(score),
                        }
                        for doc, score in docs_and_scores[:4]
                    ],
                },
            )

            _validate_and_log_transition(validate_rerank_pre(state))
            state, hits = stage_rerank(
                state,
                docs_and_scores,
                utterance=utterance,
                user_doc_id=u_id,
                user_reflection_doc_id=u_ref_id,
                near_tie_delta=near_tie_delta,
                clock=clock,
            )
            _validate_and_log_transition(validate_rerank_post(state))
            append_pipeline_snapshot("rerank", state)
        else:
            minimal_confidence = _minimal_confidence_decision_for_direct_answer(branch=retrieval_branch)
            state = replace(state, rewritten_query=state.user_input, retrieval_candidates=[], reranked_hits=[], confidence_decision=minimal_confidence)
            append_pipeline_snapshot("rewrite", state)
            append_pipeline_snapshot("retrieve", state)
            append_pipeline_snapshot("rerank", state)
            append_session_log("query_rewrite_output", {"utterance": utterance, "query": state.rewritten_query, "skipped": True})
            append_session_log(
                "retrieval_candidates",
                {
                    "query": state.rewritten_query,
                    "candidate_count": 0,
                    "top_candidates": [],
                    "skipped": True,
                },
            )
            append_session_log(
                "rerank_skipped",
                {
                    "utterance": utterance,
                    "reason": "intent_routed_to_direct_answer",
                    "intent": intent_label,
                    "retrieval_branch": retrieval_branch,
                },
            )
            hits = []

        ambiguity_score = _ambiguity_score(state.confidence_decision)
        append_session_log(
            "intent_classified",
            {
                "utterance": utterance,
                "intent": intent_label,
                "intent_classified": classified_intent.value,
                "intent_resolved": resolved_intent.value,
                "ambiguity_score": ambiguity_score,
                "user_followup_signal_proxy": round(ambiguity_score, 4),
            },
        )
        append_session_log(
            "time_target_parse",
            {
                "utterance": utterance,
                "now_ts": state.confidence_decision.get("now_ts", ""),
                "target_ts": state.confidence_decision.get("target_ts", ""),
                "sigma_seconds": state.confidence_decision.get("sigma_seconds", 0.0),
                "objective_candidates": state.confidence_decision.get("scored_candidates", []),
            },
        )
        if state.confidence_decision.get("ambiguity_detected", False):
            append_session_log(
                "ambiguity_detected",
                {
                    "query": state.rewritten_query,
                    "candidates": state.confidence_decision.get("ambiguous_candidates", []),
                },
            )

            # -----------------------
            # 3) Answer using ONLY memory + recent chat
            # -----------------------
        _validate_and_log_transition(validate_answer_pre(state))
        state = stage_answer(
            llm,
            state,
            chat_history=chat_history,
            hits=hits,
            capability_status=capability_status,
            runtime_capability_status=capability_snapshot.runtime_capability_status,
            clock=clock,
        )
        _validate_and_log_transition(validate_answer_post(state))
        append_pipeline_snapshot("answer", state)
        append_session_log(
            "final_answer_mode",
            {
                "mode": state.invariant_decisions.get("answer_mode", "dont-know"),
                "query": state.rewritten_query,
                "context_confident": state.confidence_decision.get("context_confident", False),
                "retrieved_docs": [(d.id or d.metadata.get("doc_id") or "") for d in hits],
                "claims": state.claims,
                "provenance_types": [p.value for p in state.provenance_types],
                "used_memory_refs": state.used_memory_refs,
                "used_source_evidence_refs": state.used_source_evidence_refs,
                "source_evidence_attribution": state.source_evidence_attribution,
                "basis_statement": state.basis_statement,
            },
        )
        chosen_action = str(state.invariant_decisions.get("fallback_action", "NONE"))
        followup_proxy = _user_followup_signal_proxy(
            final_answer=state.final_answer,
            fallback_action=chosen_action,
            ambiguity_score=ambiguity_score,
        )
        append_session_log(
            "fallback_action_selected",
            {
                "utterance": utterance,
                "intent": intent_label,
                "intent_classified": classified_intent.value,
                "intent_resolved": resolved_intent.value,
                "ambiguity_score": ambiguity_score,
                "chosen_action": chosen_action,
                "user_followup_signal_proxy": followup_proxy,
            },
        )
        append_session_log(
            "provenance_summary",
            {
                "utterance": utterance,
                "intent": intent_label,
                "intent_classified": classified_intent.value,
                "intent_resolved": resolved_intent.value,
                "ambiguity_score": ambiguity_score,
                "chosen_action": chosen_action,
                "user_followup_signal_proxy": followup_proxy,
                "claims": state.claims,
                "provenance_types": [p.value for p in state.provenance_types],
                "used_memory_refs": state.used_memory_refs,
                "used_source_evidence_refs": state.used_source_evidence_refs,
                "source_evidence_attribution": state.source_evidence_attribution,
                "basis_statement": state.basis_statement,
            },
        )
        append_session_log(
            "alignment_decision_evaluated",
            {
                "utterance": utterance,
                "intent": intent_label,
                "intent_classified": classified_intent.value,
                "intent_resolved": resolved_intent.value,
                "alignment_decision": state.alignment_decision,
                "alignment_dimension_inputs_raw": state.alignment_decision.get("dimension_inputs", {}).get("raw", {}),
                "alignment_dimension_inputs_normalized": state.alignment_decision.get("dimension_inputs", {}).get("normalized", {}),
                "alignment_dimensions": state.alignment_decision.get("dimensions", {}),
            },
        )

        if capability_snapshot.runtime_capability_status.debug_enabled:
            debug_trace = _format_debug_turn_trace(
                state=state,
                intent_label=intent_label,
                hits=hits,
            )
            append_session_log(
                "debug_turn_trace",
                {
                    "utterance": utterance,
                    "trace": debug_trace,
                },
            )
            send_assistant_text(debug_trace)

        unresolved_intent = (
            resolved_intent.value
            if is_clarification_answer(state.final_answer) or _is_capabilities_help_answer(state.final_answer)
            else ""
        )
        state = replace(state, prior_unresolved_intent=unresolved_intent)
        send_assistant_text(state.final_answer)

            # -----------------------
            # 4) Store assistant utterance card + reflection card
            # -----------------------
        last_user_message_ts = now_iso
        chat_history.append({"role": "user", "content": utterance})
        chat_history.append({"role": "assistant", "content": state.final_answer})
        prior_pipeline_state = state

        a_ts = clock.now().isoformat()
        a_id = str(uuid.uuid4())
        a_card = make_utterance_card(
            ts_iso=a_ts,
            speaker="assistant",
            text=state.final_answer,
            doc_id=a_id,
            channel=io_channel,
        )
        store_doc(
            store,
            doc_id=a_id,
            content=a_card,
            metadata={
                "ts": a_ts,
                "type": "assistant_utterance",
                "speaker": "assistant",
                "channel": io_channel,
                "doc_id": a_id,
                "raw": state.final_answer,
            },
        )

        a_ref_yaml = generate_reflection_yaml(llm, speaker="assistant", text=state.final_answer)
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
            metadata={
                "ts": a_ref_ts,
                "type": "reflection",
                "about": "assistant",
                "source_doc_id": a_id,
                "doc_id": a_ref_id,
            },
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
            append_session_log(
                "promoted_context_persisted",
                {
                    "source_doc_id": a_id,
                    "source_reflection_id": a_ref_id,
                    "promoted_doc_ids": promoted_doc_ids,
                    "count": len(promoted_doc_ids),
                },
            )


def _run_cli_mode(*, llm: ChatOllama, store: MemoryStore, chat_history: deque[ChatMsg], near_tie_delta: float, capability_snapshot: CapabilitySnapshot, clock: Clock) -> None:
    print("CLI chat ready. Ask memory-grounded questions; type 'stop' to exit.")

    def _read() -> str | None:
        try:
            return input("you> ")
        except EOFError:
            return None

    def _send(text: str) -> None:
        print(f"bot> {text}")

    _run_chat_loop(
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=capability_snapshot,
        read_user_utterance=_read,
        send_assistant_text=_send,
        clock=clock,
    )


def _run_satellite_mode(
    *,
    llm: ChatOllama,
    store: MemoryStore,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    api_url: str,
    token: str,
    entity_id: str,
    capability_snapshot: CapabilitySnapshot,
    clock: Clock,
) -> None:
    rest = normalize_rest_api_url(api_url)
    with Client(rest, token) as client:
        sat_say(client, entity_id, "v0 memory loop online. Ask one memory-based question. Say 'stop' to exit.")

        def _read() -> str | None:
            res = ask_question(
                channel="satellite",
                spec=AskSpec(
                    question="Ask one memory-grounded question.",
                    answers=None,
                    timeout_s=60.0,
                ),
                api_url=api_url,
                token=token,
                satellite_entity_id=entity_id,
            )
            if res.get("error"):
                sat_say(client, entity_id, f"I didn't get that. Error: {res['error']}")
                return ""
            return str(res.get("sentence") or "")

        def _send(text: str) -> None:
            sat_say(client, entity_id, text)

        _run_chat_loop(
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


def _build_runtime_capability_status(
    *,
    requested_mode: str,
    effective_mode: str | None,
    daemon_mode: bool,
    fallback_reason: str | None,
    runtime: dict[str, object],
    ha_error: str | None,
    ollama_error: str | None,
) -> RuntimeCapabilityStatus:
    effective = effective_mode or "unavailable"
    can_text_clarify = effective in {"cli", "satellite"}
    can_satellite_ask = ha_error is None and effective == "satellite"
    return RuntimeCapabilityStatus(
        ollama_available=ollama_error is None,
        ha_available=ha_error is None,
        effective_mode=effective,
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        fallback_reason=fallback_reason,
        memory_backend=str(runtime.get("memory_store_backend", "unknown")),
        debug_enabled=os.getenv("TESTBOT_DEBUG", "0") == "1",
        text_clarification_available=can_text_clarify,
        satellite_ask_available=can_satellite_ask,
    )


def build_capability_snapshot(*, requested_mode: str, daemon_mode: bool, runtime: dict[str, object]) -> CapabilitySnapshot:
    ha_error = _ha_connection_error(
        str(runtime["ha_api_url"]),
        str(runtime["ha_api_secret"]),
        str(runtime["ha_satellite_entity_id"]),
    )
    ollama_error = _ollama_connection_error(
        str(runtime["ollama_base_url"]),
        str(runtime["ollama_model"]),
        str(runtime["ollama_embedding_model"]),
    )

    effective_mode, fallback_reason, exit_reason = _resolve_effective_mode(
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        ha_error=ha_error,
        ollama_error=ollama_error,
    )

    runtime_capability_status = _build_runtime_capability_status(
        requested_mode=requested_mode,
        effective_mode=effective_mode,
        daemon_mode=daemon_mode,
        fallback_reason=fallback_reason,
        runtime=runtime,
        ha_error=ha_error,
        ollama_error=ollama_error,
    )

    return CapabilitySnapshot(
        runtime=runtime,
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        effective_mode=effective_mode,
        fallback_reason=fallback_reason,
        exit_reason=exit_reason,
        ha_error=ha_error,
        ollama_error=ollama_error,
        runtime_capability_status=runtime_capability_status,
    )


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    runtime = _read_runtime_env()

    capability_snapshot = build_capability_snapshot(
        requested_mode=args.mode,
        daemon_mode=args.daemon,
        runtime=runtime,
    )

    append_session_log(
        "startup_mode_resolution",
        {
            "requested_mode": args.mode,
            "effective_mode": capability_snapshot.effective_mode,
            "daemon_mode": args.daemon,
            "ha_available": capability_snapshot.ha_error is None,
            "ha_error": capability_snapshot.ha_error,
            "ollama_available": capability_snapshot.ollama_error is None,
            "ollama_error": capability_snapshot.ollama_error,
            "fallback_reason": capability_snapshot.fallback_reason,
            "exit_reason": capability_snapshot.exit_reason,
        },
    )

    _print_startup_status(snapshot=capability_snapshot)

    if capability_snapshot.effective_mode is None:
        if args.mode == "auto" and args.daemon:
            print(f"Daemon mode requested in auto mode and {capability_snapshot.exit_reason}", file=sys.stderr)
        else:
            print(f"Startup failed and {capability_snapshot.exit_reason}", file=sys.stderr)
        return

    llm = ChatOllama(model=str(runtime["ollama_model"]), base_url=str(runtime["ollama_base_url"]), temperature=0.0)
    embeddings = OllamaEmbeddings(model=str(runtime["ollama_embedding_model"]), base_url=str(runtime["ollama_base_url"]))
    store = build_memory_store(
        embeddings=embeddings,
        mode=str(runtime["memory_store_mode"]),
        elasticsearch_url=str(runtime["elasticsearch_url"]),
        elasticsearch_index=str(runtime["elasticsearch_index"]),
    )
    chat_history: deque[ChatMsg] = deque(maxlen=10)
    clock = SystemClock()

    _run_source_ingestion(runtime=runtime, store=store)

    if capability_snapshot.effective_mode == "satellite":
        _run_satellite_mode(
            llm=llm,
            store=store,
            chat_history=chat_history,
            near_tie_delta=float(runtime["memory_near_tie_delta"]),
            capability_snapshot=capability_snapshot,
            api_url=str(runtime["ha_api_url"]),
            token=str(runtime["ha_api_secret"]),
            entity_id=str(runtime["ha_satellite_entity_id"]),
            clock=clock,
        )
        return

    _run_cli_mode(
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=float(runtime["memory_near_tie_delta"]),
        capability_snapshot=capability_snapshot,
        clock=clock,
    )

    return


if __name__ == "__main__":
    main()
