"""WebSocket API for ai_expose_entities."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from custom_components.ai_expose_entities.api import AIExposeEntitiesAIClientError
from custom_components.ai_expose_entities.const import (
    CONF_AGENT_ID,
    CONF_ENABLE_DEBUGGING,
    CONF_RECOMMENDATION_AGGRESSIVENESS,
    DEFAULT_ENABLE_DEBUGGING,
    DEFAULT_RECOMMENDATION_AGGRESSIVENESS,
    DOMAIN,
    LOGGER,
    RECOMMENDATION_AGGRESSIVENESS_LEVELS,
)
from custom_components.ai_expose_entities.data import AIExposeEntitiesConfigEntry
from custom_components.ai_expose_entities.utils import RecommendationState, build_entity_catalog
from homeassistant.components import websocket_api
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.const import ERR_INVALID_FORMAT, ERR_NOT_FOUND, ERR_UNKNOWN_ERROR
from homeassistant.components.websocket_api.decorators import require_admin, websocket_command
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv


def async_register_websocket(hass: HomeAssistant) -> None:
    """Register WebSocket commands for the integration."""
    websocket_api.async_register_command(hass, ws_get_state)
    websocket_api.async_register_command(hass, ws_run_recommendation)
    websocket_api.async_register_command(hass, ws_apply_decisions)
    websocket_api.async_register_command(hass, ws_clear_suggestions)


def _get_entry(hass: HomeAssistant) -> AIExposeEntitiesConfigEntry | None:
    """Get the first config entry for the integration."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None
    return entries[0]


@websocket_command(
    {
        vol.Required("type"): "ai_expose_entities/get_state",
    }
)
@require_admin
@callback
def ws_get_state(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the current recommendation state."""
    entry = _get_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "No config entry")
        return

    if not hasattr(entry, "runtime_data") or entry.runtime_data is None:
        connection.send_error(
            msg["id"], ERR_UNKNOWN_ERROR, "Integration is still initializing. Please wait and try again."
        )
        return
    state = entry.runtime_data.state
    if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
        LOGGER.debug(
            "WebSocket get_state requested: pending=%d approved=%d denied=%d",
            len(state.pending),
            len(state.approved),
            len(state.denied),
        )
    connection.send_result(msg["id"], _serialize_state(state, _build_state_meta(hass, entry)))


@websocket_command(
    {
        vol.Required("type"): "ai_expose_entities/run_recommendation",
        vol.Optional(
            CONF_RECOMMENDATION_AGGRESSIVENESS,
            default=DEFAULT_RECOMMENDATION_AGGRESSIVENESS,
        ): vol.In(RECOMMENDATION_AGGRESSIVENESS_LEVELS),
    }
)
@require_admin
@callback
def ws_run_recommendation(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Trigger an AI recommendation run."""
    entry = _get_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "No config entry")
        return

    async def _run() -> None:
        try:
            if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
                LOGGER.debug("WebSocket run_recommendation requested")
            recommendations = await entry.runtime_data.coordinator.async_run_recommendation(
                aggressiveness=msg[CONF_RECOMMENDATION_AGGRESSIVENESS],
            )
        except (AIExposeEntitiesAIClientError, HomeAssistantError) as err:
            LOGGER.exception("Recommendation run failed")
            connection.send_error(msg["id"], ERR_UNKNOWN_ERROR, str(err))
            return

        if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug(
                "WebSocket recommendation complete: pending=%d",
                len(entry.runtime_data.state.pending),
            )

        response = _serialize_state(entry.runtime_data.state, _build_state_meta(hass, entry))
        if not recommendations:
            response["message"] = "No remaining entities to consider."
        else:
            response["message"] = "Recommendations generated successfully."
        connection.send_result(
            msg["id"],
            response,
        )

    hass.async_create_task(_run())


@websocket_command(
    {
        vol.Required("type"): "ai_expose_entities/apply_decisions",
        vol.Optional("approved", default=[]): [cv.entity_id],
        vol.Optional("denied", default=[]): [cv.entity_id],
    }
)
@require_admin
@callback
def ws_apply_decisions(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Apply approval/denial decisions from the UI."""
    entry = _get_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "No config entry")
        return

    approved = set(msg["approved"])
    denied = set(msg["denied"])
    overlap = approved & denied
    if overlap:
        connection.send_error(
            msg["id"],
            ERR_INVALID_FORMAT,
            f"Overlapping entity_ids: {sorted(overlap)}",
        )
        return

    entry.runtime_data.coordinator.async_apply_decisions(
        approved=approved,
        denied=denied,
    )
    if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
        LOGGER.debug(
            "WebSocket decisions applied: approved=%s denied=%s pending=%d",
            sorted(approved),
            sorted(denied),
            len(entry.runtime_data.state.pending),
        )
    connection.send_result(
        msg["id"],
        _serialize_state(entry.runtime_data.state, _build_state_meta(hass, entry)),
    )


@websocket_command(
    {
        vol.Required("type"): "ai_expose_entities/clear_suggestions",
        vol.Optional("entity_ids", default=[]): [cv.entity_id],
    }
)
@require_admin
@callback
def ws_clear_suggestions(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Clear pending recommendations without changing exposure."""
    entry = _get_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "No config entry")
        return

    entity_ids = set(msg["entity_ids"])
    entry.runtime_data.coordinator.async_clear_pending(
        entity_ids=entity_ids if entity_ids else None,
    )
    if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
        LOGGER.debug(
            "WebSocket suggestions cleared: pending=%d",
            len(entry.runtime_data.state.pending),
        )
    connection.send_result(
        msg["id"],
        _serialize_state(entry.runtime_data.state, _build_state_meta(hass, entry)),
    )


def _build_state_meta(hass: HomeAssistant, entry: AIExposeEntitiesConfigEntry) -> dict[str, Any]:
    """Build metadata for frontend status display."""
    state = entry.runtime_data.state
    include_self = entry.runtime_data.test_entities is not None
    # Determine sample size from config/options
    sample_size = entry.options.get("entity_sample_size", 500)
    try:
        sample_size = int(sample_size)
    except (ValueError, TypeError):
        sample_size = 500
    if sample_size < 1:
        sample_size = 500
    catalog = build_entity_catalog(hass, state.denied, include_self=include_self)
    agent_id = entry.options.get(CONF_AGENT_ID)
    # The number of entities actually considered (after sampling)
    considered_count = min(len(catalog), sample_size)
    total_count = len(catalog)
    return {
        "catalog_size": considered_count,
        "catalog_total": total_count,
        "agent_id": agent_id,
    }


def _serialize_state(state: RecommendationState, meta: dict[str, Any]) -> dict[str, Any]:
    """Serialize recommendation state for WebSocket responses."""
    return {
        "pending": [entry.as_dict() for entry in state.pending.values()],
        "approved": sorted(state.approved),
        "denied": sorted(state.denied),
        "last_run": state.last_run,
        "meta": meta,
    }
