"""Tests for recommendation coordinator flows."""

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
    """Fake AI client returning fixed recommendations."""

    async def async_recommend_entities(
        self,
        catalog: list[Any],
        *,
        language: str,
        context: Any | None = None,
        aggressiveness: str | None = None,
    ) -> list[RecommendationEntry]:
        return [
            RecommendationEntry(
                entity_id="light.kitchen",
                reason="Popular",
                integration="hue",
                name="Kitchen Light",
                device_name="Kitchen",
                disabled=False,
                hidden=False,
            )
        ]


class FakeStore:
    """Fake store to capture save calls."""

    def __init__(self) -> None:
        self.saved = False

    def async_schedule_save(self, state: RecommendationState) -> None:
        self.saved = True


@pytest.mark.unit
async def test_coordinator_run_recommendation(hass, config_entry) -> None:
    """Verify coordinator merges recommendations into pending state."""
    coordinator = AIExposeEntitiesDataUpdateCoordinator(
        hass=hass,
        logger=logging.getLogger(__name__),
        name="ai_expose_entities",
        config_entry=config_entry,
        update_interval=None,
        always_update=True,
    )

    state = RecommendationState()
    store = FakeStore()
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(AIExposeEntitiesAIClient, FakeClient()),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, store),
        state=state,
        test_entities=None,
    )

    with patch("custom_components.ai_expose_entities.coordinator.base.build_entity_catalog", return_value=[]):
        await coordinator.async_run_recommendation()

    assert "light.kitchen" in state.pending
    assert store.saved


@pytest.mark.unit
async def test_coordinator_apply_decisions(hass, config_entry) -> None:
    """Verify approval and denial updates state."""
    coordinator = AIExposeEntitiesDataUpdateCoordinator(
        hass=hass,
        logger=logging.getLogger(__name__),
        name="ai_expose_entities",
        config_entry=config_entry,
        update_interval=None,
        always_update=True,
    )

    state = RecommendationState(
        pending={
            "light.kitchen": RecommendationEntry(
                entity_id="light.kitchen",
                reason="Popular",
                integration="hue",
                name="Kitchen Light",
                device_name="Kitchen",
                disabled=False,
                hidden=False,
            )
        }
    )
    store = FakeStore()
    config_entry.runtime_data = AIExposeEntitiesData(
        client=cast(AIExposeEntitiesAIClient, FakeClient()),
        coordinator=coordinator,
        integration=None,  # type: ignore[arg-type]
        platforms=[],
        store=cast(AIExposeEntitiesRecommendationStore, store),
        state=state,
        test_entities=None,
    )

    with patch("custom_components.ai_expose_entities.coordinator.base.set_assist_exposure"):
        coordinator.async_apply_decisions(approved={"light.kitchen"}, denied=set())

    assert "light.kitchen" in state.approved
    assert "light.kitchen" not in state.pending
