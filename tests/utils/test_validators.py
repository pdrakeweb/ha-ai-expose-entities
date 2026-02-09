"""Tests for validation utilities."""

from __future__ import annotations

import pytest

from custom_components.ai_expose_entities.utils.validators import (
    is_valid_url,
    validate_api_response,
    validate_config_value,
)


@pytest.mark.unit
def test_validate_api_response() -> None:
    """validate_api_response should verify required fields."""
    assert validate_api_response({"title": "foo", "body": "bar"}) is True
    assert validate_api_response({"title": "foo"}) is False
    assert validate_api_response("bad") is False  # type: ignore[arg-type]


@pytest.mark.unit
def test_validate_config_value() -> None:
    """validate_config_value should apply type and bounds checks."""
    assert validate_config_value(5, int, min_val=1, max_val=10) is True
    assert validate_config_value(0, int, min_val=1) is False
    assert validate_config_value(11, int, max_val=10) is False
    assert validate_config_value("5", int) is False


@pytest.mark.unit
def test_is_valid_url() -> None:
    """is_valid_url should validate basic HTTP/HTTPS URLs."""
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("http://example.com") is True
    assert is_valid_url("ftp://example.com") is False
    assert is_valid_url("short") is False
