"""Service action handlers for AI recommendations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.ai_expose_entities.const import CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING, LOGGER
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from custom_components.ai_expose_entities.data import AIExposeEntitiesConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse


async def async_handle_run_recommendation(
    hass: HomeAssistant,
    entry: AIExposeEntitiesConfigEntry,
    call: ServiceCall,
) -> ServiceResponse:
    """Run the AI recommendation flow."""
    try:
        if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug("Starting recommendation run via service")
        recommendations = await entry.runtime_data.coordinator.async_run_recommendation()
    except Exception as err:
        raise HomeAssistantError(f"Recommendation failed: {err}") from err

    if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
        LOGGER.debug(
            "Recommendation run complete: recommended=%d pending=%d",
            len(recommendations),
            len(entry.runtime_data.state.pending),
        )

    return {
        "status": "success",
        "timestamp": dt_util.utcnow().isoformat(),
        "recommendation_count": len(recommendations),
        "pending_count": len(entry.runtime_data.state.pending),
    }


async def async_handle_apply_decisions(
    hass: HomeAssistant,
    entry: AIExposeEntitiesConfigEntry,
    call: ServiceCall,
) -> ServiceResponse:
    """Apply approval/denial decisions to recommendations."""
    approved_list = call.data.get("approved_entity_ids", [])
    denied_list = call.data.get("denied_entity_ids", [])

    if not isinstance(approved_list, list) or not isinstance(denied_list, list):
        raise ServiceValidationError("approved_entity_ids and denied_entity_ids must be lists")

    approved = {entity_id for entity_id in approved_list if isinstance(entity_id, str)}
    denied = {entity_id for entity_id in denied_list if isinstance(entity_id, str)}

    if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
        LOGGER.debug(
            "Applying decisions via service: approved=%s denied=%s",
            sorted(approved),
            sorted(denied),
        )

    overlap = approved & denied
    if overlap:
        raise ServiceValidationError(f"Entities cannot be both approved and denied: {sorted(overlap)}")

    entry.runtime_data.coordinator.async_apply_decisions(
        approved=approved,
        denied=denied,
    )

    if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
        LOGGER.debug(
            "Decisions applied: approved=%d denied=%d pending=%d",
            len(approved),
            len(denied),
            len(entry.runtime_data.state.pending),
        )

    return {
        "status": "success",
        "timestamp": dt_util.utcnow().isoformat(),
        "approved_count": len(approved),
        "denied_count": len(denied),
        "pending_count": len(entry.runtime_data.state.pending),
    }
