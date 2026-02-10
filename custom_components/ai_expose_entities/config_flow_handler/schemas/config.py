"""
Config flow schemas.

Schemas for the main configuration flow steps.

When this file grows too large (>300 lines), consider splitting into:
- user.py: User setup schemas
- reauth.py: Reauthentication schemas
- reconfigure.py: Reconfiguration schemas
"""

from __future__ import annotations

import voluptuous as vol

from custom_components.ai_expose_entities.const import (
    CONF_AGENT_ID,
    CONF_CUSTOM_PROMPT,
    CONF_CUSTOM_PROMPT_ENABLED,
    CONF_ENTITY_SAMPLE_SIZE,
    DEFAULT_CUSTOM_PROMPT,
    DEFAULT_CUSTOM_PROMPT_ENABLED,
    DEFAULT_ENTITY_SAMPLE_SIZE,
)
from homeassistant.helpers import selector


def get_user_schema(
    *,
    agent_options: list[selector.SelectOptionDict] | None = None,
    default_agent_id: str | None = None,
    default_custom_prompt_enabled: bool | None = None,
    default_custom_prompt: str | None = None,
    default_entity_sample_size: int | None = None,
) -> vol.Schema:
    """Get schema for user step (initial setup)."""
    agent_options = agent_options or []
    if not default_agent_id:
        default_agent_id = "default"  # fallback to string 'default' for AI Task
    if default_custom_prompt_enabled is None:
        default_custom_prompt_enabled = DEFAULT_CUSTOM_PROMPT_ENABLED
    if default_custom_prompt is None:
        default_custom_prompt = DEFAULT_CUSTOM_PROMPT
    if default_entity_sample_size is None:
        default_entity_sample_size = DEFAULT_ENTITY_SAMPLE_SIZE

    return vol.Schema(
        {
            vol.Optional(
                CONF_AGENT_ID,
                default=default_agent_id,
            ): selector.SelectSelector(
                {
                    "options": agent_options,
                    "mode": selector.SelectSelectorMode.DROPDOWN,
                    "translation_key": "ai_task_id",
                }
            ),
            vol.Optional(
                CONF_ENTITY_SAMPLE_SIZE,
                default=default_entity_sample_size,
            ): selector.NumberSelector(
                {
                    "min": 10,
                    "max": 2000,
                    "step": 1,
                    "mode": selector.NumberSelectorMode.BOX,
                    "translation_key": "entity_sample_size",
                }
            ),
            vol.Optional(
                CONF_CUSTOM_PROMPT_ENABLED,
                default=default_custom_prompt_enabled,
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_CUSTOM_PROMPT,
                default=default_custom_prompt,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    multiline=True,
                ),
            ),
        }
    )


__all__ = [
    "get_user_schema",
]
