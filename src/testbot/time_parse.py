from __future__ import annotations

import re
from typing import Optional

import arrow

_NUM_SMALL = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_NUM_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_NUM_SPECIAL = {"a": 1, "an": 1, "couple": 2, "few": 3}

_UNIT_ALIASES = {
    "s": "seconds",
    "sec": "seconds",
    "secs": "seconds",
    "second": "seconds",
    "seconds": "seconds",
    "m": "minutes",
    "min": "minutes",
    "mins": "minutes",
    "minute": "minutes",
    "minutes": "minutes",
    "h": "hours",
    "hr": "hours",
    "hrs": "hours",
    "hour": "hours",
    "hours": "hours",
    "d": "days",
    "day": "days",
    "days": "days",
    "w": "weeks",
    "wk": "weeks",
    "wks": "weeks",
    "week": "weeks",
    "weeks": "weeks",
    "mo": "months",
    "month": "months",
    "months": "months",
    "y": "years",
    "yr": "years",
    "yrs": "years",
    "year": "years",
    "years": "years",
}
_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _to_int(num_raw: str) -> Optional[int]:
    s = num_raw.lower().strip()
    if s.isdigit():
        return int(s)
    if s in _NUM_SPECIAL:
        return _NUM_SPECIAL[s]
    if s in _NUM_SMALL:
        return _NUM_SMALL[s]
    if s in _NUM_TENS:
        return _NUM_TENS[s]
    parts = s.split()
    if len(parts) == 2:
        tens, ones = parts
        if tens in _NUM_TENS and ones in _NUM_SMALL:
            return _NUM_TENS[tens] + _NUM_SMALL[ones]
    return None


def _unit_norm(unit_raw: str) -> Optional[str]:
    return _UNIT_ALIASES.get(unit_raw.lower())


_DURATION_RE = re.compile(
    r"\b(?P<num>"
    r"\d+|"
    r"(?:a|an|couple|few|"
    r"zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
    r"(?:\s+(?:one|two|three|four|five|six|seven|eight|nine))?"
    r")"
    r")\s*"
    r"(?P<unit>"
    r"seconds?|secs?|sec|s|"
    r"minutes?|mins?|min|m|"
    r"hours?|hrs?|hr|h|"
    r"days?|d|"
    r"weeks?|wks?|wk|w|"
    r"months?|mo|"
    r"years?|yrs?|yr|y"
    r")\b",
    flags=re.IGNORECASE,
)


def _extract_duration_seconds(text: str) -> Optional[float]:
    m = _DURATION_RE.search(text)
    if not m:
        return None
    n = _to_int(m.group("num"))
    unit = _unit_norm(m.group("unit"))
    if n is None or unit is None:
        return None
    multipliers = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
        "days": 86400,
        "weeks": 604800,
        "months": 2629800,  # avg month
        "years": 31557600,  # avg year
    }
    return float(n) * multipliers[unit]


def _weekday_shift(now: arrow.Arrow, target_weekday: int, direction: str) -> arrow.Arrow:
    today = now.weekday()  # Monday=0
    if direction == "next":
        delta = (target_weekday - today) % 7
        delta = 7 if delta == 0 else delta
        return now.shift(days=+delta)
    delta = (today - target_weekday) % 7
    delta = 7 if delta == 0 else delta
    return now.shift(days=-delta)


def parse_target_time(utterance: str, *, now: Optional[arrow.Arrow] = None) -> arrow.Arrow:
    now = now or arrow.utcnow()
    text = utterance.strip().lower()

    if "just now" in text or "right now" in text:
        return now
    if "today" in text:
        return now
    if "yesterday" in text:
        return now.shift(days=-1)
    if "tomorrow" in text:
        return now.shift(days=+1)

    if "last week" in text:
        return now.shift(weeks=-1)
    if "next week" in text:
        return now.shift(weeks=+1)
    if "last month" in text:
        return now.shift(months=-1)
    if "next month" in text:
        return now.shift(months=+1)
    if "last year" in text:
        return now.shift(years=-1)
    if "next year" in text:
        return now.shift(years=+1)

    for wd_name, wd_idx in _WEEKDAY.items():
        if f"next {wd_name}" in text:
            return _weekday_shift(now, wd_idx, "next")
        if f"last {wd_name}" in text:
            return _weekday_shift(now, wd_idx, "last")

    dur_s = _extract_duration_seconds(text)
    if dur_s is not None:
        past_cues = [" ago", " earlier", " before", " previously"]
        future_cues = [" from now", " later", " after ", " hence"]
        has_in_cue = re.search(r"\bin\b", text) is not None

        if any(cue in text for cue in past_cues):
            return now.shift(seconds=-int(round(dur_s)))
        if has_in_cue or any(cue in text for cue in future_cues):
            return now.shift(seconds=+int(round(dur_s)))

        if "since" in text:
            return now.shift(seconds=-int(round(dur_s)))
        if "until" in text or "till" in text:
            return now.shift(seconds=+int(round(dur_s)))

        return now

    return now
