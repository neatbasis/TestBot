from __future__ import annotations

from typing import Any

from .state_types import ActiveFocus, State


def expire_focus(state: State) -> dict[str, Any]:
    focus = state.get("active_focus")
    if not focus:
        return {}

    if focus.get("status") != "active":
        return {}

    current_turn = state.get("iteration", 0)
    created_turn = focus.get("created_turn", 0)
    expires_after_turns = focus.get("expires_after_turns", 0)

    if expires_after_turns <= 0:
        return {}

    if current_turn - created_turn > expires_after_turns:
        updated: ActiveFocus = {
            **focus,
            "status": "expired",
        }
        return {"active_focus": updated}

    return {}
