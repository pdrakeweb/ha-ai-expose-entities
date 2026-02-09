"""Tests for recommendation storage utilities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.ai_expose_entities.utils.recommendation_store import (
    SAVE_DELAY_SECONDS,
    AIExposeEntitiesRecommendationStore,
    RecommendationEntry,
    RecommendationState,
)


@pytest.mark.unit
async def test_recommendation_store_load_empty(hass) -> None:
    """async_load should return an empty state when no data is stored."""
    store = AIExposeEntitiesRecommendationStore(hass, entry_id="entry-1")

    with patch.object(AIExposeEntitiesRecommendationStore, "_store", create=True) as mock_store:
        mock_store.async_load = AsyncMock(return_value=None)
        state = await store.async_load()

    assert isinstance(state, RecommendationState)
    assert not state.pending
    assert not state.approved
    assert not state.denied
    assert state.last_run is None


@pytest.mark.unit
async def test_recommendation_store_load_data(hass) -> None:
    """async_load should hydrate entries from storage."""
    store = AIExposeEntitiesRecommendationStore(hass, entry_id="entry-1")
    payload = {
        "pending": [
            {
                "entity_id": "light.kitchen",
                "reason": "Frequently used",
                "disabled": False,
                "hidden": True,
            }
        ],
        "approved": ["switch.garage"],
        "denied": ["sensor.temp"],
        "last_run": "2025-01-01T00:00:00",
    }

    with patch.object(AIExposeEntitiesRecommendationStore, "_store", create=True) as mock_store:
        mock_store.async_load = AsyncMock(return_value=payload)
        state = await store.async_load()

    assert "light.kitchen" in state.pending
    assert isinstance(state.pending["light.kitchen"], RecommendationEntry)
    assert state.pending["light.kitchen"].hidden is True
    assert state.approved == {"switch.garage"}
    assert state.denied == {"sensor.temp"}
    assert state.last_run == "2025-01-01T00:00:00"


@pytest.mark.unit
def test_recommendation_store_schedule_save(hass) -> None:
    """async_schedule_save should schedule a delayed save."""
    store = AIExposeEntitiesRecommendationStore(hass, entry_id="entry-1")
    state = RecommendationState()

    with patch.object(AIExposeEntitiesRecommendationStore, "_store", create=True) as mock_store:
        delay_save = AsyncMock()
        mock_store.async_delay_save = delay_save
        store.async_schedule_save(state)

    delay_save.assert_called_once()
    data_func, delay = delay_save.call_args[0]
    assert callable(data_func)
    assert delay == SAVE_DELAY_SECONDS


@pytest.mark.unit
async def test_recommendation_store_save(hass) -> None:
    """async_save should write the serialized state."""
    store = AIExposeEntitiesRecommendationStore(hass, entry_id="entry-1")
    state = RecommendationState(
        pending={
            "light.kitchen": RecommendationEntry(entity_id="light.kitchen"),
        },
        approved={"switch.garage"},
    )

    with patch.object(AIExposeEntitiesRecommendationStore, "_store", create=True) as mock_store:
        mock_store.async_save = AsyncMock()
        await store.async_save(state)

    mock_store.async_save.assert_awaited_once_with(state.as_dict())
