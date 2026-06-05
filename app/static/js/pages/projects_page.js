import { api } from '../app.js';

const API = '/api/v1/projects';
const STATUSES = ['active','completed','on_hold','cancelled'];
let projects = [], showForm = false;

async function load() {
    try { const r = await api.get(API); projects = r.items || r || []; } catch(e) { projects = []; }
    renderContent();
}

function renderContent() {
    const c = document.getElementById('projects-content');
    if (!c) return;
    c.innerHTML = `
        <button class="btn btn-primary" id="toggle-form">+ New Project</button>
        <div id="proj-form-area" style="margin:12px 0;${showForm ? '' : 'display:none;'}">
            <form id="proj-form" class="card" style="padding:16px;display:flex;gap:8px;flex-wrap:wrap;align-items:end;">
                <input type="text" name="name" class="form-control" placeholder="Project Name" required style="width:160px;">
                <select name="status" class="form-control" style="width:120px;">${STATUSES.map(s => `<option value="${s}">${s.replace(/_/g,' ')}</option>`).join('')}</select>
                <input type="number" name="budget" class="form-control" placeholder="Budget" step="0.01" style="width:100px;">
                <input type="date" name="start_date" class="form-control" style="width:140px;">
                <input type="date" name="end_date" class="form-control" style="width:140px;">
                <input type="text" name="description" class="form-control" placeholder="Description" style="width:180px;">
                <button type="submit" class="btn btn-primary">Create</button>
            </form>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-top:16px;">
            ${projects.map(p => {
                const spent = p.spent || 0, budget = p.budget || 1;
                const pct = Math.min(100, (spent / budget) * 100);
                return `<div class="card" style="padding:16px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h3 style="margin:0;">${p.name}</h3>
                        <span class="status-badge status-${p.status || 'inactive'}">${p.status}</span>
                    </div>
                    <p class="text-muted text-sm" style="margin:4px 0;">${p.client_name || p.client_id || '—'} • ${p.start_date || '?'} → ${p.end_date || '?'}</p>
                    <div class="progress-bar"><div class="progress-bar-fill${pct>90?' danger':''}" style="width:${pct}%;"></div></div>
                    <p class="text-muted text-xs">$${spent.toFixed(2)} / $${(p.budget||0).toFixed(2)}</p>
                    <button class="btn-sm btn-danger btn-del" data-id="${p.id}">Delete</button>
                </div>`;
            }).join('') || '<p class="text-muted">No projects yet.</p>'}
        </div>`;
    bindEvents();
}

function bindEvents() {
    document.getElementById('toggle-form').onclick = () => { showForm = !showForm; renderContent(); };
    const form = document.getElementById('proj-form');
    if (form) form.onsubmit = async (ev) => {
        ev.preventDefault();
        const data = Object.fromEntries(new FormData(form).entries());
        Object.keys(data).forEach(k => { if (!data[k]) delete data[k]; });
        if (data.budget) data.budget = parseFloat(data.budget);
        try { await api.post(API, data); showForm = false; await load(); } catch(e) { alert(e.message); }
    };
    document.querySelectorAll('.btn-del').forEach(b => b.onclick = async () => {
        await api.request('DELETE', `${API}/${b.dataset.id}`); load();
    });
}

export default {
    render() {
        return `<div class="page-container">
            <div class="page-description">Track projects with budgets, timelines, and progress. Link to clients for billing.</div>
            <h1>📋 Projects</h1>
            <div id="projects-content"><p style="opacity:0.6">Loading...</p></div>
        </div>`;
    },
    init() { load(); }
};
