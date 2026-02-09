"""Assist exposure helpers for ai_expose_entities."""

from __future__ import annotations

from homeassistant.components.homeassistant import exposed_entities
from homeassistant.core import HomeAssistant

ASSISTANT_ID = "conversation"


def set_assist_exposure(
    hass: HomeAssistant,
    entity_ids: set[str],
    *,
    should_expose: bool,
) -> None:
    """Set Assist exposure for a set of entities."""
    for entity_id in entity_ids:
        exposed_entities.async_expose_entity(
            hass,
            ASSISTANT_ID,
            entity_id,
            should_expose,
        )
