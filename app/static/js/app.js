/*
  APP.JS
  Main Application Entry Point & Router
*/

const APP_ROUTES = {
    pantheon: { title: "Dashboard", module: "/static/js/pages/pantheon.js" },
    oracle: { title: "Tax God Agent", module: "/static/js/pages/oracle.js" },
    agora: { title: "Clients", module: "/static/js/pages/agora.js" },
    finance: { title: "Finance", module: "/static/js/pages/finance.js" },
    expenses: { title: "Expenses", module: "/static/js/pages/expenses.js" },
    time_tracking: { title: "Time Tracking", module: "/static/js/pages/time_tracking.js" },
    vendors: { title: "Vendors", module: "/static/js/pages/vendors.js" },
    transactions: { title: "Transactions", module: "/static/js/pages/transactions.js" },
    reports: { title: "Reports", module: "/static/js/pages/reports.js" },
    projects: { title: "Projects", module: "/static/js/pages/projects_page.js" },
    scrolls: { title: "Documents", module: "/static/js/pages/scrolls.js" },
    archives: { title: "Research", module: "/static/js/pages/archives.js" },
    tribunal: { title: "Audit", module: "/static/js/pages/tribunal.js" },
    business: { title: "Business", module: "/static/js/pages/business.js" },
    profile: { title: "Profile", module: "/static/js/pages/profile.js" },
    settings: { title: "Settings", module: "/static/js/pages/settings.js" },
};

const GATE_VIEWS = ["home", "login", "register"];

function isAppRoute(page) {
    return page && Object.prototype.hasOwnProperty.call(APP_ROUTES, page);
}

