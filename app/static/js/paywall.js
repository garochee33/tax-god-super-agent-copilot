/*
  PAYWALL.JS
  Global 402 interceptor — shows subscription modal when trial expires.
*/
(function () {
    "use strict";

    let modalEl = null;

    function createModal() {
        if (modalEl) return modalEl;
        modalEl = document.createElement("div");
        modalEl.id = "paywall-modal";
        modalEl.innerHTML = `
            <div class="paywall-backdrop"></div>
            <div class="paywall-card">
                <h2>Your trial has expired</h2>
                <p class="paywall-sub">Upgrade to continue using all Tax God features.</p>
                <div class="paywall-plan" id="paywall-plan-info"></div>
                <button class="paywall-btn paywall-btn-primary" id="paywall-subscribe">
                    Subscribe Now — $29/month
                </button>
                <button class="paywall-btn paywall-btn-secondary" id="paywall-dismiss">
                    Continue in Limited Mode
                </button>
            </div>
        `;
        document.body.appendChild(modalEl);

        modalEl.querySelector("#paywall-subscribe").addEventListener("click", handleSubscribe);
        modalEl.querySelector("#paywall-dismiss").addEventListener("click", hide);
        modalEl.querySelector(".paywall-backdrop").addEventListener("click", hide);
        return modalEl;
    }

    async function handleSubscribe() {
        const btn = modalEl.querySelector("#paywall-subscribe");
        btn.textContent = "Redirecting…";
        btn.disabled = true;
        try {
            const token = localStorage.getItem("taxgod_access_token");
            const res = await fetch("/api/v1/billing/create-checkout", {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            });
            const data = await res.json();
            if (data.url) {
                window.location.href = data.url;
            } else {
                btn.textContent = "Stripe not configured — add keys in Settings";
                setTimeout(() => { btn.textContent = "Subscribe Now — $29/month"; btn.disabled = false; }, 3000);
            }
        } catch {
            btn.textContent = "Error — try again";
            btn.disabled = false;
        }
    }

    async function loadPlanInfo() {
        try {
            const token = localStorage.getItem("taxgod_access_token");
            const res = await fetch("/api/v1/billing/status", {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const info = await res.json();
                const el = document.getElementById("paywall-plan-info");
                const tier = info.tier || "free_trial";
                const expired = info.expires_at ? new Date(info.expires_at).toLocaleDateString() : "—";
                el.textContent = `Plan: ${tier} • Expired: ${expired}`;
            }
        } catch { /* silent */ }
    }

    function show() {
        createModal();
        modalEl.classList.add("paywall-visible");
        loadPlanInfo();
    }

    function hide() {
        if (modalEl) modalEl.classList.remove("paywall-visible");
    }

    // Monkey-patch fetch to intercept 402 globally
    const _origFetch = window.fetch;
    window.fetch = async function (...args) {
        const res = await _origFetch.apply(this, args);
        if (res.status === 402) {
            show();
        }
        return res;
    };

    // Expose for manual trigger
    window.TaxGodPaywall = { show, hide };
})();
