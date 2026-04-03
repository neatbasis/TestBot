from __future__ import annotations

import importlib.util
import json
import re
from collections import deque
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

import arrow
import pytest

from testbot.entrypoints import cli
from testbot.adapters.ask_gateway import AskTurnInput, STOP_DECISION_ID
from testbot.clock import SystemClock
from testbot.interaction_policy import InteractionPolicyRequest
from testbot.interaction_standards import InteractionRequirements
from testbot.entrypoints import sat_runtime_modes
from testbot.runtime_capability_service import resolve_mode
from testbot.pipeline_state import PipelineState
from testbot.runtime_cli_args import parse_args
from testbot.application.services import context_retrieval_runtime
from testbot.answer_contract_constants import CLARIFY_ANSWER
from testbot.application.services.intent_routing_diagnostics import resolve_turn_intent
from testbot.evidence_retrieval import RetrievalInputRecord
from testbot.policies.turn_policy import RETRIEVAL_SCORE_THRESHOLD
import testbot.runtime_capability_service as runtime_capability_service


def test_sat_runtime_modes_does_not_import_monolith_runtime_for_profile_selection() -> None:
    source = Path(sat_runtime_modes.__file__).read_text()
    assert "from testbot.sat_chatbot_memory_v2" not in source


def test_sat_runtime_modes_does_not_depend_on_runtime_legacy_bridge_symbols() -> None:
    source = Path(sat_runtime_modes.__file__).read_text()
    assert "from testbot.entrypoints.runtime_legacy_bridge import" not in source


def test_runtime_loop_owner_handles_none_input_as_immediate_return(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop

    poll_calls: list[dict[str, object]] = []
    completion_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        runtime_loop,
        "poll_pending_ingestion_obligations",
        lambda *, runtime, deps: poll_calls.append(runtime),
    )

    def _fake_completion(**kwargs):
        completion_calls.append(kwargs)
        return "", None, False

    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", _fake_completion)

    runtime_loop.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ok",
        capability_snapshot=SimpleNamespace(
            runtime_capability_status=SimpleNamespace(debug_enabled=False, debug_verbose=False)
        ),
        read_user_utterance=lambda: None,
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: arrow.get("2026-01-01T00:00:00+00:00")),
    )

    assert len(poll_calls) == 1
    assert len(completion_calls) == 1


def test_runtime_loop_sat_say_delegates_to_ha_satellite_output_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop

    captured: dict[str, object] = {}

    def _fake_send_satellite_output(client, entity_id: str, text: str) -> None:
        captured["client"] = client
        captured["entity_id"] = entity_id
        captured["text"] = text

    monkeypatch.setattr("testbot.entrypoints.runtime_loop.send_satellite_output", _fake_send_satellite_output)
    fake_client = object()
    runtime_loop.sat_say(fake_client, "assist_satellite.kitchen", "hello")

    assert captured == {
        "client": fake_client,
        "entity_id": "assist_satellite.kitchen",
        "text": "hello",
    }


def test_cli_uses_runtime_bootstrap_owner_and_limits_legacy_bridge_imports() -> None:
    source = Path(cli.__file__).read_text()
    assert "from testbot.entrypoints.runtime_bootstrap import build_runtime_memory_store, read_runtime_env" in source
    assert "from testbot.entrypoints.runtime_loop import run_chat_loop" in source
    assert "from testbot.adapters.ha_satellite_output import send_satellite_output" in source
    assert "from testbot.entrypoints.runtime_legacy_bridge import" not in source
    assert "from testbot.runtime_capability_service import build_capability_snapshot" in source
    assert "from testbot.startup_status_presenter import print_startup_status" in source
    assert "from testbot.runtime_cli_args import parse_args" in source
    assert "from testbot.source_ingestion_startup import run_source_ingestion" in source
    assert "from testbot.source_ingestion_entry import apply_source_ingestion_entry" in source
    assert "def _apply_source_ingestion_selection" not in source
    assert "from testbot.sat_chatbot_memory_v2 import" not in source


