"""Tests for generated test entities."""

from __future__ import annotations

import pytest

from custom_components.ai_expose_entities.utils.test_entities import (
    TestEntityConfig as EntityConfig,
    build_test_entity_set,
    parse_test_entity_config,
)
from homeassistant.const import EntityCategory

EntityConfig.__test__ = False


@pytest.mark.unit
def test_parse_test_entity_config_clamps_values() -> None:
    """parse_test_entity_config should clamp negative values and bounds."""
    config = parse_test_entity_config(
        {
            "enabled": True,
            "count": -5,
            "relevant_count": 10,
            "seed": 42,
        }
    )

    assert config.enabled is True
    assert config.count == 0
    assert config.relevant_count == 0
    assert config.seed == 42


@pytest.mark.unit
def test_build_test_entity_set_disabled() -> None:
    """build_test_entity_set should return None when disabled."""
    config = EntityConfig(enabled=False, count=5, relevant_count=2, seed=1)
    assert build_test_entity_set(config) is None


@pytest.mark.unit
def test_build_test_entity_set_generates_entities() -> None:
    """build_test_entity_set should generate deterministic entities."""
    config = EntityConfig(enabled=True, count=3, relevant_count=2, seed=1)
    entity_set = build_test_entity_set(config)

    assert entity_set is not None
    assert len(entity_set.descriptions) == 3
    assert len(entity_set.data) >= 3

    keys = {description.key for description in entity_set.descriptions}
    assert keys.issubset(entity_set.data.keys())

    random_entities = [
        description
        for description in entity_set.descriptions
        if description.entity_category == EntityCategory.DIAGNOSTIC
    ]
    assert len(random_entities) == 1
