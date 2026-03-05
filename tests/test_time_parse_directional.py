from __future__ import annotations

import arrow
import pytest

from testbot.time_parse import parse_target_time


NOW = arrow.get("2026-03-10T11:00:00+00:00")  # Tuesday


@pytest.mark.parametrize(
    ("utterance", "expected"),
    [
        ("in 3 days", NOW.shift(days=+3)),
        ("3 days from now", NOW.shift(days=+3)),
        ("3 days ago", NOW.shift(days=-3)),
        ("3 days earlier", NOW.shift(days=-3)),
        ("since 2 hours", NOW.shift(hours=-2)),
        ("until 2 hours", NOW.shift(hours=+2)),
        ("till 2 hours", NOW.shift(hours=+2)),
    ],
)
def test_parse_target_time_duration_cues(utterance: str, expected: arrow.Arrow) -> None:
    assert parse_target_time(utterance, now=NOW) == expected


def test_parse_target_time_duration_without_direction_remains_neutral() -> None:
    assert parse_target_time("3 days", now=NOW) == NOW


@pytest.mark.parametrize(
    ("utterance", "expected"),
    [
        ("next monday", arrow.get("2026-03-16T11:00:00+00:00")),
        ("last monday", arrow.get("2026-03-09T11:00:00+00:00")),
        ("today", NOW),
        ("tomorrow", NOW.shift(days=+1)),
        ("yesterday", NOW.shift(days=-1)),
    ],
)
def test_parse_target_time_weekday_and_relative_keywords(
    utterance: str, expected: arrow.Arrow
) -> None:
    assert parse_target_time(utterance, now=NOW) == expected
