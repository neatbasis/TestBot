"""Deterministic response planning helpers for answer-stage prompting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from testbot.intent_router import PlanningDescriptor


class PlanningStage(str, Enum):
    OBSERVATION = "Observation"
    HYPOTHESIS_EXPANSION = "Hypothesis Expansion"
    PERSPECTIVE_SWITCHING = "Perspective Switching"
    SCENARIO_GENERATION = "Scenario Generation"
    LATER_CONVERGENCE = "Later Convergence"


@dataclass(frozen=True)
class PlannedStage:
    name: PlanningStage
    objective: str


@dataclass(frozen=True)
class ResponsePlan:
    descriptor: PlanningDescriptor
    stages: tuple[PlannedStage, ...]


def build_response_plan(*, descriptor: PlanningDescriptor, user_input: str) -> ResponsePlan:
    """Return a deterministic staged response plan for the current turn."""

    normalized_input = " ".join((user_input or "").split())
    topic = normalized_input[:120] if normalized_input else "the user request"
    facets = descriptor.facets

    pathway_objectives = {
        "memory_recall": (
            f"Extract the concrete memory-lookup target from: {topic}.",
            "Expand plausible memory anchors (people, events, and time windows) without inventing facts.",
            "Compare user framing against retrieved-memory framing and call out uncertainty when they diverge.",
            "Generate candidate memory-grounded responses and clarifier options.",
            "Converge on one policy-compliant answer with citation-ready evidence or a deterministic fallback.",
        ),
        "time_query": (
            f"Identify the requested temporal operation in: {topic}.",
            "Expand valid time interpretations supported by deterministic runtime inputs.",
            "Switch perspective between user-relative and system-relative timelines.",
            "Generate candidate time answers and safe limitation statements.",
            "Converge on the most direct deterministic time answer.",
        ),
        "capabilities": (
            f"Identify the capability request scope in: {topic}.",
            "Expand feasible capability routes and constraints from current runtime status.",
            "Switch perspective between user intent, available integrations, and policy-safe alternatives.",
            "Generate candidate capability responses with practical next steps.",
            "Converge on the clearest capability-grounded response.",
        ),
        "control": (
            f"Identify the control directive and immediate action in: {topic}.",
            "Expand deterministic control-safe interpretations and no-op fallbacks.",
            "Switch perspective between explicit command intent and accidental phrasing.",
            "Generate candidate control acknowledgements and safe continuations.",
            "Converge on a concise deterministic control response.",
        ),
        "non_memory": (
            f"Observe user intent and scope from: {topic}.",
            "Expand relevant non-memory response hypotheses while preserving policy constraints.",
            "Switch perspective between user utility, safety constraints, and capability limits.",
            "Generate candidate responses plus capability-based alternatives.",
            "Converge on the clearest policy-compliant response.",
        ),
    }
    objectives = list(pathway_objectives.get(descriptor.pathway, pathway_objectives["non_memory"]))

    if descriptor.pathway == "time_query" and facets.memory:
        objectives[1] = "Expand valid time interpretations plus memory anchors without inventing timeline details."
        objectives[3] = "Generate candidate time answers that reference memory constraints and safe limitation statements."
    if descriptor.pathway == "memory_recall" and facets.temporal:
        objectives[1] = "Expand plausible memory anchors including explicit time windows without inventing facts."
        objectives[2] = "Compare user framing against retrieved-memory framing and temporal references; call out uncertainty when they diverge."
    if descriptor.pathway == "non_memory" and facets.capability:
        objectives[3] = "Generate candidate responses plus capability-in-context alternatives relevant to the user request."

    stages = (
        PlannedStage(PlanningStage.OBSERVATION, objectives[0]),
        PlannedStage(PlanningStage.HYPOTHESIS_EXPANSION, objectives[1]),
        PlannedStage(PlanningStage.PERSPECTIVE_SWITCHING, objectives[2]),
        PlannedStage(PlanningStage.SCENARIO_GENERATION, objectives[3]),
        PlannedStage(PlanningStage.LATER_CONVERGENCE, objectives[4]),
    )
    return ResponsePlan(descriptor=descriptor, stages=stages)


def render_response_plan_block(plan: ResponsePlan) -> str:
    """Render plan stages as a stable prompt block."""

    lines = [
        f"planning_pathway: {plan.descriptor.pathway}",
        f"top_level_intent: {plan.descriptor.top_level_intent.value}",
        (
            "planning_facets: "
            f"temporal={str(plan.descriptor.facets.temporal).lower()}, "
            f"memory={str(plan.descriptor.facets.memory).lower()}, "
            f"capability={str(plan.descriptor.facets.capability).lower()}, "
            f"control={str(plan.descriptor.facets.control).lower()}"
        ),
        "response_planning_stages:",
    ]
    for stage in plan.stages:
        lines.append(f"- {stage.name.value}: {stage.objective}")
    return "\n".join(lines)


def plan_to_dict(plan: ResponsePlan) -> dict[str, object]:
    """Serialize a response plan for runtime logging/state fields."""

    return {
        "pathway": plan.descriptor.pathway,
        "top_level_intent": plan.descriptor.top_level_intent.value,
        "facets": {
            "temporal": plan.descriptor.facets.temporal,
            "memory": plan.descriptor.facets.memory,
            "capability": plan.descriptor.facets.capability,
            "control": plan.descriptor.facets.control,
        },
        "stages": [
            {
                "name": stage.name.value,
                "objective": stage.objective,
            }
            for stage in plan.stages
        ],
    }
