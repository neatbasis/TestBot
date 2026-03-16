from __future__ import annotations

from typing import Any

from .passage_log import latest_passage_of_kind
from .state_types import RenderContext, State
from .utils import strip_role_prefix


def recent_supporting_passages(state: State, limit: int = 3) -> list[str]:
    passages = state.get("passages", [])
    return [p["canonical_text"] for p in passages[-limit:]]


def select_supporting_passages(state: State) -> dict[str, Any]:
    latest_observation = latest_passage_of_kind(state, "observation")
    response_plan = state.get("response_plan", {})
    resolution = state.get("referent_resolution", {})

    if not latest_observation:
        return {}

    latest_user_text = strip_role_prefix(latest_observation["canonical_text"], "human")

    render_context: RenderContext = {
        "latest_user_text": latest_user_text,
        "response_mode": response_plan.get("mode", "respond"),
        "referent_kind": resolution.get("referent_kind", "none"),
        "referent_subject": resolution.get("referent_subject", ""),
        "supporting_passages": recent_supporting_passages(state, limit=3),
    }
    return {"render_context": render_context}
