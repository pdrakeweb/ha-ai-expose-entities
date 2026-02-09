"""Tests for coordinator data processing helpers."""

from __future__ import annotations

import pytest

from custom_components.ai_expose_entities.coordinator.data_processing import (
    cache_computed_values,
    transform_api_data,
    validate_api_response,
)


@pytest.mark.unit
def test_validate_api_response_logs_warning(caplog) -> None:
    """validate_api_response should return False for non-dicts."""
    assert validate_api_response(["bad"]) is False
    assert "Invalid API response" in caplog.text


@pytest.mark.unit
def test_transform_api_data_invalid_input() -> None:
    """transform_api_data should return empty dict for invalid input."""
    assert transform_api_data(["bad"]) == {}


@pytest.mark.unit
def test_cache_computed_values_passthrough() -> None:
    """cache_computed_values should return original data for now."""
    data = {"value": 1}
    assert cache_computed_values(data) == data
