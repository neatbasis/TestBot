from __future__ import annotations


def build_canonical_history_transcript() -> list[dict[str, str]]:
    return [
        {
            "role": "user",
            "content": "Please keep answers brief and only use memory-backed facts.",
        },
        {
            "role": "assistant",
            "content": "Understood. I will cite memory cards when possible.",
        },
        {
            "role": "user",
            "content": "What did I say about the garage door sensor yesterday?",
        },
        {
            "role": "assistant",
            "content": "You mentioned it was offline around 9 PM.",
        },
        {
            "role": "user",
            "content": "For the summary, include Home Assistant and Zigbee status exactly.",
        },
        {
            "role": "assistant",
            "content": "Got it. I will include Home Assistant and Zigbee status.",
        },
        {
            "role": "user",
            "content": "Can you also track Battery levels for Kitchen and Hallway?",
        },
    ]
