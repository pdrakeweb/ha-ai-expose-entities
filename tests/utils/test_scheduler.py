"""Tests for scheduling helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.ai_expose_entities.const import DEFAULT_SCHEDULE_TIME
from custom_components.ai_expose_entities.utils.scheduler import (
    ScheduleSettings,
    async_schedule_daily_run,
    get_schedule_settings,
)


@pytest.mark.unit
def test_get_schedule_settings_defaults() -> None:
    """Default schedule settings should use configured defaults."""
    settings = get_schedule_settings({})

    assert settings.enabled is False
    assert settings.hour == DEFAULT_SCHEDULE_TIME.hour
    assert settings.minute == DEFAULT_SCHEDULE_TIME.minute


@pytest.mark.unit
def test_get_schedule_settings_custom_time() -> None:
    """Custom schedule times should be parsed."""
    settings = get_schedule_settings({"schedule_enabled": True, "schedule_time": "05:30:00"})

    assert settings.enabled is True
    assert settings.hour == 5
    assert settings.minute == 30


@pytest.mark.unit
async def test_async_schedule_daily_run_disabled(hass) -> None:
    """Disabled schedule should not register a listener."""
    coordinator = SimpleNamespace(
        config_entry=SimpleNamespace(options={}),
        async_run_recommendation=AsyncMock(),
    )
    settings = ScheduleSettings(enabled=False, hour=1, minute=0)

    assert async_schedule_daily_run(hass, coordinator, settings) is None


@pytest.mark.unit
async def test_async_schedule_daily_run_triggers(hass) -> None:
    """Enabled schedule should trigger the coordinator callback."""
    coordinator = SimpleNamespace(
        config_entry=SimpleNamespace(options={}),
        async_run_recommendation=AsyncMock(),
    )
    settings = ScheduleSettings(enabled=True, hour=12, minute=0)

    callback_holder: dict[str, object] = {}

    def _track(_hass, action, *, hour: int, minute: int):
        callback_holder["callback"] = action
        return lambda: None

    with patch(
        "custom_components.ai_expose_entities.utils.scheduler.async_track_time_change",
        side_effect=_track,
    ):
        remove = async_schedule_daily_run(hass, coordinator, settings)
        assert remove is not None

    callback = callback_holder.get("callback")
    assert callable(callback)
    callback()
    await hass.async_block_till_done()

    coordinator.async_run_recommendation.assert_awaited_once()
