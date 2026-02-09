"""AI client for ai_expose_entities using Home Assistant conversation agents."""

from __future__ import annotations

import json
import re
from typing import Any

from custom_components.ai_expose_entities.const import (
    DEFAULT_CUSTOM_PROMPT,
    DEFAULT_RECOMMENDATION_AGGRESSIVENESS,
    HIDDEN_PROMPT_TEMPLATE,
    LOGGER,
    RECOMMENDATION_AGGRESSIVENESS_LEVELS,
)
from custom_components.ai_expose_entities.utils import EntityCatalogItem, RecommendationEntry
from homeassistant.components import conversation
from homeassistant.components.conversation import ConversationInput
from homeassistant.core import Context, HomeAssistant
from homeassistant.util import dt as dt_util


class AIExposeEntitiesAIClientError(Exception):
    """Base exception to indicate a general AI client error."""


class AIExposeEntitiesAIClientCommunicationError(
    AIExposeEntitiesAIClientError,
):
    """Exception to indicate a communication error with the AI agent."""


class AIExposeEntitiesAIClientAuthenticationError(
    AIExposeEntitiesAIClientError,
):
    """Exception to indicate an authentication error with the AI agent."""


class AIExposeEntitiesApiClientError(AIExposeEntitiesAIClientError):
    """Backward-compatible alias for legacy API client errors."""


class AIExposeEntitiesApiClientCommunicationError(
    AIExposeEntitiesAIClientCommunicationError,
):
    """Backward-compatible alias for legacy API client communication errors."""


class AIExposeEntitiesApiClientAuthenticationError(
    AIExposeEntitiesAIClientAuthenticationError,
):
    """Backward-compatible alias for legacy API client authentication errors."""


class AIExposeEntitiesAIClient:
    """AI client that uses Home Assistant conversation agents."""

    def __init__(
        self,
        hass: HomeAssistant,
        agent_id: str | None,
        *,
        custom_prompt: str | None = None,
        custom_prompt_enabled: bool = False,
        debug_enabled: bool = False,
    ) -> None:
        """Initialize the AI client."""
        self._hass = hass
        self._agent_id = agent_id
        self._custom_prompt = custom_prompt
        self._custom_prompt_enabled = custom_prompt_enabled
        self._debug_enabled = debug_enabled

    @property
    def agent_id(self) -> str | None:
        """Return the agent id configured for this client."""
        return self._agent_id

    async def async_recommend_entities(
        self,
        catalog: list[EntityCatalogItem],
        *,
        language: str,
        context: Context | None = None,
        aggressiveness: str | None = None,
    ) -> list[RecommendationEntry]:
        """Ask the configured conversation agent to recommend entities."""
        agent_id = self._agent_id or conversation.HOME_ASSISTANT_AGENT
        if self._debug_enabled:
            LOGGER.debug(
                "Preparing conversation agent '%s' for recommendations (catalog=%d language=%s)",
                agent_id,
                len(catalog),
                language,
            )
        try:
            await conversation.async_prepare_agent(  # type: ignore[attr-defined]
                self._hass,
                agent_id,
                language,
            )
        except Exception as err:
            raise AIExposeEntitiesAIClientAuthenticationError(
                f"Conversation agent '{agent_id}' is not available"
            ) from err

        prompt = _build_prompt(
            catalog,
            custom_prompt=self._custom_prompt,
            custom_prompt_enabled=self._custom_prompt_enabled,
            aggressiveness=aggressiveness,
        )
        user_input = ConversationInput(
            text=prompt,
            context=context or Context(),
            conversation_id=None,
            device_id=None,
            satellite_id=None,
            language=language,
            agent_id=agent_id,
            extra_system_prompt=_system_prompt(),
        )

        agent = conversation.async_get_agent(  # type: ignore[attr-defined]
            self._hass,
            agent_id,
        )
        if agent is None:
            raise AIExposeEntitiesAIClientAuthenticationError(
                f"Conversation agent '{agent_id}' is not available",
            )

        if self._debug_enabled:
            LOGGER.debug(
                "Sending recommendation request to agent '%s' (prompt_bytes=%d)",
                agent_id,
                len(prompt.encode("utf-8")),
            )

        try:
            result = await agent.async_process(user_input)
        except Exception as err:
            raise AIExposeEntitiesAIClientCommunicationError(f"Conversation agent error: {err}") from err

        response_text = _extract_response_text(result.response.speech)
        if self._debug_enabled:
            LOGGER.debug(
                "Received recommendation response (text_bytes=%d)",
                len(response_text.encode("utf-8")),
            )
            LOGGER.debug(
                "Recommendation response preview: %s",
                _truncate_debug_text(response_text),
            )
        catalog_index = {item.entity_id: item for item in catalog}
        payload = _extract_json_payload(response_text)
        integration_overview = _extract_integration_overview(payload)

        results = _parse_grouped_recommendations(payload, catalog_index)
        if results:
            requested_count = _count_grouped_items(payload)
        else:
            recommendations = payload.get("recommended", [])
            if not isinstance(recommendations, list):
                raise AIExposeEntitiesAIClientError("Invalid response: 'recommended' must be a list")

            results = []
            for item in recommendations:
                if not isinstance(item, dict):
                    continue
                entity_id = item.get("entity_id")
                if not entity_id or entity_id not in catalog_index:
                    continue
                reason = item.get("reason") if isinstance(item.get("reason"), str) else None
                catalog_item = catalog_index[entity_id]
                results.append(
                    RecommendationEntry(
                        entity_id=entity_id,
                        reason=reason,
                        integration=catalog_item.integration,
                        integration_overview=integration_overview.get(catalog_item.integration),
                        name=catalog_item.name,
                        device_name=catalog_item.device_name,
                        disabled=catalog_item.disabled,
                        hidden=catalog_item.hidden,
                    )
                )

            requested_count = len(recommendations)

        if self._debug_enabled:
            LOGGER.debug(
                "Recommendations parsed: requested=%d matched=%d",
                requested_count,
                len(results),
            )

        return results


