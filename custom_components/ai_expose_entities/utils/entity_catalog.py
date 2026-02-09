"""Entity catalog builder for ai_expose_entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from custom_components.ai_expose_entities.const import DOMAIN
from custom_components.ai_expose_entities.utils.assist_exposure import ASSISTANT_ID
from homeassistant.components.homeassistant import exposed_entities
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.helpers import device_registry as dr, entity_registry as er


@dataclass(slots=True)
class EntityCatalogItem:
    """Catalog entry for a Home Assistant entity."""

    entity_id: str
    domain: str
    integration: str
    name: str
    original_name: str | None
    device_name: str | None
    device_id: str | None
    disabled: bool
    disabled_by: str | None
    hidden: bool
    entity_category: str | None

    def as_prompt_dict(self) -> dict[str, Any]:
        """Return a compact dict for LLM prompts."""
        return {
            "entity_id": self.entity_id,
            "domain": self.domain,
            "integration": self.integration,
            "name": self.name,
            "original_name": self.original_name,
            "device_name": self.device_name,
            "disabled": self.disabled,
            "hidden": self.hidden,
            "entity_category": self.entity_category,
        }


def build_entity_catalog(
    hass: HomeAssistant,
    deny_list: set[str],
    *,
    exclude_domains: set[str] | None = None,
    include_self: bool = False,
) -> list[EntityCatalogItem]:
    """Build a catalog of entities for AI review."""
    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)
    excluded = set()
    if not include_self:
        excluded.add(DOMAIN)
    if exclude_domains:
        excluded |= exclude_domains

    catalog: list[EntityCatalogItem] = []
    for entry in entity_reg.entities.values():
        if entry.entity_id in deny_list:
            continue
        if exposed_entities.async_should_expose(hass, ASSISTANT_ID, entry.entity_id):
            continue
        domain, _ = split_entity_id(entry.entity_id)
        if domain in excluded or entry.platform in excluded:
            continue

        device_name: str | None = None
        if entry.device_id:
            if device := device_reg.async_get(entry.device_id):
                device_name = device.name_by_user or device.name

        display_name = entry.name or entry.original_name or entry.entity_id
        disabled_by = entry.disabled_by.value if entry.disabled_by else None
        entity_category = entry.entity_category.value if entry.entity_category else None

        catalog.append(
            EntityCatalogItem(
                entity_id=entry.entity_id,
                domain=domain,
                integration=entry.platform,
                name=display_name,
                original_name=entry.original_name,
                device_name=device_name,
                device_id=entry.device_id,
                disabled=entry.disabled,
                disabled_by=disabled_by,
                hidden=entry.hidden_by is not None,
                entity_category=entity_category,
            )
        )

    return catalog


def group_catalog_by_integration(
    items: list[EntityCatalogItem],
) -> dict[str, list[EntityCatalogItem]]:
    """Group catalog items by integration domain."""
    grouped: dict[str, list[EntityCatalogItem]] = {}
    for item in items:
        grouped.setdefault(item.integration, []).append(item)
    return grouped
