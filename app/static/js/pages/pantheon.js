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
                <div class="card stat-card"><div class="stat-value" id="kpi-quarterly-tax">--</div><div class="stat-label">Quarterly Tax Due</div></div>
            </div>
            <div class="grid grid-2" style="margin-top:var(--spacing-xl)">
                <div class="card"><div class="card-title">Revenue (Last 12 Months)</div><div id="revenue-chart" style="display:flex;align-items:flex-end;gap:4px;height:160px;padding:var(--spacing-md)"><p class="text-muted">Loading chart...</p></div></div>
                <div class="card"><div class="card-title">Recent Activity</div><div id="recent-activity"><p>Loading...</p></div></div>
            </div>
            <div class="grid grid-2" style="margin-top:var(--spacing-md)">
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

        api.get("/api/v1/estimates/quarterly").then(d => {
            document.getElementById("kpi-quarterly-tax").textContent = fmt(d.quarterly_payment);
        }).catch(() => {
            document.getElementById("kpi-quarterly-tax").textContent = "N/A";
        });

        const items = Array.isArray(transactions) ? transactions.slice(0, 5) : [];
        document.getElementById("recent-activity").innerHTML = items.length
            ? `<ul style="list-style:none;padding:0;margin:0">${items.map(t => `<li class="activity-item" style="padding:6px var(--spacing-md);border-bottom:1px solid var(--color-parchment-dark)">${t.date || ""} — ${t.description || "Transaction"} <strong>${fmt(t.amount)}</strong></li>`).join("")}</ul>`
            : '<p class="text-muted" style="padding:var(--spacing-md)">No recent activity</p>';

        // Revenue chart
        api.get("/api/v1/charts/revenue-monthly").then(data => {
            const el = document.getElementById("revenue-chart");
            if (!Array.isArray(data) || !data.length) { el.innerHTML = '<p class="text-muted">No revenue data</p>'; return; }
            const max = Math.max(...data.map(d => d.amount), 1);
            el.innerHTML = data.map(d => {
                const h = Math.max((d.amount / max) * 130, 2);
                return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end">
                    <div style="font-size:10px;margin-bottom:2px">${fmt(d.amount)}</div>
                    <div style="width:100%;height:${h}px;background:var(--color-gold,#d4a017);border-radius:3px 3px 0 0"></div>
                    <div style="font-size:9px;margin-top:2px">${d.month.slice(5)}</div></div>`;
            }).join("");
        }).catch(() => {
            document.getElementById("revenue-chart").innerHTML = '<p class="text-muted">Chart unavailable</p>';
        });
    }
};
