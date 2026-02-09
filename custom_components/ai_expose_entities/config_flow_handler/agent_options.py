"""Helpers for conversation agent selector options."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.components.conversation import HOME_ASSISTANT_AGENT
from homeassistant.components.conversation.agent_manager import get_agent_manager
from homeassistant.components.conversation.const import DATA_COMPONENT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.loader import IntegrationNotFound, async_get_loaded_integration


def get_agent_options(hass: HomeAssistant) -> list[selector.SelectOptionDict]:
    """Build select options for available conversation agents."""
    options: dict[str, selector.SelectOptionDict] = {
        HOME_ASSISTANT_AGENT: {
            "value": HOME_ASSISTANT_AGENT,
            "label": "Home Assistant (default)",
        }
    }

    manager = get_agent_manager(hass)
    for agent_info in manager.async_get_agent_info():
        label = _format_agent_label(
            hass,
            agent_info.id,
            _normalize_agent_name(str(agent_info.name)),
            _get_entry_domain(hass, agent_info.id),
        )
        options[agent_info.id] = {
            "value": agent_info.id,
            "label": label,
        }

    component = hass.data.get(DATA_COMPONENT)
    if component is not None:
        for entity in component.entities:
            entity_id = entity.entity_id
            if entity_id in options:
                continue
            name = entity.name if isinstance(entity.name, str) else entity_id
            label = _format_agent_label(
                hass,
                entity_id,
                _normalize_agent_name(name),
                _get_entity_domain(hass, entity),
            )
            options[entity_id] = {
                "value": entity_id,
                "label": label,
            }

    default_option = options[HOME_ASSISTANT_AGENT]
    other_options = [option for key, option in options.items() if key != HOME_ASSISTANT_AGENT]
    return [
        default_option,
        *sorted(other_options, key=lambda option: option["label"].lower()),
    ]


def _format_agent_label(
    hass: HomeAssistant,
    agent_id: str,
    base_name: str,
    domain: str | None,
) -> str:
    """Return a label that includes the integration name when available."""
    if agent_id == HOME_ASSISTANT_AGENT:
        return "Home Assistant (default)"

    integration_name = _get_integration_name(hass, domain)
    if integration_name and integration_name not in base_name:
        return f"{base_name} ({integration_name})"
    if domain and domain not in base_name:
        return f"{base_name} ({domain})"
    return base_name


def _get_entry_domain(hass: HomeAssistant, entry_id: str) -> str | None:
    """Return domain for a config entry id."""
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None:
        return None
    return entry.domain


def _get_entity_domain(hass: HomeAssistant, entity: Any) -> str | None:
    """Return domain for a conversation entity if available."""
    registry = er.async_get(hass)
    entry = registry.async_get(entity.entity_id)
    if entry and entry.config_entry_id:
        config_entry = hass.config_entries.async_get_entry(entry.config_entry_id)
        if config_entry is not None:
            return config_entry.domain
    platform = getattr(entity, "platform", None)
    if platform is None:
        return None
    return getattr(platform, "domain", None) or getattr(platform, "platform_name", None)


def _normalize_agent_name(name: str) -> str:
    """Normalize conversation agent names for display."""
    name = name.strip()
    if name.startswith("conversation."):
        name = name.removeprefix("conversation.")
        name = name.replace("_", " ")
        name = name.title()
    name = re.sub(r"\s*\(conversation.*\)\s*$", "", name, flags=re.IGNORECASE)
    return name.strip()


def _get_integration_name(hass: HomeAssistant, domain: str | None) -> str | None:
    """Return integration display name for a domain if loaded."""
    if not domain:
        return None
    try:
        integration = async_get_loaded_integration(hass, domain)
    except IntegrationNotFound:
        return None
    return integration.name


__all__ = ["get_agent_options"]
