import { api } from "../app.js";

const fmt = (v) => `$${(v || 0).toFixed(2)}`;

export default {
    render() {
        return `
            <div class="page-description">Manage vendors, suppliers, and contractors. Track payments and flag 1099-eligible vendors.</div>
            <div class="card" style="margin-bottom:var(--spacing-lg)">
                <div class="card-title">Add Vendor</div>
                <form id="vendor-form" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;padding:var(--spacing-md)">
                    <input class="form-control" name="name" placeholder="Name" required>
                    <input class="form-control" name="email" placeholder="Email" type="email">
                    <input class="form-control" name="company" placeholder="Company">
                    <select class="form-control" name="category"><option value="">Category</option><option>Contractor</option><option>Supplier</option><option>Service</option><option>Other</option></select>
                    <input class="form-control" name="tax_id" placeholder="Tax ID">
                    <label style="display:flex;align-items:center;gap:4px"><input type="checkbox" name="is_1099"> 1099 Eligible</label>
                    <button class="btn btn-primary btn-sm" type="submit">Add</button>
                </form>
            </div>
            <div class="card"><div class="card-title">Vendors</div>
                <div style="overflow-x:auto"><table class="table" id="vendor-table"><thead><tr><th>Name</th><th>Company</th><th>Category</th><th>Total Paid</th><th>1099</th></tr></thead><tbody></tbody></table></div>
            </div>`;
    },

    async init() {
        document.getElementById("vendor-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const f = new FormData(e.target);
            await api.post("/api/v1/vendors", { name: f.get("name"), email: f.get("email"), company: f.get("company"), category: f.get("category"), tax_id: f.get("tax_id"), is_1099: !!f.get("is_1099") });
            e.target.reset();
            this.load();
        });
        await this.load();
    },

    async load() {
        const vendors = await api.get("/api/v1/vendors").catch(() => []);
        const arr = Array.isArray(vendors) ? vendors : [];
        document.getElementById("vendor-table").querySelector("tbody").innerHTML = arr.map(v => {
            const alert = v.is_1099 && (v.total_paid || 0) >= 600 ? ' <span class="badge badge-warning">1099 Alert</span>' : "";
            return `<tr><td>${v.name||""}</td><td>${v.company||""}</td><td>${v.category||""}</td><td>${fmt(v.total_paid)}</td><td>${v.is_1099 ? "✓" + alert : ""}</td></tr>`;
        }).join("") || "<tr><td colspan=5>No vendors</td></tr>";
    }
};
