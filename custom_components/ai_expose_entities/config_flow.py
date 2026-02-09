"""
Config flow for ai_expose_entities.

This module provides backwards compatibility for hassfest.
The actual implementation is in the config_flow_handler package.
"""

from __future__ import annotations

from .config_flow_handler import AIExposeEntitiesConfigFlowHandler

# Home Assistant expects a class named ConfigFlow in this module
ConfigFlow = AIExposeEntitiesConfigFlowHandler

__all__ = ["AIExposeEntitiesConfigFlowHandler", "ConfigFlow"]
