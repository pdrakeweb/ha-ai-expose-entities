"""Test entity generation for ai_expose_entities."""

from __future__ import annotations

from dataclasses import dataclass
import random
import string
from typing import Any

from custom_components.ai_expose_entities.const import (
    CONF_TEST_ENTITIES_ENABLED,
    CONF_TEST_ENTITY_COUNT,
    CONF_TEST_ENTITY_RELEVANT_COUNT,
    CONF_TEST_ENTITY_SEED,
    DEFAULT_TEST_ENTITIES_ENABLED,
    DEFAULT_TEST_ENTITY_COUNT,
    DEFAULT_TEST_ENTITY_RELEVANT_COUNT,
    DEFAULT_TEST_ENTITY_SEED,
)
from custom_components.ai_expose_entities.utils.string_helpers import slugify_name
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import EntityCategory

RELEVANT_NAME_POOL: tuple[str, ...] = (
    "Living Room Temperature",
    "Kitchen Temperature",
    "Bedroom Humidity",
    "Bathroom Humidity",
    "Outdoor Temperature",
    "Garage Motion Count",
    "Front Door Activity",
    "Laundry Power Usage",
    "Basement Air Quality",
    "Office Light Level",
    "Nursery Noise Level",
    "Garden Soil Moisture",
    "Main Hall Occupancy",
    "Driveway Activity",
    "Water Heater Runtime",
    "Thermostat Setpoint",
    "Living Room CO2",
    "Attic Heat Index",
    "Solar Output",
    "Pool Pump Status",
)


@dataclass(slots=True)
class TestEntityConfig:
    """Configuration for generated test entities."""

    enabled: bool
    count: int
    relevant_count: int
    seed: int


@dataclass(slots=True)
class TestEntitySet:
    """Generated test entity metadata and data."""

    descriptions: tuple[SensorEntityDescription, ...]
    data: dict[str, Any]


def parse_test_entity_config(config: dict[str, Any] | None) -> TestEntityConfig:
    """Parse test entity configuration from YAML config."""
    raw = config or {}
    enabled = bool(raw.get(CONF_TEST_ENTITIES_ENABLED, DEFAULT_TEST_ENTITIES_ENABLED))
    count = int(raw.get(CONF_TEST_ENTITY_COUNT, DEFAULT_TEST_ENTITY_COUNT))
    relevant_count = int(raw.get(CONF_TEST_ENTITY_RELEVANT_COUNT, DEFAULT_TEST_ENTITY_RELEVANT_COUNT))
    seed = int(raw.get(CONF_TEST_ENTITY_SEED, DEFAULT_TEST_ENTITY_SEED))

    count = max(count, 0)
    relevant_count = max(relevant_count, 0)
    relevant_count = min(relevant_count, count)

    return TestEntityConfig(
        enabled=enabled,
        count=count,
        relevant_count=relevant_count,
        seed=seed,
    )


def build_test_entity_set(config: TestEntityConfig) -> TestEntitySet | None:
    """Build a generated test entity set from configuration."""
    if not config.enabled or config.count <= 0:
        return None

    rng = random.Random(config.seed)
    data: dict[str, Any] = {
        "model": "AI Expose Entities Test Rig",
        "userId": rng.randint(1, 50),
        "id": rng.randint(1, 200),
        "test_entity_count": config.count,
        "test_entity_seed": config.seed,
    }

    descriptions: list[SensorEntityDescription] = []
    used_keys: set[str] = set(data)

    relevant_names = _expand_relevant_names(config.relevant_count)
    random_count = max(0, config.count - len(relevant_names))
    random_names = _generate_random_names(random_count, rng)

    for name in relevant_names:
        key = _unique_key(slugify_name(name), used_keys)
        descriptions.append(
            SensorEntityDescription(
                key=key,
                name=name,
                has_entity_name=True,
            )
        )
        data[key] = _generate_relevant_value(name, rng)

    for name in random_names:
        key = _unique_key(slugify_name(name), used_keys)
        descriptions.append(
            SensorEntityDescription(
                key=key,
                name=name,
                has_entity_name=True,
                entity_category=EntityCategory.DIAGNOSTIC,
            )
        )
        data[key] = _generate_random_value(rng)

    return TestEntitySet(descriptions=tuple(descriptions), data=data)


def _expand_relevant_names(count: int) -> list[str]:
    if count <= 0:
        return []
    if count <= len(RELEVANT_NAME_POOL):
        return list(RELEVANT_NAME_POOL[:count])

    names = list(RELEVANT_NAME_POOL)
    suffix = 1
    while len(names) < count:
        names.append(f"{RELEVANT_NAME_POOL[(suffix - 1) % len(RELEVANT_NAME_POOL)]} {suffix}")
        suffix += 1
    return names


def _generate_random_names(count: int, rng: random.Random) -> list[str]:
    names: list[str] = []
    for _ in range(count):
        token = "".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        names.append(f"Unit {token}")
    return names


def _unique_key(base: str, used_keys: set[str]) -> str:
    key = base or "test_entity"
    if key not in used_keys:
        used_keys.add(key)
        return key

    suffix = 2
    while f"{key}_{suffix}" in used_keys:
        suffix += 1
    unique_key = f"{key}_{suffix}"
    used_keys.add(unique_key)
    return unique_key


def _generate_relevant_value(name: str, rng: random.Random) -> float | int | str:
    lower = name.lower()
    if "temperature" in lower or "heat" in lower:
        return round(rng.uniform(16.0, 28.0), 1)
    if "humidity" in lower or "moisture" in lower:
        return rng.randint(30, 80)
    if "power" in lower or "output" in lower:
        return rng.randint(50, 2500)
    if "co2" in lower:
        return rng.randint(400, 1400)
    if "light" in lower:
        return rng.randint(10, 1200)
    if "runtime" in lower:
        return rng.randint(0, 5000)
    if "status" in lower:
        return "ok"
    return rng.randint(0, 100)


def _generate_random_value(rng: random.Random) -> float | int | str:
    if rng.random() < 0.5:
        return "".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    if rng.random() < 0.5:
        return rng.randint(0, 10000)
    return round(rng.uniform(0.0, 999.9), 2)
