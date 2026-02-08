"""
Config flow for ai_expose_entities.

This module provides backwards compatibility for hassfest.
The actual implementation is in the config_flow_handler package.
"""

from __future__ import annotations

from .config_flow_handler import AIExposeEntitiesConfigFlowHandler

__all__ = ["AIExposeEntitiesConfigFlowHandler"]
