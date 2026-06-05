/*
  GATE.JS
  Public home, login, and register views. Uses window.taxGodSession and window.taxGodApi.
*/

function getSession() {
    return window.taxGodSession || {};
}

function getApi() {
    return window.taxGodApi || {};
}

function buildApiUrl(endpoint) {
    const base = (getSession().getApiBase && getSession().getApiBase()) || "";
    if (!base && /^https?:\/\//i.test(endpoint)) return endpoint;
    if (!base) return endpoint;
    return `${base.replace(/\/$/, "")}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
}

function renderHome() {
    return `
    <div class="gate-home">
        <div class="gate-logo">TAX GOD</div>
        <div class="gate-tagline">AI Advisory</div>
        <p class="gate-hero">
            Multi-agent tax, legal & financial co-pilot. Secure portal for the Oracle, Tribunal, Archives, and more.
        </p>
        <div class="gate-actions">
            <button type="button" class="btn btn-primary" data-gate-action="login">Log in</button>
            <button type="button" class="btn btn-outline" data-gate-action="register" style="border-color: var(--color-gold); color: var(--color-gold);">Sign up</button>
        </div>
    </div>`;
}

function renderLogin() {
    return `
    <div class="gate-form-card">
        <h2>Log in</h2>
        <form id="gate-login-form">
            <div class="input-group">
                <label class="input-label" for="gate-login-email">Email</label>
                <input type="email" id="gate-login-email" class="form-control" required placeholder="you@example.com" autocomplete="email">
            </div>
            <div class="input-group">
                <label class="input-label" for="gate-login-password">Password</label>
                <input type="password" id="gate-login-password" class="form-control" required placeholder="••••••••" autocomplete="current-password">
            </div>
            <div id="gate-login-error" class="gate-error" style="display: none;"></div>
            <button type="submit" class="btn btn-primary" id="gate-login-btn">Log in</button>
        </form>
        <div class="gate-link">Don't have an account? <a data-gate-to="register">Sign up</a></div>
        <div class="gate-link"><a data-gate-to="home">← Back to home</a></div>
    </div>`;
}

function renderRegister() {
    return `
    <div class="gate-form-card">
        <h2>Sign up</h2>
        <form id="gate-register-form">
            <div class="input-group">
                <label class="input-label" for="gate-register-email">Email</label>
                <input type="email" id="gate-register-email" class="form-control" required placeholder="you@example.com" autocomplete="email">
            </div>
            <div class="input-group">
                <label class="input-label" for="gate-register-password">Password (min 8 characters)</label>
                <input type="password" id="gate-register-password" class="form-control" required minlength="8" placeholder="••••••••" autocomplete="new-password">
            </div>
            <div class="input-group">
                <label class="input-label" for="gate-register-name">Full name (optional)</label>
                <input type="text" id="gate-register-name" class="form-control" placeholder="Your name" autocomplete="name">
            </div>
            <div id="gate-register-error" class="gate-error" style="display: none;"></div>
            <button type="submit" class="btn btn-primary" id="gate-register-btn">Create account</button>
        </form>
        <div class="gate-link">Already have an account? <a data-gate-to="login">Log in</a></div>
        <div class="gate-link"><a data-gate-to="home">← Back to home</a></div>
    </div>`;
}

function showError(elId, message) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.textContent = message || "";
    el.style.display = message ? "block" : "none";
}

function setFormLoading(formId, btnId, loading) {
    const btn = document.getElementById(btnId);
    if (btn) btn.disabled = loading;
}

export function render(view) {
    const content = document.getElementById("gate-content");
    if (!content) return;
    if (view === "home") content.innerHTML = renderHome();
    else if (view === "login") content.innerHTML = renderLogin();
    else if (view === "register") content.innerHTML = renderRegister();
    else content.innerHTML = renderHome();
    bindGateListeners();
}

function bindGateListeners() {
    document.querySelectorAll("[data-gate-action]").forEach((el) => {
        el.addEventListener("click", () => {
            const action = el.getAttribute("data-gate-action");
            window.location.hash = action;
            render(action);
        });
    });
    document.querySelectorAll("[data-gate-to]").forEach((el) => {
        el.addEventListener("click", (e) => {
            e.preventDefault();
            const to = el.getAttribute("data-gate-to");
            window.location.hash = to === "home" ? "" : to;
            render(to);
        });
    });

    const loginForm = document.getElementById("gate-login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("gate-login-email").value.trim();
            const password = document.getElementById("gate-login-password").value;
            showError("gate-login-error", "");
            setFormLoading("gate-login-form", "gate-login-btn", true);
            try {
                const api = getApi();
                const url = buildApiUrl("/api/v1/auth/login");
                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    showError("gate-login-error", data.detail || "Invalid email or password");
                    return;
                }
                if (data.access_token && getSession().setAccessToken) {
                    getSession().setAccessToken(data.access_token);
                }
                if (window.taxGodApp && typeof window.taxGodApp.showApp === "function") {
                    window.taxGodApp.showApp();
                }
                window.location.hash = "pantheon";
            } catch (err) {
                showError("gate-login-error", err.message || "Network error. Check API base URL in settings.");
            } finally {
                setFormLoading("gate-login-form", "gate-login-btn", false);
            }
        });
    }

    const registerForm = document.getElementById("gate-register-form");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("gate-register-email").value.trim();
            const password = document.getElementById("gate-register-password").value;
            const full_name = document.getElementById("gate-register-name").value.trim() || null;
            showError("gate-register-error", "");
            setFormLoading("gate-register-form", "gate-register-btn", true);
            try {
                const url = buildApiUrl("/api/v1/auth/register");
                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password, full_name }),
                });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    showError("gate-register-error", data.detail || "Registration failed");
                    return;
                }
                const loginUrl = buildApiUrl("/api/v1/auth/login");
                const loginRes = await fetch(loginUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                });
                const loginData = await loginRes.json().catch(() => ({}));
                if (loginRes.ok && loginData.access_token && getSession().setAccessToken) {
                    getSession().setAccessToken(loginData.access_token);
                }
                if (window.taxGodApp && typeof window.taxGodApp.showApp === "function") {
                    window.taxGodApp.showApp();
                }
                window.location.hash = "onboarding";
            } catch (err) {
                showError("gate-register-error", err.message || "Network error. Check API base URL.");
            } finally {
                setFormLoading("gate-register-form", "gate-register-btn", false);
            }
        });
    }
}
