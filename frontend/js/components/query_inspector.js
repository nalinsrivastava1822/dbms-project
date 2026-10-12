/**
 * Backend Query Inspector — Terminal Component for Live Cypher Demonstrations.
 * Intercepts, records, and renders real-time backend Cypher query executions
 * with syntax highlighting, parameter inspection, execution duration, and controls.
 */
const QueryInspector = {
    traces: [],
    isExpanded: false,
    autoScroll: true,
    filterText: '',
    filterStatus: 'ALL',
    maxTraces: 200,

    init() {
        this.createDOM();
        this.bindEvents();
        this.fetchInitialHistory();
    },

    createDOM() {
        // Avoid duplicate creation
        if (document.getElementById('query-inspector-panel')) return;

        const panel = document.createElement('aside');
        panel.id = 'query-inspector-panel';
        panel.className = 'query-inspector collapsed';
        panel.setAttribute('aria-label', 'Backend Query Inspector Terminal');

        panel.innerHTML = `
            <!-- Collapsed Bar / Header -->
            <div class="qi-header" id="qi-header" title="Click to Expand / Collapse Query Inspector">
                <div class="qi-header-left">
                    <span class="qi-pulse-dot" id="qi-pulse"></span>
                    <span class="qi-title">⚡ Backend Query Inspector</span>
                    <span class="qi-badge" id="qi-count-badge">0 queries</span>
                    <span class="qi-last-preview" id="qi-last-preview">Waiting for backend operations…</span>
                </div>
                <div class="qi-header-right">
                    <span class="qi-latency-badge" id="qi-last-latency">- ms</span>
                    <button type="button" class="qi-btn-text" id="qi-clear-btn" title="Clear terminal output">🗑️ Clear</button>
                    <button type="button" class="qi-toggle-btn" id="qi-toggle-btn" aria-label="Toggle terminal panel">
                        <span id="qi-toggle-icon">▲</span>
                    </button>
                </div>
            </div>

            <!-- Expanded Body -->
            <div class="qi-body" id="qi-body">
                <!-- Toolbar -->
                <div class="qi-toolbar">
                    <div class="qi-toolbar-left">
                        <span class="qi-tech-pill">Database: Neo4j (Cypher)</span>
                        <input type="text" id="qi-search-input" class="qi-search" placeholder="Filter queries or actions…">
                        <select id="qi-status-filter" class="qi-select">
                            <option value="ALL">All Statuses</option>
                            <option value="SUCCESS">Success Only</option>
                            <option value="FAILURE">Failures Only</option>
                        </select>
                    </div>
                    <div class="qi-toolbar-right">
                        <label class="qi-checkbox-label">
                            <input type="checkbox" id="qi-autoscroll" checked> Auto-scroll
                        </label>
                        <button type="button" class="qi-btn-sm" id="qi-copy-all-btn" title="Copy all traces to clipboard">📋 Copy All</button>
                        <button type="button" class="qi-btn-sm qi-btn-danger" id="qi-clear-all-btn" title="Clear history">Clear History</button>
                    </div>
                </div>

                <!-- Terminal Content Container -->
                <div class="qi-terminal-output" id="qi-output" role="log" aria-live="polite">
                    <div class="qi-empty-state" id="qi-empty">
                        <div class="qi-empty-icon">⚡</div>
                        <p class="qi-empty-title">Perform an action in the system to inspect its real-time backend Cypher query.</p>
                        <p class="qi-empty-hint">Try searching rooms, booking a stay, registering a guest, or viewing reservations above.</p>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(panel);
    },

    bindEvents() {
        const header = document.getElementById('qi-header');
        const toggleBtn = document.getElementById('qi-toggle-btn');
        const clearBtn = document.getElementById('qi-clear-btn');
        const clearAllBtn = document.getElementById('qi-clear-all-btn');
        const copyAllBtn = document.getElementById('qi-copy-all-btn');
        const autoScrollCb = document.getElementById('qi-autoscroll');
        const searchInput = document.getElementById('qi-search-input');
        const statusFilter = document.getElementById('qi-status-filter');

        if (header) {
            header.addEventListener('click', (e) => {
                // Don't toggle if clicking a button inside header
                if (e.target.closest('button')) return;
                this.toggle();
            });
        }

        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggle();
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.clear();
            });
        }

        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clear());
        }

        if (copyAllBtn) {
            copyAllBtn.addEventListener('click', () => this.copyAll());
        }

        if (autoScrollCb) {
            autoScrollCb.addEventListener('change', (e) => {
                this.autoScroll = e.target.checked;
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterText = e.target.value.toLowerCase().trim();
                this.renderEntries();
            });
        }

        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterStatus = e.target.value;
                this.renderEntries();
            });
        }
    },

    toggle() {
        this.isExpanded = !this.isExpanded;
        const panel = document.getElementById('query-inspector-panel');
        const icon = document.getElementById('qi-toggle-icon');
        if (panel) {
            panel.classList.toggle('collapsed', !this.isExpanded);
            panel.classList.toggle('expanded', this.isExpanded);
        }
        if (icon) {
            icon.textContent = this.isExpanded ? '▼' : '▲';
        }

        // Adjust document body padding so dashboard content isn't obscured
        document.body.style.paddingBottom = this.isExpanded ? '370px' : '46px';

        if (this.isExpanded && this.autoScroll) {
            this.scrollToBottom();
        }
    },

    async fetchInitialHistory() {
        try {
            const history = await API.getQueryHistory();
            if (Array.isArray(history) && history.length > 0) {
                this.addTraces(history, false);
            }
        } catch (_) {
            // Optional: Inspector will populate on first live user action
        }
    },

    /**
     * Add new traces to the terminal and update badges.
     * @param {Array} newTraces
     * @param {boolean} triggerPulse
     */
    addTraces(newTraces, triggerPulse = true) {
        if (!Array.isArray(newTraces) || newTraces.length === 0) return;

        newTraces.forEach(t => {
            // Prevent exact duplicates by ID if already present
            if (!this.traces.some(existing => existing.id === t.id)) {
                this.traces.push(t);
            }
        });

        if (this.traces.length > this.maxTraces) {
            this.traces = this.traces.slice(-this.maxTraces);
        }

        const latest = this.traces[this.traces.length - 1];
        this.updateHeader(latest, triggerPulse);
        this.renderEntries();

        if (this.isExpanded && this.autoScroll) {
            this.scrollToBottom();
        }
    },

    updateHeader(latest, triggerPulse = true) {
        const countBadge = document.getElementById('qi-count-badge');
        const preview = document.getElementById('qi-last-preview');
        const latency = document.getElementById('qi-last-latency');
        const pulse = document.getElementById('qi-pulse');

        if (countBadge) {
            countBadge.textContent = `${this.traces.length} execution${this.traces.length === 1 ? '' : 's'}`;
        }

        if (latest) {
            if (preview) {
                const querySnippet = (latest.cypher || '').replace(/\s+/g, ' ').slice(0, 75);
                preview.textContent = `${latest.action}: ${querySnippet}…`;
                preview.title = latest.cypher;
            }
            if (latency) {
                latency.textContent = `${latest.duration_ms} ms`;
                latency.className = latest.status === 'SUCCESS' ? 'qi-latency-badge success' : 'qi-latency-badge error';
            }
        }

        if (triggerPulse && pulse) {
            pulse.classList.remove('pulse-active');
            void pulse.offsetWidth; // Reflow
            pulse.classList.add('pulse-active');
        }
    },

    renderEntries() {
        const container = document.getElementById('qi-output');
        if (!container) return;

        let filtered = this.traces;

        if (this.filterStatus !== 'ALL') {
            filtered = filtered.filter(t => t.status === this.filterStatus);
        }

        if (this.filterText) {
            filtered = filtered.filter(t =>
                (t.action && t.action.toLowerCase().includes(this.filterText)) ||
                (t.cypher && t.cypher.toLowerCase().includes(this.filterText)) ||
                (t.endpoint && t.endpoint.toLowerCase().includes(this.filterText)) ||
                (JSON.stringify(t.parameters || {}).toLowerCase().includes(this.filterText))
            );
        }

        if (filtered.length === 0) {
            if (this.traces.length === 0) {
                container.innerHTML = `
                    <div class="qi-empty-state" id="qi-empty">
                        <div class="qi-empty-icon">⚡</div>
                        <p class="qi-empty-title">Perform an action in the system to inspect its real-time backend Cypher query.</p>
                        <p class="qi-empty-hint">Try searching rooms, booking a stay, registering a guest, or viewing reservations above.</p>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="qi-empty-state">
                        <div class="qi-empty-icon">🔍</div>
                        <p class="qi-empty-title">No queries match the active filter "${this.filterText}".</p>
                    </div>
                `;
            }
            return;
        }

        container.innerHTML = filtered.map((t, idx) => this.renderEntryHTML(t, idx + 1)).join('');
    },

    renderEntryHTML(t, num) {
        const isSuccess = t.status === 'SUCCESS';
        const statusClass = isSuccess ? 'status-success' : 'status-failed';
        const statusBadge = isSuccess
            ? '<span class="qi-status-pill success">✓ SUCCESS</span>'
            : '<span class="qi-status-pill error">✕ FAILURE</span>';

        const paramsJSON = t.parameters && Object.keys(t.parameters).length > 0
            ? JSON.stringify(t.parameters, null, 2)
            : 'None (Parameterless query)';

        const highlightedCypher = this.highlightCypher(t.cypher);

        const recordCountText = t.records_count !== undefined && t.records_count !== null
            ? `${t.records_count} record${t.records_count === 1 ? '' : 's'} returned / affected`
            : 'Execution completed';

        return `
            <article class="qi-card ${statusClass}" id="qi-card-${t.id}">
                <div class="qi-card-meta">
                    <div class="qi-card-meta-left">
                        <span class="qi-entry-num">#${t.id || num}</span>
                        <span class="qi-timestamp">${t.time_display || t.timestamp}</span>
                        <strong class="qi-action-title">${this.escapeHTML(t.action)}</strong>
                        <span class="qi-endpoint-tag">${this.escapeHTML(t.endpoint || '')}</span>
                    </div>
                    <div class="qi-card-meta-right">
                        <span class="qi-db-tag">Database: ${t.database || 'Neo4j'}</span>
                        <span class="qi-duration-tag">⏱ ${t.duration_ms} ms</span>
                        ${statusBadge}
                        <button type="button" class="qi-card-copy-btn" onclick="QueryInspector.copyQuery(${t.id})" title="Copy Cypher query">
                            📋 Copy Cypher
                        </button>
                    </div>
                </div>

                <div class="qi-card-sections">
                    <!-- CYPHER SECTION -->
                    <div class="qi-section">
                        <div class="qi-section-header">
                            <span class="qi-section-label">CYPHER:</span>
                        </div>
                        <pre class="qi-code-block cypher"><code>${highlightedCypher}</code></pre>
                    </div>

                    <!-- PARAMETERS & RESULT ROW -->
                    <div class="qi-grid-2">
                        <div class="qi-section">
                            <div class="qi-section-header">
                                <span class="qi-section-label">PARAMETERS:</span>
                            </div>
                            <pre class="qi-code-block params"><code>${this.escapeHTML(paramsJSON)}</code></pre>
                        </div>
                        <div class="qi-section">
                            <div class="qi-section-header">
                                <span class="qi-section-label">RESULT:</span>
                            </div>
                            <div class="qi-result-box ${isSuccess ? 'success' : 'error'}">
                                ${isSuccess
                                    ? `<div class="qi-result-text">✓ ${this.escapeHTML(recordCountText)}</div>`
                                    : `<div class="qi-error-text">⚠️ ${this.escapeHTML(t.error || 'Execution failed on Neo4j engine')}</div>`
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </article>
        `;
    },

    highlightCypher(cypher) {
        if (!cypher) return '';
        let escaped = this.escapeHTML(cypher);

        const keywords = [
            'MATCH', 'OPTIONAL MATCH', 'WHERE', 'RETURN', 'CREATE', 'MERGE',
            'SET', 'DELETE', 'REMOVE', 'WITH', 'ORDER BY', 'ASC', 'DESC',
            'LIMIT', 'SKIP', 'UNION', 'AS', 'IN', 'AND', 'OR', 'NOT',
            'EXISTS', 'COUNT', 'DISTINCT', 'COLLECT', 'LABELS', 'PROPERTIES'
        ];

        // Sort by length descending to match composite keywords first (e.g. 'OPTIONAL MATCH' before 'MATCH')
        keywords.sort((a, b) => b.length - a.length);

        keywords.forEach(kw => {
            const regex = new RegExp(`\\b(${kw})\\b`, 'g');
            escaped = escaped.replace(regex, '<span class="kw">$1</span>');
        });

        // Highlight parameter variables like $param
        escaped = escaped.replace(/(\$[a-zA-Z0-9_]+)/g, '<span class="param-var">$1</span>');

        // Highlight relationship types like [:BOOKS]
        escaped = escaped.replace(/(\[:[A-Za-z0-9_]+\])/g, '<span class="rel-var">$1</span>');

        // Highlight node labels like (:Room)
        escaped = escaped.replace(/(\(:[A-Za-z0-9_]+)/g, '<span class="label-var">$1</span>');

        return escaped;
    },

    escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    },

    copyQuery(id) {
        const item = this.traces.find(t => t.id === id);
        if (!item || !item.cypher) return;
        navigator.clipboard.writeText(item.cypher)
            .then(() => App.toast(`Copied Cypher query #${id} to clipboard!`, 'success'))
            .catch(() => App.toast('Could not copy query', 'error'));
    },

    copyAll() {
        if (this.traces.length === 0) {
            App.toast('No queries to copy', 'info');
            return;
        }

        const formatted = this.traces.map((t, i) => `
============================================================
[#${t.id || i + 1}] ACTION: ${t.action}
ENDPOINT: ${t.endpoint}
DATABASE: ${t.database}
STATUS: ${t.status}
DURATION: ${t.duration_ms} ms
TIMESTAMP: ${t.timestamp}

CYPHER:
${t.cypher}

PARAMETERS:
${JSON.stringify(t.parameters, null, 2)}

RESULT:
${t.status === 'SUCCESS' ? `${t.records_count} records returned` : `Error: ${t.error}`}
============================================================
`).join('\n');

        navigator.clipboard.writeText(formatted)
            .then(() => App.toast(`Copied ${this.traces.length} execution traces to clipboard!`, 'success'))
            .catch(() => App.toast('Could not copy trace history', 'error'));
    },

    async clear() {
        this.traces = [];
        this.updateHeader(null, false);
        this.renderEntries();
        try {
            await API.clearQueryHistory();
        } catch (_) {}
        App.toast('Query inspector terminal cleared', 'info');
    },

    scrollToBottom() {
        const container = document.getElementById('qi-output');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }
};

// Initialize QueryInspector once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    QueryInspector.init();
});
