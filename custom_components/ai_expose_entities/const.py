"""Constants for ai_expose_entities."""

from datetime import time
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# Integration metadata
DOMAIN = "ai_expose_entities"
ATTRIBUTION = "Data provided by Home Assistant"

# Platform parallel updates - applied to all platforms
PARALLEL_UPDATES = 1


# Configuration keys
CONF_AGENT_ID = "ai_task_id"
CONF_CUSTOM_PROMPT = "custom_prompt"
CONF_CUSTOM_PROMPT_ENABLED = "custom_prompt_enabled"
CONF_ENABLE_DEBUGGING = "enable_debugging"
CONF_RECOMMENDATION_AGGRESSIVENESS = "aggressiveness"
CONF_TEST_ENTITIES = "test_entities"
CONF_TEST_ENTITIES_ENABLED = "enabled"
CONF_TEST_ENTITY_COUNT = "count"
CONF_TEST_ENTITY_RELEVANT_COUNT = "relevant_count"
CONF_TEST_ENTITY_SEED = "seed"
CONF_SCHEDULE_ENABLED = "schedule_enabled"
CONF_SCHEDULE_TIME = "schedule_time"
# New: Entity sample size
CONF_ENTITY_SAMPLE_SIZE = "entity_sample_size"

# UI constants
PANEL_URL_PATH = "ai-expose-entities"
PANEL_TITLE = "AI Expose Entities"
PANEL_ICON = "mdi:robot"


# Default configuration values
DEFAULT_ENABLE_DEBUGGING = False
DEFAULT_RECOMMENDATION_AGGRESSIVENESS = "balanced"
DEFAULT_CUSTOM_PROMPT = (
    "You are helping Home Assistant decide which entities should be exposed to the Assist voice assistant. "
    "Prioritize actionable, user-facing entities (lights, switches, climate, media, cameras, sensors, etc)."
)
HIDDEN_PROMPT_TEMPLATE = (
    "Review the JSON entity list and recommend the best entities to expose. "
    "Avoid diagnostic, configuration, or hidden/disabled entities. "
    "Group related entities under clear group names and give a short reason for each group (1-2 sentences). "
    "For each entity, provide a short reason tied to expected voice control value. "
    "Only include entities from the list. "
    "Return ONLY valid JSON with this exact schema (no Markdown, no extra keys):\n"
    '{"integration_overview": {"light": "2-3 sentences"}, "groups": '
    '[{"name": "Lighting", "reason": "Common voice control", "entities": '
    '[{"entity_id": "light.kitchen", "reason": "Frequently used"}]}]}'
)
DEFAULT_CUSTOM_PROMPT_ENABLED = False
DEFAULT_SCHEDULE_ENABLED = False
DEFAULT_SCHEDULE_TIME = time(2, 0)
DEFAULT_TEST_ENTITIES_ENABLED = False
DEFAULT_TEST_ENTITY_COUNT = 0
DEFAULT_TEST_ENTITY_RELEVANT_COUNT = 0
DEFAULT_TEST_ENTITY_SEED = 12345
# New: Default entity sample size
DEFAULT_ENTITY_SAMPLE_SIZE = 500

RECOMMENDATION_AGGRESSIVENESS_LEVELS = (
    "minimal",
    "gentle",
    "balanced",
    "bold",
    "maximal",
)
