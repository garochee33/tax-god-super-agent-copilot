/*
  HERMES.JS
  Integrations Interface (The Temple of Hermes)
*/

import { api, session } from "../app.js";

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
                </div>

                <div id="integrations-grid" class="grid grid-2">
                    <div class="spinner" style="grid-column: span 2; margin: 0 auto;"></div>
                </div>
            </div>
        `;
    },

    async init() {
        await this.loadIntegrations();
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
                    await this.connectIntegration(provider);
                });
            });
        } catch (error) {
            console.error(error);
            grid.innerHTML = `<div class="card" style="grid-column: span 2; text-align: center;">Connection failed: ${error.message}</div>`;
        }
    },

    createCard(integration) {
        const card = document.createElement("div");
        card.className = "card integration-card";

        const isConnected = integration.status === "connected";
        const isConfigured = integration.configured !== false;
        const buttonClass = isConnected ? "btn-outline" : "btn-primary";
        const buttonText = !isConfigured ? "Configure .env" : (isConnected ? "Manage" : "Connect");
        const icon = PROVIDER_ICONS[integration.id] || "🔌";

        card.innerHTML = `
            <div class="integration-card-inner">
                <div class="provider-icon">${icon}</div>
                <div class="int-name">${integration.name}</div>
                <div class="int-desc">${integration.description || "Integration connector"}</div>
                ${isConfigured ? "" : '<div class="int-desc" style="color:#b05a00;">OAuth credentials missing</div>'}
                <div class="int-status">${statusBadge(integration.status)}</div>
                <button class="btn ${buttonClass} btn-sm" data-connect-provider="${integration.id}" ${!isConfigured ? "disabled" : ""}>${buttonText}</button>
            </div>
        `;

        return card;
    },

    async connectIntegration(providerId) {
        try {
            const res = await api.post("/api/v1/integrations/connect", {
                provider: providerId,
                user_id: session.getClientId(),
            });

            if (res?.auth_url) {
                window.open(res.auth_url, "_blank", "noopener,noreferrer");
                return;
            }

            alert(`Integration ${providerId} did not return an auth URL.`);
        } catch (error) {
            alert(`Failed to initiate ${providerId} connection: ${error.message}`);
        }
    },
};
