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
from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from collections import deque
from dataclasses import asdict, dataclass, is_dataclass, replace
from enum import Enum
from pathlib import Path

import arrow
from homeassistant_api import Client

from testbot.clock import Clock, SystemClock
from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc, utc_now_iso
from testbot.memory_strata import (
    MemoryStratum,
    SegmentDescriptor,
    SegmentType,
    apply_persistence_metadata,
    derive_segment_descriptor,
)
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType, append_pipeline_snapshot
from testbot.promotion_policy import persist_promoted_context
from testbot.reflection_policy import CapabilityStatus, decide_fallback_action, fallback_reason as derive_fallback_reason
from testbot.answer_policy import AnswerPolicyInput, AnswerRoutingDecision, resolve_answer_mode, resolve_answer_routing
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
from testbot.intent_router import (
    IntentType,
    classify_intent,
    extract_intent_facets,
    is_satellite_action_request,
    planning_pathway_for_intent,
)
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
from testbot.response_planner import build_response_plan, plan_to_dict, render_response_plan_block
from testbot.reject_taxonomy import RejectSignal, derive_reject_signal
from testbot.canonical_turn_orchestrator import CanonicalStage, CanonicalTurnContext, CanonicalTurnOrchestrator
from testbot.turn_observation import observe_turn
from testbot.candidate_encoding import encode_turn_candidates
from testbot.stabilization import StabilizedTurnState, stabilize_pre_route
from testbot.context_resolution import resolve as resolve_context
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.evidence_retrieval import (
    EvidenceBundle,
    build_evidence_bundle_from_docs_and_scores,
    build_evidence_bundle_from_hits,
    continuity_evidence_from_prior_state,
    retrieval_result,
)
from testbot.policy_decision import (
    DecisionClass,
    DecisionObject,
    decide as decide_policy,
    decide_from_evidence,
)
from testbot.answer_assembly import assemble_answer_contract
from testbot.answer_validation import validate_answer_assembly_boundary
from testbot.answer_rendering import render_answer
from testbot.answer_commit import commit_answer_stage
from testbot.retrieval_routing import decide_retrieval_routing, is_definitional_query_form

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
INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.75
RETRIEVAL_SCORE_THRESHOLD = 0.0


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
    debug_verbose: bool
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


@dataclass(frozen=True)
class AnswerAssembleResult:
    draft_answer: str
    final_answer: str
    fallback_action: str
    intent_class: str
    social_or_non_knowledge_intent: bool
    answer_policy_rationale: dict[str, object]
    capability_help_short_circuit: bool = False


@dataclass(frozen=True)
class AnswerValidateResult:
    final_answer: str
    claims: list[str]
    provenance_types: list[ProvenanceType]
    used_memory_refs: list[str]
    used_source_evidence_refs: list[str]
    source_evidence_attribution: list[dict[str, str]]
    basis_statement: str
    invariant_decisions: dict[str, object]
    alignment_decision: dict[str, object]


@dataclass(frozen=True)
class AnswerRenderResult:
    final_answer: str


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
    parser.add_argument(
        "--debug-verbose",
        action=BooleanOptionalAction,
        default=None,
        help=(
            "Enable verbose debug trace payloads when TESTBOT_DEBUG=1. "
            "Defaults to TESTBOT_DEBUG_VERBOSE environment setting."
        ),
    )
    return parser.parse_args(argv)


def _read_runtime_env() -> dict[str, object]:
    memory_store_mode = os.getenv("MEMORY_STORE_MODE", "in_memory")
    debug_verbose = os.getenv("TESTBOT_DEBUG_VERBOSE", "0") == "1"
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
        "debug_verbose": debug_verbose,
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
    debug_mode = "enabled" if snapshot.runtime_capability_status.debug_enabled else "disabled"
    debug_verbose = "enabled" if snapshot.runtime_capability_status.debug_verbose else "disabled"
    print(f"Debug tracing: {debug_mode} (TESTBOT_DEBUG), verbose payloads: {debug_verbose} (TESTBOT_DEBUG_VERBOSE/--debug-verbose)")
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
    def _normalize_json_safe(value: object) -> object:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Enum):
            return _normalize_json_safe(value.value)
        if isinstance(value, dict):
            return {str(key): _normalize_json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [_normalize_json_safe(item) for item in value]
        if isinstance(value, set):
            return [_normalize_json_safe(item) for item in sorted(value, key=repr)]

        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            try:
                return _normalize_json_safe(to_dict())
            except Exception:
                pass

        if is_dataclass(value):
            return _normalize_json_safe(asdict(value))

        if hasattr(value, "__dict__"):
            return _normalize_json_safe(vars(value))

        return repr(value)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utc_now_iso(),
        "event": event,
        "schema_version": SESSION_LOG_SCHEMA_VERSION,
        **_normalize_json_safe(payload),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _intent_telemetry_payload(
    *,
    state: PipelineState,
    utterance: str | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "intent": state.resolved_intent,
        "intent_classified": state.classified_intent,
        "intent_resolved": state.resolved_intent,
    }
    if utterance is not None:
        payload["utterance"] = utterance
    if extra:
        payload.update(extra)
    return payload


def doc_to_candidate_hit(doc: Document, score: float) -> CandidateHit:
    return CandidateHit(
        doc_id=str(doc.id or doc.metadata.get("doc_id") or ""),
        score=float(score),
        ts=str(doc.metadata.get("ts") or ""),
        card_type=str(doc.metadata.get("type") or ""),
    )


_SELF_IDENTITY_DECLARATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*i\s*(?:am|'m|’m)\s+[\w'-]+(?:\s+[\w'-]+)*\s*[.!?]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*my\s+name\s+is\s+[\w'-]+(?:\s+[\w'-]+)*\s*[.!?]*\s*$", re.IGNORECASE),
)

_SELF_REFERENTIAL_IDENTITY_RECALL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*who\s+am\s+i\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:\s+is|'s)\s+my\s+name\b", re.IGNORECASE),
    re.compile(r"\bremind\s+me\s+(?:what\s+)?my\s+name\s+is\b", re.IGNORECASE),
)

_PRIOR_IDENTITY_CANDIDATE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi\s*(?:am|'m|’m)\s+[\w'-]+", re.IGNORECASE),
    re.compile(r"\bmy\s+name\s+is\s+[\w'-]+", re.IGNORECASE),
)


def _is_self_identity_declaration(utterance: str) -> bool:
    return any(pattern.match(utterance or "") is not None for pattern in _SELF_IDENTITY_DECLARATION_PATTERNS)


def _is_self_referential_identity_recall_query(utterance: str) -> bool:
    return any(pattern.search(utterance or "") is not None for pattern in _SELF_REFERENTIAL_IDENTITY_RECALL_PATTERNS)


def _should_force_memory_retrieval_for_identity_recall(
    *,
    utterance: str,
    prior_state: PipelineState | None,
    continuity_evidence: tuple[str, ...],
    context_history_anchors: tuple[str, ...],
) -> bool:
    return _is_self_referential_identity_recall_query(utterance) and _has_prior_identity_candidates_or_continuity_markers(
        prior_state=prior_state,
        continuity_evidence=continuity_evidence,
        context_history_anchors=context_history_anchors,
    )


def _has_prior_identity_candidates_or_continuity_markers(
    *,
    prior_state: PipelineState | None,
    continuity_evidence: tuple[str, ...],
    context_history_anchors: tuple[str, ...],
) -> bool:
    if any(anchor.startswith("commit.confirmed_user_facts:") for anchor in continuity_evidence):
        return True
    if any(anchor.startswith("commit.confirmed_user_facts:") for anchor in context_history_anchors):
        return True
    if prior_state is None:
        return False

    prior_candidate_facts = prior_state.candidate_facts if isinstance(prior_state.candidate_facts, dict) else {}
    for fact in prior_candidate_facts.get("facts", []):
        if not isinstance(fact, dict):
            continue
        if str(fact.get("key") or "").strip() == "user_name":
            return True

    prior_utterance = str(prior_state.user_input or "")
    return any(pattern.search(prior_utterance) is not None for pattern in _PRIOR_IDENTITY_CANDIDATE_PATTERNS)


def stage_rewrite_query(llm: ChatOllama, state: PipelineState) -> PipelineState:
    if _is_self_identity_declaration(state.user_input):
        return replace(state, rewritten_query=state.user_input)

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


def stage_retrieve(
    store: MemoryStore,
    state: PipelineState,
    *,
    exclude_doc_ids: set[str] | None = None,
    exclude_source_ids: set[str] | None = None,
    exclude_turn_scoped_ids: set[str] | None = None,
    segment_ids: set[str] | None = None,
    segment_types: set[str] | None = None,
) -> tuple[PipelineState, list[tuple[Document, float]]]:
    normalized_exclude_doc_ids = {value for value in (exclude_doc_ids or set()) if value}
    normalized_exclude_source_ids = {value for value in (exclude_source_ids or set()) if value}
    normalized_exclude_turn_scoped_ids = {value for value in (exclude_turn_scoped_ids or set()) if value}
    normalized_segment_ids = {value for value in (segment_ids or set()) if value}
    normalized_segment_types = {value for value in (segment_types or set()) if value}
    raw_docs_and_scores = store.similarity_search_with_score(
        state.rewritten_query,
        k=18,
        exclude_doc_ids=normalized_exclude_doc_ids,
        exclude_source_ids=normalized_exclude_source_ids,
        exclude_turn_scoped_ids=normalized_exclude_turn_scoped_ids,
        segment_ids=normalized_segment_ids,
        segment_types=normalized_segment_types,
    )
    docs_and_scores = mix_source_evidence_with_memory_cards(raw_docs_and_scores, top_k=12, source_quota=3)
    retrieval_candidates = [doc_to_candidate_hit(doc, score) for doc, score in docs_and_scores]
    retrieval_telemetry = {
        "retrieval_candidates_considered": len(raw_docs_and_scores),
        "retrieval_returned_top_k": len(docs_and_scores),
        "retrieval_threshold": RETRIEVAL_SCORE_THRESHOLD,
        "retrieval_exclude_doc_ids": sorted(normalized_exclude_doc_ids),
        "retrieval_exclude_source_ids": sorted(normalized_exclude_source_ids),
        "retrieval_exclude_turn_scoped_ids": sorted(normalized_exclude_turn_scoped_ids),
        "retrieval_exclusion_invariant": "retrieve_stage_primary",
        "retrieval_segment_ids": sorted(normalized_segment_ids),
        "retrieval_segment_types": sorted(normalized_segment_types),
    }
    return replace(
        state,
        retrieval_candidates=retrieval_candidates,
        confidence_decision={**state.confidence_decision, **retrieval_telemetry},
    ), docs_and_scores


_ANAPHORA_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bit\b", re.IGNORECASE),
    re.compile(r"\bthat\b", re.IGNORECASE),
)


