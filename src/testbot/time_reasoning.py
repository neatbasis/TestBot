from __future__ import annotations

from typing import Optional

import arrow


def elapsed_since_last_user_message(last_user_ts: str | None, now: arrow.Arrow) -> int | None:
    """Return elapsed seconds from the previous user message timestamp."""
    if not last_user_ts:
        return None
    try:
        last = arrow.get(last_user_ts)
    except Exception:
        return None
    elapsed = int((now - last).total_seconds())
    return max(0, elapsed)


def resolve_relative_date(token: str, now: arrow.Arrow, timezone: str) -> Optional[str]:
    """Resolve today/tomorrow/yesterday to a YYYY-MM-DD date in the given timezone."""
    normalized = token.strip().lower()
    local_now = now.to(timezone)

    if normalized == "today":
        target = local_now
    elif normalized == "tomorrow":
        target = local_now.shift(days=+1)
    elif normalized == "yesterday":
        target = local_now.shift(days=-1)
    else:
        return None

    return target.format("YYYY-MM-DD")
