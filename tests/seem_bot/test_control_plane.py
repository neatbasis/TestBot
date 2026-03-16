from seem_bot.assistant_acts import declare_assistant_act, update_focus_from_declared_act
from seem_bot.focus_state import expire_focus
from seem_bot.referent_resolution import resolve_referent
from seem_bot.response_planner import plan_response_node
from seem_bot.user_act_classifier import classify_text


def test_confirmation_resolves_against_active_question():
    state = {
        "user_act": {"act_type": "confirmation", "confidence": 0.95},
        "active_focus": {
            "focus_id": "focus-1",
            "kind": "assistant_question",
            "subject": "database migration",
            "status": "active",
        },
    }

    resolution = resolve_referent(state)["referent_resolution"]

    assert resolution["resolved"] is True
    assert resolution["referent_kind"] == "assistant_question"
    assert resolution["referent_subject"] == "database migration"


def test_rejection_without_focus_requests_clarification():
    state = {
        "user_act": {"act_type": "rejection", "confidence": 0.95},
        "referent_resolution": {
            "resolved": False,
            "referent_kind": "none",
            "referent_subject": "",
            "source_focus_id": "",
            "reason": "no focus",
        },
    }

    plan = plan_response_node(state)["response_plan"]

    assert plan["mode"] == "clarify_missing_referent"
    assert plan["needs_clarification"] is True


def test_clarification_with_active_focus_resolves():
    state = {
        "user_act": {"act_type": "clarification", "confidence": 0.9},
        "active_focus": {
            "focus_id": "focus-2",
            "kind": "assistant_question",
            "subject": "api timeout",
            "status": "active",
        },
    }

    resolution = resolve_referent(state)["referent_resolution"]

    assert resolution["resolved"] is True
    assert resolution["source_focus_id"] == "focus-2"


def test_greeting_maps_to_casual_reply():
    act = classify_text("hi")
    state = {
        "user_act": act,
        "referent_resolution": {
            "resolved": False,
            "referent_kind": "none",
            "referent_subject": "",
            "source_focus_id": "",
            "reason": "not needed",
        },
    }

    plan = plan_response_node(state)["response_plan"]
    assert plan["mode"] == "casual_reply"


def test_summary_request_maps_to_summary_mode():
    act = classify_text("summarize what i asked")
    state = {
        "user_act": act,
        "referent_resolution": {
            "resolved": False,
            "referent_kind": "none",
            "referent_subject": "",
            "source_focus_id": "",
            "reason": "not needed",
        },
    }

    plan = plan_response_node(state)["response_plan"]
    assert plan["mode"] == "summarize_user_queries"


def test_question_act_does_not_create_new_focus_by_default():
    state = {
        "response_plan": {
            "mode": "answer",
            "needs_clarification": False,
            "should_render": True,
        },
        "referent_resolution": {
            "resolved": False,
            "referent_kind": "none",
            "referent_subject": "",
            "source_focus_id": "",
            "reason": "not needed",
        },
    }

    assistant_act = declare_assistant_act(state)["assistant_act"]
    updated = update_focus_from_declared_act({"assistant_act": assistant_act, "iteration": 1})

    assert assistant_act["act_type"] == "statement"
    assert updated == {}


def test_declared_question_creates_active_focus():
    updated = update_focus_from_declared_act(
        {
            "assistant_act": {
                "act_type": "question",
                "subject": "missing referent clarification",
                "expires_after_turns": 2,
            },
            "iteration": 3,
            "passages": [
                {
                    "passage_id": "passage-1",
                    "kind": "response",
                    "observed_at": "2025-01-01T00:00:00+00:00",
                    "sequence_index": 0,
                    "source_message_ids": ["msg-1"],
                    "canonical_text": "ai: What are you referring to?",
                    "metadata": {},
                }
            ],
        }
    )

    focus = updated["active_focus"]
    assert focus["status"] == "active"
    assert focus["kind"] == "assistant_question"
    assert focus["created_turn"] == 3


def test_focus_expires_after_turn_limit():
    state = {
        "iteration": 8,
        "active_focus": {
            "focus_id": "focus-5",
            "kind": "assistant_question",
            "subject": "direction repair",
            "created_turn": 5,
            "expires_after_turns": 2,
            "status": "active",
        },
    }

    result = expire_focus(state)
    assert result["active_focus"]["status"] == "expired"
