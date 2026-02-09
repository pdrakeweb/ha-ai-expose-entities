"""Sensor platform for ai_expose_entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.ai_expose_entities.const import PARALLEL_UPDATES as PARALLEL_UPDATES
from homeassistant.components.sensor import SensorEntityDescription

from .air_quality import ENTITY_DESCRIPTIONS as AIR_QUALITY_DESCRIPTIONS, AIExposeEntitiesAirQualitySensor
from .diagnostic import ENTITY_DESCRIPTIONS as DIAGNOSTIC_DESCRIPTIONS, AIExposeEntitiesDiagnosticSensor
from .test_entities import AIExposeEntitiesTestSensor

if TYPE_CHECKING:
    from custom_components.ai_expose_entities.data import AIExposeEntitiesConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Combine all entity descriptions from different modules
ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    *AIR_QUALITY_DESCRIPTIONS,
    *DIAGNOSTIC_DESCRIPTIONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AIExposeEntitiesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    # Add air quality sensors
    async_add_entities(
        AIExposeEntitiesAirQualitySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in AIR_QUALITY_DESCRIPTIONS
    )
    # Add diagnostic sensors
    async_add_entities(
        AIExposeEntitiesDiagnosticSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in DIAGNOSTIC_DESCRIPTIONS
    )

    test_entities = entry.runtime_data.test_entities
    if test_entities:
        async_add_entities(
            AIExposeEntitiesTestSensor(
                coordinator=entry.runtime_data.coordinator,
                entity_description=entity_description,
            )
            for entity_description in test_entities.descriptions
        )