def _contains_anaphora_cue(utterance: str) -> bool:
    text = utterance or ""
    return any(pattern.search(text) is not None for pattern in _ANAPHORA_PATTERNS)


def _contains_elapsed_time_cue(utterance: str) -> bool:
    text = (utterance or "").lower()
    return "how long ago" in text


def _contains_yesterday_cue(utterance: str) -> bool:
    return "yesterday" in (utterance or "").lower()


def _humanize_seconds_delta(delta_seconds: int) -> str:
    if delta_seconds < 60:
        return f"{delta_seconds} seconds ago"
    if delta_seconds < 3600:
        minutes = max(1, round(delta_seconds / 60))
        return f"{minutes} minutes ago"
    if delta_seconds < 86400:
        hours = max(1, round(delta_seconds / 3600))
        return f"{hours} hours ago"
    days = max(1, round(delta_seconds / 86400))
    return f"{days} days ago"


def _candidate_anchor_confidence(score: float) -> float:
    return round(max(0.0, min(1.0, float(score))), 4)


def _resolve_temporal_anaphora_bridge(
    *,
    utterance: str,
    docs_and_scores: list[tuple[Document, float]],
    now: arrow.Arrow,
) -> dict[str, object]:
    anaphora_detected = _contains_anaphora_cue(utterance)
    elapsed_time_cue = _contains_elapsed_time_cue(utterance)
    yesterday_cue = _contains_yesterday_cue(utterance)

    anchor_candidates: list[dict[str, object]] = []
    for doc, score in docs_and_scores[:5]:
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        anchor_candidates.append(
            {
                "doc_id": str(doc.id or metadata.get("doc_id") or ""),
                "ts": str(metadata.get("ts") or ""),
                "confidence": _candidate_anchor_confidence(score),
            }
        )

    selected_anchor = anchor_candidates[0] if anchor_candidates else {"doc_id": "", "ts": "", "confidence": 0.0}
    selected_anchor_ts = str(selected_anchor.get("ts") or "")
    selected_anchor_doc_id = str(selected_anchor.get("doc_id") or "")

    delta_seconds: int | None = None
    if selected_anchor_ts and elapsed_time_cue:
        try:
            anchor_ts = arrow.get(selected_anchor_ts)
            delta_seconds = max(0, int((now - anchor_ts).total_seconds()))
        except Exception:
            delta_seconds = None

    target_override_ts = ""
    if selected_anchor_ts and (anaphora_detected or elapsed_time_cue):
        target_override_ts = selected_anchor_ts

    window_start = ""
    window_end = ""
    if yesterday_cue:
        window_start = now.shift(days=-1).floor("day").isoformat()
        window_end = now.shift(days=-1).ceil("day").isoformat()

    return {
        "anaphora_detected": anaphora_detected,
        "anchor_candidates": anchor_candidates,
        "selected_anchor_doc_id": selected_anchor_doc_id,
        "selected_anchor_ts": selected_anchor_ts,
        "target_override_ts": target_override_ts,
        "delta_seconds_raw": delta_seconds,
        "delta_humanized": _humanize_seconds_delta(delta_seconds) if delta_seconds is not None else "",
        "elapsed_time_cue": elapsed_time_cue,
        "time_window": "yesterday" if yesterday_cue else "",
        "window_start": window_start,
        "window_end": window_end,
    }


def _filter_docs_for_temporal_window(
    *,
    docs_and_scores: list[tuple[Document, float]],
    bridge: dict[str, object],
) -> list[tuple[Document, float]]:
    window_start = str(bridge.get("window_start") or "")
    window_end = str(bridge.get("window_end") or "")
    if not window_start or not window_end:
        return docs_and_scores

    try:
        start_ts = arrow.get(window_start)
        end_ts = arrow.get(window_end)
    except Exception:
        return docs_and_scores

    filtered: list[tuple[Document, float]] = []
    for doc, score in docs_and_scores:
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        raw_ts = str(metadata.get("ts") or "")
        if not raw_ts:
            continue
        try:
            doc_ts = arrow.get(raw_ts)
        except Exception:
            continue
        if start_ts <= doc_ts <= end_ts:
            filtered.append((doc, score))
    return filtered


def stage_rerank(
    state: PipelineState,
    docs_and_scores: list[tuple[Document, float]],
    *,
    utterance: str,
    user_doc_id: str,
    user_reflection_doc_id: str,
    near_tie_delta: float,
    clock: Clock,
    io_channel: str = "cli",
) -> tuple[PipelineState, list[Document]]:
    now = clock.now()
    temporal_bridge = _resolve_temporal_anaphora_bridge(
        utterance=utterance,
        docs_and_scores=docs_and_scores,
        now=now,
    )
    filtered_docs_and_scores = _filter_docs_for_temporal_window(
        docs_and_scores=docs_and_scores,
        bridge=temporal_bridge,
    )
    target = parse_target_time(utterance, now=now)
    target_override_ts = str(temporal_bridge.get("target_override_ts") or "")
    if target_override_ts:
        try:
            target = arrow.get(target_override_ts)
        except Exception:
            pass
    sigma = adaptive_sigma_fractional(now=now, target=target, frac=0.25)
    rerank_outcome = rerank_docs_with_time_and_type_outcome(
        filtered_docs_and_scores,
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
        **state.confidence_decision,
        "context_confident": has_context,
        "ambiguity_detected": rerank_outcome.ambiguity_detected,
        "anaphora_detected": bool(temporal_bridge.get("anaphora_detected", False)),
        "anchor_candidates": temporal_bridge.get("anchor_candidates", []),
        "selected_anchor_doc_id": str(temporal_bridge.get("selected_anchor_doc_id") or ""),
        "selected_anchor_ts": str(temporal_bridge.get("selected_anchor_ts") or ""),
        "computed_delta_raw_seconds": temporal_bridge.get("delta_seconds_raw"),
        "computed_delta_humanized": str(temporal_bridge.get("delta_humanized") or ""),
        "ambiguous_candidates": rerank_outcome.near_tie_candidates,
        "scored_candidates": rerank_outcome.scored_candidates,
        "memory_hit_count": len(hits),
        "objective": rerank_outcome.scored_candidates[0].get("objective", "") if rerank_outcome.scored_candidates else "",
        "objective_version": rerank_outcome.scored_candidates[0].get("objective_version", "") if rerank_outcome.scored_candidates else "",
        "top_final_score_min": rerank_confidence_thresholds().top_final_score_min,
        "min_margin_to_second": rerank_confidence_thresholds().min_margin_to_second,
        "allow_ambiguity_override": rerank_confidence_thresholds().allow_ambiguity_override,
        "ambiguity_override_top_final_score_min": rerank_confidence_thresholds().ambiguity_override_top_final_score_min,
        "now_ts": now.isoformat(),
        "target_ts": target.isoformat(),
        "sigma_seconds": sigma,
        "time_window": str(temporal_bridge.get("time_window") or ""),
        "window_start": str(temporal_bridge.get("window_start") or ""),
        "window_end": str(temporal_bridge.get("window_end") or ""),
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


def resolve_turn_intent(
    *,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    diagnostic_only: bool = True,
) -> tuple[IntentType, IntentType]:
    """Resolve intent for diagnostics-only parity checks.

    This helper intentionally runs outside the canonical turn pipeline and must
    not be used for authoritative production routing decisions.
    """
    if not diagnostic_only:
        raise RuntimeError(
            "resolve_turn_intent is diagnostic-only and non-authoritative; "
            "production routing must use canonical orchestrator artifacts"
        )

    _LOGGER.warning(
        "resolve_turn_intent invoked in diagnostic-only mode; output is non-authoritative",
        extra={"authority": "non_authoritative", "helper": "resolve_turn_intent"},
    )
    seed_state = PipelineState(user_input=utterance)
    observation = observe_turn(
        seed_state,
        turn_id="offline-resolve-turn-intent",
        observed_at=utc_now_iso(),
        speaker="user",
        channel="offline",
    )
    encoded = encode_turn_candidates(seed_state, observation=observation, rewritten_query=utterance)
    segment = derive_segment_descriptor(
        utterance=observation.utterance,
        has_dialogue_state=bool(encoded.dialogue_state),
    )
    _, stabilized_turn_state = stabilize_pre_route(
        store=None,  # type: ignore[arg-type]
        state=seed_state,
        observation=observation,
        encoded=encoded,
        response_plan={"pathway": "offline_intent_resolution"},
        reflection_yaml="offline: true",
        segment=segment,
        store_doc_fn=lambda *args, **kwargs: None,
    )
    context_resolution = resolve_context(
        utterance=observation.utterance,
        prior_pipeline_state=prior_pipeline_state,
    )
    intent_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=stabilized_turn_state,
            context=context_resolution,
            fallback_utterance=observation.utterance,
        )
    )
    return intent_resolution.classified_intent, intent_resolution.resolved_intent




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




def _intent_classifier_confidence(*, utterance: str, predicted_intent: IntentType) -> float:
    normalized = (utterance or "").strip().lower()
    if not normalized:
        return INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD

    if predicted_intent == IntentType.KNOWLEDGE_QUESTION and not _is_definitional_query_form(normalized):
        return 0.82

    return 0.95


