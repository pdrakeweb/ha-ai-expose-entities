"""Tests for coordinator error handling utilities."""

from __future__ import annotations

from datetime import timedelta
import logging

import pytest

from custom_components.ai_expose_entities.coordinator.error_handling import (
    calculate_backoff_delay,
    handle_partial_data,
    log_update_failure,
    should_retry_update,
)


@pytest.mark.unit
def test_should_retry_update() -> None:
    """should_retry_update should stop after max retries."""
    assert should_retry_update(Exception("fail"), 0) is True
    assert should_retry_update(Exception("fail"), 2) is True
    assert should_retry_update(Exception("fail"), 3) is False


@pytest.mark.unit
def test_calculate_backoff_delay() -> None:
    """calculate_backoff_delay should use exponential backoff with max cap."""
    assert calculate_backoff_delay(0) == timedelta(seconds=1)
    assert calculate_backoff_delay(2) == timedelta(seconds=4)
    assert calculate_backoff_delay(10) == timedelta(seconds=60)


@pytest.mark.unit
def test_handle_partial_data(caplog) -> None:
    """handle_partial_data should return original data."""
    caplog.set_level(logging.DEBUG)
    data = {"sensor": 1}
    result = handle_partial_data(data, Exception("timeout"))

    assert result == data
    assert "Handling partial data" in caplog.text


@pytest.mark.unit
def test_log_update_failure(caplog) -> None:
    """log_update_failure should log warning then error."""
    caplog.set_level(logging.WARNING)
    log_update_failure(Exception("fail"), 0, 3)
    assert "Update failed (attempt 1/3)" in caplog.text

    caplog.clear()
    log_update_failure(Exception("fail"), 2, 3)
    assert "Update failed after 3 attempts" in caplog.text
