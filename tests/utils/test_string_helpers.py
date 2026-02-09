"""Tests for string helper utilities."""

from __future__ import annotations

import pytest

from custom_components.ai_expose_entities.utils.string_helpers import sanitize_string, slugify_name, truncate_string


@pytest.mark.unit
def test_slugify_name() -> None:
    """slugify_name should normalize names to snake_case."""
    assert slugify_name("My Device Name") == "my_device_name"
    assert slugify_name("Kitchen-Lamp!") == "kitchen_lamp"


@pytest.mark.unit
def test_truncate_string() -> None:
    """truncate_string should shorten long text and keep short text unchanged."""
    assert truncate_string("short", max_length=10) == "short"
    assert truncate_string("This is a long string", max_length=10) == "This is..."


@pytest.mark.unit
def test_sanitize_string() -> None:
    """sanitize_string should remove unsafe characters."""
    assert sanitize_string("My<>Device/Name") == "MyDeviceName"
    assert sanitize_string("Safe_Name") == "Safe_Name"