def _minimal_confidence_decision_for_direct_answer(*, branch: str, base_confidence_decision: dict[str, object]) -> dict[str, object]:
    return {
        **base_confidence_decision,
        "context_confident": False,
        "ambiguity_detected": False,
        "ambiguous_candidates": [],
        "scored_candidates": [],
        "objective": "",
        "objective_version": "",
        "retrieval_branch": branch,
        "retrieval_candidates_considered": 0,
        "retrieval_returned_top_k": 0,
        "retrieval_threshold": RETRIEVAL_SCORE_THRESHOLD,
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


def _derive_response_blocker_reason(
    *,
    answer_mode: str,
    fallback_action: str,
    context_confident: bool,
    hit_count: int,
    ambiguity_detected: bool,
    answer_contract_valid: bool,
    general_knowledge_contract_valid: bool,
) -> str:
    signal = derive_reject_signal(
        intent_label="non_memory",
        answer_mode=answer_mode,
        fallback_action=fallback_action,
        context_confident=context_confident,
        context_score=0.0,
        hit_count=hit_count,
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
    )
    return signal.reason


def _derive_reject_signal(
    *,
    intent_label: str,
    answer_mode: str,
    fallback_action: str,
    context_confident: bool,
    context_score: float,
    hit_count: int,
    ambiguity_detected: bool,
    answer_contract_valid: bool,
    general_knowledge_contract_valid: bool,
) -> RejectSignal:
    return derive_reject_signal(
        intent_label=intent_label,
        answer_mode=answer_mode,
        fallback_action=fallback_action,
        context_confident=context_confident,
        context_score=context_score,
        hit_count=hit_count,
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
    )


def _derive_response_blocker_reason_legacy(
    *,
    answer_mode: str,
    fallback_action: str,
    context_confident: bool,
    hit_count: int,
    ambiguity_detected: bool,
    answer_contract_valid: bool,
    general_knowledge_contract_valid: bool,
) -> str:
    if answer_mode == "clarify" or fallback_action in {"ASK_CLARIFYING_QUESTION", "ROUTE_TO_ASK"}:
        if hit_count == 0:
            return "no memory fragments were retrieved for this request"
        if ambiguity_detected:
            return "retrieved memory fragments were ambiguous"
        if not context_confident:
            return "retrieved memory fragments were low-confidence"
    if answer_mode == "dont-know" or fallback_action == "ANSWER_UNKNOWN":
        return "insufficient reliable memory to answer directly"
    if answer_mode == "assist" or fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        if not answer_contract_valid:
            return "answer-contract rejection: draft did not satisfy grounding/citation requirements"
        if not general_knowledge_contract_valid:
            return "general-knowledge contract rejection: response did not satisfy marker/confidence policy"
        if context_confident and hit_count > 0:
            return "policy/contract rejected direct answer despite confident retrieved context"
        if ambiguity_detected:
            return "retrieved memory fragments were ambiguous; offered capability alternatives"
        if not context_confident:
            return "retrieved memory fragments were low-confidence for a direct answer"
    if answer_mode == "deny":
        return "request blocked by safety or policy checks"
    return "none"


def _gate_metrics(*, passed: bool, score: float, threshold: float) -> dict[str, float | bool]:
    margin = round(score - threshold, 4)
    return {
        "passed": passed,
        "score": round(score, 4),
        "threshold": round(threshold, 4),
        "margin": margin,
    }


def _nearest_failure_gate(*, gates: dict[str, dict[str, float | bool]]) -> dict[str, float | str] | None:
    failed: list[tuple[str, float, float]] = []
    for name, gate in gates.items():
        passed = bool(gate.get("passed", False))
        if passed:
            continue
        score = float(gate.get("score", 0.0) or 0.0)
        threshold = float(gate.get("threshold", 0.0) or 0.0)
        failed.append((name, score, threshold))
    if not failed:
        return None
    nearest_name, nearest_score, nearest_threshold = min(
        failed,
        key=lambda item: max(0.0, item[2] - item[1]),
    )
    return {
        "gate": nearest_name,
        "current": round(nearest_score, 4),
        "required": round(nearest_threshold, 4),
        "margin_to_pass": round(max(0.0, nearest_threshold - nearest_score), 4),
    }


def _gate_delta_entry(*, family: str, gate_name: str, gate: dict[str, float | bool]) -> dict[str, float | str]:
    score = float(gate.get("score", 0.0) or 0.0)
    threshold = float(gate.get("threshold", 0.0) or 0.0)
    return {
        "family": family,
        "gate": gate_name,
        "current": round(score, 4),
        "required": round(threshold, 4),
        "delta_to_pass": round(max(0.0, threshold - score), 4),
    }


def _dominant_score_contributors(*, score_decomposition: list[dict[str, object]], max_items: int = 2) -> list[dict[str, float | str]]:
    if not score_decomposition:
        return []
    top_candidate = score_decomposition[0] if isinstance(score_decomposition[0], dict) else {}
    contributor_pairs: list[tuple[str, float]] = [
        ("time_decay_freshness", float(top_candidate.get("time_decay_freshness", 0.0) or 0.0)),
        ("semantic_similarity", float(top_candidate.get("semantic_similarity", 0.0) or 0.0)),
        ("type_prior", float(top_candidate.get("type_prior", 0.0) or 0.0)),
        ("provenance_citation_factor", float(top_candidate.get("provenance_citation_factor", 0.0) or 0.0)),
    ]
    ordered = sorted(contributor_pairs, key=lambda item: (-abs(1.0 - item[1]), item[0]))
    dominant: list[dict[str, float | str]] = []
    for component, value in ordered[:max_items]:
        dominant.append(
            {
                "component": component,
                "current": round(value, 4),
                "delta_to_ideal": round(max(0.0, 1.0 - value), 4),
            }
        )
    return dominant


def _counterfactual_policy_passes(
    *,
    intent_label: str,
    action: str,
    context_confident: bool,
    context_score: float,
    hit_count: int,
    ambiguity_detected: bool,
    answer_contract_valid: bool,
    general_knowledge_contract_valid: bool,
) -> bool:
    action_to_mode = {
        "ROUTE_TO_ASK": "clarify",
        "ASK_CLARIFYING_QUESTION": "clarify",
        "ANSWER_UNKNOWN": "dont-know",
        "ANSWER_TIME": "assist",
        "OFFER_CAPABILITY_ALTERNATIVES": "assist",
        "ANSWER_FROM_MEMORY": "memory-grounded",
        "ANSWER_GENERAL_KNOWLEDGE": "assist",
    }
    mapped_mode = action_to_mode.get(action, "assist")
    signal = _derive_reject_signal(
        intent_label=intent_label,
        answer_mode=mapped_mode,
        fallback_action=action,
        context_confident=context_confident,
        context_score=context_score,
        hit_count=hit_count,
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
    )
    return signal.reject_code == "NONE"


def _policy_action_universe(*, intent_label: str) -> list[str]:
    if intent_label == "memory_recall":
        return [
            "ROUTE_TO_ASK",
            "ASK_CLARIFYING_QUESTION",
            "OFFER_CAPABILITY_ALTERNATIVES",
            "ANSWER_FROM_MEMORY",
            "ANSWER_GENERAL_KNOWLEDGE",
            "ANSWER_UNKNOWN",
        ]
    if intent_label == "time_query":
        return ["ANSWER_TIME", "ANSWER_UNKNOWN", "ANSWER_GENERAL_KNOWLEDGE"]
    return ["ANSWER_GENERAL_KNOWLEDGE", "ANSWER_UNKNOWN", "OFFER_CAPABILITY_ALTERNATIVES"]


def _policy_alternative_rejection_reason(
    *,
    action: str,
    chosen_action: str,
    context_confident: bool,
    ambiguity_detected: bool,
    hit_count: int,
) -> str:
    if action == chosen_action:
        return "selected"
    if action == "ROUTE_TO_ASK":
        return "ask route rejected: ambiguity or ask-capability requirements were not met"
    if action == "ASK_CLARIFYING_QUESTION":
        return "clarifier rejected: policy preferred either ask route or capability alternatives"
    if action == "OFFER_CAPABILITY_ALTERNATIVES":
        if context_confident and hit_count > 0:
            return "alternatives rejected: confident retrieval context supported direct handling"
        return "alternatives rejected: policy chose a stricter uncertainty handling path"
    if action == "ANSWER_TIME":
        return "time answer rejected: intent was not a time query"
    if action == "ANSWER_UNKNOWN":
        if context_confident and not ambiguity_detected:
            return "unknown fallback rejected: confidence gates passed"
        return "unknown fallback rejected: policy preferred a more specific fallback path"
    if action == "ANSWER_FROM_MEMORY":
        return "memory-grounded path rejected: retrieval confidence or ambiguity policy did not permit direct answer"
    if action == "ANSWER_GENERAL_KNOWLEDGE":
        return "general-knowledge path rejected: retrieval/policy gates required fallback behavior"
    return "alternative rejected by deterministic fallback policy"


def _build_policy_alternatives(
    *,
    intent_label: str,
    chosen_action: str,
    context_confident: bool,
    ambiguity_detected: bool,
    hit_count: int,
) -> list[dict[str, str]]:
    alternatives: list[dict[str, str]] = []
    for action in _policy_action_universe(intent_label=intent_label):
        alternatives.append(
            {
                "action": action,
                "status": "selected" if action == chosen_action else "rejected",
                "reason": _policy_alternative_rejection_reason(
                    action=action,
                    chosen_action=chosen_action,
                    context_confident=context_confident,
                    ambiguity_detected=ambiguity_detected,
                    hit_count=hit_count,
                ),
            }
        )
    return alternatives


def _build_debug_turn_payload(*, state: PipelineState, intent_label: str, hits: list[Document]) -> dict[str, object]:
    fallback_action = str(state.invariant_decisions.get("fallback_action", "NONE"))
    retrieval_branch = str(state.confidence_decision.get("retrieval_branch", "memory_retrieval"))
    answer_mode = str(state.invariant_decisions.get("answer_mode", "dont-know"))
    context_confident = bool(state.confidence_decision.get("context_confident", False))
    ambiguity_detected = bool(state.confidence_decision.get("ambiguity_detected", False))
    answer_contract_valid = bool(state.invariant_decisions.get("answer_contract_valid", True))
    general_knowledge_contract_valid = bool(state.invariant_decisions.get("general_knowledge_contract_valid", True))
    scored_candidates = state.confidence_decision.get("scored_candidates", [])
    top_score = 0.0
    second_score = 0.0
    if isinstance(scored_candidates, list) and scored_candidates:
        top_candidate = scored_candidates[0] if isinstance(scored_candidates[0], dict) else {}
        top_score = float(top_candidate.get("final_score", 0.0) or 0.0)
        if len(scored_candidates) > 1 and isinstance(scored_candidates[1], dict):
            second_score = float(scored_candidates[1].get("final_score", 0.0) or 0.0)
    observed_margin = max(0.0, top_score - second_score)
    top_threshold = float(state.confidence_decision.get("top_final_score_min", 0.0) or 0.0)
    margin_threshold = float(state.confidence_decision.get("min_margin_to_second", 0.0) or 0.0)
    ambiguity_threshold = 0.5
    context_score = min(
        top_score / top_threshold if top_threshold > 0 else 1.0,
        observed_margin / margin_threshold if margin_threshold > 0 else 1.0,
    )

    reject_signal = _derive_reject_signal(
        intent_label=intent_label,
        answer_mode=answer_mode,
        fallback_action=fallback_action,
        context_confident=context_confident,
        context_score=context_score,
        hit_count=len(hits),
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
    )
    doc_ids = [(doc.id or doc.metadata.get("doc_id") or "") for doc in hits[:3]]
    ambiguity_score = 1.0 if not ambiguity_detected else 0.0
    observed_docs: list[dict[str, object]] = []
    for doc in hits[:3]:
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        observed_docs.append(
            {
                "doc_id": str(doc.id or metadata.get("doc_id") or ""),
                "card_type": str(metadata.get("card_type") or metadata.get("type") or ""),
                "ts": str(metadata.get("ts") or ""),
                "window_start": str(metadata.get("window_start") or state.confidence_decision.get("window_start") or ""),
                "window_end": str(metadata.get("window_end") or state.confidence_decision.get("window_end") or ""),
                "source": str(metadata.get("source") or ""),
            }
        )

    score_decomposition: list[dict[str, object]] = []
    if isinstance(scored_candidates, list):
        for candidate in scored_candidates[:3]:
            if not isinstance(candidate, dict):
                continue
            score_decomposition.append(
                {
                    "doc_id": str(candidate.get("doc_id") or ""),
                    "semantic_similarity": float(candidate.get("semantic_similarity", candidate.get("semantic_score", 0.0)) or 0.0),
                    "time_decay_freshness": float(candidate.get("time_decay_freshness", candidate.get("temporal_gaussian_weight", 0.0)) or 0.0),
                    "type_prior": float(candidate.get("type_prior", 0.0) or 0.0),
                    "provenance_citation_factor": float(candidate.get("provenance_citation_factor", 0.0) or 0.0),
                    "final_score": float(candidate.get("final_score", 0.0) or 0.0),
                    "threshold": float(candidate.get("threshold", top_threshold) or 0.0),
                    "passes_threshold": bool(candidate.get("passes_threshold", False)),
                }
            )
    policy_alternatives = _build_policy_alternatives(
        intent_label=intent_label,
        chosen_action=fallback_action,
        context_confident=context_confident,
        ambiguity_detected=ambiguity_detected,
        hit_count=len(hits),
    )
    policy_thresholds = {
        "top_final_score_min": round(top_threshold, 4),
        "min_margin_to_second": round(margin_threshold, 4),
        "ambiguity_threshold": round(ambiguity_threshold, 4),
        "context_score_target": 1.0,
    }
    policy_rationale = state.invariant_decisions.get("answer_policy_rationale", {})
    policy_fallback_reason = ""
    if isinstance(policy_rationale, dict):
        policy_fallback_reason = str(policy_rationale.get("fallback_reason") or "")
    if not policy_fallback_reason or policy_fallback_reason == "decision_object_mapping":
        source_confidence = state.confidence_decision.get("source_confidence")
        policy_fallback_reason = derive_fallback_reason(
            intent=intent_label if intent_label in {"memory_recall", "time_query", "non_memory"} else "non_memory",
            fallback_action=fallback_action if fallback_action in {
                "ANSWER_FROM_MEMORY",
                "ANSWER_TIME",
                "ANSWER_GENERAL_KNOWLEDGE",
                "ANSWER_UNKNOWN",
                "ASK_CLARIFYING_QUESTION",
                "ROUTE_TO_ASK",
                "OFFER_CAPABILITY_ALTERNATIVES",
            } else "ANSWER_UNKNOWN",
            memory_hit=context_confident,
            ambiguity=ambiguity_detected,
            source_confidence=float(source_confidence) if source_confidence is not None else None,
        )

    top_final_score_gate = _gate_metrics(
        passed=top_score >= top_threshold,
        score=top_score,
        threshold=top_threshold,
    )
    margin_gate = _gate_metrics(
        passed=observed_margin >= margin_threshold,
        score=observed_margin,
        threshold=margin_threshold,
    )
    ambiguity_gate = _gate_metrics(
        passed=not ambiguity_detected,
        score=ambiguity_score,
        threshold=ambiguity_threshold,
    )
    context_confident_gate = _gate_metrics(
        passed=context_confident,
        score=context_score,
        threshold=1.0,
    )
    answer_contract_gate = _gate_metrics(
        passed=answer_contract_valid,
        score=1.0 if answer_contract_valid else 0.0,
        threshold=1.0,
    )
    general_knowledge_contract_gate = _gate_metrics(
        passed=general_knowledge_contract_valid,
        score=1.0 if general_knowledge_contract_valid else 0.0,
        threshold=1.0,
    )

    rejected_turn = reject_signal.reject_code != "NONE"
    nearest_failure_gate = _nearest_failure_gate(
        gates={
            "top_final_score_gate": top_final_score_gate,
            "margin_gate": margin_gate,
            "ambiguity_gate": ambiguity_gate,
            "context_confident_gate": context_confident_gate,
            "answer_contract_gate": answer_contract_gate,
            "general_knowledge_contract_gate": general_knowledge_contract_gate,
        }
    )

    nearest_pass_frontier: list[dict[str, float | str]] = []
    if rejected_turn:
        gate_families: tuple[tuple[str, str, dict[str, float | bool]], ...] = (
            ("rerank", "top_final_score_gate", top_final_score_gate),
            ("rerank", "margin_gate", margin_gate),
            ("rerank", "ambiguity_gate", ambiguity_gate),
            ("confidence", "context_confident_gate", context_confident_gate),
            ("contract", "answer_contract_gate", answer_contract_gate),
            ("contract", "general_knowledge_contract_gate", general_knowledge_contract_gate),
        )
        if intent_label == "time_query" or bool(state.confidence_decision.get("anaphora_detected", False)):
            gate_families += (("temporal", "temporal_reference_gate", _gate_metrics(
                passed=reject_signal.reject_code != "TEMPORAL_REFERENCE_UNRESOLVED",
                score=reject_signal.score if reject_signal.partition == "temporal" else 1.0,
                threshold=reject_signal.threshold if reject_signal.partition == "temporal" else 1.0,
            )),)

        closest_by_family: dict[str, dict[str, float | str]] = {}
        for family, gate_name, gate in gate_families:
            if bool(gate.get("passed", False)):
                continue
            entry = _gate_delta_entry(family=family, gate_name=gate_name, gate=gate)
            current = closest_by_family.get(family)
            if current is None:
                closest_by_family[family] = entry
                continue
            if (
                float(entry["delta_to_pass"]) < float(current["delta_to_pass"])
                or (
                    float(entry["delta_to_pass"]) == float(current["delta_to_pass"])
                    and str(entry["gate"]) < str(current["gate"])
                )
            ):
                closest_by_family[family] = entry
        nearest_pass_frontier = [closest_by_family[k] for k in sorted(closest_by_family)]

    top_candidate_pass_thresholds = {
        "top_final_score_min": round(max(top_threshold, top_score), 4),
        "min_margin_to_second": round(max(margin_threshold, observed_margin), 4),
        "context_score_target": 1.0,
    }
    clarify_policy_passes = _counterfactual_policy_passes(
        intent_label=intent_label,
        action="ASK_CLARIFYING_QUESTION",
        context_confident=context_confident,
        context_score=context_score,
        hit_count=len(hits),
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
    )
    route_to_ask_policy_passes = _counterfactual_policy_passes(
        intent_label=intent_label,
        action="ROUTE_TO_ASK",
        context_confident=context_confident,
        context_score=context_score,
        hit_count=len(hits),
        ambiguity_detected=ambiguity_detected,
        answer_contract_valid=answer_contract_valid,
        general_knowledge_contract_valid=general_knowledge_contract_valid,
    )

    return {
        "debug.intent": {
            "resolved": intent_label,
            "classified": state.classified_intent,
            "predicted": str(state.confidence_decision.get("intent_predicted") or state.classified_intent),
            "confidence": float(state.confidence_decision.get("intent_classifier_confidence", 0.0) or 0.0),
            "threshold": float(state.confidence_decision.get("intent_classifier_threshold", 0.0) or 0.0),
            "prior_unresolved": state.prior_unresolved_intent,
        },
        "debug.rewrite": {
            "user_input": state.user_input,
            "rewritten_query": state.rewritten_query,
            "changed": state.user_input.strip() != state.rewritten_query.strip(),
        },
        "debug.retrieval": {
            "branch": retrieval_branch,
            "hit_count": len(hits),
            "retrieved_doc_ids": doc_ids,
            "candidates_considered": float(state.confidence_decision.get("retrieval_candidates_considered", 0.0) or 0.0),
            "returned_top_k": float(state.confidence_decision.get("retrieval_returned_top_k", 0.0) or 0.0),
            "threshold": float(state.confidence_decision.get("retrieval_threshold", 0.0) or 0.0),
            "hygiene": {
                "exclude_doc_ids": state.confidence_decision.get("retrieval_exclude_doc_ids", []),
                "exclude_source_ids": state.confidence_decision.get("retrieval_exclude_source_ids", []),
                "exclude_turn_scoped_ids": state.confidence_decision.get("retrieval_exclude_turn_scoped_ids", []),
                "exclusion_invariant": str(state.confidence_decision.get("retrieval_exclusion_invariant") or ""),
                "rerank_defense_in_depth": True,
            },
        },
        "debug.rerank": {
            "top_final_score": round(top_score, 4),
            "second_final_score": round(second_score, 4),
            "margin": round(observed_margin, 4),
            "top_final_score_gate": top_final_score_gate,
            "margin_gate": margin_gate,
            "ambiguity_gate": ambiguity_gate,
        },
        "debug.confidence": {
            "context_confident_gate": context_confident_gate,
        },
        "debug.observation": {
            "candidate_evidence": {
                "retrieved_docs": observed_docs,
                "score_components": {
                    "top_final_score": round(top_score, 4),
                    "second_final_score": round(second_score, 4),
                    "observed_margin": round(observed_margin, 4),
                    "top_gate_threshold": round(top_threshold, 4),
                    "margin_gate_threshold": round(margin_threshold, 4),
                    "context_score": round(context_score, 4),
                    "candidate_score_decomposition": score_decomposition,
                },
                "time_windows": {
                    "query_time_window": str(state.confidence_decision.get("time_window") or ""),
                    "window_start": str(state.confidence_decision.get("window_start") or ""),
                    "window_end": str(state.confidence_decision.get("window_end") or ""),
                    "last_user_message_ts": state.last_user_message_ts,
                },
                "ambiguity_state": {
                    "ambiguity_detected": ambiguity_detected,
                    "ambiguous_candidates": state.confidence_decision.get("ambiguous_candidates", []),
                    "anaphora_detected": bool(state.confidence_decision.get("anaphora_detected", False)),
                    "candidate_anchors": state.confidence_decision.get("anchor_candidates", []),
                    "selected_anchor_doc_id": str(state.confidence_decision.get("selected_anchor_doc_id") or ""),
                    "selected_anchor_ts": str(state.confidence_decision.get("selected_anchor_ts") or ""),
                    "computed_delta_raw_seconds": state.confidence_decision.get("computed_delta_raw_seconds"),
                    "computed_delta_humanized": str(state.confidence_decision.get("computed_delta_humanized") or ""),
                },
            }
        },
        "debug.contract": {
            "answer_contract_gate": answer_contract_gate,
            "general_knowledge_contract_gate": general_knowledge_contract_gate,
        },
        "debug.policy": {
            "chosen_action": fallback_action,
            "considered_alternatives": policy_alternatives,
            "decision_rationale": {
                "reject_signal": {
                    "reject_code": reject_signal.reject_code,
                    "partition": reject_signal.partition,
                    "reason": reject_signal.reason,
                    "score": reject_signal.score,
                    "threshold": reject_signal.threshold,
                    "margin": reject_signal.margin,
                },
                "thresholds": policy_thresholds,
                "answer_policy_inputs": policy_rationale if isinstance(policy_rationale, dict) else {},
            },
            "rejected_turn": rejected_turn,
            "nearest_failure_gate": nearest_failure_gate,
            "counterfactuals": {
                "top_candidate_pass_thresholds": top_candidate_pass_thresholds,
                "nearest_pass_frontier": nearest_pass_frontier,
                "dominant_contributors": _dominant_score_contributors(score_decomposition=score_decomposition),
                "alternate_routing_policy_checks": {
                    "ask_clarifying_question_passes": clarify_policy_passes,
                    "route_to_ask_passes": route_to_ask_policy_passes,
                },
            },
            "answer_mode": answer_mode,
            "fallback_action": fallback_action,
            "reject_code": reject_signal.reject_code,
            "partition": reject_signal.partition,
            "score": reject_signal.score,
            "threshold": reject_signal.threshold,
            "margin": reject_signal.margin,
            "reason": reject_signal.reason,
            "blocker_reason": reject_signal.reason,
            "fallback_reason": policy_fallback_reason,
        },
    }


def _format_debug_turn_trace_payload(*, payload: dict[str, object], verbose: bool = False) -> str:

    if verbose:
        return "[debug] " + json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def _metric_fragment(label: str, gate: dict[str, object]) -> str:
        score = float(gate.get("score", 0.0) or 0.0)
        threshold = float(gate.get("threshold", 0.0) or 0.0)
        return f"{label}={score:.3f}>{threshold:.3f}" if bool(gate.get("passed", False)) else f"{label}={score:.3f}<{threshold:.3f}"

    rerank = payload["debug.rerank"]
    confidence = payload["debug.confidence"]
    policy = payload["debug.policy"]
    top1_metric = _metric_fragment("top1", rerank["top_final_score_gate"])
    context_metric = _metric_fragment("context_conf", confidence["context_confident_gate"])
    margin_metric = _metric_fragment("margin", rerank["margin_gate"])

    nearest_failure_fragment = ""
    nearest_failure_gate = policy.get("nearest_failure_gate")
    if bool(policy.get("rejected_turn", False)) and isinstance(nearest_failure_gate, dict):
        gate_name = str(nearest_failure_gate.get("gate", ""))
        gate_margin = float(nearest_failure_gate.get("margin_to_pass", 0.0) or 0.0)
        nearest_failure_fragment = f" nearest_failure={gate_name}:+{gate_margin:.3f};"

    retrieved_doc_ids = payload["debug.retrieval"]["retrieved_doc_ids"]
    retrieved_doc_ids_compact = retrieved_doc_ids[:3] if isinstance(retrieved_doc_ids, list) else retrieved_doc_ids

    return (
        "[debug] "
        f"intent={payload['debug.intent']['resolved']}; "
        f"answer_mode={payload['debug.policy']['answer_mode']}; "
        f"fallback_action={payload['debug.policy']['fallback_action']}; "
        f"retrieval_branch={payload['debug.retrieval']['branch']}; "
        f"context_confident={payload['debug.confidence']['context_confident_gate']['passed']}; "
        f"ambiguity_detected={not payload['debug.rerank']['ambiguity_gate']['passed']}; "
        f"{top1_metric}; "
        f"{context_metric}; "
        f"{margin_metric};"
        f"{nearest_failure_fragment} "
        f"rewritten_query={payload['debug.rewrite']['rewritten_query']!r}; "
        f"retrieved_doc_ids={retrieved_doc_ids_compact}; "
        f"reject_code={payload['debug.policy']['reject_code']}; "
        f"partition={payload['debug.policy']['partition']}; "
        f"blocker_reason={payload['debug.policy']['blocker_reason']}."
    )


def _format_debug_turn_trace(*, state: PipelineState, intent_label: str, hits: list[Document], verbose: bool = False) -> str:
    payload = _build_debug_turn_payload(state=state, intent_label=intent_label, hits=hits)
    return _format_debug_turn_trace_payload(payload=payload, verbose=verbose)


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


def answer_assemble(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    answer_routing: AnswerRoutingDecision,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> AnswerAssembleResult:
    runtime_capability_status = runtime_capability_status or RuntimeCapabilityStatus(
        ollama_available=True,
        ha_available=False,
        effective_mode="cli",
        requested_mode="cli",
        daemon_mode=False,
        fallback_reason=None,
        memory_backend="in_memory",
        debug_enabled=False,
        debug_verbose=False,
        text_clarification_available=True,
        satellite_ask_available=False,
    )

    fallback_action = answer_routing.fallback_action
    clarification_allowed = answer_routing.clarification_allowed
    resolved_intent = IntentType(state.resolved_intent or IntentType.KNOWLEDGE_QUESTION.value)
    intent_class = _intent_class_for_policy(resolved_intent)
    social_or_non_knowledge_intent = _is_social_or_non_knowledge_intent(resolved_intent)
    satellite_action_request = is_satellite_action_request(state.user_input)

    def _fallback_answer_for_action(action: str, *, intent_class: str) -> str:
        if action == "ROUTE_TO_ASK":
            return ROUTE_TO_ASK_ANSWER
        if action == "ASK_CLARIFYING_QUESTION":
            if intent_class == "memory_recall":
                return build_partial_memory_clarifier(hits)
            return ASSIST_ALTERNATIVES_ANSWER
        if action == "ANSWER_UNKNOWN":
            return NON_KNOWLEDGE_UNCERTAINTY_ANSWER
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
        return AnswerAssembleResult(
            draft_answer="",
            final_answer=final_answer,
            fallback_action="ANSWER_GENERAL_KNOWLEDGE",
            intent_class=intent_class,
            social_or_non_knowledge_intent=social_or_non_knowledge_intent,
            answer_policy_rationale={"capability_help_short_circuit": True},
            capability_help_short_circuit=True,
        )

    context_str = render_context(hits)
    packed_history = pack_chat_history(list(chat_history))
    history_str = render_packed_history(packed_history)
    planning_descriptor = planning_pathway_for_intent(resolved_intent, extract_intent_facets(state.user_input))
    response_plan_block = render_response_plan_block(build_response_plan(
        descriptor=planning_descriptor,
        user_input=state.user_input,
    ))
    msgs = ANSWER_PROMPT.format_messages(
        input=state.user_input,
        chat_history=history_str,
        context=context_str,
        response_plan=response_plan_block,
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
                draft_answer = final_answer
            elif social_or_non_knowledge_intent and fallback_action == "ANSWER_GENERAL_KNOWLEDGE":
                final_answer = draft_answer
            else:
                final_answer = _clarifier_or_policy_alternative()

    return AnswerAssembleResult(
        draft_answer=draft_answer,
        final_answer=final_answer,
        fallback_action=fallback_action,
        intent_class=intent_class,
        social_or_non_knowledge_intent=social_or_non_knowledge_intent,
        answer_policy_rationale=dict(answer_routing.rationale),
        capability_help_short_circuit=False,
    )


def answer_validate(
    state: PipelineState,
    *,
    assembled: AnswerAssembleResult,
    hits: list[Document],
    chat_history: deque[ChatMsg],
) -> AnswerValidateResult:
    packed_history = pack_chat_history(list(chat_history))
    provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
        final_answer=assembled.final_answer,
        hits=hits,
        chat_history=chat_history,
        packed_history=packed_history,
    )

    if assembled.capability_help_short_circuit:
        alignment_decision = evaluate_alignment_decision(
            user_input=state.user_input,
            draft_answer="",
            final_answer=assembled.final_answer,
            confidence_decision=state.confidence_decision,
            claims=claims,
            provenance_types=provenance_types,
            basis_statement=basis_statement,
        )
        return AnswerValidateResult(
            final_answer=assembled.final_answer,
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

    general_knowledge_contract_valid = (
        True
        if assembled.fallback_action == "ANSWER_TIME"
        else validate_general_knowledge_contract(
            assembled.final_answer,
            provenance_types=provenance_types,
            confidence_decision=state.confidence_decision,
        )
    )
    if assembled.final_answer != FALLBACK_ANSWER and not general_knowledge_contract_valid and not (
        assembled.social_or_non_knowledge_intent
        and bool(assembled.draft_answer)
        and assembled.final_answer == assembled.draft_answer
    ):
        safe_final = NON_KNOWLEDGE_UNCERTAINTY_ANSWER
        provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
            final_answer=safe_final,
            hits=hits,
            chat_history=chat_history,
            packed_history=packed_history,
        )
        assembled = replace(assembled, final_answer=safe_final)

    alignment_decision = evaluate_alignment_decision(
        user_input=state.user_input,
        draft_answer=assembled.draft_answer,
        final_answer=assembled.final_answer,
        confidence_decision=state.confidence_decision,
        claims=claims,
        provenance_types=provenance_types,
        basis_statement=basis_statement,
    )

    answer_mode_decision = resolve_answer_mode(
        final_answer=assembled.final_answer,
        fallback_action=assembled.fallback_action,
        social_or_non_knowledge_intent=assembled.social_or_non_knowledge_intent,
        is_clarification_answer=is_clarification_answer(assembled.final_answer),
        is_deny_answer=assembled.final_answer == DENY_ANSWER,
        is_assist_alternatives_answer=assembled.final_answer == ASSIST_ALTERNATIVES_ANSWER,
        is_fallback_answer=assembled.final_answer == FALLBACK_ANSWER,
        is_non_knowledge_uncertainty_answer=assembled.final_answer == NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    )
    answer_mode = answer_mode_decision.answer_mode
    ambiguity_policy_allows_non_memory_clarify = bool(state.confidence_decision.get("allow_non_memory_clarify", False))
    if answer_mode == "clarify" and assembled.intent_class != "memory_recall" and not ambiguity_policy_allows_non_memory_clarify:
        raise AssertionError(
            "Non-memory intent produced answer_mode=clarify without explicit ambiguity policy override."
        )

    invariant_decisions = {
        "response_contains_claims": bool(claims),
        "raw_claim_like_text_detected": raw_claim_like_text_detected(assembled.draft_answer),
        "has_required_memory_citation": has_required_memory_citation(assembled.draft_answer),
        "answer_contract_valid": validate_answer_contract(assembled.draft_answer),
        "general_knowledge_contract_valid": general_knowledge_contract_valid,
        "has_general_knowledge_marker": has_general_knowledge_marker(assembled.final_answer),
        "general_knowledge_confidence_gate_passed": passes_general_knowledge_confidence_gate(state.confidence_decision),
        "answer_mode": answer_mode,
        "fallback_action": assembled.fallback_action,
        "answer_policy_rationale": assembled.answer_policy_rationale,
        "answer_mode_rationale": answer_mode_decision.rationale,
        "provenance_recorded": bool(not is_non_trivial_answer(assembled.final_answer) or provenance_types),
    }
    return AnswerValidateResult(
        final_answer=assembled.final_answer,
        claims=claims,
        provenance_types=provenance_types,
        used_memory_refs=used_memory_refs,
        used_source_evidence_refs=used_source_evidence_refs,
        source_evidence_attribution=source_evidence_attribution,
        basis_statement=basis_statement,
        invariant_decisions=invariant_decisions,
        alignment_decision=alignment_decision,
    )


def answer_render(validated: AnswerValidateResult) -> AnswerRenderResult:
    return AnswerRenderResult(final_answer=validated.final_answer)


def answer_commit(
    state: PipelineState,
    *,
    assembled: AnswerAssembleResult,
    validated: AnswerValidateResult,
    rendered: AnswerRenderResult,
) -> PipelineState:
    return replace(
        state,
        draft_answer=assembled.draft_answer,
        final_answer=rendered.final_answer,
        claims=validated.claims,
        provenance_types=validated.provenance_types,
        used_memory_refs=validated.used_memory_refs,
        used_source_evidence_refs=validated.used_source_evidence_refs,
        source_evidence_attribution=validated.source_evidence_attribution,
        basis_statement=validated.basis_statement,
        invariant_decisions=validated.invariant_decisions,
        alignment_decision=validated.alignment_decision,
    )


def _answer_routing_from_decision_object(
    decision: DecisionObject,
    *,
    capability_status: CapabilityStatus,
) -> AnswerRoutingDecision:
    match decision.decision_class:
        case DecisionClass.ANSWER_FROM_MEMORY:
            fallback_action = "ANSWER_FROM_MEMORY"
            token = "LLM_DRAFT"
            clarification_allowed = False
        case DecisionClass.ASK_FOR_CLARIFICATION:
            fallback_action = "ASK_CLARIFYING_QUESTION"
            token = "PARTIAL_MEMORY_CLARIFIER"
            clarification_allowed = True
        case DecisionClass.CONTINUE_REPAIR_RECONSTRUCTION:
            fallback_action = "ASK_CLARIFYING_QUESTION"
            token = "PARTIAL_MEMORY_CLARIFIER"
            clarification_allowed = True
        case DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED:
            fallback_action = "ANSWER_GENERAL_KNOWLEDGE"
            token = "LLM_DRAFT"
            clarification_allowed = False

    return AnswerRoutingDecision(
        fallback_action=fallback_action,
        canonical_response_token=token,
        route_to_ask_expected=False,
        clarification_allowed=clarification_allowed,
        rationale={
            "authority": "decision_object",
            "decision_class": decision.decision_class.value,
            "decision_rationale": decision.rationale,
            "decision_reasoning": dict(decision.reasoning),
            "capability_status": capability_status,
            "fallback_reason": "decision_object_mapping",
            "considered_alternatives": [
                {
                    "action": fallback_action,
                    "status": "selected",
                    "reason": "selected by canonical decision_object authority",
                }
            ],
        },
    )


def _answer_assemble_stage(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None = None,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> AnswerAssembleResult:
    resolved_intent = IntentType(state.resolved_intent or classify_intent(state.user_input).value)
    if not state.resolved_intent:
        state = replace(state, resolved_intent=resolved_intent.value)

    if selected_decision is not None:
        answer_routing = _answer_routing_from_decision_object(
            selected_decision,
            capability_status=capability_status,
        )
    else:
        answer_routing = resolve_answer_routing(
            AnswerPolicyInput(
                intent=_intent_class_for_policy(resolved_intent),
                confidence_decision=state.confidence_decision,
                capability_status=capability_status,
                source_confidence=(
                    float(state.confidence_decision["source_confidence"])
                    if "source_confidence" in state.confidence_decision
                    else None
                ),
            ),
            fallback_decider=decide_fallback_action,
        )
    return answer_assemble(
        llm,
        state,
        chat_history=chat_history,
        hits=hits,
        capability_status=capability_status,
        answer_routing=answer_routing,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        timezone=timezone,
    )


def _answer_validate_stage(
    state: PipelineState,
    *,
    assembled: AnswerAssembleResult,
    hits: list[Document],
    chat_history: deque[ChatMsg],
) -> AnswerValidateResult:
    return answer_validate(
        state,
        assembled=assembled,
        hits=hits,
        chat_history=chat_history,
    )


def _answer_render_stage(validated: AnswerValidateResult) -> AnswerRenderResult:
    return answer_render(validated)


def _answer_commit_stage(
    state: PipelineState,
    *,
    assembled: AnswerAssembleResult,
    validated: AnswerValidateResult,
    rendered: AnswerRenderResult,
) -> PipelineState:
    return answer_commit(
        state,
        assembled=assembled,
        validated=validated,
        rendered=rendered,
    )


def stage_answer(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None = None,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    timezone: str = "Europe/Helsinki",
) -> PipelineState:
    assembled = _answer_assemble_stage(
        llm,
        state,
        chat_history=chat_history,
        hits=hits,
        capability_status=capability_status,
        selected_decision=selected_decision,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        timezone=timezone,
    )
    validated = _answer_validate_stage(
        state,
        assembled=assembled,
        hits=hits,
        chat_history=chat_history,
    )
    rendered = _answer_render_stage(validated)
    return _answer_commit_stage(
        state,
        assembled=assembled,
        validated=validated,
        rendered=rendered,
    )




def answer_commit_persistence(
    *,
    llm: ChatOllama,
    store: MemoryStore,
    state: PipelineState,
    io_channel: str,
    clock: Clock,
) -> None:
    a_ts = clock.now().isoformat()
    a_id = str(uuid.uuid4())
    a_card = make_utterance_card(
        ts_iso=a_ts,
        speaker="assistant",
        text=state.final_answer,
        doc_id=a_id,
        channel=io_channel,
    )
    commit_segment = derive_segment_descriptor(utterance=state.user_input, has_dialogue_state=False)
    store_doc(
        store,
        doc_id=a_id,
        content=a_card,
        metadata=apply_persistence_metadata(
            metadata={
                "ts": a_ts,
                "type": "assistant_utterance",
                "speaker": "assistant",
                "channel": io_channel,
                "doc_id": a_id,
                "raw": state.final_answer,
            },
            stratum=MemoryStratum.EPISODIC,
            segment=commit_segment,
            member_doc_id=a_id,
        ),
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
        metadata=apply_persistence_metadata(
            metadata={
                "ts": a_ref_ts,
                "type": "reflection",
                "about": "assistant",
                "source_doc_id": a_id,
                "doc_id": a_ref_id,
            },
            stratum=MemoryStratum.SEMANTIC,
            segment=commit_segment,
            member_doc_id=a_ref_id,
        ),
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
            "Use ONLY the provided memory context and recent chat.\nHeuristic packed-history hints are advisory context only, never hard evidence.\n"
            "If memory is empty or low-confidence, ask one targeted clarifying question or offer at least two capability-based alternatives.\n"
            "If memory is partial or ambiguous, provide a short user-facing summary and one bridging clarifier.\n"
            "Keep the exact phrase \"I don't know from memory.\" only for explicit deny/safety-policy cases.\n"
            "For any factual claim, include at least one cited memory with both doc_id and ts.\n\n"
            "Recent chat:\n{chat_history}\n\n"
            "Memory context:\n{context}\n\n"
            "Deterministic response plan:\n{response_plan}\n",
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
    for idx, d in enumerate(docs, start=1):
        snippet = re.sub(r"\s+", " ", (d.page_content or "").strip())
        if not snippet:
            continue
        doc_id = str(d.metadata.get("doc_id") or d.id or "")
        ts = str(d.metadata.get("ts") or "")
        doc_type = str(d.metadata.get("type") or "")
        block = (
            f"[doc_{idx}]\n"
            f"doc_id: {doc_id}\n"
            f"ts: {ts}\n"
            f"type: {doc_type}\n"
            f"content: {snippet}\n"
            "---\n"
        )
        if total + len(block) > limit_chars:
            break
        chunks.append(block)
        total += len(block)
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
    return sorted(dict.fromkeys(refs))


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
    deduped_refs = sorted(dict.fromkeys(refs))
    deduped_attributions = list({json.dumps(item, sort_keys=True): item for item in attributions}.values())
    deduped_attributions.sort(key=lambda item: (item.get("doc_id", ""), item.get("source_uri", ""), item.get("retrieved_at", "")))
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
            else "Answer synthesized from recent chat history (advisory signals only)."
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
        NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
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



def _run_canonical_turn_pipeline(
    *,
    llm: ChatOllama,
    store: MemoryStore,
    state: PipelineState,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    turn_id: str,
    near_tie_delta: float,
    chat_history: deque[ChatMsg],
    capability_status: CapabilityStatus,
    capability_snapshot: CapabilitySnapshot,
    clock: Clock,
    io_channel: str = "cli",
) -> tuple[PipelineState, list[Document]]:
    context = CanonicalTurnContext(
        state=state,
        artifacts={
            "utterance": utterance,
            "policy_decision": None,
            "turn_id": turn_id,
            "docs_and_scores": [],
            "hits": [],
            "ambiguity_score": 0.0,
        },
    )

    def _observe_turn(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        _validate_and_log_transition(validate_observe_pre(ctx.state))
        observation = observe_turn(
            ctx.state,
            turn_id=ctx.artifacts["turn_id"],
            observed_at=clock.now().isoformat(),
            speaker="user",
            channel=io_channel,
        )
        ctx.artifacts["turn_observation"] = observation
        ctx.state = observe_stage(ctx.state)
        _validate_and_log_transition(validate_observe_post(ctx.state))
        append_pipeline_snapshot("observe", ctx.state)
        return ctx

    def _encode_candidates(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        _validate_and_log_transition(validate_encode_pre(ctx.state))
        rewritten_state = encode_stage(llm, ctx.state)
        _validate_and_log_transition(validate_encode_post(rewritten_state))
        rewritten_query = rewritten_state.rewritten_query
        append_session_log("query_rewrite_output", {"utterance": utterance, "query": rewritten_query})

        encoded = encode_turn_candidates(
            ctx.state,
            observation=ctx.artifacts["turn_observation"],
            rewritten_query=rewritten_query,
        )
        ctx.artifacts["encoded_candidates"] = encoded
        ctx.state = replace(
            ctx.state,
            rewritten_query=encoded.rewritten_query,
            candidate_facts=encoded.as_artifact_payload(),
        )
        append_pipeline_snapshot("rewrite", ctx.state)
        return ctx

    def _stabilize_pre_route(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        planning_descriptor = planning_pathway_for_intent(IntentType(state.classified_intent), extract_intent_facets(utterance))
        response_plan = build_response_plan(descriptor=planning_descriptor, user_input=utterance)
        reflection_yaml = generate_reflection_yaml(llm, speaker="user", text=utterance)
        prior_candidate_facts = ctx.state.candidate_facts if isinstance(ctx.state.candidate_facts, dict) else {}
        prior_segment_id = str(prior_candidate_facts.get("segment_id") or "")
        prior_segment_type = str(prior_candidate_facts.get("segment_type") or "")
        prior_segment = None
        if prior_segment_id and prior_segment_type:
            continuity_probe = derive_segment_descriptor(
                utterance=utterance,
                has_dialogue_state=bool(ctx.artifacts["encoded_candidates"].dialogue_state),
            )
            try:
                prior_segment = SegmentDescriptor(
                    segment_type=SegmentType(prior_segment_type),
                    segment_id=prior_segment_id,
                    continuity_key=continuity_probe.continuity_key,
                )
            except ValueError:
                prior_segment = None
        segment = derive_segment_descriptor(
            utterance=utterance,
            prior_descriptor=prior_segment,
            has_dialogue_state=bool(ctx.artifacts["encoded_candidates"].dialogue_state),
        )
        ctx.state, stabilized = stabilize_pre_route(
            store=store,
            state=ctx.state,
            observation=ctx.artifacts["turn_observation"],
            encoded=ctx.artifacts["encoded_candidates"],
            response_plan=plan_to_dict(response_plan),
            reflection_yaml=reflection_yaml,
            segment=segment,
            store_doc_fn=store_doc,
        )
        ctx.artifacts["stabilized_turn_state"] = stabilized
        append_pipeline_snapshot("stabilize", ctx.state)
        return ctx

    def _context_resolve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        stabilized: StabilizedTurnState = ctx.artifacts["stabilized_turn_state"]
        stabilized_utterance = next((fact.value for fact in stabilized.candidate_facts if fact.key == "utterance_raw"), "")
        context_resolution = resolve_context(
            utterance=stabilized_utterance or utterance,
            prior_pipeline_state=prior_pipeline_state,
        )
        continuity_evidence = continuity_evidence_from_prior_state(prior_pipeline_state)
        ctx.artifacts["resolved_context"] = context_resolution
        ctx.artifacts["retrieval_continuity_evidence"] = continuity_evidence
        ctx.state = replace(
            ctx.state,
            resolved_context={
                "history_anchors": list(context_resolution.history_anchors),
                "ambiguity_flags": list(context_resolution.ambiguity_flags),
                "continuity_posture": context_resolution.continuity_posture.value,
                "prior_intent": context_resolution.prior_intent.value if context_resolution.prior_intent is not None else "",
            },
            confidence_decision={
                **ctx.state.confidence_decision,
                "retrieval_continuity_evidence": list(continuity_evidence),
            },
        )
        append_pipeline_snapshot("context", ctx.state)
        return ctx

    def _intent_resolve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        stabilized: StabilizedTurnState = ctx.artifacts["stabilized_turn_state"]
        stabilized_utterance = next((fact.value for fact in stabilized.candidate_facts if fact.key == "utterance_raw"), "")
        context_resolution = ctx.artifacts["resolved_context"]
        intent_resolution = resolve_intent(
            resolution_input=IntentResolutionInput(
                stabilized_turn_state=stabilized,
                context=context_resolution,
                fallback_utterance=utterance,
            )
        )
        recall_query = stabilized_utterance or utterance
        continuity_evidence = tuple(ctx.artifacts.get("retrieval_continuity_evidence", ()))
        context_history_anchors = tuple(getattr(context_resolution, "history_anchors", ()))
        guard_forced_memory_retrieval = _should_force_memory_retrieval_for_identity_recall(
            utterance=recall_query,
            prior_state=prior_pipeline_state,
            continuity_evidence=continuity_evidence,
            context_history_anchors=context_history_anchors,
        )
        retrieval_routing = decide_retrieval_routing(
            utterance=recall_query,
            intent=intent_resolution.resolved_intent,
            guard_forced_memory_retrieval=guard_forced_memory_retrieval,
        )
        ctx.artifacts["retrieval_requirement"] = {
            "requires_retrieval": retrieval_routing.requires_retrieval,
            "reason": retrieval_routing.reason,
            "retrieval_branch": retrieval_routing.retrieval_branch,
        }
        ctx.artifacts["guard_forced_memory_retrieval"] = guard_forced_memory_retrieval
        ctx.state = replace(
            ctx.state,
            classified_intent=intent_resolution.classified_intent.value,
            resolved_intent=intent_resolution.resolved_intent.value,
            policy_decision={
                "policy": "intent_retrieval_requirement",
                "decision": "retrieval_requirement_only",
                "intent_classified": intent_resolution.classified_intent.value,
                "intent_resolved": intent_resolution.resolved_intent.value,
                "requires_retrieval": retrieval_routing.requires_retrieval,
                "reason": retrieval_routing.reason,
                "retrieval_branch": retrieval_routing.retrieval_branch,
            },
        )
        append_session_log(
            "retrieval_branch_selected",
            _intent_telemetry_payload(
                state=ctx.state,
                utterance=utterance,
                extra={
                    "retrieval_branch": retrieval_routing.retrieval_branch,
                    "retrieval_requirement": dict(ctx.artifacts["retrieval_requirement"]),
                    "stabilized_turn_id": stabilized.turn_id,
                    "stabilized_candidate_fact_count": len(stabilized.candidate_facts),
                    "stabilized_dialogue_state_count": len(stabilized.candidate_dialogue_state),
                    "context_continuity_posture": context_resolution.continuity_posture.value,
                    "context_history_anchors": list(context_resolution.history_anchors),
                    "guard_forced_memory_retrieval": bool(ctx.artifacts.get("guard_forced_memory_retrieval", False)),
                },
            ),
        )
        append_pipeline_snapshot("intent", ctx.state)
        return ctx

    def _retrieve_evidence(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        retrieval_requirement = ctx.artifacts.get("retrieval_requirement") or {}
        if bool(retrieval_requirement.get("requires_retrieval", False)):
            _validate_and_log_transition(validate_retrieve_pre(ctx.state))
            same_turn_exclusion_doc_ids = set(ctx.state.same_turn_exclusion.get("excluded_doc_ids", []))
            retrieval_exclude_doc_ids = same_turn_exclusion_doc_ids
            retrieval_exclude_source_ids = {
                ctx.artifacts["stabilized_turn_state"].utterance_doc_id,
            }
            retrieval_exclude_turn_scoped_ids = same_turn_exclusion_doc_ids
            segment_constraints = ctx.state.candidate_facts.get("retrieval_constraints", {})
            retrieval_segment_ids = set(segment_constraints.get("segment_ids", []))
            retrieval_segment_types = set(segment_constraints.get("segment_types", []))
            ctx.state, docs_and_scores = stage_retrieve(
                store,
                ctx.state,
                exclude_doc_ids=retrieval_exclude_doc_ids,
                exclude_source_ids=retrieval_exclude_source_ids,
                exclude_turn_scoped_ids=retrieval_exclude_turn_scoped_ids,
                segment_ids=retrieval_segment_ids,
                segment_types=retrieval_segment_types,
            )
            _validate_and_log_transition(validate_retrieve_post(ctx.state))
            ctx.artifacts["docs_and_scores"] = docs_and_scores
            considered = int(ctx.state.confidence_decision.get("retrieval_candidates_considered", len(docs_and_scores)) or 0)
            prerank_bundle = build_evidence_bundle_from_docs_and_scores(docs_and_scores)
            ctx.artifacts["pre_rerank_evidence_bundle"] = prerank_bundle
            ctx.artifacts["retrieval_result"] = retrieval_result(
                evidence_bundle=prerank_bundle,
                retrieval_candidates_considered=considered,
                hit_count=0,
            )
            append_session_log(
                "retrieval_candidates",
                {
                    "query": ctx.state.rewritten_query,
                    "candidate_count": len(docs_and_scores),
                    "top_candidates": [
                        {"doc_id": (doc.id or doc.metadata.get("doc_id") or ""), "score": float(score)}
                        for doc, score in docs_and_scores[:4]
                    ],
                    "hygiene": {
                        "exclude_doc_ids": sorted(retrieval_exclude_doc_ids),
                        "exclude_source_ids": sorted(retrieval_exclude_source_ids),
                        "exclude_turn_scoped_ids": sorted(retrieval_exclude_turn_scoped_ids),
                        "primary_invariant": "retrieve_stage_exclusion",
                        "rerank_defense_in_depth": True,
                        "segment_ids": sorted(retrieval_segment_ids),
                        "segment_types": sorted(retrieval_segment_types),
                    },
                },
            )
        else:
            ctx.artifacts["pre_rerank_evidence_bundle"] = EvidenceBundle()
            ctx.artifacts["retrieval_result"] = retrieval_result(
                evidence_bundle=EvidenceBundle(),
                retrieval_candidates_considered=0,
                hit_count=0,
            )
            append_session_log(
                "retrieval_candidates",
                {"query": ctx.state.rewritten_query, "candidate_count": 0, "top_candidates": [], "skipped": True},
            )
        append_pipeline_snapshot("retrieve", ctx.state)
        return ctx

    def _policy_decide(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        resolved_intent = IntentType(ctx.state.resolved_intent)
        retrieval_requirement = ctx.artifacts.get("retrieval_requirement") or {}
        requires_retrieval = bool(retrieval_requirement.get("requires_retrieval", False))
        if requires_retrieval:
            _validate_and_log_transition(validate_rerank_pre(ctx.state))
            stabilized: StabilizedTurnState = ctx.artifacts["stabilized_turn_state"]
            ctx.state, hits = stage_rerank(
                ctx.state,
                ctx.artifacts["docs_and_scores"],
                utterance=utterance,
                user_doc_id=stabilized.utterance_doc_id,
                user_reflection_doc_id=stabilized.reflection_doc_id,
                near_tie_delta=near_tie_delta,
                clock=clock,
            )
            _validate_and_log_transition(validate_rerank_post(ctx.state))
            ctx.artifacts["hits"] = hits
            considered = int(ctx.state.confidence_decision.get("retrieval_candidates_considered", len(ctx.artifacts["docs_and_scores"])) or 0)
            policy_decision = decide_policy(
                utterance=utterance,
                intent=resolved_intent,
                retrieval_candidates_considered=considered,
                hit_count=len(hits),
                guard_forced_memory_retrieval=bool(ctx.artifacts.get("guard_forced_memory_retrieval", False)),
            )
            ctx.artifacts["policy_decision"] = policy_decision
            finalized_bundle = build_evidence_bundle_from_hits(hits)
            ctx.artifacts["retrieval_result"] = retrieval_result(
                evidence_bundle=finalized_bundle,
                retrieval_candidates_considered=considered,
                hit_count=len(hits),
            )
            ctx.artifacts["decision_object"] = decide_from_evidence(
                intent=resolved_intent,
                retrieval=ctx.artifacts["retrieval_result"],
            )
        else:
            policy_decision = decide_policy(
                utterance=utterance,
                intent=resolved_intent,
                guard_forced_memory_retrieval=bool(ctx.artifacts.get("guard_forced_memory_retrieval", False)),
            )
            ctx.artifacts["policy_decision"] = policy_decision
            ctx.artifacts["decision_object"] = decide_from_evidence(
                intent=resolved_intent,
                retrieval=ctx.artifacts["retrieval_result"],
            )
            minimal_confidence = _minimal_confidence_decision_for_direct_answer(
                branch=ctx.artifacts["policy_decision"].retrieval_branch,
                base_confidence_decision=ctx.state.confidence_decision,
            )
            ctx.state = replace(
                ctx.state,
                retrieval_candidates=[],
                reranked_hits=[],
                confidence_decision=minimal_confidence,
            )
            append_session_log(
                "rerank_skipped",
                _intent_telemetry_payload(
                    state=ctx.state,
                    utterance=utterance,
                    extra={
                        "reason": "intent_routed_to_direct_answer",
                        "retrieval_branch": ctx.artifacts["policy_decision"].retrieval_branch,
                    },
                ),
            )
        append_pipeline_snapshot("rerank", ctx.state)
        return ctx

    def _answer_assemble(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        _validate_and_log_transition(validate_answer_pre(ctx.state))
        ctx.artifacts["assembled_answer"] = _answer_assemble_stage(
            llm,
            ctx.state,
            chat_history=chat_history,
            hits=ctx.artifacts["hits"],
            capability_status=capability_status,
            selected_decision=ctx.artifacts["decision_object"],
            runtime_capability_status=capability_snapshot.runtime_capability_status,
            clock=clock,
        )
        decision_object = ctx.artifacts["decision_object"]
        retrieval_result_obj = ctx.artifacts["retrieval_result"]
        ctx.artifacts["answer_assembly_contract"] = assemble_answer_contract(
            decision=decision_object,
            evidence_bundle=retrieval_result_obj.evidence_bundle,
        )
        append_pipeline_snapshot("answer.assemble", ctx.state)
        return ctx

    def _answer_validate(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["validated_answer"] = _answer_validate_stage(
            ctx.state,
            assembled=ctx.artifacts["assembled_answer"],
            hits=ctx.artifacts["hits"],
            chat_history=chat_history,
        )
        ctx.artifacts["answer_validation_contract"] = validate_answer_assembly_boundary(
            ctx.artifacts["answer_assembly_contract"]
        )
        if not ctx.artifacts["answer_validation_contract"].passed:
            raise RuntimeError("answer assembly contract validation failed before render/commit")
        append_pipeline_snapshot("answer.validate", ctx.state)
        return ctx

    def _answer_render(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["rendered_answer"] = _answer_render_stage(ctx.artifacts["validated_answer"])
        ctx.artifacts["answer_render_contract"] = render_answer(
            assembly=ctx.artifacts["answer_assembly_contract"],
            validation=ctx.artifacts["answer_validation_contract"],
            preferred_text=ctx.artifacts["rendered_answer"].final_answer,
        )
        append_pipeline_snapshot("answer.render", ctx.state)
        return ctx

    def _answer_commit(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.state = _answer_commit_stage(
            ctx.state,
            assembled=ctx.artifacts["assembled_answer"],
            validated=ctx.artifacts["validated_answer"],
            rendered=ctx.artifacts["rendered_answer"],
        )
        _validate_and_log_transition(validate_answer_post(ctx.state))
        ctx.state, ctx.artifacts["committed_turn_state"] = commit_answer_stage(
            ctx.state,
            assembly=ctx.artifacts["answer_assembly_contract"],
            validation=ctx.artifacts["answer_validation_contract"],
            rendered=ctx.artifacts["answer_render_contract"],
            commit_stage_id="answer.commit",
        )
        append_pipeline_snapshot("answer", ctx.state)
        ambiguity_score = _ambiguity_score(ctx.state.confidence_decision)
        ctx.artifacts["ambiguity_score"] = ambiguity_score
        append_session_log(
            "intent_classified",
            _intent_telemetry_payload(
                state=ctx.state,
                utterance=utterance,
                extra={
                    "ambiguity_score": ambiguity_score,
                    "user_followup_signal_proxy": round(ambiguity_score, 4),
                },
            ),
        )
        append_session_log(
            "commit_stage_recorded",
            {
                "stage": "answer.commit",
                "commit_stage": ctx.state.commit_receipt.get("commit_stage", "answer.commit"),
                "pipeline_state_snapshot": ctx.state.commit_receipt.get("pipeline_state_snapshot", "recorded"),
                "pending_repair_state": ctx.state.commit_receipt.get("pending_repair_state", {}),
                "resolved_obligations": ctx.state.commit_receipt.get("resolved_obligations", []),
                "remaining_obligations": ctx.state.commit_receipt.get("remaining_obligations", []),
                "confirmed_user_facts": ctx.state.commit_receipt.get("confirmed_user_facts", []),
                "retrieval_continuity_evidence": list(ctx.artifacts.get("retrieval_continuity_evidence", ())),
            },
        )
        append_session_log(
            "final_answer_mode",
            {
                "mode": ctx.state.invariant_decisions.get("answer_mode", "dont-know"),
                "query": ctx.state.rewritten_query,
                "context_confident": ctx.state.confidence_decision.get("context_confident", False),
                "retrieved_docs": [(d.id or d.metadata.get("doc_id") or "") for d in ctx.artifacts["hits"]],
                "claims": ctx.state.claims,
                "provenance_types": [p.value for p in ctx.state.provenance_types],
                "used_memory_refs": ctx.state.used_memory_refs,
                "used_source_evidence_refs": ctx.state.used_source_evidence_refs,
                "source_evidence_attribution": ctx.state.source_evidence_attribution,
                "basis_statement": ctx.state.basis_statement,
                "stage_audit_trail": list(ctx.stage_audit_trail),
                "commit_stage": ctx.state.commit_receipt.get("commit_stage", "answer.commit"),
            },
        )
        append_pipeline_snapshot("answer.commit", ctx.state)
        return ctx

    orchestrator = CanonicalTurnOrchestrator(
        stages=[
            CanonicalStage("observe.turn", _observe_turn),
            CanonicalStage("encode.candidates", _encode_candidates),
            CanonicalStage("stabilize.pre_route", _stabilize_pre_route),
            CanonicalStage("context.resolve", _context_resolve),
            CanonicalStage("intent.resolve", _intent_resolve),
            CanonicalStage("retrieve.evidence", _retrieve_evidence),
            CanonicalStage("policy.decide", _policy_decide),
            CanonicalStage("answer.assemble", _answer_assemble),
            CanonicalStage("answer.validate", _answer_validate),
            CanonicalStage("answer.render", _answer_render),
            CanonicalStage("answer.commit", _answer_commit),
        ]
    )
    final_context = orchestrator.run(context)
    final_state = replace(
        final_context.state,
        confidence_decision={
            **final_context.state.confidence_decision,
            "stage_audit_trail": list(final_context.stage_audit_trail),
        },
    )
    return final_state, list(final_context.artifacts["hits"])

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

        state = PipelineState(
            user_input=utterance,
            last_user_message_ts=last_user_message_ts,
            classified_intent=IntentType.KNOWLEDGE_QUESTION.value,
            resolved_intent="",
            prior_unresolved_intent=(
                prior_pipeline_state.prior_unresolved_intent
                if prior_pipeline_state is not None
                else ""
            ),
            confidence_decision={},
        )
        append_pipeline_snapshot("ingest", state)
        turn_id = str(uuid.uuid4())

        state, hits = _run_canonical_turn_pipeline(
            llm=llm,
            store=store,
            state=state,
            utterance=utterance,
            prior_pipeline_state=prior_pipeline_state,
            turn_id=turn_id,
            near_tie_delta=near_tie_delta,
            chat_history=chat_history,
            capability_status=capability_status,
            capability_snapshot=capability_snapshot,
            clock=clock,
            io_channel=io_channel,
        )

        ambiguity_score = _ambiguity_score(state.confidence_decision)
        chosen_action = str(state.invariant_decisions.get("fallback_action", "NONE"))
        followup_proxy = _user_followup_signal_proxy(
            final_answer=state.final_answer,
            fallback_action=chosen_action,
            ambiguity_score=ambiguity_score,
        )
        append_session_log(
            "fallback_action_selected",
            _intent_telemetry_payload(
                state=state,
                utterance=utterance,
                extra={
                    "ambiguity_score": ambiguity_score,
                    "chosen_action": chosen_action,
                    "user_followup_signal_proxy": followup_proxy,
                },
            ),
        )
        append_session_log(
            "provenance_summary",
            _intent_telemetry_payload(
                state=state,
                utterance=utterance,
                extra={
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
            ),
        )
        append_session_log(
            "alignment_decision_evaluated",
            _intent_telemetry_payload(
                state=state,
                utterance=utterance,
                extra={
                    "alignment_decision": state.alignment_decision.to_dict(),
                    "alignment_dimension_inputs_raw": state.alignment_decision.get("dimension_inputs", {}).get("raw", {}),
                    "alignment_dimension_inputs_normalized": state.alignment_decision.get("dimension_inputs", {}).get("normalized", {}),
                    "alignment_dimensions": state.alignment_decision.get("dimensions", {}),
                },
            ),
        )

        if capability_snapshot.runtime_capability_status.debug_enabled:
            debug_payload = _build_debug_turn_payload(state=state, intent_label=state.resolved_intent, hits=hits)
            debug_trace = _format_debug_turn_trace_payload(
                payload=debug_payload,
                verbose=capability_snapshot.runtime_capability_status.debug_verbose,
            )
            append_session_log(
                "debug_turn_trace",
                {
                    "utterance": utterance,
                    "payload": debug_payload,
                    "trace": debug_trace,
                },
            )
            send_assistant_text(debug_trace)

        unresolved_intent = (
            state.resolved_intent
            if is_clarification_answer(state.final_answer) or _is_capabilities_help_answer(state.final_answer)
            else ""
        )
        state = replace(state, prior_unresolved_intent=unresolved_intent)
        send_assistant_text(state.final_answer)

            # -----------------------
            # 4) Store assistant utterance card + reflection card
            # -----------------------
        last_user_message_ts = clock.now().isoformat()
        chat_history.append({"role": "user", "content": utterance})
        chat_history.append({"role": "assistant", "content": state.final_answer})
        prior_pipeline_state = state

        answer_commit_persistence(
            llm=llm,
            store=store,
            state=state,
            io_channel=io_channel,
            clock=clock,
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
                channel=io_channel,
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
        debug_verbose=bool(runtime.get("debug_verbose", False)),
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
    debug_verbose_override = getattr(args, "debug_verbose", None)
    if debug_verbose_override is not None:
        runtime["debug_verbose"] = debug_verbose_override

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
