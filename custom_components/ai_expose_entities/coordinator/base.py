"""
Core DataUpdateCoordinator implementation for ai_expose_entities.

This module contains the main coordinator class that manages data fetching
and updates for all entities in the integration. It handles refresh cycles,
error handling, and triggers reauthentication when needed.

For more information on coordinators:
https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
"""

from __future__ import annotations

from datetime import timedelta
from logging import Logger
from typing import TYPE_CHECKING, Any

from custom_components.ai_expose_entities.const import (
    CONF_ENABLE_DEBUGGING,
    DEFAULT_ENABLE_DEBUGGING,
    DEFAULT_RECOMMENDATION_AGGRESSIVENESS,
    LOGGER,
)
from custom_components.ai_expose_entities.utils import RecommendationEntry, build_entity_catalog
from custom_components.ai_expose_entities.utils.assist_exposure import ASSISTANT_ID, set_assist_exposure
from homeassistant.components.homeassistant import exposed_entities
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from custom_components.ai_expose_entities.data import AIExposeEntitiesConfigEntry
    from homeassistant.core import HomeAssistant


class AIExposeEntitiesDataUpdateCoordinator(DataUpdateCoordinator[Any]):
    """
    Class to manage fetching data from the API.

    This coordinator handles all data fetching for the integration and distributes
    updates to all entities. It manages:
    - Periodic data updates based on update_interval
    - Error handling and recovery
    - Authentication failure detection and reauthentication triggers
    - Data distribution to all entities
    - Context-based data fetching (only fetch data for active entities)

    For more information:
    https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities

    Attributes:
        config_entry: The config entry for this integration instance.
    """

    config_entry: AIExposeEntitiesConfigEntry

    def __init__(
        self,
        *,
        hass: HomeAssistant,
        logger: Logger,
        name: str,
        config_entry: AIExposeEntitiesConfigEntry,
        update_interval: timedelta | None,
        always_update: bool,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=logger,
            name=name,
            update_interval=update_interval,
            always_update=always_update,
        )
        self.config_entry = config_entry
        self._entity_data: dict[str, Any] = {}

    def set_entity_data(self, data: dict[str, Any]) -> None:
        """Set the data snapshot used by entities."""
        self._entity_data = data

    async def _async_setup(self) -> None:
        """
        Set up the coordinator.

        This method is called automatically during async_config_entry_first_refresh()
        and is the ideal place for one-time initialization tasks such as:
        - Loading device information
        - Setting up event listeners
        - Initializing caches

        This runs before the first data fetch, ensuring any required setup
        is complete before entities start requesting data.
        """
        # Example: Fetch device info once at startup
        # device_info = await self.config_entry.runtime_data.client.get_device_info()
        # self._device_id = device_info["id"]
        LOGGER.debug("Coordinator setup complete for %s", self.config_entry.entry_id)

    async def _async_update_data(self) -> dict[str, Any]:
        """Return the cached entity data."""
        return self._entity_data

    async def async_run_recommendation(
        self,
        *,
        aggressiveness: str | None = None,
    ) -> list[RecommendationEntry]:
        """Run the AI recommendation flow and update state."""
        state = self.config_entry.runtime_data.state
        if state.approved:
            no_longer_exposed = {
                entity_id
                for entity_id in state.approved
                if not exposed_entities.async_should_expose(self.hass, ASSISTANT_ID, entity_id)
            }
            if no_longer_exposed:
                if self.config_entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
                    LOGGER.debug(
                        "Removing approvals for entities no longer exposed: %s",
                        sorted(no_longer_exposed),
                    )
                state.approved.difference_update(no_longer_exposed)
        include_self = self.config_entry.runtime_data.test_entities is not None
        catalog = build_entity_catalog(self.hass, state.denied, include_self=include_self)
        aggressiveness_value = aggressiveness or DEFAULT_RECOMMENDATION_AGGRESSIVENESS

        if self.config_entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug(
                "Running recommendation: catalog_size=%d denied=%d aggressiveness=%s",
                len(catalog),
                len(state.denied),
                aggressiveness_value,
            )

        recommendations = await self.config_entry.runtime_data.client.async_recommend_entities(
            catalog,
            language=self.hass.config.language,
            aggressiveness=aggressiveness_value,
        )

        approved = state.approved
        denied = state.denied
        for entry in recommendations:
            if entry.entity_id in approved or entry.entity_id in denied:
                continue
            if entry.disabled or entry.hidden:
                continue
            state.pending[entry.entity_id] = entry

        state.last_run = dt_util.utcnow().isoformat()
        self.config_entry.runtime_data.store.async_schedule_save(state)
        self.async_set_updated_data(self._entity_data)

        if self.config_entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug(
                "Recommendation updated: recommended=%d pending=%d last_run=%s",
                len(recommendations),
                len(state.pending),
                state.last_run,
            )
        return recommendations

    def async_apply_decisions(
        self,
        *,
        approved: set[str],
        denied: set[str],
    ) -> None:
        """Apply approval and denial decisions and update exposure."""
        state = self.config_entry.runtime_data.state

        if self.config_entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug(
                "Applying decisions: approved=%s denied=%s",
                sorted(approved),
                sorted(denied),
            )

        for entity_id in approved:
            if entity_id in state.pending:
                state.pending.pop(entity_id, None)
            state.approved.add(entity_id)
            state.denied.discard(entity_id)

        for entity_id in denied:
            if entity_id in state.pending:
                state.pending.pop(entity_id, None)
            state.denied.add(entity_id)
            state.approved.discard(entity_id)

        if approved:
            set_assist_exposure(self.hass, approved, should_expose=True)
        if denied:
            set_assist_exposure(self.hass, denied, should_expose=False)

        self.config_entry.runtime_data.store.async_schedule_save(state)
        self.async_set_updated_data(self._entity_data)

        if self.config_entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug(
                "Decisions applied: approved=%d denied=%d pending=%d",
                len(approved),
                len(denied),
                len(state.pending),
            )

    def async_clear_pending(self, *, entity_ids: set[str] | None = None) -> None:
        """Clear pending recommendations without changing exposure."""
        state = self.config_entry.runtime_data.state
        if not state.pending:
            return

        if entity_ids is None:
            pending_count = len(state.pending)
            state.pending.clear()
        else:
            if not entity_ids:
                return
            pending_count = 0
            for entity_id in entity_ids:
                if entity_id in state.pending:
                    state.pending.pop(entity_id, None)
                    pending_count += 1

        if pending_count == 0:
            return

        self.config_entry.runtime_data.store.async_schedule_save(state)
        self.async_set_updated_data(self._entity_data)

        if self.config_entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug("Cleared pending recommendations: count=%d", pending_count)
