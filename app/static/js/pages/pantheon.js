/*
  PANTHEON.JS
  Dashboard View
*/

import { api, session } from "../app.js";
import { escapeHtml, safeMarkdown } from '../utils.js';

function formatCurrency(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
    }).format(value || 0);
}

export default {
    render() {
        return `
            <div class="pantheon-container">
                <div class="grid grid-4">
                    <div class="card stat-card">
                        <div class="card-header">
                            <span class="card-title">Total Queries</span>
                            <span class="badge badge-gold">Live</span>
                        </div>
                        <div class="stat-value pantheon-skeleton" id="metric-total-queries">--</div>
                        <div class="stat-trend neutral pantheon-skeleton" id="metric-cache-rate">Cache hit rate --</div>
                    </div>

                    <div class="card stat-card">
                        <div class="card-header">
                            <span class="card-title">Total Spend</span>
                            <span class="badge badge-warning">Budget</span>
                        </div>
                        <div class="stat-value pantheon-skeleton" id="metric-total-spend">--</div>
                        <div class="stat-trend neutral pantheon-skeleton" id="metric-avg-cost">Avg cost/query --</div>
                    </div>

                    <div class="card stat-card">
                        <div class="card-header">
                            <span class="card-title">Daily Spend</span>
                            <span class="badge badge-gold" id="metric-budget-mode">Mode: --</span>
                        </div>
                        <div class="stat-value pantheon-skeleton" id="metric-daily-spend">--</div>
                        <div class="stat-trend neutral">System-wide today</div>
                    </div>

                    <div class="card stat-card">
                        <div class="card-header">
                            <span class="card-title">Client Budget</span>
                            <span class="badge badge-primary">Local Profile</span>
                        </div>
                        <div class="stat-value pantheon-skeleton" id="metric-client-remaining">--</div>
                        <div class="stat-trend neutral pantheon-skeleton" id="metric-client-spend">Monthly spend --</div>
                    </div>
                </div>

                <div class="grid grid-2" style="margin-top: var(--spacing-xl);">
                    <div class="card realm-influence">
                        <div class="card-header">
                            <span class="card-title">Realm Influence (Tax Nexus)</span>
                            <button class="btn btn-outline btn-sm" id="refresh-dashboard">Refresh Metrics</button>
                        </div>
                        <div class="map-placeholder">
                            <svg viewBox="0 0 800 500" class="nexus-map">
                                <path d="M50,100 Q200,50 350,100 T650,100" fill="none" stroke="#e0e0e0" stroke-width="2"/>
                                <circle cx="100" cy="150" r="8" fill="var(--color-gold)" class="nexus-point"/>
                                <circle cx="680" cy="180" r="8" fill="var(--color-gold)" class="nexus-point"/>
                                <circle cx="400" cy="250" r="6" fill="var(--color-primary-light)" class="nexus-point"/>
                                <text x="120" y="155" font-size="12" fill="#666">California</text>
                                <text x="700" y="185" font-size="12" fill="#666">New York</text>
                            </svg>
                            <div class="nexus-legend">
                                <div class="legend-item"><span class="dot gold"></span> High Exposure</div>
                                <div class="legend-item"><span class="dot blue"></span> Low Exposure</div>
                            </div>
                        </div>
                    </div>

                    <div class="card activity-scroll">
                        <div class="card-header">
                            <span class="card-title">System Signals</span>
                            <span class="badge badge-gold">Live API</span>
                        </div>
                        <div class="activity-list" id="activity-list">
                            <div class="activity-item">
                                <div class="activity-icon">🛰️</div>
                                <div class="activity-details">
                                    <div class="activity-title">Loading operational metrics...</div>
                                    <div class="activity-meta">Tax God control plane</div>
                                </div>
                            </div>
                        </div>
                        <div class="pantheon-tools" style="margin-top: var(--spacing-lg); padding-top: var(--spacing-md); border-top: 1px solid #eee;">
                            <div class="card-title" style="font-size: 14px; margin-bottom: 8px;">Cost estimate</div>
                            <div style="display: flex; gap: 8px;">
                                <input type="text" id="estimate-query" class="form-control" placeholder="e.g. What is the standard deduction for 2024?" style="flex: 1;">
                                <button type="button" id="run-estimate" class="btn btn-outline btn-sm">Estimate</button>
                            </div>
                            <div id="estimate-result" style="margin-top: 8px; font-size: 12px; color: #666;"></div>
                            <div class="card-title" style="font-size: 14px; margin: var(--spacing-md) 0 8px;">God Mode v3.0 — Decompose</div>
                            <div style="display: flex; gap: 8px;">
                                <input type="text" id="decompose-query" class="form-control" placeholder="Same or different query for DTDA..." style="flex: 1;">
                                <button type="button" id="run-decompose" class="btn btn-primary btn-sm">Decompose</button>
                            </div>
                            <div id="decompose-result" style="margin-top: 8px; font-size: 12px; color: #444;"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    async init() {
        const refreshButton = document.getElementById("refresh-dashboard");
        refreshButton.addEventListener("click", () => this.loadMetrics());
        const runEstimate = document.getElementById("run-estimate");
        const estimateQuery = document.getElementById("estimate-query");
        const estimateResult = document.getElementById("estimate-result");
        if (runEstimate && estimateQuery && estimateResult) {
            runEstimate.addEventListener("click", async () => {
                const q = estimateQuery.value.trim();
                if (!q) { estimateResult.textContent = "Enter a query to estimate cost."; return; }
                estimateResult.textContent = "Estimating...";
                try {
                    const res = await api.post("/api/v1/analytics/estimate", { query: q, client_id: session.getClientId() });
                    const cost = res?.estimated_cost_usd ?? 0;
                    const model = res?.model_name ?? "—";
                    estimateResult.textContent = `~$${cost.toFixed(4)} (${model})`;
                } catch (err) {
                    estimateResult.textContent = err.message || "Estimate failed.";
                }
            });
        }
        const runDecompose = document.getElementById("run-decompose");
        const decomposeQuery = document.getElementById("decompose-query");
        const decomposeResult = document.getElementById("decompose-result");
        if (runDecompose && decomposeQuery && decomposeResult) {
            runDecompose.addEventListener("click", async () => {
                const q = decomposeQuery.value.trim() || estimateQuery?.value?.trim() || "";
                if (!q) { decomposeResult.innerHTML = "Enter a query to decompose (or use the one above)."; return; }
                decomposeResult.innerHTML = "Decomposing (DTDA)...";
                try {
                    const res = await api.post("/api/v1/advanced/decompose", {
                        query: q,
                        client_id: session.getClientId(),
                        context: {}
                    });
                    const plan = res?.execution_plan ?? "—";
                    const taskType = res?.task_type ?? "—";
                    const complexity = res?.complexity ?? 0;
                    const cost = res?.estimated_cost ?? 0;
                    const time = res?.estimated_time ?? 0;
                    const subtasks = res?.subtasks?.length ?? 0;
                    decomposeResult.innerHTML = `
                        <div style="margin-bottom: 6px;"><strong>Plan:</strong> ${escapeHtml(plan)} &nbsp;|&nbsp; <strong>Type:</strong> ${escapeHtml(String(taskType))} &nbsp;|&nbsp; <strong>Complexity:</strong> ${complexity.toFixed(1)}</div>
                        <div style="margin-bottom: 6px;"><strong>Est. cost:</strong> ~$${cost.toFixed(4)} &nbsp;|&nbsp; <strong>Time:</strong> ${time}s &nbsp;|&nbsp; <strong>Subtasks:</strong> ${subtasks}</div>
                        ${(res?.subtasks?.length ? "<div style=\"margin-top: 4px;\"><strong>Subtasks:</strong> " + res.subtasks.map(s => escapeHtml(s.task || s.description || "")).join("; ") + "</div>" : "")}
                    `;
                } catch (err) {
                    decomposeResult.innerHTML = `<span style="color: var(--color-danger);">${escapeHtml(err.message || "Decompose failed.")}</span>`;
                }
            });
        }
        await this.loadMetrics();
    },

    async loadMetrics() {
        const clientId = session.getClientId();
        document.querySelectorAll(".pantheon-skeleton").forEach((el) => el.classList.add("loading"));

        try {
            const [usage, budget] = await Promise.all([
                api.get("/api/v1/analytics/usage"),
                api.get(`/api/v1/analytics/budget/${clientId}`),
            ]);

            document.getElementById("metric-total-queries").textContent = (usage?.total_queries ?? 0).toLocaleString();
            document.getElementById("metric-total-spend").textContent = formatCurrency(usage?.total_cost ?? 0);
            document.getElementById("metric-daily-spend").textContent = formatCurrency(usage?.daily_spend ?? 0);
            document.getElementById("metric-client-remaining").textContent = formatCurrency(budget?.month_remaining ?? 0);

            const cacheRatePct = Math.round((usage?.cache_hit_rate ?? 0) * 100);
            document.getElementById("metric-cache-rate").textContent = `Cache hit rate ${cacheRatePct}%`;

            const avgCost = usage?.avg_cost_per_query ?? 0;
            document.getElementById("metric-avg-cost").textContent = `Avg cost/query $${avgCost.toFixed(3)}`;

            const monthlySpend = budget?.month_spend ?? 0;
            const monthlyLimit = budget?.month_limit ?? 0;
            document.getElementById("metric-client-spend").textContent =
                `Monthly spend ${formatCurrency(monthlySpend)} / ${formatCurrency(monthlyLimit)}`;

            const budgetMode = usage?.budget_mode || "normal";
            document.getElementById("metric-budget-mode").textContent = `Mode: ${budgetMode}`;

            document.querySelectorAll(".pantheon-skeleton").forEach((el) => el.classList.remove("loading"));
            this.renderSignals(usage, budget);
        } catch (error) {
            document.querySelectorAll(".pantheon-skeleton").forEach((el) => el.classList.remove("loading"));
            this.renderErrorState(error.message);
        }
    },

    renderSignals(usage, budget) {
        const activity = document.getElementById("activity-list");
        const modelDistribution = usage?.model_distribution || {};
        const dominantModel = Object.entries(modelDistribution).sort((a, b) => b[1] - a[1])[0];

        activity.innerHTML = `
            <div class="activity-item">
                <div class="activity-icon">🧠</div>
                <div class="activity-details">
                    <div class="activity-title">Top model: ${dominantModel ? escapeHtml(dominantModel[0]) : "n/a"}</div>
                    <div class="activity-meta">${dominantModel ? `${escapeHtml(dominantModel[1])} queries` : "No model usage yet"}</div>
                </div>
                <span class="badge badge-primary">Routing</span>
            </div>
            <div class="activity-item">
                <div class="activity-icon">💳</div>
                <div class="activity-details">
                    <div class="activity-title">Daily budget utilization</div>
                    <div class="activity-meta">${formatCurrency(usage?.daily_spend ?? 0)} of ${formatCurrency(budget?.daily_system_limit ?? 0)}</div>
                </div>
                <span class="badge badge-warning">${escapeHtml(usage?.budget_mode || "normal")}</span>
            </div>
            <div class="activity-item">
                <div class="activity-icon">📦</div>
                <div class="activity-details">
                    <div class="activity-title">Cache effectiveness</div>
                    <div class="activity-meta">${Math.round((usage?.cache_hit_rate ?? 0) * 100)}% cache hit rate</div>
                </div>
                <span class="badge badge-success">Savings</span>
            </div>
        `;
    },

    renderErrorState(message) {
        document.getElementById("activity-list").innerHTML = `
            <div class="activity-item">
                <div class="activity-icon">⚠️</div>
                <div class="activity-details">
                    <div class="activity-title">Unable to load dashboard metrics</div>
                    <div class="activity-meta">${escapeHtml(message)}</div>
                </div>
            </div>
        `;
    },
};