def test_runtime_loop_owner_uses_canonical_turn_pipeline_helper_not_monolith_turn_pipeline_helper() -> None:
    from testbot.entrypoints import runtime_loop

    source = Path(runtime_loop.__file__).read_text()
    assert "from testbot.entrypoints.runtime_background_ingestion import (" in source
    assert "from testbot.entrypoints.runtime_commit_persistence import (" in source
    assert "from testbot.entrypoints.runtime_turn_pipeline import RuntimeTurnPipelineHooks, run_runtime_turn_pipeline" in source
    assert "from testbot.entrypoints.runtime_turn_telemetry import (" in source
    assert "RuntimeTurnTelemetryDependencies" in source
    assert "emit_runtime_turn_telemetry" in source
    assert "from testbot.application.services import answer_stage_runtime as answer_stage_runtime_service" in source
    assert "from testbot.application.services import continuity_runtime as continuity_runtime_service" in source
    assert "from testbot.application.services import answer_stage_presentation as answer_stage_presentation_service" in source
    assert "from testbot.application.services import context_retrieval_runtime as context_retrieval_runtime_service" in source
    assert "_poll_pending_ingestion_obligations(" not in source
    assert "_process_background_ingestion_completion(" not in source
    assert "_run_canonical_turn_pipeline(" not in source
    assert "_intent_telemetry_payload(" not in source
    assert "_build_debug_turn_payload(" not in source
    assert "_format_debug_turn_trace_payload(" not in source
    assert "_resolve_answer_routing_for_stage" not in source
    assert "_answer_assemble_for_turn_service" not in source
    assert "_answer_validate_for_turn_service" not in source
    assert "build_provenance_metadata=getattr(_legacy_runtime" not in source
    assert "evaluate_alignment_decision=getattr(_legacy_runtime" not in source
    assert "render_context=getattr(_legacy_runtime" not in source
    assert "answer_prompt=getattr(_legacy_runtime" not in source
    assert "_detect_capability_offer" not in source
    assert "_should_force_memory_retrieval_for_identity_recall" not in source
    assert "_stage_retrieve_for_turn_service" not in source
    assert "_stage_rerank_for_turn_service" not in source
    assert "_document_from_retrieval_input" not in source
    assert "_legacy_runtime.resolve_context" not in source
    assert "run_canonical_turn_pipeline(" not in source
    assert "_legacy_runtime.answer_commit_persistence(" not in source
    assert "_legacy_runtime.is_clarification_answer" not in source
    assert "_legacy_runtime._is_capabilities_help_answer" not in source
    assert "_legacy_runtime.append_session_log(" not in source
    assert "continuity_runtime_service.apply_unresolved_intent_carryover(state)" in source
    assert "TurnPipelineDependencies(" not in source


def test_runtime_loop_monolith_touchpoints_are_allowlisted_for_deliberate_shrink_only() -> None:
    from testbot.entrypoints import runtime_loop

    source = Path(runtime_loop.__file__).read_text()
    observed_symbols = set(re.findall(r"_legacy_runtime\.([A-Za-z_][A-Za-z0-9_]*)", source))
    assert observed_symbols == set()


def test_runtime_loop_background_ingestion_deps_use_canonical_append_session_log(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop
    from testbot.observability import session_log as session_log_module

    observed_background_loggers: list[object] = []
    observed_connector_loggers: list[object] = []

    monkeypatch.setattr(
        "testbot.sat_chatbot_memory_v2.append_session_log",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("legacy append_session_log should not own background-ingestion dependency logging")
        ),
    )

    def _poll_with_connector_probe(*, runtime, deps):
        observed_background_loggers.append(deps.append_session_log)
        deps.build_source_connector({"source_connector_type": "none"})

    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", _poll_with_connector_probe)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(
        runtime_loop,
        "build_source_connector",
        lambda *, runtime, append_session_log: observed_connector_loggers.append(append_session_log) or None,
    )

    runtime_loop.run_chat_loop(
        runtime={"source_connector_type": "none"},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ok",
        capability_snapshot=SimpleNamespace(
            runtime_capability_status=SimpleNamespace(debug_enabled=False, debug_verbose=False)
        ),
        read_user_utterance=lambda: None,
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: arrow.get("2026-01-01T00:00:00+00:00")),
    )

    assert observed_background_loggers == [session_log_module.append_session_log]
    observed_background_loggers[0]("runtime_loop_background_ingestion_logger_proof", {})

    assert observed_connector_loggers == [session_log_module.append_session_log]


def test_runtime_loop_commit_persistence_deps_use_canonical_append_session_log(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop
    from testbot.observability import session_log as session_log_module

    observed_commit_loggers: list[object] = []

    monkeypatch.setattr(
        "testbot.sat_chatbot_memory_v2.append_session_log",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("legacy append_session_log should not own commit-persistence dependency logging")
        ),
    )

    monkeypatch.setattr(
        runtime_loop,
        "persist_answer_commit",
        lambda **kwargs: observed_commit_loggers.append(kwargs["deps"].append_session_log),
    )

    def _completion_with_commit_probe(**kwargs):
        kwargs["deps"].answer_commit_persistence(
            llm=object(),
            store=object(),
            state=runtime_loop.PipelineState(user_input="background replay", final_answer="done"),
            io_channel="cli",
            clock=SimpleNamespace(now=lambda: arrow.get("2026-01-01T00:00:00+00:00")),
        )
        return "", None, False

    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", _completion_with_commit_probe)

    runtime_loop.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ok",
        capability_snapshot=SimpleNamespace(
            runtime_capability_status=SimpleNamespace(debug_enabled=False, debug_verbose=False)
        ),
        read_user_utterance=lambda: None,
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: arrow.get("2026-01-01T00:00:00+00:00")),
    )

    assert observed_commit_loggers == [session_log_module.append_session_log]
    observed_commit_loggers[0]("runtime_loop_commit_persistence_logger_proof", {})


