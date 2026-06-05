import { api } from "../app.js";

const fmt = (v) => `$${(v || 0).toFixed(2)}`;

export default {
    render() {
        return `
            <div class="page-description">Log billable hours by project. Track time, set rates, and generate invoices from time entries.</div>
            <div class="card" style="margin-bottom:var(--spacing-lg)">
                <div class="card-title">Log Time</div>
                <form id="time-form" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;padding:var(--spacing-md)">
                    <input class="form-control" name="project" placeholder="Project" required>
                    <input class="form-control" name="description" placeholder="Description">
                    <input class="form-control" name="hours" type="number" step="0.25" placeholder="Hours" required>
                    <input class="form-control" name="date" type="date" required>
                    <input class="form-control" name="rate" type="number" step="0.01" placeholder="Rate ($)">
                    <label style="display:flex;align-items:center;gap:4px"><input type="checkbox" name="billable" checked> Billable</label>
                    <button class="btn btn-primary btn-sm" type="submit">Add</button>
                </form>
            </div>
            <div class="card" style="margin-bottom:var(--spacing-lg)">
                <div class="card-title">Summary</div>
                <div id="time-summary" style="padding:var(--spacing-md)">Loading...</div>
            </div>
            <div class="card"><div class="card-title">Time Entries</div>
                <div style="overflow-x:auto"><table class="table" id="time-table"><thead><tr><th>Date</th><th>Project</th><th>Description</th><th>Hours</th><th>Rate</th><th>Total</th><th>Billable</th></tr></thead><tbody></tbody></table></div>
            </div>`;
    },

    async init() {
        document.getElementById("time-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const f = new FormData(e.target);
            await api.post("/api/v1/time-entries", { project: f.get("project"), description: f.get("description"), hours: +f.get("hours"), date: f.get("date"), rate: +f.get("rate") || 0, billable: !!f.get("billable") });
            e.target.reset();
            this.load();
        });
        await this.load();
    },

    async load() {
        const [entries, summary] = await Promise.all([
            api.get("/api/v1/time-entries").catch(() => []),
            api.get("/api/v1/time-entries/summary").catch(() => ({})),
        ]);
        const arr = Array.isArray(entries) ? entries : [];
        document.getElementById("time-table").querySelector("tbody").innerHTML = arr.map(e => `<tr><td>${e.date||""}</td><td>${e.project||""}</td><td>${e.description||""}</td><td>${e.hours}</td><td>${fmt(e.rate)}</td><td>${fmt(e.hours*e.rate)}</td><td>${e.billable?"✓":""}</td></tr>`).join("") || "<tr><td colspan=7>No entries</td></tr>";
        document.getElementById("time-summary").innerHTML = `<strong>${summary.total_hours ?? 0}h</strong> this week &nbsp;|&nbsp; Billable: <strong>${fmt(summary.billable_amount ?? 0)}</strong>`;
    }
};
