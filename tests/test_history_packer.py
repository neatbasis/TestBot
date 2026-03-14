from testbot.history_packer import labeled_history_claims, pack_chat_history, render_packed_history
from tests.helpers.history_transcripts import build_canonical_history_transcript


def test_pack_chat_history_canonical_transcript_structure() -> None:
    transcript = build_canonical_history_transcript()

    packed = pack_chat_history(transcript, last_n_user_turns=3, last_n_assistant_turns=3)

    assert packed.last_user_turns == [
        "What did I say about the garage door sensor yesterday?",
        "For the summary, include Home Assistant and Zigbee status exactly.",
        "Can you also track Battery levels for Kitchen and Hallway?",
    ]
    assert packed.last_assistant_turns == [
        "Understood. I will cite memory cards when possible.",
        "You mentioned it was offline around 9 PM.",
        "Got it. I will include Home Assistant and Zigbee status.",
    ]
    assert packed.constraints == [
        "Please keep answers brief and only use memory-backed facts. [derived_by=heuristic confidence=medium source=user_turn]",
        "For the summary, include Home Assistant and Zigbee status exactly. [derived_by=heuristic confidence=medium source=user_turn]",
    ]
    assert packed.open_questions == [
        "Can you also track Battery levels for Kitchen and Hallway? [derived_by=heuristic confidence=medium source=user_turn]",
    ]
    assert packed.topic_entity_hints == [
        "assistant [derived_by=heuristic confidence=low source=transcript_tokens]",
        "home [derived_by=heuristic confidence=low source=transcript_tokens]",
        "include [derived_by=heuristic confidence=low source=transcript_tokens]",
        "status [derived_by=heuristic confidence=low source=transcript_tokens]",
        "will [derived_by=heuristic confidence=low source=transcript_tokens]",
        "zigbee [derived_by=heuristic confidence=low source=transcript_tokens]",
        "about [derived_by=heuristic confidence=low source=transcript_tokens]",
        "also [derived_by=heuristic confidence=low source=transcript_tokens]",
    ]


def test_pack_chat_history_is_deterministic_for_same_transcript() -> None:
    transcript = build_canonical_history_transcript()

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

    assert packed.constraints == [
        "You must include citations. [derived_by=heuristic confidence=medium source=user_turn]",
        "Do not guess. [derived_by=heuristic confidence=medium source=user_turn]",
    ]


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

    assert packed.constraints == [
        "DON’T improvise. [derived_by=heuristic confidence=medium source=user_turn]",
        "Use AT LEAST two examples. [derived_by=heuristic confidence=medium source=user_turn]",
    ]


def test_labeled_history_claims_marks_history_as_optional_advisory() -> None:
    packed = pack_chat_history([
        {"role": "user", "content": "Must include Zigbee status exactly."},
        {"role": "user", "content": "Kitchen battery?"},
    ])

    claims = labeled_history_claims(packed)

    assert any(claim.startswith("CHAT_HISTORY_OPTIONAL: constraint=") for claim in claims)
    assert any("derived_by=heuristic" in claim for claim in claims)
    assert any(claim.endswith("advisory=true") for claim in claims if claim.startswith("INFERENCE:"))
