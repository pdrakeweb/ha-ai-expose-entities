"""Tests for coordinator listener utilities."""

from __future__ import annotations

import logging

import pytest

from custom_components.ai_expose_entities.coordinator.listeners import (
    create_entity_callback,
    should_notify_entity,
    track_update_performance,
)


@pytest.mark.unit
async def test_create_entity_callback_logs_exception(caplog) -> None:
    """create_entity_callback should swallow exceptions and log them."""
    caplog.set_level(logging.ERROR)

    async def _bad_callback() -> None:
        raise ValueError("boom")

    wrapped = create_entity_callback("sensor.test", _bad_callback)
    await wrapped()

    assert "Error in callback for sensor.test" in caplog.text


@pytest.mark.unit
def test_should_notify_entity() -> None:
    """should_notify_entity should detect meaningful changes."""
    assert should_notify_entity({}, {}, "temperature") is False
    assert should_notify_entity({}, {"temperature": 1}, "temperature") is True
    assert should_notify_entity({"temperature": 1}, {}, "temperature") is True
    assert should_notify_entity({"temperature": 1}, {"temperature": 1}, "temperature") is False
    assert should_notify_entity({"temperature": 1}, {"temperature": 2}, "temperature") is True


@pytest.mark.unit
def test_track_update_performance(caplog) -> None:
    """track_update_performance should log at expected levels."""
    caplog.set_level(logging.DEBUG)
    track_update_performance(0.1)
    assert "Coordinator update took" in caplog.text

    caplog.clear()
    track_update_performance(6.0)
    assert "slow" in caplog.text

    caplog.clear()
    track_update_performance(11.0)
    assert "very slow" in caplog.text
