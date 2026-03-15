from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pytest


class IntentClass(str, Enum):
    HAZARD_ALERT = "hazard_alert"
    ROUTE_REQUEST = "route_request"
    MEMORY_RECALL = "memory_recall"


class DecisionClass(str, Enum):
    HAZARD_INTERRUPT = "hazard_interrupt"
    ANSWER_FROM_EVIDENCE = "answer_from_evidence"
    ASK_FOR_CLARIFICATION = "ask_for_clarification"
    SAFE_FALLBACK = "safe_fallback"
    CONTINUE_REPAIR = "continue_repair"


@dataclass(frozen=True)
class Decision:
    decision_class: DecisionClass
    requires_interrupt: bool
    priority: int


def policy_decide(*, intent: IntentClass, evidence_present: bool, repair_active: bool) -> Decision:
    if intent is IntentClass.HAZARD_ALERT:
        return Decision(
            decision_class=DecisionClass.HAZARD_INTERRUPT,
            requires_interrupt=True,
            priority=1,
        )

    if repair_active:
        return Decision(
            decision_class=DecisionClass.CONTINUE_REPAIR,
            requires_interrupt=False,
            priority=2,
        )

    if evidence_present:
        return Decision(
            decision_class=DecisionClass.ANSWER_FROM_EVIDENCE,
            requires_interrupt=False,
            priority=4,
        )

    if intent is IntentClass.ROUTE_REQUEST:
        return Decision(
            decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
            requires_interrupt=False,
            priority=3,
        )

    return Decision(
        decision_class=DecisionClass.SAFE_FALLBACK,
        requires_interrupt=False,
        priority=3,
    )


@pytest.mark.parametrize(
    (
        "intent",
        "evidence_present",
        "repair_active",
        "expected_decision_class",
        "expected_requires_interrupt",
        "expected_priority",
    ),
    [
        (IntentClass.HAZARD_ALERT, False, False, DecisionClass.HAZARD_INTERRUPT, True, 1),
        (IntentClass.HAZARD_ALERT, True, False, DecisionClass.HAZARD_INTERRUPT, True, 1),
        (IntentClass.HAZARD_ALERT, False, True, DecisionClass.HAZARD_INTERRUPT, True, 1),
        (IntentClass.HAZARD_ALERT, True, True, DecisionClass.HAZARD_INTERRUPT, True, 1),
        (IntentClass.ROUTE_REQUEST, False, False, DecisionClass.ASK_FOR_CLARIFICATION, False, 3),
        (IntentClass.ROUTE_REQUEST, True, False, DecisionClass.ANSWER_FROM_EVIDENCE, False, 4),
        (IntentClass.ROUTE_REQUEST, False, True, DecisionClass.CONTINUE_REPAIR, False, 2),
        (IntentClass.ROUTE_REQUEST, True, True, DecisionClass.CONTINUE_REPAIR, False, 2),
        (IntentClass.MEMORY_RECALL, False, False, DecisionClass.SAFE_FALLBACK, False, 3),
        (IntentClass.MEMORY_RECALL, True, False, DecisionClass.ANSWER_FROM_EVIDENCE, False, 4),
        (IntentClass.MEMORY_RECALL, False, True, DecisionClass.CONTINUE_REPAIR, False, 2),
        (IntentClass.MEMORY_RECALL, True, True, DecisionClass.CONTINUE_REPAIR, False, 2),
    ],
)
def test_policy_decide_matrix(
    intent: IntentClass,
    evidence_present: bool,
    repair_active: bool,
    expected_decision_class: DecisionClass,
    expected_requires_interrupt: bool,
    expected_priority: int,
) -> None:
    decision = policy_decide(intent=intent, evidence_present=evidence_present, repair_active=repair_active)

    assert decision.decision_class is expected_decision_class
    assert decision.requires_interrupt is expected_requires_interrupt
    assert decision.priority == expected_priority


def test_hazard_alert_always_interrupts_with_top_priority() -> None:
    decision = policy_decide(intent=IntentClass.HAZARD_ALERT, evidence_present=False, repair_active=False)

    assert decision.decision_class is DecisionClass.HAZARD_INTERRUPT
    assert decision.requires_interrupt is True
    assert decision.priority == 1


def test_route_request_without_evidence_asks_for_clarification() -> None:
    decision = policy_decide(intent=IntentClass.ROUTE_REQUEST, evidence_present=False, repair_active=False)

    assert decision.decision_class is DecisionClass.ASK_FOR_CLARIFICATION


def test_memory_recall_without_evidence_uses_safe_fallback() -> None:
    decision = policy_decide(intent=IntentClass.MEMORY_RECALL, evidence_present=False, repair_active=False)

    assert decision.decision_class is DecisionClass.SAFE_FALLBACK


def test_repair_active_paths_continue_repair_when_not_hazard() -> None:
    route_decision = policy_decide(intent=IntentClass.ROUTE_REQUEST, evidence_present=False, repair_active=True)
    memory_decision = policy_decide(intent=IntentClass.MEMORY_RECALL, evidence_present=True, repair_active=True)

    assert route_decision.decision_class is DecisionClass.CONTINUE_REPAIR
    assert memory_decision.decision_class is DecisionClass.CONTINUE_REPAIR
