"""Tests for config flow input sanitizers."""

from __future__ import annotations

import pytest

from custom_components.ai_expose_entities.config_flow_handler.validators import sanitize_username


@pytest.mark.unit
def test_sanitize_username() -> None:
    """sanitize_username should strip whitespace."""
    assert sanitize_username("  user  ") == "user"
    assert sanitize_username("user") == "user"
