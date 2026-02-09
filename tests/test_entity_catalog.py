"""Tests for entity catalog builder."""

from __future__ import annotations

import pytest

from custom_components.ai_expose_entities.utils import build_entity_catalog, group_catalog_by_integration
from custom_components.ai_expose_entities.utils.assist_exposure import ASSISTANT_ID
from homeassistant.components.homeassistant.const import DATA_EXPOSED_ENTITIES
from homeassistant.components.homeassistant.exposed_entities import ExposedEntities, async_expose_entity
from homeassistant.helpers import device_registry as dr, entity_registry as er


@pytest.mark.unit
async def test_build_entity_catalog_filters_denied(hass, config_entry) -> None:
    """Verify deny-list filtering and metadata extraction."""
    config_entry.add_to_hass(hass)
    hass.data[DATA_EXPOSED_ENTITIES] = ExposedEntities(hass)
    await hass.data[DATA_EXPOSED_ENTITIES].async_initialize()
    hass.data[DATA_EXPOSED_ENTITIES].async_set_expose_new_entities(ASSISTANT_ID, False)
    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)

    device = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("test_domain", "device-1")},
        name="Test Device",
    )

    entry_1 = entity_reg.async_get_or_create(
        "light",
        "hue",
        "lamp",
        device_id=device.id,
        original_name="Desk Lamp",
    )
    entry_2 = entity_reg.async_get_or_create(
        "sensor",
        "demo",
        "temperature",
        original_name="Temp",
    )

    catalog = build_entity_catalog(hass, {entry_2.entity_id})
    assert len(catalog) == 1
    item = catalog[0]
    assert item.entity_id == entry_1.entity_id
    assert item.integration == "hue"
    assert item.device_name == "Test Device"

    grouped = group_catalog_by_integration(catalog)
    assert "hue" in grouped
    assert grouped["hue"][0].entity_id == entry_1.entity_id


@pytest.mark.unit
async def test_build_entity_catalog_excludes_exposed(hass, config_entry) -> None:
    """Verify that already-exposed entities are excluded from the catalog."""
    config_entry.add_to_hass(hass)
    hass.data[DATA_EXPOSED_ENTITIES] = ExposedEntities(hass)
    await hass.data[DATA_EXPOSED_ENTITIES].async_initialize()

    entity_reg = er.async_get(hass)
    entry = entity_reg.async_get_or_create(
        "light",
        "hue",
        "lamp",
        original_name="Desk Lamp",
    )

    async_expose_entity(hass, ASSISTANT_ID, entry.entity_id, True)

    catalog = build_entity_catalog(hass, set())
    assert not any(item.entity_id == entry.entity_id for item in catalog)
