"""Deterministic response planning helpers for answer-stage prompting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
    pathway: str
    stages: tuple[PlannedStage, ...]


def build_response_plan(*, pathway: str, user_input: str) -> ResponsePlan:
    """Return a deterministic staged response plan for the current turn."""

    normalized_input = " ".join((user_input or "").split())
    topic = normalized_input[:120] if normalized_input else "the user request"

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
        "non_memory": (
            f"Observe user intent and scope from: {topic}.",
            "Expand relevant non-memory response hypotheses while preserving policy constraints.",
            "Switch perspective between user utility, safety constraints, and capability limits.",
            "Generate candidate responses plus capability-based alternatives.",
            "Converge on the clearest policy-compliant response.",
        ),
    }
    objectives = pathway_objectives.get(pathway, pathway_objectives["non_memory"])
    stages = (
        PlannedStage(PlanningStage.OBSERVATION, objectives[0]),
        PlannedStage(PlanningStage.HYPOTHESIS_EXPANSION, objectives[1]),
        PlannedStage(PlanningStage.PERSPECTIVE_SWITCHING, objectives[2]),
        PlannedStage(PlanningStage.SCENARIO_GENERATION, objectives[3]),
        PlannedStage(PlanningStage.LATER_CONVERGENCE, objectives[4]),
    )
    return ResponsePlan(pathway=pathway, stages=stages)


def render_response_plan_block(plan: ResponsePlan) -> str:
    """Render plan stages as a stable prompt block."""

    lines = [f"planning_pathway: {plan.pathway}", "response_planning_stages:"]
    for stage in plan.stages:
        lines.append(f"- {stage.name.value}: {stage.objective}")
    return "\n".join(lines)


def plan_to_dict(plan: ResponsePlan) -> dict[str, object]:
    """Serialize a response plan for runtime logging/state fields."""

    return {
        "pathway": plan.pathway,
        "stages": [
            {
                "name": stage.name.value,
                "objective": stage.objective,
            }
            for stage in plan.stages
        ],
    }
