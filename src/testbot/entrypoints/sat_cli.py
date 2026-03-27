"""Runtime CLI entrypoint.

Bridge usage is intentionally centralized here while runtime bootstrap/chat-loop
ownership is incrementally migrated out of monolith compatibility exports.
"""

from __future__ import annotations

from collections import deque
import sys
from types import SimpleNamespace

from langchain_ollama import ChatOllama, OllamaEmbeddings

from testbot.adapters.ask_gateway import AskGateway
from testbot.domain import build_system_clock
from testbot.entrypoints.sat_runtime_modes import run_cli_mode, run_satellite_mode
from testbot.observability.session_log import append_session_log
from testbot.runtime_capability_service import build_capability_snapshot
from testbot.startup_status_presenter import print_startup_status

# Legacy bridge imports are intentionally grouped and replaced incrementally
# as extracted runtime ownership becomes stable.
from testbot.entrypoints.runtime_legacy_bridge import (
    build_runtime_memory_store,
    read_runtime_env,
    run_chat_loop,
    run_source_ingestion,
    sat_say,
)
from testbot.runtime_cli_args import parse_args


def _apply_source_ingestion_selection(*, args, runtime: dict[str, object]) -> None:
    selection = str(getattr(args, "source_ingestion", "env") or "env").strip().lower()
    if selection == "env":
        runtime["source_ingest_selection_source"] = "environment"
        return

    if selection == "off":
        runtime["source_ingest_enabled"] = False
        runtime["source_ingest_selection_source"] = "cli"
        append_session_log(
            "source_ingest_selection",
            {
                "selection_source": "cli",
                "source_ingestion": "off",
                "source_ingest_enabled": False,
                "source_connector_type": str(runtime.get("source_connector_type", "")).strip().lower(),
            },
        )
        return

    runtime["source_ingest_enabled"] = True
    runtime["source_connector_type"] = selection
    runtime["source_ingest_selection_source"] = "cli"
    append_session_log(
        "source_ingest_selection",
        {
            "selection_source": "cli",
            "source_ingestion": selection,
            "source_ingest_enabled": True,
            "source_connector_type": selection,
        },
    )


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    runtime = read_runtime_env()
    debug_verbose_override = getattr(args, "debug_verbose", None)
    if debug_verbose_override is not None:
        runtime["debug_verbose"] = debug_verbose_override
    _apply_source_ingestion_selection(args=args, runtime=runtime)

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
    startup_status_snapshot = SimpleNamespace(
        runtime=runtime,
        effective_mode=capability_snapshot.effective_mode,
        requested_mode=capability_snapshot.requested_mode,
        daemon_mode=capability_snapshot.daemon_mode,
        fallback_reason=capability_snapshot.fallback_reason,
        ollama_error=capability_snapshot.ollama_error,
        ha_error=capability_snapshot.ha_error,
        runtime_capability_status=capability_snapshot.runtime_capability_status,
    )
    print_startup_status(snapshot=startup_status_snapshot)

    if capability_snapshot.effective_mode is None:
        if args.mode == "auto" and args.daemon:
            print(f"Daemon mode requested in auto mode and {capability_snapshot.exit_reason}", file=sys.stderr)
        else:
            print(f"Startup failed and {capability_snapshot.exit_reason}", file=sys.stderr)
        return

    ollama_client_kwargs = {}
    if str(runtime.get("x_ollama_key", "")).strip():
        ollama_client_kwargs["client_kwargs"] = {"headers": {"X-Ollama-Key": str(runtime["x_ollama_key"])}}

    llm = ChatOllama(model=str(runtime["ollama_model"]), base_url=str(runtime["ollama_base_url"]), **ollama_client_kwargs, temperature=0.0)
    embeddings = OllamaEmbeddings(model=str(runtime["ollama_embedding_model"]), base_url=str(runtime["ollama_base_url"]), **ollama_client_kwargs)
    store = build_runtime_memory_store(runtime=runtime, embeddings=embeddings)
    chat_history = deque(maxlen=10)
    clock = build_system_clock()
    run_source_ingestion(runtime=runtime, store=store)

    if capability_snapshot.effective_mode == "satellite":
        run_satellite_mode(
            runtime=runtime,
            llm=llm,
            store=store,
            chat_history=chat_history,
            near_tie_delta=float(runtime["memory_near_tie_delta"]),
            capability_snapshot=capability_snapshot,
            clock=clock,
            ask_gateway=AskGateway.from_runtime(runtime),
            run_chat_loop=run_chat_loop,
            satellite_say=sat_say,
        )
        return

    run_cli_mode(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=float(runtime["memory_near_tie_delta"]),
        capability_snapshot=capability_snapshot,
        clock=clock,
        run_chat_loop=run_chat_loop,
    )
