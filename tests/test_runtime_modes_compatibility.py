from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest

from testbot.entrypoints import sat_cli
from testbot.entrypoints.runtime_legacy_bridge import read_runtime_env
from testbot import sat_chatbot_memory_v2 as runtime


def test_entrypoints_package_exposes_lazy_main_wrapper_without_eager_sat_cli_import() -> None:
    source = Path("src/testbot/entrypoints/__init__.py").read_text()
    assert "from .sat_cli import main\n" not in source
    assert "def main(" in source
    assert "from .cli import main as cli_main" in source


def test_runtime_legacy_bridge_warns_on_monolith_compat_usage() -> None:
    with pytest.deprecated_call(match="runtime_legacy_bridge depends on testbot.sat_chatbot_memory_v2"):
        read_runtime_env()


def test_runtime_legacy_bridge_run_chat_loop_delegates_to_runtime_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_legacy_bridge

    runtime_legacy_bridge._LEGACY_RUNTIME_WARNING_EMITTED = False
    captured: dict[str, object] = {}

    def _fake_runtime_loop(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("testbot.entrypoints.runtime_loop.run_chat_loop", _fake_runtime_loop)
    with pytest.deprecated_call(match="runtime_legacy_bridge depends on testbot.sat_chatbot_memory_v2"):
        runtime_legacy_bridge.run_chat_loop(
            runtime={},
            llm=object(),
            store=object(),
            chat_history=deque(),
            near_tie_delta=0.3,
            io_channel="satellite",
            capability_status="ok",
            capability_snapshot=object(),
            read_user_utterance=lambda: None,
            send_assistant_text=lambda _text: None,
            clock=object(),
        )

    assert captured["io_channel"] == "satellite"
    assert captured["near_tie_delta"] == 0.3


def test_monolith_run_chat_loop_delegates_to_runtime_loop_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _fake_runtime_loop(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("testbot.entrypoints.runtime_loop.run_chat_loop", _fake_runtime_loop)

    runtime.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.3,
        io_channel="cli",
        capability_status="ok",
        capability_snapshot=object(),
        read_user_utterance=lambda: None,
        send_assistant_text=lambda _text: None,
        clock=object(),
    )

    assert captured["io_channel"] == "cli"
    assert captured["near_tie_delta"] == 0.3


def test_legacy_runtime_main_warns_once_and_delegates_to_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    forwarded: list[list[str] | None] = []

    def _fake_cli_main(argv: list[str] | None = None) -> None:
        forwarded.append(argv)

    monkeypatch.setattr("testbot.entrypoints.cli.main", _fake_cli_main)
    runtime._LEGACY_MAIN_WARNING_EMITTED = False

    with pytest.warns(DeprecationWarning, match=r"testbot\.sat_chatbot_memory_v2\.main\(\.\.\.\)"):
        runtime.main(["--mode", "cli"])
    runtime.main(["--mode", "satellite"])

    assert len(forwarded) == 2
    assert forwarded[0] == ["--mode", "cli"]
    assert forwarded[1] == ["--mode", "satellite"]


def test_legacy_capabilities_help_answer_helper_delegates_to_canonical_continuity_owner() -> None:
    from testbot.application.services import continuity_runtime

    samples = [
        "Runtime mode: cli\nMemory recall: available\nHome Assistant: unavailable",
        "not a capabilities payload",
    ]

    for text in samples:
        assert runtime._is_capabilities_help_answer(text) is continuity_runtime.is_capabilities_help_answer(text)


def test_sat_cli_is_transitional_wrapper_to_canonical_cli() -> None:
    source = Path(sat_cli.__file__).read_text()
    assert "compatibility-only" in source
    assert "from .cli import main as cli_main" in source