def test_runtime_loop_background_completion_replay_dependency_is_canonical_runtime_turn_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from testbot.entrypoints import runtime_loop
    from testbot.application.services.background_ingestion_runtime import BackgroundIngestionReplayRequest

    captured: dict[str, object] = {}
    expected_runtime: dict[str, object] = {}
    fake_pipeline_state = runtime_loop.PipelineState(
        user_input="x",
        last_user_message_ts="",
        classified_intent="knowledge_question",
        resolved_intent="",
        prior_unresolved_intent="",
        confidence_decision={},
    )

    class _CapturingDeps:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(runtime_loop, "RuntimeBackgroundIngestionDependencies", _CapturingDeps)
    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(
        runtime_loop,
        "run_runtime_turn_pipeline",
        lambda **kwargs: (fake_pipeline_state, []),
    )
    runtime_loop.run_chat_loop(
        runtime=expected_runtime,
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ok",
        capability_snapshot=SimpleNamespace(
            runtime_capability_status=SimpleNamespace(debug_enabled=False, debug_verbose=False)
        ),
        read_user_utterance=lambda: None,
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: arrow.get("2026-01-01T00:00:00+00:00")),
    )

    replay = captured["replay_background_completion_turn"]
    assert callable(replay)
    replay_result = replay(
        BackgroundIngestionReplayRequest(
            runtime=expected_runtime,
            llm=object(),
            store=object(),
            utterance="Need grounded update",
            last_user_message_ts="2026-01-01T00:00:00+00:00",
            prior_pipeline_state=None,
            near_tie_delta=0.1,
            chat_history=deque(),
            capability_status="ok",
            capability_snapshot={},
            clock=object(),
            io_channel="cli",
            turn_id="turn-1",
        )
    )
    assert replay_result is fake_pipeline_state


def test_runtime_loop_context_retrieval_residual_monolith_touchpoints_are_explicit_policy_core_only() -> None:
    from testbot.entrypoints import runtime_loop

    source = Path(runtime_loop.__file__).read_text()
    assert "_legacy_runtime.stage_retrieve" not in source
    assert "_legacy_runtime.stage_rerank" not in source
    assert "_legacy_runtime.resolve_context" not in source
    assert "_legacy_runtime._should_force_memory_retrieval_for_identity_recall" not in source
    assert "_legacy_runtime._stage_retrieve_for_turn_service" not in source
    assert "_legacy_runtime._stage_rerank_for_turn_service" not in source
    assert "_legacy_runtime._document_from_retrieval_input" not in source


def test_runtime_loop_binds_migrated_context_retrieval_hook_surfaces_via_canonical_service() -> None:
    from testbot.entrypoints import runtime_loop

    source = Path(runtime_loop.__file__).read_text()
    assert (
        "should_force_memory_retrieval_for_identity_recall="
        "context_retrieval_runtime_service.should_force_memory_retrieval_for_identity_recall"
    ) in source
    assert "resolve_context_fn=context_retrieval_runtime_service.resolve_context" in source
    assert "context_retrieval_runtime_service.stage_retrieve_for_turn_service(" in source
    assert "context_retrieval_runtime_service.stage_rerank_for_turn_service(" in source
    assert "document_from_retrieval_input=context_retrieval_runtime_service.document_from_retrieval_input" in source


def test_runtime_loop_turn_pipeline_logging_residual_monolith_touchpoints_are_removed_from_selected_bundle() -> None:
    from testbot.entrypoints import runtime_loop

    source = Path(runtime_loop.__file__).read_text()
    assert "build_runtime_turn_pipeline_hooks(\n        append_session_log=append_runtime_session_log," in source
    assert "append_session_log=_legacy_runtime.append_session_log" not in source
    assert "validate_and_log_transition=_legacy_runtime._validate_and_log_transition" not in source


