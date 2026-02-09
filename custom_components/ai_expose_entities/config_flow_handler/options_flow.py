"""
Options flow for ai_expose_entities.

This module implements the options flow that allows users to modify settings
after the initial configuration, such as agent selection and scheduling.

For more information:
https://developers.home-assistant.io/docs/config_entries_options_flow_handler
"""

from __future__ import annotations

from typing import Any

from custom_components.ai_expose_entities.config_flow_handler.ai_task_options import get_ai_task_options
from custom_components.ai_expose_entities.config_flow_handler.schemas import get_options_schema
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
from homeassistant import config_entries


class AIExposeEntitiesOptionsFlow(config_entries.OptionsFlow):
    """
    Handle options flow for the integration.

    This class manages the options that users can modify after initial setup,
    such as agent selection and daily scheduling.

    The options flow always starts with async_step_init and provides a single
    form for all configurable options.

    For more information:
    https://developers.home-assistant.io/docs/config_entries_options_flow_handler
    """

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Manage the options for the integration.

        This is the entry point for the options flow, allowing users to
        configure agent selection, scheduling, and debugging.

        Args:
            user_input: The user input from the options form, or None for initial display.

        Returns:
            The config flow result, either showing a form or creating an options entry.

        """

        if user_input is not None:
            options = dict(self.config_entry.options)
            agent_id = user_input.get(CONF_AGENT_ID)
            if agent_id:
                options[CONF_AGENT_ID] = agent_id
            else:
                options.pop(CONF_AGENT_ID, None)

            # Entity sample size
            entity_sample_size = user_input.get(CONF_ENTITY_SAMPLE_SIZE, DEFAULT_ENTITY_SAMPLE_SIZE)
            options[CONF_ENTITY_SAMPLE_SIZE] = int(entity_sample_size)

            options[CONF_SCHEDULE_ENABLED] = bool(user_input.get(CONF_SCHEDULE_ENABLED, DEFAULT_SCHEDULE_ENABLED))
            options[CONF_SCHEDULE_TIME] = user_input.get(CONF_SCHEDULE_TIME, DEFAULT_SCHEDULE_TIME)

            custom_prompt_enabled = bool(user_input.get(CONF_CUSTOM_PROMPT_ENABLED, DEFAULT_CUSTOM_PROMPT_ENABLED))
            options[CONF_CUSTOM_PROMPT_ENABLED] = custom_prompt_enabled
            custom_prompt = user_input.get(CONF_CUSTOM_PROMPT, DEFAULT_CUSTOM_PROMPT)
            if custom_prompt_enabled and custom_prompt:
                options[CONF_CUSTOM_PROMPT] = custom_prompt
            else:
                options.pop(CONF_CUSTOM_PROMPT, None)

            options[CONF_ENABLE_DEBUGGING] = bool(user_input.get(CONF_ENABLE_DEBUGGING, DEFAULT_ENABLE_DEBUGGING))

            return self.async_create_entry(title="", data=options)

        defaults = dict(self.config_entry.options)
        ai_task_options = get_ai_task_options(self.hass)
        return self.async_show_form(
            step_id="init",
            data_schema=get_options_schema(
                defaults,
                agent_options=ai_task_options,
            ),
        )


__all__ = ["AIExposeEntitiesOptionsFlow"]
