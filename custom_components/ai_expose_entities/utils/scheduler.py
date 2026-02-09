"""Scheduling helpers for ai_expose_entities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import time
from typing import cast

from custom_components.ai_expose_entities.const import (
    CONF_ENABLE_DEBUGGING,
    CONF_SCHEDULE_ENABLED,
    CONF_SCHEDULE_TIME,
    DEFAULT_ENABLE_DEBUGGING,
    DEFAULT_SCHEDULE_ENABLED,
    DEFAULT_SCHEDULE_TIME,
    LOGGER,
)
from custom_components.ai_expose_entities.coordinator import AIExposeEntitiesDataUpdateCoordinator
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util


@dataclass(slots=True)
class ScheduleSettings:
    """Schedule settings for the daily AI run."""

    enabled: bool
    hour: int
    minute: int


def get_schedule_settings(options: Mapping[str, object]) -> ScheduleSettings:
    """Parse schedule settings from config entry options."""
    enabled = bool(options.get(CONF_SCHEDULE_ENABLED, DEFAULT_SCHEDULE_ENABLED))
    schedule_value = options.get(CONF_SCHEDULE_TIME, DEFAULT_SCHEDULE_TIME)
    schedule_time = _parse_time(cast(time | str, schedule_value))
    return ScheduleSettings(
        enabled=enabled,
        hour=schedule_time.hour,
        minute=schedule_time.minute,
    )


def async_schedule_daily_run(
    hass: HomeAssistant,
    coordinator: AIExposeEntitiesDataUpdateCoordinator,
    settings: ScheduleSettings,
) -> CALLBACK_TYPE | None:
    """Schedule daily AI recommendations."""
    if not settings.enabled:
        return None

    @callback
    def _handle_time(_: object | None = None) -> None:
        if coordinator.config_entry.options.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING):
            LOGGER.debug("Scheduled recommendation run triggered")
        hass.async_create_task(coordinator.async_run_recommendation())

    LOGGER.debug(
        "Scheduling daily recommendation run at %02d:%02d",
        settings.hour,
        settings.minute,
    )
    return async_track_time_change(
        hass,
        _handle_time,
        hour=settings.hour,
        minute=settings.minute,
    )


def _parse_time(value: time | str) -> time:
    """Parse a time selector value into a time object."""
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        parsed = dt_util.parse_time(value)
        if parsed:
            return parsed
    return DEFAULT_SCHEDULE_TIME
