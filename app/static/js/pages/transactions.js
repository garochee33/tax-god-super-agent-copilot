import { api } from "../app.js";

export default {
    render() {
        return `
            <div class="page-description">View and reconcile transactions. Import bank statements via CSV or manually enter transactions.</div>
            <div style="display:flex;gap:8px;margin-bottom:var(--spacing-lg);flex-wrap:wrap;align-items:center">
                <button class="btn btn-primary btn-sm" id="import-csv-btn">Import CSV</button>
                <input class="form-control" id="filter-account" placeholder="Filter account" style="width:150px">
                <select class="form-control" id="filter-reconciled" style="width:150px"><option value="">All</option><option value="true">Reconciled</option><option value="false">Unreconciled</option></select>
                <button class="btn btn-outline btn-sm" id="apply-filters">Filter</button>
            </div>
            <div id="csv-modal" style="display:none;margin-bottom:var(--spacing-lg)" class="card">
                <div class="card-title" style="padding:var(--spacing-md)">Paste CSV</div>
                <textarea id="csv-input" class="form-control" rows="5" style="margin:0 var(--spacing-md);width:calc(100% - 2*var(--spacing-md))" placeholder="date,description,amount,category"></textarea>
                <div style="padding:var(--spacing-md)"><button class="btn btn-primary btn-sm" id="parse-csv">Parse & Import</button></div>
            </div>
            <div class="card"><div class="card-title">Transactions</div>
                <div style="overflow-x:auto"><table class="table" id="txn-table"><thead><tr><th>Date</th><th>Description</th><th>Amount</th><th>Category</th><th>Reconciled</th><th>Actions</th></tr></thead><tbody></tbody></table></div>
            </div>`;
    },

    async init() {
        document.getElementById("import-csv-btn").addEventListener("click", () => {
            const m = document.getElementById("csv-modal");
            m.style.display = m.style.display === "none" ? "block" : "none";
        });
        document.getElementById("parse-csv").addEventListener("click", async () => {
            const csv = document.getElementById("csv-input").value.trim();
            if (!csv) return;
            await api.post("/api/v1/transactions/import-csv", { csv_content: csv });
            document.getElementById("csv-modal").style.display = "none";
            this.load();
        });
        document.getElementById("apply-filters").addEventListener("click", () => this.load());
        await this.load();
    },

    async load() {
        let url = "/api/v1/transactions";
        const params = [];
        const acct = document.getElementById("filter-account").value.trim();
        const rec = document.getElementById("filter-reconciled").value;
        if (acct) params.push(`account=${encodeURIComponent(acct)}`);
        if (rec) params.push(`reconciled=${rec}`);
        if (params.length) url += "?" + params.join("&");

        const txns = await api.get(url).catch(() => []);
        const arr = Array.isArray(txns) ? txns : [];
        document.getElementById("txn-table").querySelector("tbody").innerHTML = arr.map(t => {
            const color = (t.amount || 0) >= 0 ? "text-success" : "text-danger";
            return `<tr><td>${t.date||""}</td><td>${t.description||""}</td><td class="${color}">$${Math.abs(t.amount||0).toFixed(2)}</td><td>${t.category||""}</td><td>${t.reconciled?"✓":""}</td><td>${!t.reconciled?`<button class="btn btn-outline btn-sm" onclick="window._reconcile('${t.id}')">Reconcile</button>`:""}</td></tr>`;
        }).join("") || "<tr><td colspan=6>No transactions</td></tr>";

        window._reconcile = async (id) => {
            await api.request("PATCH", `/api/v1/transactions/${id}/reconcile`);
            this.load();
        };
    }
};
