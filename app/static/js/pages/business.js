import { api } from '../app.js';

const API = '/api/v1/businesses';
const TYPES = ['llc','corporation','sole_prop','partnership','nonprofit','trust'];
let businesses = [];

async function load() {
    try { const r = await api.get(API); businesses = r.items || r || []; } catch(e) { businesses = []; }
    renderContent();
}

function renderContent() {
    const c = document.getElementById('business-content');
    if (!c) return;
    c.innerHTML = `
        <div class="card" style="padding:16px;margin-bottom:16px;">
            <form id="biz-form" style="display:flex;gap:8px;flex-wrap:wrap;align-items:end;">
                <input type="text" name="name" class="form-control" placeholder="Business Name" required style="width:160px;">
                <select name="business_type" class="form-control" style="width:140px;">${TYPES.map(t => `<option value="${t}">${t.replace(/_/g,' ')}</option>`).join('')}</select>
                <input type="text" name="ein" class="form-control" placeholder="EIN" style="width:120px;">
                <input type="text" name="address" class="form-control" placeholder="Address" style="width:180px;">
                <input type="text" name="currency" class="form-control" placeholder="USD" value="USD" style="width:70px;">
                <input type="date" name="fiscal_year_start" class="form-control" style="width:140px;">
                <button type="submit" class="btn btn-primary">Create</button>
            </form>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;">
            ${businesses.map(b => `<div class="card" style="padding:16px;${b.is_default ? 'border:2px solid var(--accent, #4ade80);' : ''}">
                <h3>${b.name} ${b.is_default ? '<span class="status-badge status-active">DEFAULT</span>' : ''}</h3>
                <p style="opacity:0.7;font-size:0.85rem;">${(b.business_type||'').replace(/_/g,' ')} ${b.ein ? '• EIN: '+b.ein : ''}</p>
                <p style="opacity:0.7;font-size:0.85rem;">${b.address || ''} ${b.currency ? '• '+b.currency : ''}</p>
                <div style="margin-top:8px;display:flex;gap:8px;">
                    ${!b.is_default ? `<button class="btn-sm btn-default" data-id="${b.id}">Set Default</button>` : ''}
                    <button class="btn-sm btn-danger btn-del" data-id="${b.id}">Delete</button>
                </div>
            </div>`).join('') || '<p style="opacity:0.6">No businesses yet.</p>'}
        </div>`;
    bindEvents();
}

function bindEvents() {
    const form = document.getElementById('biz-form');
    if (form) form.onsubmit = async (ev) => {
        ev.preventDefault();
        const data = Object.fromEntries(new FormData(form).entries());
        Object.keys(data).forEach(k => { if (!data[k]) delete data[k]; });
        try { await api.post(API, data); await load(); } catch(e) { alert(e.message); }
    };
    document.querySelectorAll('.btn-default').forEach(b => b.onclick = async () => {
        await api.post(`${API}/${b.dataset.id}/set-default`); load();
    });
    document.querySelectorAll('.btn-del').forEach(b => b.onclick = async () => {
        await api.request('DELETE', `${API}/${b.dataset.id}`); load();
    });
}

export default {
    render() {
        return `<div class="page-container">
            <div class="page-description">Set up and manage your businesses. Each business has its own accounts, expenses, and tax context.</div>
            <h1>🏢 Businesses</h1>
            <div id="business-content"><p style="opacity:0.6">Loading...</p></div>
        </div>`;
    },
    init() { load(); }
};
