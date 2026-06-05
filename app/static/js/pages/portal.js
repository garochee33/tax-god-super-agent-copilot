import { api } from "../app.js";

export default {
    render() {
        return `
            <div class="page-description">Client Portal — Preview what your clients see when they log in.</div>
            <div class="card" style="margin-bottom:var(--spacing-lg)">
                <div class="card-title">Invoices</div>
                <table class="table" id="portal-invoices"><thead><tr><th>#</th><th>Amount</th><th>Status</th><th>Due</th></tr></thead><tbody></tbody></table>
            </div>
            <div class="card" style="margin-bottom:var(--spacing-lg)">
                <div class="card-title">Projects</div>
                <table class="table" id="portal-projects"><thead><tr><th>Name</th><th>Status</th><th>Start</th><th>End</th></tr></thead><tbody></tbody></table>
            </div>
            <div class="card" style="margin-bottom:var(--spacing-lg)">
                <div class="card-title">Upload Document</div>
                <form id="portal-upload" style="padding:var(--spacing-md);display:flex;gap:8px;align-items:center">
                    <input type="file" name="file" class="form-control" required>
                    <button class="btn btn-primary btn-sm" type="submit">Upload</button>
                </form>
                <div id="upload-status"></div>
            </div>
            <div class="card">
                <div class="card-title">Messages</div>
                <div id="portal-messages" style="padding:var(--spacing-md);max-height:300px;overflow-y:auto"></div>
                <form id="portal-msg-form" style="padding:var(--spacing-md);display:flex;gap:8px">
                    <input class="form-control" name="content" placeholder="Type a message..." required style="flex:1">
                    <button class="btn btn-primary btn-sm" type="submit">Send</button>
                </form>
            </div>`;
    },

    async init() {
        document.getElementById("portal-upload").addEventListener("submit", async (e) => {
            e.preventDefault();
            const f = new FormData(e.target);
            const res = await api.upload("/api/v1/portal/documents/upload", f).catch(() => null);
            document.getElementById("upload-status").textContent = res ? `Uploaded: ${res.filename}` : "Upload failed";
            e.target.reset();
        });
        document.getElementById("portal-msg-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const content = new FormData(e.target).get("content");
            await api.post("/api/v1/portal/messages", { content }).catch(() => null);
            e.target.reset();
            this.loadMessages();
        });
        await this.load();
    },

    async load() {
        const invoices = await api.get("/api/v1/portal/invoices").catch(() => []);
        document.getElementById("portal-invoices").querySelector("tbody").innerHTML =
            (invoices || []).map(i => `<tr><td>${i.invoice_number}</td><td>$${(i.amount||0).toFixed(2)}</td><td>${i.status}</td><td>${i.due_date||"—"}</td></tr>`).join("") || "<tr><td colspan=4>No invoices</td></tr>";

        const projects = await api.get("/api/v1/portal/projects").catch(() => []);
        document.getElementById("portal-projects").querySelector("tbody").innerHTML =
            (projects || []).map(p => `<tr><td>${p.name}</td><td>${p.status}</td><td>${p.start_date||"—"}</td><td>${p.end_date||"—"}</td></tr>`).join("") || "<tr><td colspan=4>No projects</td></tr>";

        await this.loadMessages();
    },

    async loadMessages() {
        const messages = await api.get("/api/v1/portal/messages").catch(() => []);
        document.getElementById("portal-messages").innerHTML =
            (messages || []).map(m => `<div style="margin-bottom:8px"><strong>${m.sender}:</strong> ${m.content} <small style="color:var(--text-muted)">${m.created_at}</small></div>`).join("") || "<p>No messages yet.</p>";
    }
};
