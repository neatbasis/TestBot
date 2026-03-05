import json
from pathlib import Path

from testbot.history_packer import labeled_history_claims, pack_chat_history, render_packed_history


FIXTURE_PATH = Path("tests/fixtures/history_transcript_fixture.json")


def test_pack_chat_history_exact_structure_from_fixture() -> None:
    transcript = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    packed = pack_chat_history(transcript, last_n_user_turns=3, last_n_assistant_turns=3)

    assert packed.to_dict() == {
        "last_user_turns": [
            "What did I say about the garage door sensor yesterday?",
            "For the summary, include Home Assistant and Zigbee status exactly.",
            "Can you also track Battery levels for Kitchen and Hallway?",
        ],
        "last_assistant_turns": [
            "Understood. I will cite memory cards when possible.",
            "You mentioned it was offline around 9 PM.",
            "Got it. I will include Home Assistant and Zigbee status.",
        ],
        "open_questions": [
            "Can you also track Battery levels for Kitchen and Hallway?",
        ],
        "topic_entity_hints": [
            "assistant",
            "home",
            "include",
            "status",
            "will",
            "zigbee",
            "about",
            "also",
        ],
        "constraints": [
            "Please keep answers brief and only use memory-backed facts.",
            "For the summary, include Home Assistant and Zigbee status exactly.",
        ],
    }


def test_pack_chat_history_is_deterministic_for_same_transcript() -> None:
    transcript = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    first = pack_chat_history(transcript)
    second = pack_chat_history(transcript)

    assert first.to_dict() == second.to_dict()
    assert render_packed_history(first) == render_packed_history(second)
    assert labeled_history_claims(first) == labeled_history_claims(second)


def test_extract_constraints_true_positives() -> None:
    transcript = [
        {"role": "user", "content": "You must include citations."},
        {"role": "user", "content": "Do not guess."},
    ]

    packed = pack_chat_history(transcript)

    assert packed.constraints == ["You must include citations.", "Do not guess."]


def test_extract_constraints_avoids_substring_false_positives() -> None:
    transcript = [
        {"role": "user", "content": "I have shoulder pain."},
        {"role": "user", "content": "Mustard is in the fridge."},
    ]

    packed = pack_chat_history(transcript)

    assert packed.constraints == []


def test_extract_constraints_handles_punctuation_and_case_variants() -> None:
    transcript = [
        {"role": "user", "content": "DON’T improvise."},
        {"role": "user", "content": "Use AT LEAST two examples."},
    ]

    packed = pack_chat_history(transcript)

    assert packed.constraints == ["DON’T improvise.", "Use AT LEAST two examples."]
