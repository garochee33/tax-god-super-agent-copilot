/*
  HERMES.JS
  Integrations Interface (The Temple of Hermes)
*/

import { api, session } from "../app.js";
import { escapeHtml, safeMarkdown } from '../utils.js';

const PROVIDER_ICONS = {
    google: `
        <svg viewBox="0 0 24 24" class="provider-icon-svg">
            <path fill="#4285F4" d="M23.49 12.27c0-.79-.07-1.56-.2-2.3H12v4.35h6.47a5.53 5.53 0 0 1-2.4 3.63v3.01h3.88c2.28-2.1 3.54-5.2 3.54-8.69z"/>
            <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.94-2.9l-3.88-3.01c-1.08.72-2.46 1.15-4.06 1.15-3.12 0-5.76-2.11-6.7-4.95H1.29v3.11A12 12 0 0 0 12 24z"/>
            <path fill="#FBBC05" d="M5.3 14.29A7.2 7.2 0 0 1 4.94 12c0-.8.13-1.57.36-2.29V6.6H1.29A12 12 0 0 0 0 12c0 1.94.46 3.78 1.29 5.4l4.01-3.11z"/>
            <path fill="#EA4335" d="M12 4.77c1.76 0 3.35.61 4.59 1.8l3.44-3.44C17.95 1.19 15.23 0 12 0A12 12 0 0 0 1.29 6.6l4.01 3.11C6.24 6.88 8.88 4.77 12 4.77z"/>
        </svg>
    `,
    quickbooks: `
        <svg viewBox="0 0 24 24" class="provider-icon-svg">
            <circle cx="12" cy="12" r="11" fill="#2CA01C"/>
            <path d="M11 7h2v10h-2z" fill="#fff"/>
            <path d="M7 11h10v2H7z" fill="#fff"/>
        </svg>
    `,
};

function statusBadge(status) {
    if (status === "connected") {
        return '<span class="badge badge-success">Connected</span>';
    }
    return '<span class="badge badge-warning">Disconnected</span>';
}