def test_runtime_loop_runtime_hooks_resolve_context_retrieval_control_point_at_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    from dataclasses import replace

    from testbot.application.services import context_retrieval_runtime as context_retrieval_runtime_service
    from testbot.entrypoints import runtime_loop

    captured: dict[str, object] = {}
    sent: list[str] = []

    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(runtime_loop, "emit_runtime_turn_telemetry", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)

    def _fake_turn_pipeline(**kwargs):
        captured["hooks"] = kwargs["hooks"]
        state = kwargs["state"]
        return (
            replace(
                state,
                final_answer="ok",
                commit_receipt={"pending_ingestion_request_id": ""},
            ),
            [],
        )

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _fake_turn_pipeline)

    utterances = iter(["hello", "stop"])
    runtime_loop.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=object(),
        read_user_utterance=lambda: next(utterances, None),
        send_assistant_text=lambda text: sent.append(text),
        clock=SystemClock(),
    )

    hooks = captured["hooks"]
    assert hooks.should_force_memory_retrieval_for_identity_recall is context_retrieval_runtime_service.should_force_memory_retrieval_for_identity_recall
    assert hooks.resolve_context_fn is context_retrieval_runtime_service.resolve_context
    assert hooks.document_from_retrieval_input is context_retrieval_runtime_service.document_from_retrieval_input

    observed: dict[str, object] = {}

    def _fake_stage_retrieve_for_turn_service(*args, **kwargs):
        observed["retrieve_kwargs"] = kwargs
        return args[1], []

    def _fake_stage_rerank_for_turn_service(*args, **kwargs):
        observed["rerank_kwargs"] = kwargs
        return args[0], []

    monkeypatch.setattr(context_retrieval_runtime_service, "stage_retrieve_for_turn_service", _fake_stage_retrieve_for_turn_service)
    monkeypatch.setattr(context_retrieval_runtime_service, "stage_rerank_for_turn_service", _fake_stage_rerank_for_turn_service)

    probe_state = PipelineState(user_input="probe", rewritten_query="probe")
    hooks.stage_retrieve(object(), probe_state)
    hooks.stage_rerank(
        probe_state,
        [],
        utterance="probe",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=SystemClock(),
    )

    assert observed["retrieve_kwargs"]["retrieval_score_threshold"] == RETRIEVAL_SCORE_THRESHOLD
    assert "stage_retrieve_fn" not in observed["retrieve_kwargs"]
    assert "stage_rerank_fn" not in observed["rerank_kwargs"]
    assert sent[0] == "ok"


def test_runtime_loop_canonical_stage_rerank_path_consumes_runtime_decision_policy_assembly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    import arrow
    from langchain_core.documents import Document

    from testbot.application.services import context_retrieval_runtime as context_retrieval_runtime_service
    from testbot.entrypoints import runtime_loop
    from testbot.rerank import RerankOutcome

    captured: dict[str, object] = {}

    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(runtime_loop, "emit_runtime_turn_telemetry", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)

    def _fake_turn_pipeline(**kwargs):
        captured["hooks"] = kwargs["hooks"]
        state = kwargs["state"]
        return replace(state, final_answer="ok", commit_receipt={"pending_ingestion_request_id": ""}), []

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _fake_turn_pipeline)

    utterances = iter(["hello", "stop"])
    runtime_loop.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=object(),
        read_user_utterance=lambda: next(utterances, None),
        send_assistant_text=lambda _text: None,
        clock=SystemClock(),
    )

    hooks = captured["hooks"]
    observed: dict[str, object] = {}
    now = arrow.get("2026-03-10T12:00:00+00:00")
    original_stage_rerank_for_turn_service = context_retrieval_runtime_service.stage_rerank_for_turn_service

    def _proxy_stage_rerank_for_turn_service(
        state,
        retrieval_candidates,
        *,
        stage_rerank_fn=None,
        utterance,
        user_doc_id,
        user_reflection_doc_id,
        near_tie_delta,
        clock,
        io_channel="cli",
    ):
        del retrieval_candidates, io_channel
        if stage_rerank_fn is None:
            updated_state, hits = original_stage_rerank_for_turn_service(
                state,
                [RetrievalInputRecord(ref_id="doc-1", score=0.9, content="candidate", metadata={"doc_id": "doc-1"})],
                utterance=utterance,
                user_doc_id=user_doc_id,
                user_reflection_doc_id=user_reflection_doc_id,
                near_tie_delta=near_tie_delta,
                clock=clock,
            )
        else:
            updated_state, hits = stage_rerank_fn(
                state,
                [(Document(id="doc-1", page_content="candidate", metadata={"doc_id": "doc-1"}), 0.9)],
                utterance=utterance,
                user_doc_id=user_doc_id,
                user_reflection_doc_id=user_reflection_doc_id,
                near_tie_delta=near_tie_delta,
                clock=clock,
            )
        return updated_state, [RetrievalInputRecord(ref_id=str(doc.id), score=1.0, content=doc.page_content, metadata=doc.metadata) for doc in hits]

    monkeypatch.setattr(context_retrieval_runtime_service, "stage_rerank_for_turn_service", _proxy_stage_rerank_for_turn_service)
    monkeypatch.setattr(
        context_retrieval_runtime_service,
        "resolve_temporal_anaphora_bridge",
        lambda *, utterance, docs_and_scores, now: {
            "anaphora_detected": False,
            "anchor_candidates": [],
            "selected_anchor_doc_id": "",
            "selected_anchor_ts": "",
            "target_override_ts": "",
            "delta_seconds_raw": None,
            "delta_humanized": "",
            "time_window": "",
            "window_start": "",
            "window_end": "",
        },
    )
    monkeypatch.setattr(context_retrieval_runtime_service, "filter_documents_for_temporal_window", lambda *, docs_and_scores, bridge: docs_and_scores)
    monkeypatch.setattr(context_retrieval_runtime_service, "resolve_rerank_target_time", lambda *, utterance, bridge, now: now)
    monkeypatch.setattr(
        context_retrieval_runtime_service,
        "resolve_rerank_sigma_seconds",
        lambda *, now, target, sigma_fraction=0.25, sigma_policy_fn=None: 600.0,
    )

    def _fake_assemble_decision_policy(*, sigma_seconds, user_doc_id, user_reflection_doc_id, near_tie_delta, top_k=4):
        observed["assembled"] = {
            "sigma_seconds": sigma_seconds,
            "user_doc_id": user_doc_id,
            "user_reflection_doc_id": user_reflection_doc_id,
            "near_tie_delta": near_tie_delta,
            "top_k": top_k,
        }
        return context_retrieval_runtime_service.RerankDecisionPolicy(
            invocation_policy=context_retrieval_runtime_service.RerankInvocationPolicy(
                sigma_seconds=77.0,
                exclude_doc_ids={"policy-doc"},
                exclude_source_ids={"policy-source"},
                top_k=3,
                near_tie_delta=0.27,
            ),
            threshold_profile_policy=context_retrieval_runtime_service.RerankThresholdProfilePolicy(
                top_final_score_min=0.51,
                min_margin_to_second=0.08,
                allow_ambiguity_override=True,
                ambiguity_override_top_final_score_min=0.9,
            ),
        )

    monkeypatch.setattr(context_retrieval_runtime_service, "assemble_rerank_decision_policy", _fake_assemble_decision_policy)
    monkeypatch.setattr(
        context_retrieval_runtime_service,
        "execute_rerank_scorer_contract",
        lambda request: (
            observed.setdefault(
                "rerank_kwargs",
                {
                    "sigma_seconds": request.sigma_seconds,
                    "exclude_doc_ids": request.exclude_doc_ids,
                    "exclude_source_ids": request.exclude_source_ids,
                    "top_k": request.top_k,
                    "near_tie_delta": request.near_tie_delta,
                },
            ),
            context_retrieval_runtime_service.ScorerExecutionResult(
                rerank_outcome=RerankOutcome(docs=[], scored_candidates=[], ambiguity_detected=False, near_tie_candidates=[])
            ),
        )[1],
    )

    class _Clock:
        def now(self):
            return now

    updated_state, _ = hooks.stage_rerank(
        PipelineState(user_input="probe", rewritten_query="probe", confidence_decision={}),
        [RetrievalInputRecord(ref_id="seed", score=0.5, content="seed", metadata={"doc_id": "seed"})],
        utterance="probe",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=_Clock(),
    )
    observed["state"] = updated_state

    assert observed["assembled"] == {
        "sigma_seconds": 600.0,
        "user_doc_id": "user-doc",
        "user_reflection_doc_id": "reflection-doc",
        "near_tie_delta": 0.1,
        "top_k": 4,
    }
    assert observed["rerank_kwargs"]["sigma_seconds"] == 77.0
    assert observed["rerank_kwargs"]["exclude_doc_ids"] == {"policy-doc"}
    assert observed["rerank_kwargs"]["exclude_source_ids"] == {"policy-source"}
    assert observed["rerank_kwargs"]["top_k"] == 3
    assert observed["rerank_kwargs"]["near_tie_delta"] == 0.27
    assert observed["state"].confidence_decision["top_final_score_min"] == 0.51
    assert observed["state"].confidence_decision["min_margin_to_second"] == 0.08
    assert observed["state"].confidence_decision["allow_ambiguity_override"] is True
    assert observed["state"].confidence_decision["ambiguity_override_top_final_score_min"] == 0.9


