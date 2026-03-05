from __future__ import annotations

import arrow

from testbot.time_parse import parse_target_time


NOW = arrow.get("2026-03-10T11:00:00+00:00")


def test_parse_target_time_in_two_weeks_moves_forward() -> None:
    assert parse_target_time("in 2 weeks", now=NOW) == NOW.shift(weeks=+2)


def test_parse_target_time_internal_in_two_weeks_moves_forward() -> None:
    utterance = "what did I say in 2 weeks"
    assert parse_target_time(utterance, now=NOW) == NOW.shift(weeks=+2)


def test_parse_target_time_two_weeks_ago_moves_backward() -> None:
    assert parse_target_time("2 weeks ago", now=NOW) == NOW.shift(weeks=-2)


def test_parse_target_time_duration_without_direction_is_neutral() -> None:
    assert parse_target_time("2 weeks", now=NOW) == NOW
