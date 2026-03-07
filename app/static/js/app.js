/*
  APP.JS
  Main Application Entry Point & Router
*/

const routes = {
    pantheon: { title: "The Pantheon", module: "/static/js/pages/pantheon.js" },
    oracle: { title: "The Oracle", module: "/static/js/pages/oracle.js" },
    tribunal: { title: "Gabriel's Tribunal", module: "/static/js/pages/tribunal.js" },
    archives: { title: "The Archives", module: "/static/js/pages/archives.js" },
    scrolls: { title: "Sacred Scrolls", module: "/static/js/pages/scrolls.js" },
    agora: { title: "The Agora", module: "/static/js/pages/agora.js" },
    hermes: { title: "Temple of Hermes", module: "/static/js/pages/hermes.js" },
};

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
    if (!base) return endpoint;
    return `${base.replace(/\/$/, "")}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
}

class App {
    constructor() {
        this.appContainer = document.getElementById("app");
        this.pageTitle = document.getElementById("page-title");
        this.navItems = document.querySelectorAll(".nav-item");
        this.currentPage = "pantheon";
        this.clientId = ensureClientId();

        this.init();
    }

    init() {
        this.navItems.forEach((item) => {
            item.addEventListener("click", (e) => {
                const page = e.currentTarget.dataset.page;
                this.navigate(page);
            });
        });

        // Hash navigation is the source of truth for SPA routes.
        window.addEventListener("hashchange", () => {
            this.loadPage(this.getPageFromHash());
        });

        this.loadPage(this.getPageFromHash());
    }

    getPageFromHash() {
        const page = window.location.hash.substring(1) || "pantheon";
        return routes[page] ? page : "pantheon";
    }

    navigate(page) {
        const target = routes[page] ? page : "pantheon";
        if (target === this.currentPage) return;
        window.location.hash = target;
    }

    async loadPage(pageId) {
        const route = routes[pageId] || routes.pantheon;
        this.currentPage = pageId;

        this.updateActiveNav(pageId);
        this.pageTitle.textContent = route.title;
        this.appContainer.innerHTML = '<div class="spinner"></div>';

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

document.addEventListener("DOMContentLoaded", () => {
    window.taxGodApp = new App();
    // Backward compatibility for any page module still referencing window.app.
    window.app = window.taxGodApp;
});
