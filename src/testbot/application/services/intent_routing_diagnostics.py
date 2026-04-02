"""Diagnostics-only intent routing parity helpers.

Ownership:
- Canonical owner for non-authoritative intent-resolution parity checks used by
  tests and diagnostics tooling.
- This module must not be used for production routing decisions.
- Compatibility façades may delegate here while legacy surfaces are retired.
"""

from __future__ import annotations

import logging

from testbot.candidate_encoding import encode_turn_candidates
from testbot.context_resolution import resolve as resolve_context
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.intent_router import IntentType
from testbot.memory_cards import utc_now_iso
from testbot.memory_strata import derive_segment_descriptor
from testbot.pipeline_state import PipelineState
from testbot.stabilization import stabilize_pre_route
from testbot.turn_observation import observe_turn

_LOGGER = logging.getLogger(__name__)


def _enforce_diagnostics_only_guard(*, diagnostic_only: bool, helper_name: str) -> None:
    if diagnostic_only:
        return
    raise RuntimeError(
        f"{helper_name} is diagnostic-only and non-authoritative; "
        "production routing must use canonical orchestrator artifacts"
    )


def resolve_turn_intent(
    *,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    diagnostic_only: bool = True,
) -> tuple[IntentType, IntentType]:
    """Resolve intent for diagnostics-only parity checks."""

    _enforce_diagnostics_only_guard(diagnostic_only=diagnostic_only, helper_name="resolve_turn_intent")

    _LOGGER.warning(
        "resolve_turn_intent invoked in diagnostic-only mode; output is non-authoritative",
        extra={"authority": "non_authoritative", "helper": "resolve_turn_intent"},
    )
    seed_state = PipelineState(user_input=utterance)
    observation = observe_turn(
        seed_state,
        turn_id="offline-resolve-turn-intent",
        observed_at=utc_now_iso(),
        speaker="user",
        channel="offline",
    )
    encoded = encode_turn_candidates(seed_state, observation=observation, rewritten_query=utterance)
    segment = derive_segment_descriptor(
        utterance=observation.utterance,
        has_dialogue_state=bool(encoded.dialogue_state),
    )
    _, stabilized_turn_state = stabilize_pre_route(
        store=None,  # type: ignore[arg-type]
        state=seed_state,
        observation=observation,
        encoded=encoded,
        response_plan={"pathway": "offline_intent_resolution"},
        reflection_yaml="offline: true",
        segment=segment,
        store_doc_fn=lambda *args, **kwargs: None,
    )
    context_resolution = resolve_context(
        utterance=observation.utterance,
        prior_pipeline_state=prior_pipeline_state,
    )
    intent_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=stabilized_turn_state,
            context=context_resolution,
            fallback_utterance=observation.utterance,
        )
    )
    return intent_resolution.classified_intent, intent_resolution.resolved_intent
