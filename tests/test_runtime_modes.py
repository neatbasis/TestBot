from __future__ import annotations

from testbot.sat_chatbot_memory_v2 import _parse_args, _resolve_mode


def test_parse_args_defaults() -> None:
    args = _parse_args([])
    assert args.mode == "auto"
    assert args.daemon is False


def test_parse_args_satellite_daemon() -> None:
    args = _parse_args(["--mode", "satellite", "--daemon"])
    assert args.mode == "satellite"
    assert args.daemon is True


def test_resolve_mode_prefers_satellite_when_ha_available() -> None:
    assert _resolve_mode("auto", None) == "satellite"


def test_resolve_mode_falls_back_to_cli_when_ha_unavailable() -> None:
    assert _resolve_mode("auto", "auth failed") == "cli"
    assert _resolve_mode("cli", "auth failed") == "cli"
