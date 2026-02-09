"""Helpers for AI Task selector options."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

LOGGER = logging.getLogger(__name__)


def get_ai_task_options(hass: HomeAssistant) -> list[selector.SelectOptionDict]:
    """Build select options for available AI Tasks."""

    options: list[selector.SelectOptionDict] = []

    ai_task_data = hass.data.get("ai_task")
    LOGGER.debug("AI Task selector: hass.data['ai_task'] type=%s, value=%r", type(ai_task_data), ai_task_data)
    if not ai_task_data:
        LOGGER.debug("AI Task selector: ai_task_data missing from hass.data")
        return []

    # Expose all ai_task entities
    options = []
    if hasattr(ai_task_data, "entities"):
        for entity in ai_task_data.entities:
            entity_id = getattr(entity, "entity_id", None)
            name = getattr(entity, "name", None)
            if isinstance(entity_id, str):
                label = name if isinstance(name, str) else entity_id
                options.append(
                    {
                        "value": entity_id,
                        "label": label,
                    }
                )
        LOGGER.debug("AI Task selector: found %d ai_task entities: %r", len(options), [o["value"] for o in options])
    else:
        LOGGER.debug("AI Task selector: ai_task_data has no 'entities' attribute")
    return sorted(options, key=lambda option: option["label"].lower())


__all__ = ["get_ai_task_options"]
