"""Tests for coordinator business logic."""

from __future__ import annotations

import logging
from typing import Any, cast
from unittest.mock import patch

import pytest

from custom_components.ai_expose_entities.api import AIExposeEntitiesAIClient
from custom_components.ai_expose_entities.coordinator import AIExposeEntitiesDataUpdateCoordinator
from custom_components.ai_expose_entities.data import AIExposeEntitiesData
from custom_components.ai_expose_entities.utils import RecommendationEntry, RecommendationState
from custom_components.ai_expose_entities.utils.recommendation_store import AIExposeEntitiesRecommendationStore


class FakeClient:
    """Fake AI client returning recommendations."""

    def __init__(self, recommendations: list[RecommendationEntry]) -> None:
        self._recommendations = recommendations

    async def async_recommend_entities(
        self,
        catalog: list[Any],
        *,
        language: str,
        context: Any | None = None,
        aggressiveness: str | None = None,
    ) -> list[RecommendationEntry]:
        return list(self._recommendations)


class FakeStore:
    """Fake store to capture save calls."""

    def __init__(self) -> None:
        self.saved = False

    def async_schedule_save(self, state: RecommendationState) -> None:
        self.saved = True


def _build_coordinator(hass, config_entry) -> AIExposeEntitiesDataUpdateCoordinator:
    return AIExposeEntitiesDataUpdateCoordinator(
        hass=hass,
        logger=logging.getLogger(__name__),
        name="ai_expose_entities",
        config_entry=config_entry,
        update_interval=None,
        always_update=True,
    )


@pytest.mark.unit
async def test_async_run_recommendation_removes_unexposed(hass, config_entry) -> None:
    """Approved entries no longer exposed should be removed."""
    coordinator = _build_coordinator(hass, config_entry)
    state = RecommendationState(approved={"light.kitchen", "switch.garage"})
    store = FakeStore()
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(AIExposeEntitiesAIClient, FakeClient([])),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, store),
        state=state,
        test_entities=None,
    )

    def _should_expose(_hass, _assistant, entity_id: str) -> bool:
        return entity_id == "switch.garage"

    with (
        patch("custom_components.ai_expose_entities.coordinator.base.build_entity_catalog", return_value=[]),
        patch(
            "custom_components.ai_expose_entities.coordinator.base.exposed_entities.async_should_expose", _should_expose
        ),
    ):
        await coordinator.async_run_recommendation()

    assert "light.kitchen" not in state.approved
    assert "switch.garage" in state.approved
    assert store.saved


@pytest.mark.unit
async def test_async_run_recommendation_filters_disabled_hidden(hass, config_entry) -> None:
    """Disabled/hidden recommendations should not be added to pending."""
    coordinator = _build_coordinator(hass, config_entry)
    state = RecommendationState(approved={"light.approved"}, denied={"light.denied"})
    store = FakeStore()
    recommendations = [
        RecommendationEntry(entity_id="light.approved"),
        RecommendationEntry(entity_id="light.denied"),
        RecommendationEntry(entity_id="light.hidden", hidden=True),
        RecommendationEntry(entity_id="light.disabled", disabled=True),
        RecommendationEntry(entity_id="light.allowed"),
    ]
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(AIExposeEntitiesAIClient, FakeClient(recommendations)),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, store),
        state=state,
        test_entities=None,
    )

    with (
        patch("custom_components.ai_expose_entities.coordinator.base.build_entity_catalog", return_value=[]),
        patch(
            "custom_components.ai_expose_entities.coordinator.base.exposed_entities.async_should_expose",
            return_value=True,
        ),
    ):
        await coordinator.async_run_recommendation()

    assert "light.allowed" in state.pending
    assert "light.hidden" not in state.pending
    assert "light.disabled" not in state.pending
    assert "light.approved" not in state.pending
    assert "light.denied" not in state.pending


@pytest.mark.unit
def test_async_clear_pending(hass, config_entry) -> None:
    """async_clear_pending should clear requested pending entries."""
    coordinator = _build_coordinator(hass, config_entry)
    state = RecommendationState(
        pending={
            "light.kitchen": RecommendationEntry(entity_id="light.kitchen"),
            "sensor.temp": RecommendationEntry(entity_id="sensor.temp"),
        }
    )
    store = FakeStore()
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(AIExposeEntitiesAIClient, FakeClient([])),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, store),
        state=state,
        test_entities=None,
    )

    coordinator.async_clear_pending(entity_ids={"sensor.temp"})

    assert "sensor.temp" not in state.pending
    assert "light.kitchen" in state.pending
    assert store.saved
