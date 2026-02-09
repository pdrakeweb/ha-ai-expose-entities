"""Tests for Assist exposure helpers."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from custom_components.ai_expose_entities.utils.assist_exposure import ASSISTANT_ID, set_assist_exposure


@pytest.mark.unit
def test_set_assist_exposure(hass) -> None:
    """set_assist_exposure should call async_expose_entity for each entity."""
    with patch("homeassistant.components.homeassistant.exposed_entities.async_expose_entity") as expose:
        set_assist_exposure(hass, {"light.kitchen", "switch.garage"}, should_expose=True)

    expose.assert_any_call(hass, ASSISTANT_ID, "light.kitchen", True)
    expose.assert_any_call(hass, ASSISTANT_ID, "switch.garage", True)
    assert expose.call_count == 2