def test_run_satellite_mode_uses_planner_selected_requirements(monkeypatch) -> None:
    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    planned_requirements = InteractionRequirements(
        stable_id_required=True,
        deterministic_field_collection_required=True,
        open_text_preferred=False,
        sentence_style_fit="structured_sentence",
        machine_actionable=False,
    )

    monkeypatch.setattr(
        sat_runtime_modes,
        "select_interaction_policy_request",
        lambda **_kwargs: SimpleNamespace(
            request=InteractionPolicyRequest(
                intent="collect_turn_input",
                channel_context="satellite",
                task_flow_context="memory_chat_loop",
                interaction_requirements=planned_requirements,
                policy_id="test.policy.v1",
            ),
            interaction_requirements=planned_requirements,
        ),
    )

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert interaction_policy.channel_context == "satellite"
            assert question == "Ask one memory-grounded question."
            assert timeout_s == 60.0
            assert recent_successful_channel_context is None
            assert interaction_policy.interaction_requirements == planned_requirements
            return AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None)

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        assert read_user_utterance() == "stop"

    sat_runtime_modes.run_satellite_mode(
        runtime={"ha_base_url": "http://localhost:8123", "ha_api_token": "token", "ha_satellite_entity_id": "assist_satellite.kitchen"},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )


def test_run_cli_mode_uses_terminal_channel_ask_gateway(monkeypatch) -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert interaction_policy.channel_context == "cli"
            assert question == "Ask one memory-grounded question."
            assert timeout_s == 60.0
            assert recent_successful_channel_context is None
            assert interaction_policy.interaction_requirements == InteractionRequirements(
                stable_id_required=False,
                deterministic_field_collection_required=False,
                open_text_preferred=True,
                sentence_style_fit="plain_sentence",
                machine_actionable=False,
            )
            return AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None)

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        assert capability_status == "ask_available"
        assert read_user_utterance() == "stop"

    sat_runtime_modes.run_cli_mode(
        runtime={},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )


