from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

RuntimeParityFamily = Literal[
    "ordering_topx_fallback_confidence",
    "edge_time",
    "ambiguous_intent",
    "observation_making_processes",
    "temporal_uncertainty",
    "divergent_analysis",
]
RuntimeParityIntent = Literal["memory-grounded", "dont-know"]


class RuntimeParityCandidate(TypedDict, total=False):
    doc_id: str
    sim_score: float
    type: str
    ts: str
    source_doc_id: str


class RuntimeParityExpected(TypedDict, total=False):
    ranked_doc_ids_top_k: list[str]
    top_k: int
    intent: RuntimeParityIntent
    mode: str
    ambiguity_detected: bool
    context_confident: bool
    near_tie_min_count: int


@dataclass(frozen=True)
class RuntimeParityScenario:
    fixture_id: str
    family: RuntimeParityFamily
    utterance: str
    candidates: list[RuntimeParityCandidate]
    expected: RuntimeParityExpected


def runtime_parity_scenarios() -> tuple[RuntimeParityScenario, ...]:
    return (
        RuntimeParityScenario(
            fixture_id="ordering-clear-winner",
            family="ordering_topx_fallback_confidence",
            utterance="When did I mention the sprint demo?",
            candidates=[
                {"doc_id": "mem_demo_tuesday", "sim_score": 0.86, "type": "user_utterance", "ts": "2026-03-09T09:00:00+00:00"},
                {
                    "doc_id": "mem_demo_notes",
                    "sim_score": 0.61,
                    "type": "reflection",
                    "source_doc_id": "mem_demo_tuesday",
                    "ts": "2026-03-09T09:01:00+00:00",
                },
                {"doc_id": "mem_lunch", "sim_score": 0.52, "type": "user_utterance", "ts": "2026-03-09T12:00:00+00:00"},
            ],
            expected={"ranked_doc_ids_top_k": ["mem_demo_tuesday"], "top_k": 1, "intent": "memory-grounded"},
        ),
        RuntimeParityScenario(
            fixture_id="topx-three-stable",
            family="ordering_topx_fallback_confidence",
            utterance="What did I write about budget this week?",
            candidates=[
                {"doc_id": "mem_budget_cap", "sim_score": 0.82, "type": "user_utterance", "ts": "2026-03-08T10:00:00+00:00"},
                {
                    "doc_id": "mem_budget_reflection",
                    "sim_score": 0.81,
                    "type": "reflection",
                    "source_doc_id": "mem_budget_cap",
                    "ts": "2026-03-08T10:01:00+00:00",
                },
                {"doc_id": "mem_budget_followup", "sim_score": 0.79, "type": "user_utterance", "ts": "2026-03-08T11:00:00+00:00"},
                {"doc_id": "mem_unrelated", "sim_score": 0.33, "type": "user_utterance", "ts": "2026-03-07T08:00:00+00:00"},
            ],
            expected={
                "ranked_doc_ids_top_k": ["mem_budget_cap", "mem_budget_followup", "mem_unrelated"],
                "top_k": 3,
                "intent": "memory-grounded",
            },
        ),
        RuntimeParityScenario(
            fixture_id="fallback-low-confidence",
            family="ordering_topx_fallback_confidence",
            utterance="Do you remember my passport number?",
            candidates=[
                {"doc_id": "mem_trip_note", "sim_score": 0.31, "type": "user_utterance", "ts": "2026-03-01T11:00:00+00:00"},
                {"doc_id": "mem_pet_note", "sim_score": 0.29, "type": "user_utterance", "ts": "2026-03-02T09:30:00+00:00"},
            ],
            expected={"ranked_doc_ids_top_k": ["mem_trip_note"], "top_k": 1, "intent": "dont-know"},
        ),
        RuntimeParityScenario(
            fixture_id="confidence-boundary-min-hit",
            family="ordering_topx_fallback_confidence",
            utterance="What did I say about hydration?",
            candidates=[
                {"doc_id": "mem_hydration_goal", "sim_score": 0.35, "type": "user_utterance", "ts": "2026-03-10T06:30:00+00:00"},
                {
                    "doc_id": "mem_hydration_reflection",
                    "sim_score": 0.34,
                    "type": "reflection",
                    "source_doc_id": "mem_hydration_goal",
                    "ts": "2026-03-10T06:31:00+00:00",
                },
            ],
            expected={"ranked_doc_ids_top_k": ["mem_hydration_goal"], "top_k": 1, "intent": "dont-know"},
        ),
        RuntimeParityScenario(
            fixture_id="edge-time-three-hours-ago",
            family="edge_time",
            utterance="What did I say 3 hours ago about medication?",
            candidates=[
                {"doc_id": "mem_medication_0800", "sim_score": 0.72, "type": "user_utterance", "ts": "2026-03-10T08:00:00+00:00"},
                {"doc_id": "mem_medication_tomorrow", "sim_score": 0.78, "type": "user_utterance", "ts": "2026-03-11T08:00:00+00:00"},
                {
                    "doc_id": "mem_medication_reflection",
                    "sim_score": 0.65,
                    "type": "reflection",
                    "source_doc_id": "mem_medication_0800",
                    "ts": "2026-03-10T08:01:00+00:00",
                },
            ],
            expected={"ranked_doc_ids_top_k": ["mem_medication_0800"], "top_k": 1, "intent": "memory-grounded"},
        ),
        RuntimeParityScenario(
            fixture_id="edge-time-two-weeks-forward",
            family="edge_time",
            utterance="What did I say to do in 2 weeks?",
            candidates=[
                {"doc_id": "mem_checkin_2w", "sim_score": 0.73, "type": "user_utterance", "ts": "2026-03-24T11:00:00+00:00"},
                {"doc_id": "mem_checkin_yesterday", "sim_score": 0.79, "type": "user_utterance", "ts": "2026-03-09T11:00:00+00:00"},
                {
                    "doc_id": "mem_checkin_reflection",
                    "sim_score": 0.58,
                    "type": "reflection",
                    "source_doc_id": "mem_checkin_2w",
                    "ts": "2026-03-24T11:01:00+00:00",
                },
            ],
            expected={"ranked_doc_ids_top_k": ["mem_checkin_2w"], "top_k": 1, "intent": "memory-grounded"},
        ),
        RuntimeParityScenario(
            fixture_id="edge-time-leading-in-two-weeks-forward",
            family="edge_time",
            utterance="in 2 weeks what did I say to do?",
            candidates=[
                {"doc_id": "mem_checkin_2w_leading", "sim_score": 0.73, "type": "user_utterance", "ts": "2026-03-24T11:00:00+00:00"},
                {"doc_id": "mem_checkin_recent", "sim_score": 0.79, "type": "user_utterance", "ts": "2026-03-09T11:00:00+00:00"},
                {
                    "doc_id": "mem_checkin_2w_reflection",
                    "sim_score": 0.58,
                    "type": "reflection",
                    "source_doc_id": "mem_checkin_2w_leading",
                    "ts": "2026-03-24T11:01:00+00:00",
                },
            ],
            expected={"ranked_doc_ids_top_k": ["mem_checkin_2w_leading"], "top_k": 1, "intent": "memory-grounded"},
        ),
        RuntimeParityScenario(
            fixture_id="ambiguous-intent-near-tie",
            family="ambiguous_intent",
            utterance="Which project note did I mention this morning?",
            candidates=[
                {"doc_id": "mem_project_note_a", "sim_score": 0.62, "type": "user_utterance", "ts": "2026-03-10T09:00:00+00:00"},
                {"doc_id": "mem_project_note_b", "sim_score": 0.62, "type": "user_utterance", "ts": "2026-03-10T09:00:00+00:00"},
                {
                    "doc_id": "mem_project_note_reflection",
                    "sim_score": 0.6,
                    "type": "reflection",
                    "source_doc_id": "mem_project_note_a",
                    "ts": "2026-03-10T09:01:00+00:00",
                },
            ],
            expected={"ranked_doc_ids_top_k": ["mem_project_note_a"], "top_k": 1, "intent": "memory-grounded", "near_tie_min_count": 2},
        ),
        RuntimeParityScenario(
            fixture_id="observation-making-processes-morning-routine",
            family="observation_making_processes",
            utterance="What did I observe while making coffee this morning?",
            candidates=[
                {
                    "doc_id": "mem_obs_coffee_grinder",
                    "sim_score": 0.77,
                    "type": "user_utterance",
                    "ts": "2026-03-10T07:15:00+00:00",
                },
                {
                    "doc_id": "mem_obs_process_reflection",
                    "sim_score": 0.75,
                    "type": "reflection",
                    "source_doc_id": "mem_obs_coffee_grinder",
                    "ts": "2026-03-10T07:16:00+00:00",
                },
                {"doc_id": "mem_obs_weather", "sim_score": 0.55, "type": "user_utterance", "ts": "2026-03-10T07:10:00+00:00"},
            ],
            expected={"ranked_doc_ids_top_k": ["mem_obs_coffee_grinder", "mem_obs_weather"], "top_k": 2, "intent": "dont-know"},
        ),
        RuntimeParityScenario(
            fixture_id="temporal-uncertainty-missing-ts-wins-on-semantic",
            family="temporal_uncertainty",
            utterance="What did I note about my sleep routine?",
            candidates=[
                {"doc_id": "mem_sleep_missing_ts", "sim_score": 0.7, "type": "user_utterance", "ts": ""},
                {"doc_id": "mem_sleep_old", "sim_score": 0.72, "type": "user_utterance", "ts": "2025-12-01T08:00:00+00:00"},
                {"doc_id": "mem_sleep_recent_low_sim", "sim_score": 0.45, "type": "user_utterance", "ts": "2026-03-10T06:00:00+00:00"},
            ],
            expected={"ranked_doc_ids_top_k": ["mem_sleep_missing_ts", "mem_sleep_old"], "top_k": 2, "intent": "memory-grounded"},
        ),
        RuntimeParityScenario(
            fixture_id="temporal-uncertainty-mixed-valid-missing-near-margin",
            family="temporal_uncertainty",
            utterance="When did I mention hydration this morning?",
            candidates=[
                {"doc_id": "mem_hydration_missing_ts", "sim_score": 0.34, "type": "user_utterance", "ts": ""},
                {"doc_id": "mem_hydration_valid", "sim_score": 0.31, "type": "user_utterance", "ts": "2026-03-10T09:00:00+00:00"},
                {"doc_id": "mem_hydration_old", "sim_score": 0.5, "type": "user_utterance", "ts": "2025-11-10T09:00:00+00:00"},
            ],
            expected={"ranked_doc_ids_top_k": ["mem_hydration_valid", "mem_hydration_missing_ts"], "top_k": 2, "intent": "memory-grounded"},
        ),
        RuntimeParityScenario(
            fixture_id="divergent-analysis-ambiguous-near-tie",
            family="divergent_analysis",
            utterance="I feel stuck and overwhelmed; what might be going on?",
            candidates=[
                {
                    "doc_id": "mem_stuck_overwhelmed_workload",
                    "sim_score": 0.64,
                    "type": "user_utterance",
                    "ts": "2026-03-10T08:40:00+00:00",
                },
                {
                    "doc_id": "mem_stuck_overwhelmed_sleep",
                    "sim_score": 0.64,
                    "type": "user_utterance",
                    "ts": "2026-03-10T08:39:00+00:00",
                },
                {
                    "doc_id": "mem_stuck_meta_reflection",
                    "sim_score": 0.63,
                    "type": "reflection",
                    "source_doc_id": "mem_stuck_overwhelmed_workload",
                    "ts": "2026-03-10T08:41:00+00:00",
                },
            ],
            expected={
                "ranked_doc_ids_top_k": ["mem_stuck_overwhelmed_workload"],
                "top_k": 1,
                "intent": "dont-know",
                "mode": "dont-know-low-confidence",
                "ambiguity_detected": False,
                "context_confident": False,
                "near_tie_min_count": 2,
            },
        ),
        RuntimeParityScenario(
            fixture_id="divergent-analysis-low-confidence-broad-query",
            family="divergent_analysis",
            utterance="Can you help me analyze why everything feels off lately?",
            candidates=[
                {"doc_id": "mem_off_lately_weather", "sim_score": 0.36, "type": "user_utterance", "ts": "2026-03-08T12:00:00+00:00"},
                {"doc_id": "mem_off_lately_meeting", "sim_score": 0.35, "type": "user_utterance", "ts": "2026-03-09T15:10:00+00:00"},
                {
                    "doc_id": "mem_off_lately_reflection",
                    "sim_score": 0.34,
                    "type": "reflection",
                    "source_doc_id": "mem_off_lately_weather",
                    "ts": "2026-03-08T12:02:00+00:00",
                },
            ],
            expected={
                "ranked_doc_ids_top_k": ["mem_off_lately_weather"],
                "top_k": 1,
                "intent": "dont-know",
                "mode": "dont-know-low-confidence",
                "ambiguity_detected": False,
                "context_confident": False,
            },
        ),
        RuntimeParityScenario(
            fixture_id="divergent-analysis-grounded-specific-followup",
            family="divergent_analysis",
            utterance="What explanation did I write this morning for feeling behind?",
            candidates=[
                {
                    "doc_id": "mem_feeling_behind_explanation",
                    "sim_score": 0.84,
                    "type": "user_utterance",
                    "ts": "2026-03-10T08:20:00+00:00",
                },
                {
                    "doc_id": "mem_feeling_behind_reflection",
                    "sim_score": 0.82,
                    "type": "reflection",
                    "source_doc_id": "mem_feeling_behind_explanation",
                    "ts": "2026-03-10T08:21:00+00:00",
                },
                {
                    "doc_id": "mem_feeling_behind_unrelated",
                    "sim_score": 0.41,
                    "type": "user_utterance",
                    "ts": "2026-03-05T08:00:00+00:00",
                },
            ],
            expected={
                "ranked_doc_ids_top_k": ["mem_feeling_behind_explanation"],
                "top_k": 1,
                "intent": "memory-grounded",
                "mode": "memory-grounded",
                "ambiguity_detected": False,
                "context_confident": True,
            },
        ),
    )
