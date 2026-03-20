from __future__ import annotations

from collections import deque
import sys

from langchain_ollama import ChatOllama, OllamaEmbeddings

from testbot.clock import SystemClock
from testbot.entrypoints.sat_runtime_modes import run_cli_mode, run_satellite_mode
from testbot.observability.session_log import append_session_log
from testbot.sat_chatbot_memory_v2 import (
    build_capability_snapshot,
    build_runtime_memory_store,
    parse_args,
    print_startup_status,
    read_runtime_env,
    run_chat_loop,
    run_source_ingestion,
    sat_say,
)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    runtime = read_runtime_env()
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
    print_startup_status(snapshot=capability_snapshot)

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
    clock = SystemClock()
    run_source_ingestion(runtime=runtime, store=store)

    if capability_snapshot.effective_mode == "satellite":
        run_satellite_mode(
            runtime=runtime,
            llm=llm,
            store=store,
            chat_history=chat_history,
            near_tie_delta=float(runtime["memory_near_tie_delta"]),
            capability_snapshot=capability_snapshot,
            api_url=str(runtime["ha_api_url"]),
            token=str(runtime["ha_api_secret"]),
            entity_id=str(runtime["ha_satellite_entity_id"]),
            clock=clock,
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
