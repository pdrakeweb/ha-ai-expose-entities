"""Recommendation storage for ai_expose_entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from custom_components.ai_expose_entities.const import DOMAIN, LOGGER
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

STORAGE_VERSION = 1
STORAGE_KEY_TEMPLATE = f"{DOMAIN}.recommendations.{{entry_id}}"
SAVE_DELAY_SECONDS = 10


@dataclass(slots=True)
class RecommendationEntry:
    """A single recommended entity and its metadata."""

    entity_id: str
    reason: str | None = None
    group_name: str | None = None
    group_reason: str | None = None
    integration: str | None = None
    integration_overview: str | None = None
    name: str | None = None
    device_name: str | None = None
    disabled: bool = False
    hidden: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecommendationEntry:
        """Create from stored data."""
        return cls(
            entity_id=data["entity_id"],
            reason=data.get("reason"),
            group_name=data.get("group_name"),
            group_reason=data.get("group_reason"),
            integration=data.get("integration"),
            integration_overview=data.get("integration_overview"),
            name=data.get("name"),
            device_name=data.get("device_name"),
            disabled=bool(data.get("disabled", False)),
            hidden=bool(data.get("hidden", False)),
        )

    def as_dict(self) -> dict[str, Any]:
        """Serialize for storage."""
        return {
            "entity_id": self.entity_id,
            "reason": self.reason,
            "group_name": self.group_name,
            "group_reason": self.group_reason,
            "integration": self.integration,
            "integration_overview": self.integration_overview,
            "name": self.name,
            "device_name": self.device_name,
            "disabled": self.disabled,
            "hidden": self.hidden,
        }


@dataclass(slots=True)
class RecommendationState:
    """Stored recommendation state."""

    pending: dict[str, RecommendationEntry] = field(default_factory=dict)
    approved: set[str] = field(default_factory=set)
    denied: set[str] = field(default_factory=set)
    last_run: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Serialize for storage."""
        return {
            "pending": [entry.as_dict() for entry in self.pending.values()],
            "approved": sorted(self.approved),
            "denied": sorted(self.denied),
            "last_run": self.last_run,
        }


class AIExposeEntitiesRecommendationStore:
    """Storage wrapper for recommendation state."""

    def __init__(self, hass: HomeAssistant, entry_id: str, *, debug_enabled: bool = False) -> None:
        """Initialize the recommendation storage wrapper."""
        self._store = Store(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY_TEMPLATE.format(entry_id=entry_id),
            serialize_in_event_loop=True,
        )
        self._debug_enabled = debug_enabled

    async def async_load(self) -> RecommendationState:
        """Load state from storage."""
        if self._debug_enabled:
            LOGGER.debug("Loading recommendation state from storage")
        data = await self._store.async_load()
        if not data:
            if self._debug_enabled:
                LOGGER.debug("No stored recommendation state found")
            return RecommendationState()

        pending_entries = {
            entry["entity_id"]: RecommendationEntry.from_dict(entry)
            for entry in data.get("pending", [])
            if "entity_id" in entry
        }
        state = RecommendationState(
            pending=pending_entries,
            approved=set(data.get("approved", [])),
            denied=set(data.get("denied", [])),
            last_run=data.get("last_run"),
        )
        if self._debug_enabled:
            LOGGER.debug(
                "Recommendation state loaded: pending=%d approved=%d denied=%d",
                len(state.pending),
                len(state.approved),
                len(state.denied),
            )
        return state

    def async_schedule_save(self, state: RecommendationState) -> None:
        """Schedule a delayed save of the current state."""
        if self._debug_enabled:
            LOGGER.debug(
                "Scheduling recommendation state save: pending=%d approved=%d denied=%d",
                len(state.pending),
                len(state.approved),
                len(state.denied),
            )
        self._store.async_delay_save(state.as_dict, SAVE_DELAY_SECONDS)

    async def async_save(self, state: RecommendationState) -> None:
        """Persist state immediately."""
        if self._debug_enabled:
            LOGGER.debug(
                "Saving recommendation state: pending=%d approved=%d denied=%d",
                len(state.pending),
                len(state.approved),
                len(state.denied),
            )
        await self._store.async_save(state.as_dict())