function getGateViewFromHash() {
    const hash = (window.location.hash || "").replace(/^#/, "").toLowerCase();
    if (hash === "login" || hash === "register") return hash;
    return "home";
}

const STORAGE_KEYS = {
    clientId: "taxgod_client_id",
    apiBase: "taxgod_api_base",
    accessToken: "taxgod_access_token",
};

function ensureClientId() {
    const existing = localStorage.getItem(STORAGE_KEYS.clientId);
    if (existing) return existing;
    const generated = `web-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(STORAGE_KEYS.clientId, generated);
    return generated;
}

function getApiBase() {
    return (localStorage.getItem(STORAGE_KEYS.apiBase) || "").trim();
}

function buildApiUrl(endpoint) {
    if (/^https?:\/\//i.test(endpoint)) return endpoint;
    const base = getApiBase();
    const origin = (typeof window !== "undefined" && window.location?.origin) || "";
    const root = base || origin;
    if (!root) return endpoint;
    return `${root.replace(/\/$/, "")}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
}

class App {
    constructor() {
        this.appContainer = document.getElementById("app");
        this.pageTitle = document.getElementById("page-title");
        this.navItems = document.querySelectorAll(".nav-item");
        this.currentPage = "pantheon";
        this.clientId = ensureClientId();
        this._appReady = false;
    }

    getPageFromHash() {
        const page = (window.location.hash || "").replace(/^#/, "") || "pantheon";
        return isAppRoute(page) ? page : "pantheon";
    }

    navigate(page) {
        const target = isAppRoute(page) ? page : "pantheon";
        if (target === this.currentPage) return;
        window.location.hash = target;
    }

    async loadPage(pageId) {
        const route = APP_ROUTES[pageId] || APP_ROUTES.pantheon;
        this.currentPage = pageId;

        this.updateActiveNav(pageId);
        if (this.pageTitle) this.pageTitle.textContent = route.title;
        if (this.appContainer) this.appContainer.innerHTML = '<div class="spinner"></div>';

        try {
            const module = await import(route.module);
            if (!module.default || typeof module.default.render !== "function") {
                throw new Error("Invalid page module");
            }

            this.appContainer.innerHTML = module.default.render();

            if (typeof module.default.init === "function") {
                await module.default.init();
            }
        } catch (error) {
            console.error("Page load error:", error);
            const msg = document.createElement("p");
            msg.style.cssText = "margin-top: 8px; color: #666;";
            msg.textContent = error.message;
            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = '<div class="card-title">Failed to Load Page</div>';
            card.appendChild(msg);
            this.appContainer.innerHTML = "";
            this.appContainer.appendChild(card);
        }
    }

    updateActiveNav(activePageId) {
        this.navItems.forEach((item) => {
            item.classList.toggle("active", item.dataset.page === activePageId);
        });
    }

    showApp() {
        const gate = document.getElementById("gate");
        const shell = document.getElementById("app-shell");
        if (gate) gate.style.display = "none";
        if (shell) shell.style.display = "flex";
        this._appReady = true;
        this.refreshUserDisplay();
        this.bindLogout();
        this.initAppRouter();
    }

    showGate() {
        const gate = document.getElementById("gate");
        const shell = document.getElementById("app-shell");
        if (shell) shell.style.display = "none";
        if (gate) gate.style.display = "flex";
        this._appReady = false;
        const view = getGateViewFromHash();
        import("/static/js/gate.js").then((g) => g.render(view));
    }

    async refreshUserDisplay() {
        const nameEl = document.getElementById("user-name");
        const avatarEl = document.getElementById("user-avatar");
        if (!nameEl) return;
        try {
            const me = await api.get("/api/v1/auth/me");
            const name = me.full_name || me.email || "User";
            nameEl.textContent = name;
            if (avatarEl) avatarEl.textContent = (name || "?").charAt(0).toUpperCase();
        } catch (_) {
            nameEl.textContent = "User";
            if (avatarEl) avatarEl.textContent = "?";
        }
    }

    bindLogout() {
        const profile = document.getElementById("user-profile");
        if (!profile) return;
        profile.replaceWith(profile.cloneNode(true));
        document.getElementById("user-profile").addEventListener("click", () => this.logout());
    }

    logout() {
        session.clearAuth();
        this.showGate();
        window.location.hash = "";
        import("/static/js/gate.js").then((g) => g.render("home"));
    }

    initAppRouter() {
        const menu = document.querySelector(".nav-menu");
        if (menu && !menu._navBound) {
            menu._navBound = true;
            menu.addEventListener("click", (e) => {
                const item = e.target.closest(".nav-item");
                if (item && item.dataset.page) this.navigate(item.dataset.page);
            });
        }
        this.loadPage(this.getPageFromHash());
    }
}

let _tokenPromise = null;
async function ensureAccessToken() {
    if (localStorage.getItem(STORAGE_KEYS.accessToken)) return;
    if (_tokenPromise) return _tokenPromise;

    _tokenPromise = (async () => {
        try {
            const res = await fetch(buildApiUrl("/api/v1/auth/dev-token"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            });
            if (res.ok) {
                const data = await res.json();
                if (data.access_token) {
                    localStorage.setItem(STORAGE_KEYS.accessToken, data.access_token);
                }
            }
        } catch (_) {
            /* dev-token not available (production) — user must login manually */
        } finally {
            _tokenPromise = null;
        }
    })();
    return _tokenPromise;
}

export const session = {
    getClientId() {
        return ensureClientId();
    },
    setClientId(clientId) {
        localStorage.setItem(STORAGE_KEYS.clientId, clientId);
    },
    getApiBase,
    setApiBase(apiBase) {
        localStorage.setItem(STORAGE_KEYS.apiBase, apiBase);
    },
    getAccessToken() {
        return localStorage.getItem(STORAGE_KEYS.accessToken);
    },
    setAccessToken(token) {
        localStorage.setItem(STORAGE_KEYS.accessToken, token);
    },
    clearAuth() {
        localStorage.removeItem(STORAGE_KEYS.accessToken);
    },
};

function normalizeErrorDetail(payload, response) {
    const d = payload?.detail ?? payload?.message ?? response.statusText ?? "Request failed";
    if (Array.isArray(d)) return d.map((x) => (x && x.msg) || String(x)).join("; ");
    return String(d);
}

export const api = {
    async request(method, endpoint, data = null, options = {}) {
        const { retries = 0 } = options;
        const url = buildApiUrl(endpoint);

        await ensureAccessToken();

        let lastErr;
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                const headers = { "Content-Type": "application/json" };
                const token = localStorage.getItem(STORAGE_KEYS.accessToken);
                if (token) {
                    headers["Authorization"] = `Bearer ${token}`;
                }

                const response = await fetch(url, {
                    method,
                    headers,
                    body: data ? JSON.stringify(data) : undefined,
                });

                const text = await response.text();
                let payload = null;
                try {
                    payload = text ? JSON.parse(text) : {};
                } catch (_) {
                    payload = { raw: text };
                }

                if (!response.ok) {
                    const detail = normalizeErrorDetail(payload, response);
                    const err = new Error(detail);
                    err.status = response.status;
                    err.payload = payload;
                    if (response.status === 401 || response.status === 403) {
                        err.unauthorized = true;
                    }
                    throw err;
                }
                return payload;
            } catch (e) {
                lastErr = e;
                if (e.unauthorized || attempt >= retries) throw e;
            }
        }
        throw lastErr;
    },

    async get(endpoint, options) {
        return this.request("GET", endpoint, null, options);
    },

    async post(endpoint, data, options) {
        return this.request("POST", endpoint, data, options);
    },
};

document.addEventListener("DOMContentLoaded", async () => {
    window.taxGodSession = session;
    window.taxGodApi = api;
    const app = new App();
    window.taxGodApp = app;
    window.app = app;

    await ensureAccessToken();
    const token = session.getAccessToken();

    if (token) {
        try {
            await api.get("/api/v1/auth/me");
        } catch (e) {
            if (e.unauthorized) session.clearAuth();
        }
    }

    if (session.getAccessToken()) {
        app.showApp();
    } else {
        let hash = (window.location.hash || "").replace(/^#/, "").toLowerCase();
        if (isAppRoute(hash)) {
            window.location.hash = "login";
            hash = "login";
        }
        app.showGate();
        const view = hash === "login" || hash === "register" ? hash : "home";
        const gate = await import("/static/js/gate.js");
        gate.render(view);
    }

    window.addEventListener("hashchange", () => {
        if (app._appReady) {
            app.loadPage(app.getPageFromHash());
        } else {
            const page = (window.location.hash || "").replace(/^#/, "").toLowerCase();
            if (isAppRoute(page)) {
                window.location.hash = "login";
                import("/static/js/gate.js").then((g) => g.render("login"));
            } else {
                import("/static/js/gate.js").then((g) => g.render(getGateViewFromHash()));
            }
        }
    });
});
