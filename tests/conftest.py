"""Shared test fixtures for ai_expose_entities."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ai_expose_entities.const import DOMAIN


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data={}, options={})