def _system_prompt() -> str:
    """Return the system prompt instructions for the agent."""
    return (
        "You are helping Home Assistant decide which entities should be exposed to voice assistants. "
        "Prefer actionable, user-facing entities.  Err on the side of including too many entities not too few. Include a limited amount of diagnostic entities and avoid duplicates but do include some. Include relatively few internal entities, and do not "
        "recommend entities that are disabled. Only include hidden entities in bold or aggressive runs.  Group related entities and explain why each "
        "group should be exposed in 1-2 sentences. "
        "Respond ONLY with valid JSON. Do not include Markdown, code fences, or extra commentary."
    )


def _build_prompt(
    catalog: list[EntityCatalogItem],
    *,
    custom_prompt: str | None,
    custom_prompt_enabled: bool,
    aggressiveness: str | None,
) -> str:
    """Build the user prompt with serialized entity metadata."""
    payload = _build_prompt_payload(catalog)
    aggressiveness_value = _normalize_aggressiveness(aggressiveness)
    guidance = "\n\n".join(
        [
            _format_aggressiveness_guidance(aggressiveness_value),
            _format_integration_overview_instructions(),
        ]
    )
    if custom_prompt_enabled and custom_prompt:
        return _build_custom_prompt(custom_prompt, payload, guidance)

    return _build_custom_prompt(DEFAULT_CUSTOM_PROMPT, payload, guidance)


def _build_prompt_payload(catalog: list[EntityCatalogItem]) -> dict[str, Any]:
    """Return the base payload for prompt rendering."""
    return {
        "requested_at": dt_util.utcnow().isoformat(),
        "entities": [item.as_prompt_dict() for item in catalog],
    }


def _build_custom_prompt(custom_prompt: str, payload: dict[str, Any], guidance: str) -> str:
    """Build the prompt using a user-supplied template."""
    entity_list = json.dumps(payload, ensure_ascii=True)
    visible_prompt = custom_prompt.replace("{entity_list}", "").strip()
    hidden_prompt = f"{HIDDEN_PROMPT_TEMPLATE}\n\n{guidance}\n\nEntity list:\n{entity_list}"
    if visible_prompt:
        return f"{visible_prompt}\n\n{hidden_prompt}"
    return hidden_prompt


def _normalize_aggressiveness(value: str | None) -> str:
    """Normalize aggressiveness input to a supported value."""
    if value in RECOMMENDATION_AGGRESSIVENESS_LEVELS:
        return value
    return DEFAULT_RECOMMENDATION_AGGRESSIVENESS


