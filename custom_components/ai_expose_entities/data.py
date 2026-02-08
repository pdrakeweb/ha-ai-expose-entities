"""Custom types for ai_expose_entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import AIExposeEntitiesApiClient
    from .coordinator import AIExposeEntitiesDataUpdateCoordinator


type AIExposeEntitiesConfigEntry = ConfigEntry[AIExposeEntitiesData]


@dataclass
class AIExposeEntitiesData:
    """Data for ai_expose_entities."""

    client: AIExposeEntitiesApiClient
    coordinator: AIExposeEntitiesDataUpdateCoordinator
    integration: Integration
