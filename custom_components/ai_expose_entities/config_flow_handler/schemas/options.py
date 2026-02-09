"""
Options flow schemas.

Schemas for the options flow that allows users to modify settings
after initial configuration.

When adding many options, consider grouping them:
- basic_options.py: Common settings (update interval, debug mode)
- advanced_options.py: Advanced settings
- device_options.py: Device-specific settings
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import time
from typing import Any

import voluptuous as vol

from custom_components.ai_expose_entities.const import (
    CONF_AGENT_ID,
    CONF_CUSTOM_PROMPT,
    CONF_CUSTOM_PROMPT_ENABLED,
    CONF_ENABLE_DEBUGGING,
    CONF_ENTITY_SAMPLE_SIZE,
    CONF_SCHEDULE_ENABLED,
    CONF_SCHEDULE_TIME,
    DEFAULT_CUSTOM_PROMPT,
    DEFAULT_CUSTOM_PROMPT_ENABLED,
    DEFAULT_ENABLE_DEBUGGING,
    DEFAULT_ENTITY_SAMPLE_SIZE,
    DEFAULT_SCHEDULE_ENABLED,
    DEFAULT_SCHEDULE_TIME,
)
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util


def get_options_schema(
    defaults: Mapping[str, Any] | None = None,
    *,
    agent_options: list[selector.SelectOptionDict] | None = None,
) -> vol.Schema:
    """
    Get schema for options flow.

    Args:
        defaults: Optional dictionary of current option values.

    Returns:
        Voluptuous schema for options configuration.

    """
    defaults = defaults or {}
    agent_options = agent_options or []
    schedule_time = defaults.get(CONF_SCHEDULE_TIME, DEFAULT_SCHEDULE_TIME)
    if isinstance(schedule_time, str):
        schedule_time = dt_util.parse_time(schedule_time) or DEFAULT_SCHEDULE_TIME
    if not isinstance(schedule_time, time):
        schedule_time = DEFAULT_SCHEDULE_TIME

    return vol.Schema(
        {
            vol.Optional(
                CONF_AGENT_ID,
                default=defaults.get(CONF_AGENT_ID),
            ): selector.SelectSelector(
                {
                    "options": agent_options,
                    "mode": selector.SelectSelectorMode.DROPDOWN,
                    "translation_key": "ai_task_id",
                }
            ),
            vol.Optional(
                CONF_ENTITY_SAMPLE_SIZE,
                default=defaults.get(CONF_ENTITY_SAMPLE_SIZE, DEFAULT_ENTITY_SAMPLE_SIZE),
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
                CONF_SCHEDULE_ENABLED,
                default=defaults.get(CONF_SCHEDULE_ENABLED, DEFAULT_SCHEDULE_ENABLED),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_SCHEDULE_TIME,
                default=schedule_time,
            ): selector.TimeSelector(),
            vol.Optional(
                CONF_CUSTOM_PROMPT_ENABLED,
                default=defaults.get(CONF_CUSTOM_PROMPT_ENABLED, DEFAULT_CUSTOM_PROMPT_ENABLED),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_CUSTOM_PROMPT,
                default=defaults.get(CONF_CUSTOM_PROMPT, DEFAULT_CUSTOM_PROMPT),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    multiline=True,
                ),
            ),
            vol.Optional(
                CONF_ENABLE_DEBUGGING,
                default=defaults.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING),
            ): selector.BooleanSelector(),
        },
    )


__all__ = [
    "get_options_schema",
]
