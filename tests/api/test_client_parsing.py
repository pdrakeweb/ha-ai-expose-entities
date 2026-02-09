"""Tests for AI client parsing and prompt behavior."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from custom_components.ai_expose_entities.api import AIExposeEntitiesAIClient, AIExposeEntitiesAIClientError
from custom_components.ai_expose_entities.utils import EntityCatalogItem
from homeassistant.components.conversation import ConversationInput, ConversationResult
from homeassistant.helpers.intent import IntentResponse


class RecordingAgent:
    """Recording agent that stores the last input."""

    def __init__(self, speech: Any) -> None:
        self._speech = speech
        self.last_input: ConversationInput | None = None

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        self.last_input = user_input
        response = IntentResponse(language=user_input.language)
        response.speech = self._speech
        return ConversationResult(response=response)


def _catalog() -> list[EntityCatalogItem]:
    return [
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
        ),
        EntityCatalogItem(
            entity_id="sensor.temp",
            domain="sensor",
            integration="demo",
            name="Temperature",
            original_name="Temperature",
            device_name=None,
            device_id=None,
            disabled=False,
            disabled_by=None,
            hidden=False,
            entity_category=None,
        ),
    ]


@pytest.mark.unit
async def test_ai_client_parses_grouped_response(hass) -> None:
    """Ensure grouped responses produce recommendation entries."""
    payload = {
        "integration_overview": {"hue": "Lighting overview"},
        "groups": [
            {
                "name": "Lighting",
                "reason": "Common voice control",
                "entities": [
                    {
                        "entity_id": "light.kitchen",
                        "reason": "Frequently used",
                    }
                ],
            }
        ],
    }
    agent = RecordingAgent(json.dumps(payload))
    client = AIExposeEntitiesAIClient(hass, agent_id="test_agent")

    with (
        patch("homeassistant.components.conversation.async_prepare_agent"),
        patch("homeassistant.components.conversation.async_get_agent", return_value=agent),
    ):
        results = await client.async_recommend_entities(_catalog(), language="en")

    assert len(results) == 1
    result = results[0]
    assert result.entity_id == "light.kitchen"
    assert result.group_name == "Lighting"
    assert result.group_reason == "Common voice control"
    assert result.integration_overview == "Lighting overview"


@pytest.mark.unit
async def test_ai_client_parses_fenced_json(hass) -> None:
    """Ensure code-fenced JSON is parsed correctly."""
    payload = {"recommended": [{"entity_id": "light.kitchen", "reason": "Daily use"}]}
    speech = f"```json\n{json.dumps(payload)}\n```"
    agent = RecordingAgent(speech)
    client = AIExposeEntitiesAIClient(hass, agent_id="test_agent")

    with (
        patch("homeassistant.components.conversation.async_prepare_agent"),
        patch("homeassistant.components.conversation.async_get_agent", return_value=agent),
    ):
        results = await client.async_recommend_entities(_catalog(), language="en")

    assert [entry.entity_id for entry in results] == ["light.kitchen"]


@pytest.mark.unit
async def test_ai_client_extracts_json_with_prefix(hass) -> None:
    """Ensure JSON is extracted when extra text surrounds it."""
    payload = {"recommended": [{"entity_id": "sensor.temp", "reason": "Useful"}]}
    speech = f"Sure!\n{json.dumps(payload)}\nThanks!"
    agent = RecordingAgent([speech])
    client = AIExposeEntitiesAIClient(hass, agent_id="test_agent")

    with (
        patch("homeassistant.components.conversation.async_prepare_agent"),
        patch("homeassistant.components.conversation.async_get_agent", return_value=agent),
    ):
        results = await client.async_recommend_entities(_catalog(), language="en")

    assert len(results) == 1
    assert results[0].entity_id == "sensor.temp"


@pytest.mark.unit
async def test_ai_client_rejects_invalid_recommended_type(hass) -> None:
    """Ensure invalid payload types raise an error."""
    payload = {"recommended": "bad"}
    agent = RecordingAgent(json.dumps(payload))
    client = AIExposeEntitiesAIClient(hass, agent_id="test_agent")

    with (
        patch("homeassistant.components.conversation.async_prepare_agent"),
        patch("homeassistant.components.conversation.async_get_agent", return_value=agent),
        pytest.raises(AIExposeEntitiesAIClientError),
    ):
        await client.async_recommend_entities(_catalog(), language="en")


@pytest.mark.unit
async def test_ai_client_builds_custom_prompt(hass) -> None:
    """Ensure custom prompts include guidance and entity list."""
    payload = {"recommended": []}
    agent = RecordingAgent(json.dumps(payload))
    client = AIExposeEntitiesAIClient(
        hass,
        agent_id="test_agent",
        custom_prompt="Hello {entity_list}",
        custom_prompt_enabled=True,
    )

    with (
        patch("homeassistant.components.conversation.async_prepare_agent"),
        patch("homeassistant.components.conversation.async_get_agent", return_value=agent),
    ):
        await client.async_recommend_entities(_catalog(), language="en", aggressiveness="unknown")

    assert agent.last_input is not None
    prompt = agent.last_input.text
    assert "Hello" in prompt
    assert "Entity list:" in prompt
    assert "Aggressiveness options" in prompt
    assert "Selected aggressiveness for this run: balanced." in prompt