def test_run_cli_mode_passes_non_stop_sentence_through_unchanged() -> None:
    sentence = "What did I ask you about source ingestion earlier?"

    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert interaction_policy.channel_context == "cli"
            assert question == "Ask one memory-grounded question."
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=None, sentence=sentence, error=None)

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        observed["capability_status"] = capability_status
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime={},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert observed["capability_status"] == "ask_available"
    assert observed["utterance"] == sentence


@pytest.mark.parametrize(
    ("decision_id", "sentence"),
    [
        (STOP_DECISION_ID, ""),
        ("cancelled", ""),
        ("user_aborted", ""),
        ("eof", ""),
        (None, "stop"),
        (None, "cancel"),
        (None, "EXIT"),
    ],
)
def test_run_cli_mode_collapses_terminal_stop_signals_to_stop(decision_id: str | None, sentence: str) -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=decision_id, sentence=sentence, error=None)

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        observed["capability_status"] = capability_status
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime={},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert observed["capability_status"] == "ask_available"
    assert observed["utterance"] == "stop"


def test_run_cli_mode_reports_retryable_ask_errors_as_retry_prompt() -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=None, sentence="", error="temporary timeout from ask")

    observed: dict[str, object] = {}
    output = StringIO()

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        observed["capability_status"] = capability_status
        observed["utterance"] = read_user_utterance()

    with redirect_stdout(output):
        sat_runtime_modes.run_cli_mode(
            runtime={},
            llm=SimpleNamespace(),
            store=SimpleNamespace(),
            chat_history=deque(),
            near_tie_delta=0.05,
            capability_snapshot=SimpleNamespace(),
            clock=SimpleNamespace(),
            ask_gateway=_FakeGateway(),
            run_chat_loop=_fake_run_chat_loop,
        )

    assert observed["capability_status"] == "ask_available"
    assert observed["utterance"] == ""
    assert "Please try again." in output.getvalue()


def test_run_cli_mode_stops_on_non_retryable_ask_errors() -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=None, sentence="", error="permission denied")

    observed: dict[str, object] = {}
    output = StringIO()

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        observed["capability_status"] = capability_status
        observed["utterance"] = read_user_utterance()

    with redirect_stdout(output):
        sat_runtime_modes.run_cli_mode(
            runtime={},
            llm=SimpleNamespace(),
            store=SimpleNamespace(),
            chat_history=deque(),
            near_tie_delta=0.05,
            capability_snapshot=SimpleNamespace(),
            clock=SimpleNamespace(),
            ask_gateway=_FakeGateway(),
            run_chat_loop=_fake_run_chat_loop,
        )

    assert observed["capability_status"] == "ask_available"
    assert observed["utterance"] == "stop"
    assert "Ask input is unavailable (permission denied). Stopping." in output.getvalue()


def test_run_cli_mode_handles_empty_ask_reply_as_silence() -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=None, sentence="   ", error=None)

    output = StringIO()
    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    with redirect_stdout(output):
        sat_runtime_modes.run_cli_mode(
            runtime={},
            llm=SimpleNamespace(),
            store=SimpleNamespace(),
            chat_history=deque(),
            near_tie_delta=0.05,
            capability_snapshot=SimpleNamespace(),
            clock=SimpleNamespace(),
            ask_gateway=_FakeGateway(),
            run_chat_loop=_fake_run_chat_loop,
        )

    assert observed["utterance"] == ""
    assert "bot> I heard silence. Try again." in output.getvalue()


def test_run_cli_mode_persists_last_successful_ask_channel_as_cli() -> None:
    runtime_state: dict[str, object] = {}

    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(
                decision_id=None,
                sentence="What did I ask about earlier?",
                error=None,
                resolved_channel="terminal",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert observed["utterance"] == "What did I ask about earlier?"
    assert runtime_state["last_successful_ask_channel_context"] == "cli"


def test_run_satellite_mode_persists_last_successful_ask_channel_as_satellite(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(
                decision_id=None,
                sentence="Tell me what changed.",
                error=None,
                resolved_channel="satellite",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )

    assert observed["utterance"] == "Tell me what changed."
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"


@pytest.mark.parametrize(
    "artifact_sentence",
    [
        "thank you for watching",
        "  THANK   YOU   FOR   WATCHING  ",
        "thanks for listening",
        "see you next time",
        "subtitles by",
        "thank you thank you thank you thank you",
    ],
)
def test_run_satellite_mode_rejects_low_information_transcript_artifacts(
    monkeypatch: pytest.MonkeyPatch, artifact_sentence: str
) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }

    spoken: list[str] = []

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(
                decision_id=None,
                sentence=artifact_sentence,
                error=None,
                resolved_channel="satellite",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda _client, _entity_id, text: spoken.append(text),
    )

    assert observed["utterance"] == ""
    assert spoken == [
        "v0 memory loop online. Say 'stop' to exit.",
        "I heard a low-information transcript artifact. Please try again.",
    ]
    assert "last_successful_ask_channel_context" not in runtime_state


def test_run_satellite_mode_artifact_rejection_does_not_overwrite_recent_successful_channel_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "last_successful_ask_channel_context": "satellite",
    }
    captured_recent: dict[str, object] = {}

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            captured_recent["value"] = recent_successful_channel_context
            return AskTurnInput(
                decision_id=None,
                sentence="thank you for listening",
                error=None,
                resolved_channel="satellite",
                resolution_source="recent_successful_ask_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )

    assert captured_recent["value"] == "satellite"
    assert observed["utterance"] == ""
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"


def test_run_satellite_mode_keeps_meaningful_sentence_when_non_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }
    sentence = "What changed in runtime acceptance policy?"

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            return AskTurnInput(
                decision_id=None,
                sentence=sentence,
                error=None,
                resolved_channel="satellite",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )

    assert observed["utterance"] == sentence
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"


