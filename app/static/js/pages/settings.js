/**
 * Tax God — Admin Settings Page
 * Manage API keys, Stripe, integrations from the UI.
 */

const SECTION_CONFIG = {
    ai: {
        label: "🤖 AI API Keys",
        keys: {
            OPENAI_API_KEY: { help: "Get from OpenAI dashboard", url: "https://platform.openai.com/api-keys" },
            ANTHROPIC_API_KEY: { help: "Get from Anthropic console", url: "https://console.anthropic.com/settings/keys" },
        }
    },
    stripe: {
        label: "💳 Stripe (Payments)",
        keys: {
            STRIPE_SECRET_KEY: { help: "Secret key from Stripe", url: "https://dashboard.stripe.com/apikeys" },
            STRIPE_PUBLISHABLE_KEY: { help: "Publishable key", url: "https://dashboard.stripe.com/apikeys" },
            STRIPE_WEBHOOK_SECRET: { help: "Webhook signing secret", url: "https://dashboard.stripe.com/webhooks" },
            STRIPE_PRICE_MONTHLY: { help: "Price ID for $29/mo plan", url: "https://dashboard.stripe.com/products" },
        }
    },
    database: {
        label: "🗄️ Database & Cache",
        keys: {
            DATABASE_URL: { help: "PostgreSQL async connection string" },
            REDIS_URL: { help: "Redis connection string" },
        }
    },
    integrations: {
        label: "🔗 OAuth & Integrations",
        keys: {
            GOOGLE_CLIENT_ID: { help: "Google OAuth client ID", url: "https://console.cloud.google.com/apis/credentials" },
            GOOGLE_CLIENT_SECRET: { help: "Google OAuth secret", url: "https://console.cloud.google.com/apis/credentials" },
            GOOGLE_REDIRECT_URI: { help: "OAuth redirect URI" },
            QUICKBOOKS_CLIENT_ID: { help: "QuickBooks app client ID", url: "https://developer.intuit.com/app/developer/dashboard" },
            QUICKBOOKS_CLIENT_SECRET: { help: "QuickBooks secret", url: "https://developer.intuit.com/app/developer/dashboard" },
            QUICKBOOKS_REDIRECT_URI: { help: "OAuth redirect URI" },
            INTEGRATION_ENCRYPTION_KEY: { help: "Fernet key for credential encryption" },
        }
    },
    outreach: {
        label: "📧 Outreach & Email",
        keys: {
            SENDGRID_API_KEY: { help: "SendGrid API key", url: "https://app.sendgrid.com/settings/api_keys" },
            APOLLO_API_KEY: { help: "Apollo.io API key", url: "https://app.apollo.io/#/settings/integrations/api" },
        }
    },
    app: {
        label: "⚙️ Application",
        keys: {
            SECRET_KEY: { help: "JWT signing key (min 32 chars)" },
            ENVIRONMENT: { help: "development | staging | production", type: "select", options: ["development", "staging", "production"] },
            DEBUG: { help: "Enable debug mode", type: "select", options: ["true", "false"] },
            LOG_LEVEL: { help: "Logging level", type: "select", options: ["DEBUG", "INFO", "WARNING", "ERROR"] },
        }
    },
};

function buildApiUrl(path) { return `${window.location.origin}${path}`; }

async function apiGet(path) {
    const token = localStorage.getItem("access_token");
    const res = await fetch(buildApiUrl(path), { headers: { "Authorization": `Bearer ${token}` } });
    if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
    return res.json();
}

async function apiPut(path, body) {
    const token = localStorage.getItem("access_token");
    const res = await fetch(buildApiUrl(path), {
        method: "PUT",
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || res.statusText); }
    return res.json();
}

