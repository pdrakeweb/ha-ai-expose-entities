"""Custom types for ai_expose_entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.const import Platform

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import AIExposeEntitiesAIClient
    from .coordinator import AIExposeEntitiesDataUpdateCoordinator
    from .utils import AIExposeEntitiesRecommendationStore, RecommendationState, TestEntitySet


type AIExposeEntitiesConfigEntry = ConfigEntry[AIExposeEntitiesData]


@dataclass
class AIExposeEntitiesData:
    """Data for ai_expose_entities."""

    client: AIExposeEntitiesAIClient
    coordinator: AIExposeEntitiesDataUpdateCoordinator
    integration: Integration
    platforms: list[Platform]
    store: AIExposeEntitiesRecommendationStore
    state: RecommendationState
    test_entities: TestEntitySet | None
