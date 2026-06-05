/**
 * Tax God — Onboarding Setup Guide
 * Shown after first registration. Walks user through API key setup.
 */

function buildApiUrl(path) { return `${window.location.origin}${path}`; }

async function apiPut(path, body) {
    const token = localStorage.getItem("access_token");
    const res = await fetch(buildApiUrl(path), {
        method: "PUT",
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    return res.json();
}

async function apiGet(path) {
    const token = localStorage.getItem("access_token");
    const res = await fetch(buildApiUrl(path), { headers: { "Authorization": `Bearer ${token}` } });
    return res.json();
}

const STEPS = [
    {
        id: "welcome",
        title: "Welcome to Tax God 🏛️",
        html: `<p>Your sovereign AI co-pilot for law, taxes, finance, and accounting.</p>
               <p style="color:#aaa;margin-top:1rem;">This quick setup takes ~2 minutes. You can skip and configure later in ⚙️ Settings.</p>
               <div class="onboard-features">
                   <div class="onboard-feat">🤖 <b>Oracle</b> — AI-powered tax research</div>
                   <div class="onboard-feat">🛡️ <b>Tribunal</b> — Audit defense</div>
                   <div class="onboard-feat">📊 <b>Pantheon</b> — Financial analytics</div>
                   <div class="onboard-feat">📜 <b>Scrolls</b> — Document generation</div>
               </div>`,
        action: null,
    },
    {
        id: "ai-keys",
        title: "AI API Keys",
        html: `<p>Add at least one AI key to enable the agents. Both work — use whichever you prefer.</p>
               <div class="onboard-field">
                   <label>OpenAI API Key <a href="https://platform.openai.com/api-keys" target="_blank" style="color:var(--color-gold);">Get one →</a></label>
                   <input type="password" id="onboard-openai" placeholder="sk-..." class="form-control" />
               </div>
               <div class="onboard-field">
                   <label>Anthropic API Key <a href="https://console.anthropic.com/settings/keys" target="_blank" style="color:var(--color-gold);">Get one →</a></label>
                   <input type="password" id="onboard-anthropic" placeholder="sk-ant-..." class="form-control" />
               </div>`,
        action: async () => {
            const updates = {};
            const openai = document.getElementById("onboard-openai").value.trim();
            const anthropic = document.getElementById("onboard-anthropic").value.trim();
            if (openai) updates.OPENAI_API_KEY = openai;
            if (anthropic) updates.ANTHROPIC_API_KEY = anthropic;
            if (Object.keys(updates).length > 0) {
                await apiPut("/api/v1/settings", { updates });
            }
        },
    },
    {
        id: "billing",
        title: "Subscription",
        html: `<p>You're on a <b>7-day free trial</b> — full access to all features.</p>
               <p style="color:#aaa;margin-top:.75rem;">After 7 days, subscribe for $29/month to continue. No credit card needed now.</p>
               <div id="onboard-trial-info" style="margin-top:1rem;padding:1rem;background:#1a1a2e;border-radius:8px;border:1px solid #333;">
                   <span style="color:var(--color-gold);font-size:1.1rem;">⏳ Loading trial info...</span>
               </div>`,
        action: async () => {
            // Just informational — no action needed
        },
        onShow: async () => {
            try {
                const sub = await apiGet("/api/v1/billing/status");
                const ends = new Date(sub.trial_ends_at).toLocaleDateString();
                document.getElementById("onboard-trial-info").innerHTML = `
                    <span style="color:#2ecc71;font-size:1.1rem;">✅ Free trial active</span><br/>
                    <span style="color:#aaa;font-size:.85rem;">Expires: ${ends}</span>
                `;
            } catch { /* ignore */ }
        }
    },
    {
        id: "done",
        title: "You're All Set! 🎉",
        html: `<p>Tax God is ready. Here's what you can do:</p>
               <div class="onboard-features">
                   <div class="onboard-feat">💬 <b>Ask Oracle</b> — tax questions, research, citations</div>
                   <div class="onboard-feat">🛡️ <b>Run Tribunal</b> — audit risk assessment</div>
                   <div class="onboard-feat">📊 <b>Open Pantheon</b> — financial projections</div>
                   <div class="onboard-feat">⚙️ <b>Settings</b> — add integrations anytime</div>
               </div>
               <p style="color:#aaa;margin-top:1rem;">All data stays on your machine. 100% sovereign.</p>`,
        action: null,
    },
];

let currentStep = 0;

export default {
    render() {
        return `
            <div class="card onboard-card">
                <div class="onboard-progress" id="onboard-progress"></div>
                <div id="onboard-content"></div>
                <div class="onboard-actions">
                    <button id="onboard-skip" class="btn btn-outline" style="border-color:#555;color:#888;">Skip setup</button>
                    <button id="onboard-next" class="btn-gold">Continue →</button>
                </div>
            </div>
        `;
    },

    async init() {
        currentStep = 0;
        renderStep();

        document.getElementById("onboard-next").addEventListener("click", async () => {
            const step = STEPS[currentStep];
            if (step.action) await step.action();

            if (currentStep < STEPS.length - 1) {
                currentStep++;
                renderStep();
            } else {
                // Done — mark onboarding complete and go to app
                localStorage.setItem("taxgod_onboarded", "1");
                window.location.hash = "oracle";
            }
        });

        document.getElementById("onboard-skip").addEventListener("click", () => {
            localStorage.setItem("taxgod_onboarded", "1");
            window.location.hash = "pantheon";
        });
    }
};

function renderStep() {
    const step = STEPS[currentStep];
    const progressHtml = STEPS.map((s, i) =>
        `<div class="onboard-dot ${i === currentStep ? "active" : i < currentStep ? "done" : ""}"></div>`
    ).join("");
    document.getElementById("onboard-progress").innerHTML = progressHtml;
    document.getElementById("onboard-content").innerHTML = `
        <h2 class="onboard-title">${step.title}</h2>
        ${step.html}
    `;
    const nextBtn = document.getElementById("onboard-next");
    nextBtn.textContent = currentStep === STEPS.length - 1 ? "🚀 Start Using Tax God" : "Continue →";

    if (step.onShow) step.onShow();
}
