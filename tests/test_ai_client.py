"""Tests for AI conversation client."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from custom_components.ai_expose_entities.api import AIExposeEntitiesAIClient, AIExposeEntitiesAIClientError
from custom_components.ai_expose_entities.utils import EntityCatalogItem
from homeassistant.components.conversation import ConversationInput, ConversationResult
from homeassistant.helpers.intent import IntentResponse


class FakeAgent:
    """Fake conversation agent for testing."""

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        response = IntentResponse(language=user_input.language)
        response.async_set_speech(
            json.dumps(
                {
                    "recommended": [
                        {
                            "entity_id": "light.kitchen",
                            "reason": "Frequently used",
                        }
                    ]
                }
            )
        )
        return ConversationResult(response=response)


@pytest.mark.unit
async def test_ai_client_recommendations(hass) -> None:
    """Test successful recommendation parsing."""
    client = AIExposeEntitiesAIClient(hass, agent_id="test_agent")
    catalog = [
        EntityCatalogItem(
            entity_id="light.kitchen",
            domain="light",
            integration="hue",
            name="Kitchen Light",
            original_name="Kitchen Light",
            device_name="Kitchen",
            device_id="device-1",
            disabled=False,
            disabled_by=None,
            hidden=False,
            entity_category=None,
        )
    ]

    with (
        patch("homeassistant.components.conversation.async_prepare_agent"),
        patch(
            "homeassistant.components.conversation.async_get_agent",
            return_value=FakeAgent(),
        ),
        patch(
            "homeassistant.core.ServiceRegistry.async_call",
            return_value={"data": {"recommended": [{"entity_id": "light.kitchen", "reason": "Frequently used"}]}},
        ),
    ):
        result = await client.async_recommend_entities(catalog, language="en")

    assert len(result) == 1
    assert result[0].entity_id == "light.kitchen"
    assert result[0].reason == "Frequently used"


@pytest.mark.unit
async def test_ai_client_invalid_response(hass) -> None:
    """Test invalid response handling."""
    client = AIExposeEntitiesAIClient(hass, agent_id="test_agent")
    catalog = []

    class BadAgent:
        async def async_process(self, user_input: ConversationInput) -> ConversationResult:
            response = IntentResponse(language=user_input.language)
            response.async_set_speech("not-json")
            return ConversationResult(response=response)

    with (
        patch("homeassistant.components.conversation.async_prepare_agent"),
        patch(
            "homeassistant.components.conversation.async_get_agent",
            return_value=BadAgent(),
        ),
        pytest.raises(AIExposeEntitiesAIClientError),
    ):
        await client.async_recommend_entities(catalog, language="en")
