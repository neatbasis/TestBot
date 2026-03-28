from __future__ import annotations

from homeassistant_api import Client


def send_satellite_output(client: Client, entity_id: str, text: str) -> None:
    """Send text output to a Home Assistant Assist satellite entity."""
    client.trigger_service(
        "assist_satellite",
        "start_conversation",
        entity_id=entity_id,
        start_message=text,
        preannounce=False,
    )


__all__ = ["send_satellite_output"]
