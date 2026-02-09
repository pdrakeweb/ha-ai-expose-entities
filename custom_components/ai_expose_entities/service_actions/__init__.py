"""Service actions package for ai_expose_entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.ai_expose_entities.const import CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING, DOMAIN, LOGGER
from custom_components.ai_expose_entities.service_actions.recommendation import (
    async_handle_apply_decisions,
    async_handle_run_recommendation,
)
from homeassistant.core import ServiceCall, SupportsResponse

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceResponse

# Service action names - only used within service_actions module
SERVICE_APPLY_DECISIONS = "apply_decisions"
SERVICE_RUN_RECOMMENDATION = "run_recommendation"


async def async_setup_services(hass: HomeAssistant) -> None:
    """
    Register services for the integration.

    Services are registered at component level (in async_setup) rather than
    per config entry. This is a Silver Quality Scale requirement and ensures:
    - Service validation works correctly
    - Services are available even without config entries
    - Helpful error messages are provided

    Service handlers iterate over all config entries to find the relevant one.
    """

    async def handle_run_recommendation(call: ServiceCall) -> ServiceResponse | None:
        """Handle the run_recommendation service call."""
        # Find all config entries for this domain
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            LOGGER.warning("No config entries found for %s", DOMAIN)
            return None

        # Use first entry (or implement logic to select specific entry)
        entry = entries[0]
        if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug(
                "Service run_recommendation called with data: %s",
                call.data,
            )
        return await async_handle_run_recommendation(hass, entry, call)

    async def handle_apply_decisions(call: ServiceCall) -> ServiceResponse | None:
        """Handle the apply_decisions service call."""
        # Find all config entries for this domain
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            LOGGER.warning("No config entries found for %s", DOMAIN)
            return None

        # Use first entry (or implement logic to select specific entry)
        entry = entries[0]
        if entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug(
                "Service apply_decisions called with data: %s",
                call.data,
            )
        return await async_handle_apply_decisions(hass, entry, call)

    # Register services (only once at component level)
    if not hass.services.has_service(DOMAIN, SERVICE_RUN_RECOMMENDATION):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RUN_RECOMMENDATION,
            handle_run_recommendation,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_APPLY_DECISIONS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_APPLY_DECISIONS,
            handle_apply_decisions,
            supports_response=SupportsResponse.OPTIONAL,
        )

    LOGGER.debug("Services registered for %s", DOMAIN)