def _format_aggressiveness_guidance(level: str) -> str:
    """Return human-readable guidance for aggressiveness."""
    selected_level = level if level in RECOMMENDATION_AGGRESSIVENESS_LEVELS else DEFAULT_RECOMMENDATION_AGGRESSIVENESS
    options_text = (
        "Aggressiveness options: minimal (include only a few entities), gentle (small set), balanced "
        "(moderate set of useful entities), bold (broad coverage), maximal (very inclusive selection, most entities including diagnostic and debugging entities). "
        "Follow the selected aggressiveness to decide how many entities to include."
    )
    return f"{options_text} Selected aggressiveness for this run: {selected_level}."


def _format_integration_overview_instructions() -> str:
    """Return instructions for per-integration overviews."""
    return (
        "Also include an 'integration_overview' object keyed by integration domain. "
        "Each value must be a 2-3 sentence overview explaining why recommendations were made for that integration."
    )


def _parse_grouped_recommendations(
    payload: dict[str, Any],
    catalog_index: dict[str, EntityCatalogItem],
) -> list[RecommendationEntry]:
    """Parse grouped recommendations into recommendation entries."""
    groups = payload.get("groups")
    if not isinstance(groups, list):
        return []

    integration_overview = _extract_integration_overview(payload)

    results: list[RecommendationEntry] = []
    seen: set[str] = set()
    for group in groups:
        if not isinstance(group, dict):
            continue
        group_name = group.get("name") if isinstance(group.get("name"), str) else None
        group_reason = group.get("reason") if isinstance(group.get("reason"), str) else None
        entities = group.get("entities")
        if not isinstance(entities, list):
            continue

        for item in entities:
            if not isinstance(item, dict):
                continue
            entity_id = item.get("entity_id")
            if not entity_id or entity_id not in catalog_index or entity_id in seen:
                continue
            reason = item.get("reason") if isinstance(item.get("reason"), str) else None
            catalog_item = catalog_index[entity_id]
            results.append(
                RecommendationEntry(
                    entity_id=entity_id,
                    reason=reason,
                    group_name=group_name,
                    group_reason=group_reason,
                    integration=catalog_item.integration,
                    integration_overview=integration_overview.get(catalog_item.integration),
                    name=catalog_item.name,
                    device_name=catalog_item.device_name,
                    disabled=catalog_item.disabled,
                    hidden=catalog_item.hidden,
                )
            )
            seen.add(entity_id)

    return results


def _count_grouped_items(payload: dict[str, Any]) -> int:
    """Count the number of entities listed in grouped recommendations."""
    groups = payload.get("groups")
    if not isinstance(groups, list):
        return 0

    count = 0
    for group in groups:
        if not isinstance(group, dict):
            continue
        entities = group.get("entities")
        if isinstance(entities, list):
            count += len(entities)
    return count


def _extract_integration_overview(payload: dict[str, Any]) -> dict[str, str]:
    """Extract per-integration overview text from the payload."""
    raw = payload.get("integration_overview")
    if not isinstance(raw, dict):
        return {}
    return {key: value for key, value in raw.items() if isinstance(key, str) and isinstance(value, str)}


def _extract_response_text(speech: Any) -> str:
    """Extract text content from an intent response speech block."""
    if isinstance(speech, str):
        return speech
    if isinstance(speech, list):
        return "\n".join(str(item) for item in speech)
    if isinstance(speech, dict):
        if "plain" in speech and isinstance(speech["plain"], dict):
            return str(speech["plain"].get("speech", ""))
        if "ssml" in speech and isinstance(speech["ssml"], dict):
            return str(speech["ssml"].get("speech", ""))
    return ""


def _extract_json_payload(response_text: str) -> dict[str, Any]:
    """Extract JSON payload from a response text."""
    response_text = response_text.strip()
    if not response_text:
        raise AIExposeEntitiesAIClientError("AI response was empty")

    fenced_payload = _extract_json_from_fences(response_text)
    if fenced_payload is not None:
        return fenced_payload

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    start = response_text.find("{")
    end = response_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise AIExposeEntitiesAIClientError("AI response did not contain JSON")

    try:
        return json.loads(response_text[start : end + 1])
    except json.JSONDecodeError as err:
        raise AIExposeEntitiesAIClientError("AI response JSON was invalid") from err


def _extract_json_from_fences(response_text: str) -> dict[str, Any] | None:
    """Extract JSON object from Markdown-style code fences if present."""
    for match in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL | re.IGNORECASE):
        candidate = match.group(1).strip()
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _truncate_debug_text(text: str, *, limit: int = 2000) -> str:
    """Return a short preview suitable for debug logging."""
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...(truncated)"