def test_artifact_context_matrix_is_explicit_and_deterministic() -> None:
    question = "Ask one memory-grounded question."

    high_artifact_low_context = sat_runtime_modes._classify_artifact_vs_context(
        sentence="thank you for watching",
        question=question,
    )
    assert high_artifact_low_context.likely_artifact is True
    assert high_artifact_low_context.context_consistent is False
    assert high_artifact_low_context.should_reject is True
    assert "exact_known_phrase" in high_artifact_low_context.artifact_reasons

    high_artifact_higher_context = sat_runtime_modes._classify_artifact_vs_context(
        sentence="thanks for watching, can you answer my memory question about source ingestion?",
        question=question,
    )
    assert high_artifact_higher_context.likely_artifact is True
    assert high_artifact_higher_context.context_consistent is True
    assert high_artifact_higher_context.should_reject is False

    repeated_loop = sat_runtime_modes._classify_artifact_vs_context(
        sentence="thank you thank you thank you thank you",
        question=question,
    )
    assert repeated_loop.likely_artifact is True
    assert repeated_loop.context_consistent is False
    assert repeated_loop.should_reject is True
    assert "repeated_low_information_loop" in repeated_loop.artifact_reasons

    normal_meaningful_sentence = sat_runtime_modes._classify_artifact_vs_context(
        sentence="What changed in runtime acceptance policy?",
        question=question,
    )
    assert normal_meaningful_sentence.likely_artifact is False
    assert normal_meaningful_sentence.context_consistent is True
    assert normal_meaningful_sentence.should_reject is False
    assert normal_meaningful_sentence.artifact_reasons == ()


def test_run_satellite_mode_allows_context_consistent_sentence_with_artifact_substring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }
    sentence = "Thanks for watching, my memory question is about source ingestion."
    spoken: list[str] = []

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            return AskTurnInput(
                decision_id=None,
                sentence=sentence,
                error=None,
                resolved_channel="satellite",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda _client, _entity_id, text: spoken.append(text),
    )

    assert observed["utterance"] == sentence
    assert spoken == ["v0 memory loop online. Say 'stop' to exit."]
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"


def test_run_cli_mode_uses_recent_successful_channel_when_policy_channel_unavailable() -> None:
    runtime_state: dict[str, object] = {"last_successful_ask_channel_context": "cli"}
    captured_recent: dict[str, object] = {}

    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            captured_recent["value"] = recent_successful_channel_context
            return AskTurnInput(
                decision_id=None,
                sentence="continue",
                error=None,
                resolved_channel="terminal",
                resolution_source="recent_successful_ask_channel",
                fallback_used=True,
                fallback_reason="policy_and_override_unavailable",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert captured_recent["value"] == "cli"
    assert observed["utterance"] == "continue"
    assert runtime_state["last_successful_ask_channel_context"] == "cli"


@pytest.mark.parametrize(
    ("ask_result", "expected_utterance"),
    [
        (AskTurnInput(decision_id=None, sentence="", error="temporary timeout from ask", resolved_channel="terminal"), ""),
        (AskTurnInput(decision_id=None, sentence="", error="permission denied", resolved_channel="terminal"), "stop"),
        (AskTurnInput(decision_id=None, sentence="   ", error=None, resolved_channel="terminal"), ""),
        (AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None, resolved_channel="terminal"), "stop"),
    ],
)
def test_run_cli_mode_error_empty_and_stop_paths_do_not_overwrite_recent_successful_channel(
    ask_result: AskTurnInput, expected_utterance: str
) -> None:
    runtime_state: dict[str, object] = {"last_successful_ask_channel_context": "satellite"}

    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context == "satellite"
            return ask_result

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert observed["utterance"] == expected_utterance
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"

