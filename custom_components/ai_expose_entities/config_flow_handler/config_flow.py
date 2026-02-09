"""
Config flow for ai_expose_entities.

This module implements the main configuration flow for initial setup.

For more information:
https://developers.home-assistant.io/docs/config_entries_config_flow_handler
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.ai_expose_entities.config_flow_handler.agent_options import get_agent_options
from custom_components.ai_expose_entities.config_flow_handler.schemas import get_user_schema
from custom_components.ai_expose_entities.const import (
    CONF_AGENT_ID,
    CONF_CUSTOM_PROMPT,
    CONF_CUSTOM_PROMPT_ENABLED,
    DEFAULT_CUSTOM_PROMPT,
    DEFAULT_CUSTOM_PROMPT_ENABLED,
    DOMAIN,
)
from homeassistant import config_entries
from homeassistant.components.conversation import HOME_ASSISTANT_AGENT

if TYPE_CHECKING:
    from custom_components.ai_expose_entities.config_flow_handler.options_flow import AIExposeEntitiesOptionsFlow


class AIExposeEntitiesConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Handle a config flow for ai_expose_entities.

    This class manages the configuration flow for the integration, including
    initial setup.

    Supported flows:
    - user: Initial setup via UI

    For more details:
    https://developers.home-assistant.io/docs/config_entries_config_flow_handler
    """

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AIExposeEntitiesOptionsFlow:
        """
        Get the options flow for this handler.

        Returns:
            The options flow instance for modifying integration options.

        """
        from custom_components.ai_expose_entities.config_flow_handler.options_flow import (  # noqa: PLC0415
            AIExposeEntitiesOptionsFlow,
        )

        return AIExposeEntitiesOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Handle a flow initialized by the user.

        This is the entry point when a user adds the integration from the UI.

        Args:
            user_input: The user input from the config flow form, or None for initial display.

        Returns:
            The config flow result, either showing a form or creating an entry.

        """
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            options: dict[str, Any] = {}
            agent_id = user_input.get(CONF_AGENT_ID)
            if agent_id:
                options[CONF_AGENT_ID] = agent_id

            custom_prompt_enabled = bool(user_input.get(CONF_CUSTOM_PROMPT_ENABLED, DEFAULT_CUSTOM_PROMPT_ENABLED))
            options[CONF_CUSTOM_PROMPT_ENABLED] = custom_prompt_enabled
            custom_prompt = user_input.get(CONF_CUSTOM_PROMPT, DEFAULT_CUSTOM_PROMPT)
            if custom_prompt_enabled and custom_prompt:
                options[CONF_CUSTOM_PROMPT] = custom_prompt

            return self.async_create_entry(
                title="AI Expose Entities",
                data={},
                options=options,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=get_user_schema(
                agent_options=get_agent_options(self.hass),
            ),
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by reconfigure."""
        entry = self._get_reconfigure_entry()

        if entry.unique_id:
            await self.async_set_unique_id(entry.unique_id)
            self._abort_if_unique_id_mismatch()

        if user_input is not None:
            options = dict(entry.options)
            agent_id = user_input.get(CONF_AGENT_ID)
            if agent_id:
                options[CONF_AGENT_ID] = agent_id
            else:
                options.pop(CONF_AGENT_ID, None)

            custom_prompt_enabled = bool(user_input.get(CONF_CUSTOM_PROMPT_ENABLED, DEFAULT_CUSTOM_PROMPT_ENABLED))
            options[CONF_CUSTOM_PROMPT_ENABLED] = custom_prompt_enabled
            custom_prompt = user_input.get(CONF_CUSTOM_PROMPT, DEFAULT_CUSTOM_PROMPT)
            if custom_prompt_enabled and custom_prompt:
                options[CONF_CUSTOM_PROMPT] = custom_prompt
            else:
                options.pop(CONF_CUSTOM_PROMPT, None)

            self.hass.config_entries.async_update_entry(entry, options=options)
            return self.async_update_reload_and_abort(entry, reason="reconfigure_successful")

        defaults = dict(entry.options)
        defaults.setdefault(CONF_AGENT_ID, HOME_ASSISTANT_AGENT)
        defaults.setdefault(CONF_CUSTOM_PROMPT_ENABLED, DEFAULT_CUSTOM_PROMPT_ENABLED)
        defaults.setdefault(CONF_CUSTOM_PROMPT, DEFAULT_CUSTOM_PROMPT)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_user_schema(
                agent_options=get_agent_options(self.hass),
                default_agent_id=defaults.get(CONF_AGENT_ID),
                default_custom_prompt_enabled=defaults.get(CONF_CUSTOM_PROMPT_ENABLED),
                default_custom_prompt=defaults.get(CONF_CUSTOM_PROMPT),
            ),
            description_placeholders={"name": entry.title},
        )


__all__ = ["AIExposeEntitiesConfigFlowHandler"]
