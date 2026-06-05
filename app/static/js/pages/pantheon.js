import { api } from "../app.js";

const fmt = (v) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v || 0);

export default {
    render() {
        return `
            <div class="page-description">Your financial command center — live KPIs, recent activity, and quick actions at a glance.</div>
            <div class="grid grid-4">
                <div class="card stat-card"><div class="stat-value" id="kpi-revenue">--</div><div class="stat-label">Revenue This Month</div></div>
                <div class="card stat-card"><div class="stat-value" id="kpi-outstanding">--</div><div class="stat-label">Outstanding Invoices</div></div>
                <div class="card stat-card"><div class="stat-value" id="kpi-expenses">--</div><div class="stat-label">Expenses This Month</div></div>
                <div class="card stat-card"><div class="stat-value" id="kpi-profit">--</div><div class="stat-label">Net Profit</div></div>
            </div>
            <div class="grid grid-2" style="margin-top:var(--spacing-xl)">
                <div class="card"><div class="card-title">Recent Activity</div><div id="recent-activity"><p>Loading...</p></div></div>
                <div class="card"><div class="card-title">Quick Actions</div><div style="display:flex;flex-wrap:wrap;gap:8px;padding:var(--spacing-md)">
                    <button class="btn btn-primary btn-sm" onclick="window.location.hash='finance'">New Invoice</button>
                    <button class="btn btn-outline btn-sm" onclick="window.location.hash='expenses'">Add Expense</button>
                    <button class="btn btn-outline btn-sm" onclick="window.location.hash='agora'">New Client</button>
                    <button class="btn btn-gold btn-sm" onclick="window.location.hash='oracle'">Ask Tax God</button>
                </div></div>
            </div>`;
    },

    async init() {
        const [paid, sent, expSummary, transactions] = await Promise.all([
            api.get("/api/v1/invoices?status=paid").catch(() => []),
            api.get("/api/v1/invoices?status=sent").catch(() => []),
            api.get("/api/v1/expenses/summary").catch(() => ({ total: 0 })),
            api.get("/api/v1/transactions?limit=5").catch(() => []),
        ]);

        const now = new Date();
        const thisMonth = (inv) => { const d = new Date(inv.created_at || inv.date || ""); return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear(); };
        const revenue = (Array.isArray(paid) ? paid : []).filter(thisMonth).reduce((s, i) => s + (i.total || i.amount || 0), 0);
        const sentArr = Array.isArray(sent) ? sent : [];
        const outstanding = sentArr.reduce((s, i) => s + (i.total || i.amount || 0), 0);
        const expenses = expSummary?.total ?? expSummary?.total_expenses ?? 0;

        document.getElementById("kpi-revenue").textContent = fmt(revenue);
        document.getElementById("kpi-outstanding").textContent = `${sentArr.length} / ${fmt(outstanding)}`;
        document.getElementById("kpi-expenses").textContent = fmt(expenses);
        document.getElementById("kpi-profit").textContent = fmt(revenue - expenses);

        const items = Array.isArray(transactions) ? transactions.slice(0, 5) : [];
        document.getElementById("recent-activity").innerHTML = items.length
            ? `<ul style="list-style:none;padding:0;margin:0">${items.map(t => `<li class="activity-item" style="padding:6px var(--spacing-md);border-bottom:1px solid var(--color-parchment-dark)">${t.date || ""} — ${t.description || "Transaction"} <strong>${fmt(t.amount)}</strong></li>`).join("")}</ul>`
            : '<p class="text-muted" style="padding:var(--spacing-md)">No recent activity</p>';
    }
};
