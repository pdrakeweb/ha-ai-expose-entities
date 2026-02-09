"""Custom panel registration for ai_expose_entities."""

from __future__ import annotations

from pathlib import Path

from custom_components.ai_expose_entities.const import DOMAIN, PANEL_ICON, PANEL_TITLE, PANEL_URL_PATH
from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

URL_BASE = "/ai_expose_entities_static"
MODULE_URL = f"{URL_BASE}/panel.js"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the custom panel and static assets."""
    panel_path = Path(__file__).resolve().parent / "frontend"
    await hass.http.async_register_static_paths([StaticPathConfig(URL_BASE, str(panel_path), cache_headers=False)])

    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=PANEL_URL_PATH,
        config_panel_domain=DOMAIN,
        webcomponent_name="ai-expose-entities-panel",
        module_url=MODULE_URL,
        embed_iframe=False,
        require_admin=True,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
    )
