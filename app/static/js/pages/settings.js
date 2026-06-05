/**
 * Tax God — Admin Settings Page
 * Manage API keys, Stripe, integrations from the UI.
 */

const SECTION_LABELS = {
    ai: "🤖 AI API Keys",
    stripe: "💳 Stripe (Payments)",
    database: "🗄️ Database & Redis",
    integrations: "🔗 OAuth & Integrations",
    outreach: "📧 Outreach",
    app: "⚙️ Application",
};

function buildApiUrl(path) {
    return `${window.location.origin}${path}`;
}

async function apiGet(path) {
    const token = localStorage.getItem("access_token");
    const res = await fetch(buildApiUrl(path), {
        headers: { "Authorization": `Bearer ${token}` },
    });
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
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `${res.status}: ${res.statusText}`);
    }
    return res.json();
}

export default {
    render() {
        return `
            <div class="card" style="max-width:800px;">
                <div class="card-title">⚙️ Settings</div>
                <p style="color:#aaa;margin-bottom:1.5rem;">Manage secrets, API keys, and integrations. Changes update your <code>.env</code> file.</p>
                <div id="settings-sections"><div class="spinner"></div></div>
                <div id="settings-status" style="margin-top:1rem;"></div>
            </div>
        `;
    },

    async init() {
        const sectionsEl = document.getElementById("settings-sections");
        const statusEl = document.getElementById("settings-status");

        try {
            const data = await apiGet("/api/v1/settings");
            renderSections(data.sections, sectionsEl, statusEl);
        } catch (err) {
            sectionsEl.innerHTML = `<p style="color:#e74c3c;">Failed to load: ${err.message}</p>
                <p style="color:#888;">Only admins can access settings.</p>`;
        }
    }
};

function renderSections(sections, container, statusEl) {
    let html = "";
    for (const [section, keys] of Object.entries(sections)) {
        const label = SECTION_LABELS[section] || section;
        html += `<div style="margin-bottom:1.5rem;border-bottom:1px solid #333;padding-bottom:1rem;">
            <h3 style="color:var(--color-gold);margin-bottom:.75rem;">${label}</h3>`;
        for (const [key, value] of Object.entries(keys)) {
            const masked = value.startsWith("••");
            html += `
                <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.5rem;">
                    <label style="width:240px;font-size:.85rem;color:#ccc;font-family:monospace;">${key}</label>
                    <input type="${masked ? "password" : "text"}"
                           data-key="${key}"
                           placeholder="${masked ? "Enter new value to rotate" : "Not set"}"
                           value="${masked ? "" : value}"
                           style="flex:1;padding:.4rem .6rem;background:#1a1a2e;border:1px solid #333;border-radius:4px;color:#eee;font-size:.85rem;" />
                    ${masked ? `<span style="font-size:.75rem;color:#666;">${value}</span>` : ""}
                </div>`;
        }
        html += `</div>`;
    }
    html += `<button id="settings-save" style="padding:.6rem 1.5rem;background:var(--color-gold);color:#1a1a2e;border:none;border-radius:4px;font-weight:600;cursor:pointer;">Save Changes</button>`;
    container.innerHTML = html;

    container.querySelector("#settings-save").addEventListener("click", async () => {
        const inputs = container.querySelectorAll("input[data-key]");
        const updates = {};
        inputs.forEach(input => {
            if (input.value.trim()) {
                updates[input.dataset.key] = input.value.trim();
            }
        });

        if (Object.keys(updates).length === 0) {
            statusEl.innerHTML = `<span style="color:#888;">No changes to save.</span>`;
            return;
        }

        try {
            const res = await apiPut("/api/v1/settings", { updates });
            statusEl.innerHTML = `<span style="color:#2ecc71;">✅ ${res.message}</span>`;
            inputs.forEach(input => { if (input.type === "password") input.value = ""; });
        } catch (err) {
            statusEl.innerHTML = `<span style="color:#e74c3c;">❌ ${err.message}</span>`;
        }
    });
}