def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.mode == "auto"
    assert args.daemon is False
    assert args.source_ingestion == "env"
    assert args.source_reference == "wikipedia_hilbert"
    assert args.source_freeform == ""


def test_parse_args_satellite_daemon() -> None:
    args = parse_args(["--mode", "satellite", "--daemon"])
    assert args.mode == "satellite"
    assert args.daemon is True
    assert args.source_ingestion == "env"


def test_parse_args_source_ingestion_selection() -> None:
    args = parse_args(["--source-ingestion", "reference", "--source-reference", "local_alignment_docs"])
    assert args.source_ingestion == "reference"
    assert args.source_reference == "local_alignment_docs"


def test_parse_args_debug_verbose_defaults_to_none() -> None:
    args = parse_args([])
    assert args.debug_verbose is None


def test_parse_args_debug_verbose_opt_in() -> None:
    args = parse_args(["--debug-verbose"])
    assert args.debug_verbose is True


def test_parse_args_debug_verbose_opt_out() -> None:
    args = parse_args(["--no-debug-verbose"])
    assert args.debug_verbose is False


def test_resolve_mode_prefers_satellite_when_ha_available() -> None:
    assert resolve_mode("auto", None) == "satellite"


def test_resolve_mode_falls_back_to_cli_when_ha_unavailable() -> None:
    assert resolve_mode("auto", "auth failed") == "cli"
    assert resolve_mode("cli", "auth failed") == "cli"


def test_ollama_connection_error_returns_validation_error_before_urlopen(monkeypatch) -> None:
    called = {"urlopen": False}

    def _unexpected_urlopen(*_args, **_kwargs):
        called["urlopen"] = True
        raise AssertionError("urlopen should not be called for invalid base URL")

    monkeypatch.setattr(runtime_capability_service, "urlopen", _unexpected_urlopen)

    err = runtime_capability_service.ollama_connection_error("localhost:11434", "llama3.1:latest", "nomic-embed-text")

    assert err == "Invalid OLLAMA_BASE_URL 'localhost:11434'; must be full http(s) URL"
    assert called["urlopen"] is False
def test_ollama_connection_error_accepts_implicit_latest_alias(monkeypatch) -> None:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"},{"model":"nomic-embed-text:latest"}]}'

    monkeypatch.setattr(runtime_capability_service, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime_capability_service.ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text")
    assert err is None


def test_ollama_connection_error_includes_x_ollama_key_when_configured(monkeypatch) -> None:
    observed = {"x_ollama_key": None}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"},{"model":"nomic-embed-text:latest"}]}'

    def _fake_urlopen(request, **_kwargs):
        observed["x_ollama_key"] = request.get_header("X-ollama-key")
        return _Resp()

    monkeypatch.setattr(runtime_capability_service, "urlopen", _fake_urlopen)
    err = runtime_capability_service.ollama_connection_error(
        "http://localhost:11434",
        "llama3.1:latest",
        "nomic-embed-text",
        x_ollama_key="test-key",
    )
    assert err is None
    assert observed["x_ollama_key"] == "test-key"


def test_ollama_connection_error_accepts_explicit_latest_alias(monkeypatch) -> None:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"},{"model":"nomic-embed-text"}]}'

    monkeypatch.setattr(runtime_capability_service, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime_capability_service.ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text:latest")
    assert err is None


def test_ollama_connection_error_detects_missing_embedding_model(monkeypatch) -> None:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"}]}'

    monkeypatch.setattr(runtime_capability_service, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime_capability_service.ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text")
    assert "embedding model" in str(err)


def test_resolve_turn_intent_affirmation_preserves_clarification_intent() -> None:
    prior_state = PipelineState(
        user_input="what happened?",
        resolved_intent="memory_recall",
        prior_unresolved_intent="memory_recall",
        final_answer=CLARIFY_ANSWER,
    )

    classified, resolved = resolve_turn_intent(utterance="yes", prior_pipeline_state=prior_state)

    assert classified.value == "knowledge_question"
    assert resolved.value == "memory_recall"


def test_resolve_turn_intent_non_affirmation_does_not_preserve_prior_intent() -> None:
    prior_state = PipelineState(
        user_input="what happened?",
        resolved_intent="memory_recall",
        prior_unresolved_intent="memory_recall",
        final_answer=CLARIFY_ANSWER,
    )

    classified, resolved = resolve_turn_intent(utterance="no, never mind", prior_pipeline_state=prior_state)

    assert classified.value == "control"
    assert resolved.value == "control"


def test_resolve_turn_intent_temporal_followup_after_memory_recall_avoids_knowledge_question_fallback() -> None:
    prior_state = PipelineState(
        user_input="Who am I?",
        resolved_intent="memory_recall",
        prior_unresolved_intent="memory_recall",
        final_answer="You are Sam.",
        commit_receipt={"confirmed_user_facts": ["name=Sam"]},
    )

    classified, resolved = resolve_turn_intent(utterance="when was that again?", prior_pipeline_state=prior_state)

    assert classified.value == "knowledge_question"
    assert resolved.value == "time_query"
