"""Generated test sensors for ai_expose_entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.ai_expose_entities.entity import AIExposeEntitiesEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

if TYPE_CHECKING:
    from custom_components.ai_expose_entities.coordinator import AIExposeEntitiesDataUpdateCoordinator


class AIExposeEntitiesTestSensor(SensorEntity, AIExposeEntitiesEntity):
    """Sensor for generated test entities."""

    def __init__(
        self,
        coordinator: AIExposeEntitiesDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entity_description)

    @property
    def native_value(self) -> int | float | str | None:
        """Return the sensor value."""
        if not self.coordinator.last_update_success:
            return None
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.entity_description.key in self.coordinator.data
