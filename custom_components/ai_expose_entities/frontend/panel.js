class AIExposeEntitiesPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._pending = [];
    this._approved = [];
    this._denied = [];
    this._lastRun = null;
    this._selected = new Set();
    this._loading = false;
    this._groupIndex = new Map();
    this._aggressiveness = "balanced";
    this._expandedGroups = new Set();
    this._runningRecommendation = false;
    this._stateMeta = {};
    this._loadingDetails = "";
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialized = true;
      this._render();
      this._fetchState();
    }
  }

  connectedCallback() {
    if (!this._initialized && this._hass) {
      this._initialized = true;
      this._render();
      this._fetchState();
    }
  }

  async _fetchState() {
    this._setLoading(true);
    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "ai_expose_entities/get_state",
      });
      this._applyState(result);
    } catch (err) {
      this._showError(err);
    } finally {
      this._setLoading(false);
    }
  }

  async _runRecommendation() {
    this._loadingDetails = this._buildRecommendationLoadingDetails();
    this._setRunningRecommendation(true);
    this._setLoading(true);
    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "ai_expose_entities/run_recommendation",
        aggressiveness: this._aggressiveness,
      });
      this._applyState(result, true);
    } catch (err) {
      this._showError(err);
    } finally {
      this._setRunningRecommendation(false);
      this._setLoading(false);
    }
  }

  async _applyDecisions() {
    this._loadingDetails = "";
    this._setLoading(true);
    const approved = Array.from(this._selected);

    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "ai_expose_entities/apply_decisions",
        approved,
        denied: [],
      });
      this._applyState(result, true);
    } catch (err) {
      this._showError(err);
    } finally {
      this._setLoading(false);
    }
  }

  async _blocklistSelected() {
    this._loadingDetails = "";
    this._setLoading(true);
    const denied = Array.from(this._selected);
    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "ai_expose_entities/apply_decisions",
        approved: [],
        denied,
      });
      this._applyState(result, true);
    } catch (err) {
      this._showError(err);
    } finally {
      this._setLoading(false);
    }
  }

  async _clearSuggestions() {
    this._loadingDetails = "";
    this._setLoading(true);
    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "ai_expose_entities/clear_suggestions",
        entity_ids: Array.from(this._selected),
      });
      this._applyState(result, true);
    } catch (err) {
      this._showError(err);
    } finally {
      this._setLoading(false);
    }
  }

  _applyState(state, resetSelection = false) {
    this._pending = Array.isArray(state.pending) ? state.pending : [];
    this._approved = Array.isArray(state.approved) ? state.approved : [];
    this._denied = Array.isArray(state.denied) ? state.denied : [];
    this._lastRun = state.last_run || null;
    this._stateMeta = state.meta && typeof state.meta === "object" ? state.meta : {};

    if (resetSelection || this._selected.size === 0) {
      this._selected = new Set(this._pending.map((entry) => entry.entity_id));
    } else {
      const current = new Set(this._pending.map((entry) => entry.entity_id));
      this._selected = new Set(
        Array.from(this._selected).filter((entityId) => current.has(entityId))
      );
      for (const entry of this._pending) {
        if (!this._selected.has(entry.entity_id)) {
          this._selected.add(entry.entity_id);
        }
      }
    }

    this._render();
  }

  _toggleGroup(groupName, checked) {
    const entries = this._groupIndex.get(groupName) || [];
    if (checked) {
      for (const entityId of entries) {
        this._selected.add(entityId);
      }
    } else {
      for (const entityId of entries) {
        this._selected.delete(entityId);
      }
    }
    this._render();
  }

  _toggleEntity(entityId, checked) {
    if (checked) {
      this._selected.add(entityId);
    } else {
      this._selected.delete(entityId);
    }
    this._updateSelectionCount();
    this._updateGroupToggles();
  }

  _toggleGroupExpanded(groupName) {
    if (this._expandedGroups.has(groupName)) {
      this._expandedGroups.delete(groupName);
    } else {
      this._expandedGroups.add(groupName);
    }
    this._render();
  }

  _setLoading(isLoading) {
    this._loading = isLoading;
    const loadingEl = this.querySelector(".ae-loading");
    if (loadingEl) {
      if (isLoading) {
        const details = this._loadingDetails ? ` ${this._loadingDetails}` : "";
        loadingEl.textContent = `Working...${details}`;
      } else {
        loadingEl.textContent = "";
      }
    }
    if (!isLoading) {
      this._loadingDetails = "";
    }
  }

  _setRunningRecommendation(isRunning) {
    this._runningRecommendation = isRunning;
    const runButton = this.querySelector("#run-recommendation");
    if (runButton) {
      runButton.disabled = isRunning;
    }
  }

  _showError(err) {
    const errorEl = this.querySelector(".ae-error");
    if (errorEl) {
      errorEl.textContent = err?.message || String(err);
    }
  }

  _buildRecommendationLoadingDetails() {
    const details = [];
    if (typeof this._stateMeta.catalog_size === "number") {
      details.push(`${this._stateMeta.catalog_size} entities considered`);
    }
    if (this._stateMeta.agent_id) {
      details.push(`Agent: ${this._stateMeta.agent_id}`);
    }
    if (this._aggressiveness) {
      details.push(`Aggressiveness: ${this._aggressiveness}`);
    }
    return details.join(" | ");
  }

  _updateSelectionCount() {
    const countEl = this.querySelector(".ae-selected-count");
    if (countEl) {
      countEl.textContent = `${this._selected.size} selected`;
    }
  }

  _groupPending() {
    const grouped = new Map();
    for (const entry of this._pending) {
      const integrationName = entry.integration || null;
      const aiGroupName = entry.group_name || null;
      const groupName = integrationName || aiGroupName || "Ungrouped";
      const groupKind = integrationName ? "integration" : aiGroupName ? "ai" : "ungrouped";

      if (!grouped.has(groupName)) {
        grouped.set(groupName, {
          name: groupName,
          kind: groupKind,
          reason: groupKind === "ai" ? entry.group_reason || null : null,
          integrationOverview:
            groupKind === "integration" ? entry.integration_overview || null : null,
          entries: [],
        });
      }

      const group = grouped.get(groupName);
      if (group) {
        if (group.kind !== "integration" && groupKind === "integration") {
          group.kind = "integration";
          group.reason = null;
          group.integrationOverview = entry.integration_overview || null;
        }
        if (!group.reason && group.kind === "ai" && entry.group_reason) {
          group.reason = entry.group_reason;
        }
        if (!group.integrationOverview && group.kind === "integration" && entry.integration_overview) {
          group.integrationOverview = entry.integration_overview;
        }
        group.entries.push(entry);
      }
    }
    return Array.from(grouped.values()).sort((a, b) => a.name.localeCompare(b.name));
  }

  _aggressivenessOptions() {
    return [
      { value: "minimal", label: "Minimal" },
      { value: "gentle", label: "Gentle" },
      { value: "balanced", label: "Balanced" },
      { value: "bold", label: "Bold" },
      { value: "maximal", label: "Maximal" },
    ];
  }

  _updateGroupToggles() {
    this.querySelectorAll("input[data-group-name]").forEach((input) => {
      const groupName = input.getAttribute("data-group-name");
      if (!groupName) {
        return;
      }
      const entries = this._groupIndex.get(groupName) || [];
      const selectedCount = entries.filter((entityId) => this._selected.has(entityId)).length;
      input.checked = selectedCount > 0 && selectedCount === entries.length;
      input.indeterminate = selectedCount > 0 && selectedCount < entries.length;
    });
  }

  _render() {
    const grouped = this._groupPending();
    const lastRun = this._lastRun ? new Date(this._lastRun).toLocaleString() : "Never";
    const selectedCount = this._selected.size;
    const aggressivenessOptions = this._aggressivenessOptions();
    this._groupIndex = new Map(
      grouped.map((group) => [group.name, group.entries.map((entry) => entry.entity_id)])
    );

    this.innerHTML = `
      <style>
                @media (prefers-color-scheme: dark) {
                  :host {
                    color: #e5e7eb;
                    background: radial-gradient(circle at 10% 10%, #23272f, #1e293b 45%, #23272f 100%);
                  }
                  .ae-shell {
                    background: #23272f;
                    box-shadow: 0 20px 50px rgba(24, 24, 27, 0.18);
                  }
                  .ae-title {
                    color: #f3f4f6;
                  }
                  .ae-section-title {
                    color: #e5e7eb;
                  }
                  .ae-subtitle {
                    color: #a1a1aa;
                  }
                  .ae-card {
                    background: #1e293b;
                    border: 1px solid #374151;
                  }
                  .ae-group-reason {
                    color: #a1a1aa;
                  }
                  .ae-group-toggle {
                    background: #23272f;
                    color: #60a5fa;
                    border: 1px solid #374151;
                  }
                  .ae-expand-toggle {
                    background: #23272f;
                    color: #60a5fa;
                    border: 1px solid #374151;
                  }
                  .ae-group-count {
                    color: #60a5fa;
                  }
                  .ae-entity-meta {
                    color: #a1a1aa;
                  }
                  .ae-tag {
                    background: #374151;
                    color: #60a5fa;
                  }
                  .ae-tag.warn {
                    background: #7f1d1d;
                    color: #fca5a5;
                  }
                  .ae-button {
                    background: #2563eb;
                    color: #f3f4f6;
                  }
                  .ae-button.secondary {
                    background: #374151;
                    color: #60a5fa;
                    border: 1px solid #60a5fa;
                  }
                  .ae-button.danger {
                    background: #7f1d1d;
                    color: #fca5a5;
                    border: 1px solid #fca5a5;
                  }
                  .ae-button.ghost {
                    background: #23272f;
                    color: #e5e7eb;
                    border: 1px dashed #374151;
                  }
                  .ae-error {
                    color: #fca5a5;
                  }
                  .ae-loading {
                    color: #60a5fa;
                  }
                }
        :host {
          display: block;
          padding: 24px;
          font-family: "Sora", "Avenir Next", "Segoe UI", sans-serif;
          color: #1e1d22;
          background: radial-gradient(circle at 10% 10%, #f7f4ed, #eef4ff 45%, #f2f2f8 100%);
          min-height: 100vh;
        }
        .ae-shell {
          max-width: 1100px;
          margin: 0 auto;
          background: #ffffff;
          border-radius: 20px;
          padding: 24px;
          box-shadow: 0 20px 50px rgba(24, 24, 27, 0.08);
        }
        .ae-header {
          display: flex;
          flex-wrap: wrap;
          justify-content: space-between;
          gap: 16px;
          align-items: center;
          margin-bottom: 20px;
        }
        .ae-title {
          font-size: 24px;
          letter-spacing: -0.02em;
          color: #23272f;
        }
        .ae-subtitle {
          font-size: 14px;
          color: #585260;
        }
        .ae-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          align-items: center;
        }
        .ae-aggressiveness {
          display: flex;
          flex-direction: column;
          gap: 6px;
          min-width: 220px;
        }
        .ae-aggressiveness label {
          font-size: 11px;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #6b7280;
        }
        .ae-aggressiveness select {
          padding: 8px 12px;
          border-radius: 12px;
          border: 1px solid #c7d2fe;
          background: #ffffff;
          font-size: 14px;
          color: #1f2937;
        }
        .ae-aggressiveness .ae-help {
          font-size: 12px;
          color: #6b7280;
        }
        .ae-button {
          padding: 10px 16px;
          border-radius: 999px;
          border: none;
          cursor: pointer;
          background: #1f3b8f;
          color: #ffffff;
          font-weight: 600;
        }
        .ae-button:disabled {
          cursor: not-allowed;
          opacity: 0.6;
        }
        .ae-button.secondary {
          background: #eef2ff;
          color: #1f3b8f;
          border: 1px solid #c7d2fe;
        }
        .ae-button.danger {
          background: #fee2e2;
          color: #9f1239;
          border: 1px solid #fecdd3;
        }
        .ae-button.ghost {
          background: #f8fafc;
          color: #1f2937;
          border: 1px dashed #cbd5f5;
        }
        .ae-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 16px;
        }
        .ae-card {
          border-radius: 16px;
          padding: 16px;
          background: #f9fafb;
          border: 1px solid #eceff4;
        }
        .ae-group-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 8px;
        }
        .ae-section-title {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
          text-transform: capitalize;
          color: #1f2937;
        }
        .ae-group-reason {
          font-size: 12px;
          color: #374151;
        }
        .ae-group-toggle {
          display: inline-flex;
          gap: 8px;
          align-items: center;
          font-size: 12px;
          color: #1f3b8f;
          background: #eef2ff;
          padding: 6px 10px;
          border-radius: 999px;
          border: 1px solid #c7d2fe;
        }
        .ae-group-controls {
          display: inline-flex;
          gap: 8px;
          align-items: center;
        }
        .ae-expand-toggle {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          border-radius: 999px;
          border: 1px solid #c7d2fe;
          background: #ffffff;
          color: #1f3b8f;
          cursor: pointer;
        }
        .ae-expand-toggle[aria-expanded="true"] .ae-expand-icon {
          transform: rotate(90deg);
        }
        .ae-expand-icon {
          display: inline-block;
          transition: transform 0.2s ease;
        }
        .ae-group-count {
          font-size: 12px;
          color: #4338ca;
        }
        .ae-entity {
          display: grid;
          grid-template-columns: auto 1fr;
          gap: 12px;
          padding: 10px 0;
          border-bottom: 1px solid #e5e7eb;
        }
        .ae-entity:last-child {
          border-bottom: none;
        }
        .ae-entity-name {
          font-weight: 600;
          font-size: 14px;
        }
        .ae-entity-meta {
          font-size: 12px;
          color: #6b7280;
        }
        .ae-tags {
          display: inline-flex;
          gap: 6px;
          margin-top: 4px;
        }
        .ae-tag {
          font-size: 11px;
          padding: 2px 6px;
          border-radius: 999px;
          background: #e0e7ff;
          color: #3730a3;
        }
        .ae-tag.warn {
          background: #fee2e2;
          color: #991b1b;
        }
        .ae-footer {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          align-items: center;
          margin-top: 16px;
        }
        .ae-error {
          color: #b91c1c;
          font-size: 13px;
        }
        .ae-loading {
          color: #1f3b8f;
          font-size: 13px;
        }
        @media (max-width: 720px) {
          .ae-header {
            flex-direction: column;
            align-items: flex-start;
          }
          .ae-actions {
            width: 100%;
          }
          .ae-aggressiveness {
            width: 100%;
          }
          .ae-button {
            width: 100%;
            justify-content: center;
          }
        }
      </style>
      <div class="ae-shell">
        <div class="ae-header">
          <div>
            <div class="ae-title">AI Entity Exposure</div>
            <div class="ae-subtitle">Last run: ${lastRun}</div>
            <div class="ae-subtitle">Pending: ${this._pending.length} | Approved: ${this._approved.length} | Denied: ${this._denied.length}</div>
          </div>
          <div class="ae-actions">
            <div class="ae-aggressiveness">
              <label for="recommendation-aggressiveness">Aggressiveness</label>
              <select id="recommendation-aggressiveness">
                ${aggressivenessOptions
                  .map(
                    (option) =>
                      `<option value="${option.value}" ${
                        this._aggressiveness === option.value ? "selected" : ""
                      }>${option.label}</option>`
                  )
                  .join("")}
              </select>
              <div class="ae-help">
                Minimal may make few to no suggestions. Maximal may suggest up to 50% or more.
              </div>
            </div>
            <button class="ae-button" id="run-recommendation" ${
              this._runningRecommendation ? "disabled" : ""
            }>Generate Recommendations</button>
            <button class="ae-button secondary" id="apply-decisions">Apply Selected</button>
            <button class="ae-button danger" id="blocklist-selected">Blocklist Selected</button>
            <button class="ae-button ghost" id="clear-suggestions">Clear Suggestions</button>
          </div>
        </div>
        <div class="ae-footer">
          <div class="ae-selected-count">${selectedCount} selected</div>
          <div class="ae-loading"></div>
          <div class="ae-error"></div>
        </div>
        <div class="ae-grid">
          ${grouped
            .map(
              (group) => {
                const isIntegration = group.kind === "integration";
                const isExpanded = !isIntegration || this._expandedGroups.has(group.name);
                return `
                <div class="ae-card">
                  <div class="ae-group-header">
                    <div>
                      <div class="ae-section-title">${group.name}</div>
                      ${
                        isIntegration
                          ? `<div class="ae-group-count">${group.entries.length} recommendations</div>`
                          : ""
                      }
                      <div class="ae-group-reason">${
                        group.kind === "integration"
                          ? group.integrationOverview || `Entities from the ${group.name} integration.`
                          : group.reason || "No group reason provided"
                      }</div>
                    </div>
                    <div class="ae-group-controls">
                      <label class="ae-group-toggle">
                        <input type="checkbox" data-group-name="${group.name}" />
                        <span>Select all</span>
                      </label>
                      ${
                        isIntegration
                          ? `<button class="ae-expand-toggle" type="button" data-expand-group="${group.name}" aria-expanded="${
                              isExpanded
                            }" aria-label="Toggle ${group.name} recommendations">
                              <span class="ae-expand-icon">></span>
                            </button>`
                          : ""
                      }
                    </div>
                  </div>
                  <div class="ae-group-entries" ${isExpanded ? "" : "hidden"}>
                  ${group.entries
                    .map(
                      (entry) => `
                        <label class="ae-entity">
                          <input type="checkbox" data-entity-id="${entry.entity_id}" ${
                            this._selected.has(entry.entity_id) ? "checked" : ""
                          } />
                          <div>
                            <div class="ae-entity-name">${entry.name}</div>
                            <div class="ae-entity-meta">${entry.entity_id} ${
                        entry.device_name ? `| ${entry.device_name}` : ""
                      }</div>
                            <div class="ae-entity-meta">${entry.reason || "No reason provided"}</div>
                            <div class="ae-tags">
                              ${
                                entry.group_name && group.kind === "integration"
                                  ? `<span class="ae-tag">${entry.group_name}</span>`
                                  : ""
                              }
                              ${entry.disabled ? '<span class="ae-tag warn">Disabled</span>' : ""}
                              ${entry.hidden ? '<span class="ae-tag warn">Hidden</span>' : ""}
                            </div>
                          </div>
                        </label>
                      `
                    )
                    .join("")}
                  </div>
                </div>
              `;
              }
            )
            .join("")}
        </div>
      </div>
    `;

    this.querySelector("#run-recommendation")?.addEventListener("click", () =>
      this._runRecommendation()
    );
    this.querySelector("#apply-decisions")?.addEventListener("click", () =>
      this._applyDecisions()
    );
    this.querySelector("#blocklist-selected")?.addEventListener("click", () =>
      this._blocklistSelected()
    );
    this.querySelector("#clear-suggestions")?.addEventListener("click", () =>
      this._clearSuggestions()
    );
    this.querySelector("#recommendation-aggressiveness")?.addEventListener(
      "change",
      (event) => {
        const target = event.target;
        if (!target || !target.value) {
          return;
        }
        this._aggressiveness = target.value;
      }
    );
    this.querySelectorAll("input[data-group-name]").forEach((input) => {
      const groupName = input.getAttribute("data-group-name");
      if (!groupName) {
        return;
      }
      input.addEventListener("change", (event) => {
        const target = event.target;
        this._toggleGroup(groupName, target.checked);
      });
    });

    this.querySelectorAll("input[data-entity-id]").forEach((input) => {
      input.addEventListener("change", (event) => {
        const target = event.target;
        const entityId = target.getAttribute("data-entity-id");
        if (!entityId) {
          return;
        }
        this._toggleEntity(entityId, target.checked);
      });
    });

    this.querySelectorAll("button[data-expand-group]").forEach((button) => {
      button.addEventListener("click", () => {
        const groupName = button.getAttribute("data-expand-group");
        if (!groupName) {
          return;
        }
        this._toggleGroupExpanded(groupName);
      });
    });

    this._updateGroupToggles();
  }
}

customElements.define("ai-expose-entities-panel", AIExposeEntitiesPanel);
