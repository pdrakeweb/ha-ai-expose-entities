## Plan: AI-Driven Entity Exposure

The integration will gather entity metadata from the registry, ask a selected HA LLM provider to recommend which entities to expose to Assist, store recommendations alongside pending/approved/denied state, and provide a custom panel for user review. We will implement an on-demand recommendation run (from the panel and a service) and optionally schedule a daily run based on options. The plan assumes Assist exposure is controlled via the entity registry and that HA’s built-in LLM/Conversation APIs are the provider interface; we will verify both APIs and the correct exposure flags before coding.

**Steps**

1. Confirm HA APIs for Assist exposure, LLM/conversation calls, and custom panel registration; review HA developer docs for exposure flags and panel patterns, then map the chosen APIs into the integration (no code yet).
2. Define persistent state for recommendations and decisions using `homeassistant.helpers.storage.Store` in a new helper module, and extend `AIExposeEntitiesData` to hold store + in-memory caches in [custom_components/ai_expose_entities/data.py](custom_components/ai_expose_entities/data.py).
3. Implement an entity catalog builder that gathers entity metadata and groups by integration using the entity/device registries; place helper logic in a new module under utils (e.g., custom_components/ai_expose_entities/utils/entity_catalog.py) and keep deny-list filtering there.
4. Add an AI client wrapper that uses HA’s LLM/Conversation interface to submit a structured prompt and parse a structured response (JSON list of entity_ids + reasoning); implement in a new module under api and wire into [custom_components/ai_expose_entities/api/client.py](custom_components/ai_expose_entities/api/client.py) or a sibling module.
5. Update the coordinator to expose a method like `async_run_recommendation()` that calls the AI client, merges results into pending/proposed state, and updates storage; ensure deny-list exclusions are applied before prompting in [custom_components/ai_expose_entities/coordinator/base.py](custom_components/ai_expose_entities/coordinator/base.py).
6. Add service actions for on-demand recommendation run and for applying approval/deny decisions; define schemas in [custom_components/ai_expose_entities/services.yaml](custom_components/ai_expose_entities/services.yaml) and handlers in [custom_components/ai_expose_entities/service_actions/**init**.py](custom_components/ai_expose_entities/service_actions/__init__.py).
7. Implement Assist exposure updates by writing to the entity registry options for Assist exposure (exact key confirmed in step 1); centralize this logic in a helper module and call it from services and the panel approval flow.
8. Build a custom panel UI that shows grouped entities, recommended selections, and allow approve/deny with bulk actions; register a panel module in [custom_components/ai_expose_entities/**init**.py](custom_components/ai_expose_entities/__init__.py) and add a frontend JS bundle under custom_components/ai_expose_entities/frontend/ plus websocket endpoints in a new custom_components/ai_expose_entities/websocket.py for data fetch and submit.
9. Update the config flow/options to remove username/password, add LLM provider/model selection, and daily schedule settings; implement options in [custom_components/ai_expose_entities/config_flow_handler/options_flow.py](custom_components/ai_expose_entities/config_flow_handler/options_flow.py) and schemas in [custom_components/ai_expose_entities/config_flow_handler/schemas/options.py](custom_components/ai_expose_entities/config_flow_handler/schemas/options.py).
10. Wire daily scheduling based on options using HA’s event helpers; schedule the recommendation run and reconfigure on options change in [custom_components/ai_expose_entities/**init**.py](custom_components/ai_expose_entities/__init__.py) or a new scheduler helper module.
11. Update diagnostics to include counts and timestamps for approved/denied/pending and provider info in [custom_components/ai_expose_entities/diagnostics.py](custom_components/ai_expose_entities/diagnostics.py), ensuring redaction of any provider tokens if present.
12. Adjust manifest and translations to reflect the new functionality (panel title, service names, options labels); update [custom_components/ai_expose_entities/manifest.json](custom_components/ai_expose_entities/manifest.json) and [custom_components/ai_expose_entities/translations/en.json](custom_components/ai_expose_entities/translations/en.json). If this changes config entry data shape, add a migration path in [custom_components/ai_expose_entities/**init**.py](custom_components/ai_expose_entities/__init__.py).

**Verification**

- Perform a deep code review. Examine the entity catalog builder for correct metadata gathering and deny-list filtering, the AI client for proper prompt construction and response parsing, and the coordinator for correct state management and storage updates.
- Review common HomeAssistant coding patterns for API calls, service handling, and panel integration and ensure that templates are followed correctly.
- Write unit tests for any complex functionality and implement python test scripts that can be run with `pytest` to validate the core logic of the entity catalog builder, AI client, and coordinator recommendation flow.
- Run the pytest suite to ensure all tests pass.
- Run `./script/check` after implementation.
- Run the integration in a dev HA instance, trigger the recommendation flow, and verify that entities are recommended, approvals/denials update state correctly, and Assist exposure flags are set in the entity registry as expected.
- Manual: open the custom panel, run recommendation, approve/deny, confirm Assist exposure toggles in the entity registry, and validate daily schedule triggers.

**Decisions**

- Use Home Assistant Assist exposure controls as the target system.
- Use HA’s built-in LLM/Conversation APIs for model access.
- Provide a custom panel UI for review and approvals.
- Offer an on-demand run from the panel plus optional daily scheduling via options.
