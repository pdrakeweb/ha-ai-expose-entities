"""Tests for recommendation service actions."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ai_expose_entities.const import DOMAIN
from custom_components.ai_expose_entities.data import AIExposeEntitiesData
from custom_components.ai_expose_entities.service_actions import async_setup_services
from custom_components.ai_expose_entities.service_actions.recommendation import (
    async_handle_apply_decisions,
    async_handle_run_recommendation,
)
from custom_components.ai_expose_entities.utils import RecommendationEntry, RecommendationState
from custom_components.ai_expose_entities.utils.recommendation_store import AIExposeEntitiesRecommendationStore
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError


@pytest.mark.unit
async def test_async_handle_run_recommendation(hass, config_entry) -> None:
    """async_handle_run_recommendation should return counts."""
    coordinator = SimpleNamespace(async_run_recommendation=AsyncMock(return_value=[RecommendationEntry("light.k")]))
    state = RecommendationState(pending={"light.k": RecommendationEntry("light.k")})
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(object, None),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, SimpleNamespace()),
        state=state,
        test_entities=None,
    )

    result = await async_handle_run_recommendation(hass, config_entry, SimpleNamespace(data={}))

    assert result["status"] == "success"
    assert result["recommendation_count"] == 1
    assert result["pending_count"] == 1


@pytest.mark.unit
async def test_async_handle_run_recommendation_error(hass, config_entry) -> None:
    """Errors in coordinator should surface as HomeAssistantError."""
    coordinator = SimpleNamespace(async_run_recommendation=AsyncMock(side_effect=RuntimeError("boom")))
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(object, None),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, SimpleNamespace()),
        state=RecommendationState(),
        test_entities=None,
    )

    with pytest.raises(HomeAssistantError):
        await async_handle_run_recommendation(hass, config_entry, SimpleNamespace(data={}))


@pytest.mark.unit
async def test_async_handle_apply_decisions_validation(hass, config_entry) -> None:
    """async_handle_apply_decisions should validate input lists."""
    coordinator = SimpleNamespace(async_apply_decisions=MagicMock())
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(object, None),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, SimpleNamespace()),
        state=RecommendationState(),
        test_entities=None,
    )

    with pytest.raises(ServiceValidationError):
        await async_handle_apply_decisions(
            hass,
            config_entry,
            SimpleNamespace(data={"approved_entity_ids": "bad"}),
        )


@pytest.mark.unit
async def test_async_handle_apply_decisions_overlap(hass, config_entry) -> None:
    """Overlapping IDs should raise a validation error."""
    coordinator = SimpleNamespace(async_apply_decisions=MagicMock())
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(object, None),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, SimpleNamespace()),
        state=RecommendationState(),
        test_entities=None,
    )

    with pytest.raises(ServiceValidationError):
        await async_handle_apply_decisions(
            hass,
            config_entry,
            SimpleNamespace(data={"approved_entity_ids": ["light.k"], "denied_entity_ids": ["light.k"]}),
        )


@pytest.mark.unit
async def test_async_handle_apply_decisions_success(hass, config_entry) -> None:
    """async_handle_apply_decisions should call coordinator."""
    coordinator = SimpleNamespace(async_apply_decisions=MagicMock())
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(object, None),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, SimpleNamespace()),
        state=RecommendationState(),
        test_entities=None,
    )

    result = await async_handle_apply_decisions(
        hass,
        config_entry,
        SimpleNamespace(data={"approved_entity_ids": ["light.k"], "denied_entity_ids": ["switch.g"]}),
    )

    coordinator.async_apply_decisions.assert_called_once_with(approved={"light.k"}, denied={"switch.g"})
    assert result["approved_count"] == 1
    assert result["denied_count"] == 1


@pytest.mark.unit
async def test_services_call_via_hass(hass, config_entry) -> None:
    """Service registration should route calls through hass services."""
    coordinator = SimpleNamespace(async_run_recommendation=AsyncMock(return_value=[]))
    state = RecommendationState()
    config_entry.add_to_hass(hass)
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(object, None),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, SimpleNamespace()),
        state=state,
        test_entities=None,
    )

    await async_setup_services(hass)

    response = await hass.services.async_call(
        DOMAIN,
        "run_recommendation",
        {},
        blocking=True,
        return_response=True,
    )

    assert response is not None
    assert response["status"] == "success"
    coordinator.async_run_recommendation.assert_awaited_once()
