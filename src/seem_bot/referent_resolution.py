from __future__ import annotations

from typing import Any, cast

from .state_types import ReferentResolution, State


def resolve_referent(state: State) -> dict[str, Any]:
    user_act = state.get("user_act")
    if not user_act:
        return {}

    focus = state.get("active_focus")
    act_type = user_act["act_type"]

    if act_type in {"confirmation", "rejection", "clarification"}:
        if focus and focus.get("status") == "active":
            result: ReferentResolution = {
                "resolved": True,
                "referent_kind": cast(Any, focus.get("kind", "none")),
                "referent_subject": focus.get("subject", ""),
                "source_focus_id": focus.get("focus_id", ""),
                "reason": f"{act_type} resolved against active focus",
            }
            return {"referent_resolution": result}

        result: ReferentResolution = {
            "resolved": False,
            "referent_kind": "none",
            "referent_subject": "",
            "source_focus_id": "",
            "reason": f"{act_type} had no active focus to resolve against",
        }
        return {"referent_resolution": result}

    result = {
        "resolved": False,
        "referent_kind": "none",
        "referent_subject": "",
        "source_focus_id": "",
        "reason": f"no referent resolution needed for act_type={act_type}",
    }
    return {"referent_resolution": result}