export default {
    render() {
        return `
            <div class="card" style="max-width:900px;">
                <div class="card-title">⚙️ Settings</div>
                <p style="color:#aaa;margin-bottom:.5rem;">Manage API keys, secrets, and integrations. Changes write to <code>.env</code> and take effect on restart.</p>
                <p style="color:#666;font-size:.8rem;margin-bottom:1.5rem;">🔗 Click key labels to open the provider dashboard. Sensitive values are masked — enter a new value to rotate.</p>
                <div id="settings-sections"><div class="spinner"></div></div>
                <div id="settings-actions" style="display:none;margin-top:1.5rem;display:flex;gap:1rem;align-items:center;">
                    <button id="settings-save" class="btn-gold">💾 Save All Changes</button>
                    <span id="settings-status"></span>
                </div>
            </div>
        `;
    },

    async init() {
        const sectionsEl = document.getElementById("settings-sections");
        const statusEl = document.getElementById("settings-status");
        const actionsEl = document.getElementById("settings-actions");

        try {
            const data = await apiGet("/api/v1/settings");
            renderSections(data.sections, sectionsEl, statusEl);
            actionsEl.style.display = "flex";
        } catch (err) {
            sectionsEl.innerHTML = `<p style="color:#e74c3c;">Failed to load: ${err.message}</p>
                <p style="color:#888;">Only admin users can access settings.</p>`;
        }
    }
};

function renderSections(sections, container, statusEl) {
    let html = "";
    for (const [section, keys] of Object.entries(sections)) {
        const cfg = SECTION_CONFIG[section] || { label: section, keys: {} };
        html += `<div class="settings-section">
            <h3 class="settings-section-title">${cfg.label}</h3>
            <div class="settings-grid">`;

        for (const [key, value] of Object.entries(keys)) {
            const keyCfg = cfg.keys?.[key] || {};
            const masked = value.startsWith("••");
            const hasUrl = !!keyCfg.url;
            const isSelect = keyCfg.type === "select";

            const labelHtml = hasUrl
                ? `<a href="${keyCfg.url}" target="_blank" rel="noopener" class="settings-key-link">${key} ↗</a>`
                : `<span class="settings-key">${key}</span>`;

            let inputHtml;
            if (isSelect) {
                const opts = (keyCfg.options || []).map(o =>
                    `<option value="${o}" ${o === value ? "selected" : ""}>${o}</option>`
                ).join("");
                inputHtml = `<select data-key="${key}" class="settings-input">${opts}</select>`;
            } else {
                inputHtml = `<div class="settings-input-wrap">
                    <input type="${masked ? "password" : "text"}"
                           data-key="${key}"
                           data-masked="${masked}"
                           placeholder="${masked ? "Enter new value to rotate" : "Not set"}"
                           value="${masked ? "" : value}"
                           class="settings-input" />
                    ${masked ? `<button class="btn-toggle-vis" title="Show/hide">👁</button>` : ""}
                    ${masked ? `<span class="settings-masked">${value}</span>` : ""}
                </div>`;
            }

            html += `<div class="settings-row">
                <div class="settings-label">${labelHtml}
                    ${keyCfg.help ? `<span class="settings-help">${keyCfg.help}</span>` : ""}
                </div>
                ${inputHtml}
            </div>`;
        }
        html += `</div></div>`;
    }
    container.innerHTML = html;

    // Toggle visibility buttons
    container.querySelectorAll(".btn-toggle-vis").forEach(btn => {
        btn.addEventListener("click", () => {
            const input = btn.parentElement.querySelector("input");
            input.type = input.type === "password" ? "text" : "password";
            btn.textContent = input.type === "password" ? "👁" : "🙈";
        });
    });

    // Save button
    document.getElementById("settings-save").addEventListener("click", async () => {
        const els = container.querySelectorAll("[data-key]");
        const updates = {};
        els.forEach(el => {
            const val = el.value.trim();
            if (val && el.dataset.masked !== "true") {
                updates[el.dataset.key] = val;
            } else if (val && el.dataset.masked === "true") {
                updates[el.dataset.key] = val;
            }
        });

        if (Object.keys(updates).length === 0) {
            statusEl.innerHTML = `<span style="color:#888;">No changes detected.</span>`;
            return;
        }

        try {
            const res = await apiPut("/api/v1/settings", { updates });
            statusEl.innerHTML = `<span style="color:#2ecc71;">✅ ${res.message}</span>`;
            // Clear password fields
            container.querySelectorAll('input[type="password"]').forEach(i => { i.value = ""; });
        } catch (err) {
            statusEl.innerHTML = `<span style="color:#e74c3c;">❌ ${err.message}</span>`;
        }
    });
}
