from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import testbot.sat_chatbot_memory_v2 as runtime
from testbot.observability.session_log import SESSION_LOG_SCHEMA_VERSION, append_session_log


class _Signal(Enum):
    GREEN = "green"


@dataclass(frozen=True)
class _Artifact:
    count: int


class _ToDictPayload:
    def to_dict(self) -> dict[str, object]:
        return {"status": _Signal.GREEN, "artifact": _Artifact(count=2)}


class _ObjectPayload:
    def __init__(self) -> None:
        self.flag = True


def _read_last_row(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return json.loads(lines[-1])


def _representative_payload() -> dict[str, object]:
    return {
        "nested": {
            "enum": _Signal.GREEN,
            "dataclass": _Artifact(count=1),
            "set": {"z", "a"},
            "tuple": (_ToDictPayload(), _ObjectPayload()),
        },
        "top_object": _ObjectPayload(),
    }


def test_legacy_append_session_log_import_path_still_works(tmp_path) -> None:
    legacy_log = tmp_path / "legacy.jsonl"
    runtime.append_session_log("legacy_event", _representative_payload(), log_path=legacy_log)

    row = _read_last_row(legacy_log)
    assert row["event"] == "legacy_event"
    assert row["schema_version"] == SESSION_LOG_SCHEMA_VERSION


def test_canonical_append_session_log_import_path_works(tmp_path) -> None:
    canonical_log = tmp_path / "canonical.jsonl"
    append_session_log("canonical_event", _representative_payload(), log_path=canonical_log)

    row = _read_last_row(canonical_log)
    assert row["event"] == "canonical_event"
    assert row["schema_version"] == SESSION_LOG_SCHEMA_VERSION


def test_legacy_and_canonical_payload_shapes_match(tmp_path) -> None:
    legacy_log = tmp_path / "legacy.jsonl"
    canonical_log = tmp_path / "canonical.jsonl"

    payload = _representative_payload()
    runtime.append_session_log("shape_event", payload, log_path=legacy_log)
    append_session_log("shape_event", payload, log_path=canonical_log)

    legacy_row = _read_last_row(legacy_log)
    canonical_row = _read_last_row(canonical_log)

    assert legacy_row["schema_version"] == SESSION_LOG_SCHEMA_VERSION
    assert canonical_row["schema_version"] == SESSION_LOG_SCHEMA_VERSION

    legacy_ts = legacy_row.pop("ts")
    canonical_ts = canonical_row.pop("ts")
    assert isinstance(legacy_ts, str)
    assert isinstance(canonical_ts, str)

    expected_payload = {
        "event": "shape_event",
        "schema_version": SESSION_LOG_SCHEMA_VERSION,
        "nested": {
            "enum": "green",
            "dataclass": {"count": 1},
            "set": ["a", "z"],
            "tuple": [
                {"status": "green", "artifact": {"count": 2}},
                {"flag": True},
            ],
        },
        "top_object": {"flag": True},
    }
    assert legacy_row == expected_payload
    assert canonical_row == expected_payload