export default {
    render() {
        return `
            <div class="hermes-container">
                <div class="card" style="margin-bottom: var(--spacing-lg);">
                    <div class="card-header">
                        <span class="card-title">Foreign Relations (Integrations)</span>
                        <div class="subtitle">Connect with the realms of Google and Intuit.</div>
                    </div>
                    <div id="hermes-message" class="hermes-message" role="alert" style="display: none; margin-top: var(--spacing-md); padding: var(--spacing-md); border-radius: var(--border-radius-md);"></div>
                </div>

                <div id="integrations-grid" class="grid grid-2">
                    <div class="spinner" style="grid-column: span 2; margin: 0 auto;"></div>
                </div>

                <div class="card" style="margin-top: var(--spacing-lg);">
                    <div class="card-header">
                        <span class="card-title">2026 Roadmap</span>
                        <div class="subtitle">Planned integrations: research, compliance, documents, planning, connectivity.</div>
                    </div>
                    <div id="hermes-roadmap" class="hermes-roadmap" style="padding: var(--spacing-md);">
                        <div class="spinner"></div>
                    </div>
                </div>
            </div>
        `;
    },

    async init() {
        await this.loadIntegrations();
        await this.loadRoadmap();
    },

    async loadIntegrations() {
        const grid = document.getElementById("integrations-grid");

        try {
            const res = await api.get("/api/v1/integrations/list");
            if (!res?.integrations?.length) {
                grid.innerHTML = '<div class="card" style="grid-column: span 2; text-align: center;">No integrations available.</div>';
                return;
            }

            grid.innerHTML = "";
            res.integrations.forEach((integration) => {
                grid.appendChild(this.createCard(integration));
            });

            grid.querySelectorAll("[data-connect-provider]").forEach((button) => {
                button.addEventListener("click", async (event) => {
                    const provider = event.currentTarget.dataset.connectProvider;
                    const integration = res.integrations.find((i) => i.id === provider);
                    if (integration?.status === "connected") {
                        await this.disconnectIntegration(provider);
                    } else {
                        await this.connectIntegration(provider);
                    }
                });
            });

            await this.bindQuickBooksPanel();
        } catch (error) {
            console.error(error);
            grid.innerHTML = `<div class="card" style="grid-column: span 2; text-align: center;">Connection failed: ${escapeHtml(error.message)}</div>`;
        }
    },

    async loadRoadmap() {
        const el = document.getElementById("hermes-roadmap");
        if (!el) return;
        try {
            const res = await api.get("/api/v1/integrations/roadmap");
            const categories = res?.categories || [];
            if (!categories.length) {
                el.innerHTML = "<p>No roadmap data.</p>";
                return;
            }
            let html = "";
            categories.forEach((cat) => {
                const tools = (cat.tools || []).map((t) =>
                    `<span class="badge badge-outline" style="margin: 2px 4px 2px 0;" title="${escapeHtml(t.description || "")}">${escapeHtml(t.name)}</span>`
                ).join("");
                html += `
                    <div class="hermes-roadmap-category" style="margin-bottom: var(--spacing-md);">
                        <div style="font-weight: 600; margin-bottom: 4px;">${escapeHtml(cat.name)}</div>
                        <div style="font-size: 12px; color: var(--color-muted); margin-bottom: 6px;">${escapeHtml(cat.description || "")}</div>
                        <div>${tools}</div>
                    </div>`;
            });
            el.innerHTML = html;
        } catch (err) {
            el.innerHTML = `<p style="color: var(--color-danger);">Could not load roadmap.</p>`;
        }
    },

    showMessage(text, type = "info") {
        const el = document.getElementById("hermes-message");
        if (!el) return;
        el.textContent = text;
        el.style.display = "block";
        el.style.background = type === "error" ? "rgba(192,57,43,0.1)" : type === "success" ? "rgba(39,174,96,0.1)" : "rgba(212,165,116,0.15)";
        el.style.color = type === "error" ? "var(--color-danger)" : type === "success" ? "var(--color-success)" : "inherit";
        setTimeout(() => { el.style.display = "none"; }, 5000);
    },

    async disconnectIntegration(providerId) {
        try {
            await api.post("/api/v1/integrations/disconnect", {
                provider: providerId,
                user_id: session.getClientId(),
            });
            this.showMessage(`${providerId} disconnected.`, "success");
            await this.loadIntegrations();
        } catch (error) {
            this.showMessage(`Failed to disconnect ${providerId}: ${error.message}`, "error");
        }
    },

    createCard(integration) {
        const card = document.createElement("div");
        card.className = "card integration-card";

        const isConnected = integration.status === "connected";
        const isConfigured = integration.configured !== false;
        const buttonClass = isConnected ? "btn-outline" : "btn-primary";
        const connectText = !isConfigured ? "Configure .env" : (isConnected ? "Disconnect" : "Connect");
        const icon = PROVIDER_ICONS[integration.id] || "🔌";

        const quickbooksDataPanel =
            integration.id === "quickbooks" && isConnected
                ? `
            <div class="quickbooks-data-panel" style="margin-top: var(--spacing-md); padding-top: var(--spacing-md); border-top: 1px solid #eee;">
                <div class="card-title" style="font-size: 13px; margin-bottom: 8px;">QuickBooks Data</div>
                <div id="qb-company-name" style="font-size: 12px; color: #666; margin-bottom: 10px;">Loading company...</div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
                    <span>P&L:</span>
                    <select id="qb-pl-year" class="form-control" style="width: 80px; display: inline-block;">
                        <option value="2025">2025</option>
                        <option value="2024" selected>2024</option>
                        <option value="2023">2023</option>
                    </select>
                    <button type="button" id="qb-load-pl" class="btn btn-sm btn-outline">View P&L</button>
                    <button type="button" id="qb-load-bs" class="btn btn-sm btn-outline">View Balance Sheet</button>
                    <button type="button" id="qb-load-vendors" class="btn btn-sm btn-outline">View Vendors</button>
                </div>
                <div id="qb-result" style="font-size: 12px; margin-top: 8px; min-height: 24px;"></div>
            </div>
                `
                : "";

        card.innerHTML = `
            <div class="integration-card-inner">
                <div class="provider-icon">${icon}</div>
                <div class="int-name">${escapeHtml(integration.name)}</div>
                <div class="int-desc">${escapeHtml(integration.description || "Integration connector")}</div>
                ${isConfigured ? "" : '<div class="int-desc" style="color:#b05a00;">OAuth credentials missing</div>'}
                <div class="int-status">${statusBadge(integration.status)}</div>
                <div class="int-actions" style="display: flex; gap: 8px; margin-top: 8px;">
                    <button class="btn ${isConnected ? "btn-outline" : "btn-primary"} btn-sm" data-connect-provider="${escapeHtml(integration.id)}" ${!isConfigured ? "disabled" : ""}>${escapeHtml(connectText)}</button>
                </div>
                ${quickbooksDataPanel}
            </div>
        `;

        return card;
    },

    async bindQuickBooksPanel() {
        const companyEl = document.getElementById("qb-company-name");
        const resultEl = document.getElementById("qb-result");
        const plYear = document.getElementById("qb-pl-year");
        const loadPl = document.getElementById("qb-load-pl");
        const loadBs = document.getElementById("qb-load-bs");
        const loadVendors = document.getElementById("qb-load-vendors");
        if (!companyEl || !resultEl) return;

        const userId = session.getClientId();

        try {
            const companyRes = await api.get("/api/v1/integrations/quickbooks/company?user_id=" + encodeURIComponent(userId));
            const company = companyRes?.company?.CompanyInfo;
            const name = company?.CompanyName || company?.LegalName || "QuickBooks company";
            companyEl.textContent = name;
        } catch (e) {
            companyEl.textContent = "Could not load company.";
        }

        const qbButtons = [loadPl, loadBs, loadVendors].filter(Boolean);
        const setQbButtonsDisabled = (disabled) => qbButtons.forEach((b) => { b.disabled = disabled; });

        function quickbooksErrorMessage(err, fallback) {
            const status = err?.status ?? err?.statusCode;
            const msg = err?.message ?? err?.detail ?? "";
            if (status === 429 || status === 503 || (msg && String(msg).toLowerCase().includes("rate limit"))) {
                return "Rate limited; try again in a minute.";
            }
            return escapeHtml(msg || fallback);
        }

        if (loadPl) {
            loadPl.addEventListener("click", async () => {
                const year = plYear?.value || "2024";
                resultEl.innerHTML = "<span>Loading P&L...</span>";
                setQbButtonsDisabled(true);
                try {
                    const res = await api.get(`/api/v1/integrations/quickbooks/profit-loss?user_id=${encodeURIComponent(userId)}&year=${year}`);
                    const report = res?.report;
                    const summary = this.summarizeProfitLoss(report);
                    resultEl.innerHTML = summary;
                } catch (err) {
                    resultEl.innerHTML = `<span style="color: var(--color-danger);">${quickbooksErrorMessage(err, "Failed to load P&L.")}</span>`;
                } finally {
                    setQbButtonsDisabled(false);
                }
            });
        }
        if (loadBs) {
            loadBs.addEventListener("click", async () => {
                resultEl.innerHTML = "<span>Loading Balance Sheet...</span>";
                setQbButtonsDisabled(true);
                try {
                    const res = await api.get(`/api/v1/integrations/quickbooks/balance-sheet?user_id=${encodeURIComponent(userId)}`);
                    const report = res?.report;
                    const summary = this.summarizeBalanceSheet(report);
                    resultEl.innerHTML = summary;
                } catch (err) {
                    resultEl.innerHTML = `<span style="color: var(--color-danger);">${quickbooksErrorMessage(err, "Failed to load Balance Sheet.")}</span>`;
                } finally {
                    setQbButtonsDisabled(false);
                }
            });
        }
        if (loadVendors) {
            loadVendors.addEventListener("click", async () => {
                resultEl.innerHTML = "<span>Loading Vendors...</span>";
                setQbButtonsDisabled(true);
                try {
                    const res = await api.get(`/api/v1/integrations/quickbooks/vendors?user_id=${encodeURIComponent(userId)}&max_results=100`);
                    const vendors = res?.vendors || [];
                    const html = this.renderVendorsTable(vendors);
                    resultEl.innerHTML = html;
                } catch (err) {
                    resultEl.innerHTML = `<span style="color: var(--color-danger);">${quickbooksErrorMessage(err, "Failed to load Vendors.")}</span>`;
                } finally {
                    setQbButtonsDisabled(false);
                }
            });
        }
    },

    summarizeProfitLoss(report) {
        if (!report?.Rows?.Row) return "<p>No P&L data in report.</p>";
        const rows = Array.isArray(report.Rows.Row) ? report.Rows.Row : [report.Rows.Row];
        let totalIncome = null, totalExpenses = null, netIncome = null;
        const walk = (r) => {
            if (!r) return;
            if (r.Summary?.ColData) {
                const cols = r.Summary.ColData;
                const label = (cols[0]?.value || "").toLowerCase();
                const value = cols[1]?.value;
                if (label.includes("total income")) totalIncome = value;
                else if (label.includes("total expense")) totalExpenses = value;
                else if (label.includes("net income") || label.includes("net profit")) netIncome = value;
            }
            (r.Rows?.Row || []).forEach(walk);
        };
        rows.forEach(walk);
        const parts = [];
        if (totalIncome != null) parts.push(`<strong>Total Income:</strong> ${escapeHtml(totalIncome)}`);
        if (totalExpenses != null) parts.push(`<strong>Total Expenses:</strong> ${escapeHtml(totalExpenses)}`);
        if (netIncome != null) parts.push(`<strong>Net Income:</strong> ${escapeHtml(netIncome)}`);
        if (parts.length === 0) return "<p>P&L report loaded. (Summary not parsed.)</p>";
        return "<p>" + parts.join(" &middot; ") + "</p>";
    },

    summarizeBalanceSheet(report) {
        if (!report?.Rows?.Row) return "<p>No Balance Sheet data in report.</p>";
        const rows = Array.isArray(report.Rows.Row) ? report.Rows.Row : [report.Rows.Row];
        let totalAssets = null, totalLiabilities = null, totalEquity = null;
        const walk = (r) => {
            if (!r) return;
            if (r.Summary?.ColData) {
                const cols = r.Summary.ColData;
                const label = (cols[0]?.value || "").toLowerCase();
                const value = cols[1]?.value;
                if (label.includes("total assets")) totalAssets = value;
                else if (label.includes("total liabilities")) totalLiabilities = value;
                else if (label.includes("total equity")) totalEquity = value;
            }
            (r.Rows?.Row || []).forEach(walk);
        };
        rows.forEach(walk);
        const parts = [];
        if (totalAssets != null) parts.push(`<strong>Total Assets:</strong> ${escapeHtml(totalAssets)}`);
        if (totalLiabilities != null) parts.push(`<strong>Total Liabilities:</strong> ${escapeHtml(totalLiabilities)}`);
        if (totalEquity != null) parts.push(`<strong>Total Equity:</strong> ${escapeHtml(totalEquity)}`);
        if (parts.length === 0) return "<p>Balance Sheet loaded. (Summary not parsed.)</p>";
        return "<p>" + parts.join(" &middot; ") + "</p>";
    },

    renderVendorsTable(vendors) {
        if (!vendors.length) return "<p>No vendors in QuickBooks.</p>";
        let table = '<p style="margin-bottom: 6px;">Use for 1099 prep. Missing TIN = may need W-9.</p><table style="width: 100%; border-collapse: collapse; font-size: 12px;"><thead><tr style="text-align: left; border-bottom: 1px solid #ddd;"><th style="padding: 6px;">Name</th><th style="padding: 6px;">Company</th><th style="padding: 6px;">TIN</th></tr></thead><tbody>';
        vendors.forEach((v) => {
            const name = escapeHtml(v.DisplayName || v.CompanyName || "—");
            const company = escapeHtml(v.CompanyName || "—");
            const tin = escapeHtml(v.TaxIdentifier || "—");
            const missing = !v.TaxIdentifier ? ' <span class="badge badge-warning">Missing TIN</span>' : "";
            table += `<tr style="border-bottom: 1px solid #eee;"><td style="padding: 6px;">${name}${missing}</td><td style="padding: 6px;">${company}</td><td style="padding: 6px;">${tin}</td></tr>`;
        });
        table += "</tbody></table>";
        return table;
    },

    async connectIntegration(providerId) {
        try {
            const res = await api.post("/api/v1/integrations/connect", {
                provider: providerId,
                user_id: session.getClientId(),
            });

            if (res?.auth_url) {
                window.open(res.auth_url, "_blank", "noopener,noreferrer");
                this.showMessage("Open the popup to complete authorization.", "info");
                return;
            }

            this.showMessage(`Integration ${providerId} did not return an auth URL.`, "error");
        } catch (error) {
            this.showMessage(`Failed to initiate ${providerId}: ${error.message}`, "error");
        }
    },
};
