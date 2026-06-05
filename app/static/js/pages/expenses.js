import { api } from '../app.js';

const API = '/api/v1/expenses';
const CATEGORIES = ['office','travel','meals','auto','insurance','professional_services','utilities','software','marketing','rent','payroll','taxes','other'];
let expenses = [], summary = {};

async function load() {
    try { const r = await api.get(API); expenses = r.items || r || []; } catch(e) { expenses = []; }
    try { summary = await api.get(`${API}/summary`) || {}; } catch(e) { summary = {}; }
    renderContent();
}

function renderContent() {
    const c = document.getElementById('expenses-content');
    if (!c) return;
    const monthTotal = Object.values(summary).reduce((a, v) => a + (v || 0), 0);
    const topCat = Object.entries(summary).sort((a, b) => b[1] - a[1])[0];
    const deductTotal = expenses.filter(e => e.tax_deductible).reduce((a, e) => a + (e.amount || 0), 0);

    c.innerHTML = `
        <div class="card" style="margin-bottom:16px;"><div style="display:flex;gap:24px;flex-wrap:wrap;padding:16px;">
            <div><strong>Month Total:</strong> $${monthTotal.toFixed(2)}</div>
            <div><strong>Top Category:</strong> ${topCat ? topCat[0] : '—'}</div>
            <div><strong>Deductible Total:</strong> $${deductTotal.toFixed(2)}</div>
        </div></div>
        <div class="card" style="margin-bottom:16px;padding:16px;">
            <form id="expense-form" style="display:flex;gap:8px;flex-wrap:wrap;align-items:end;">
                <input type="date" name="date" class="form-control" required style="width:140px;">
                <input type="text" name="vendor" class="form-control" placeholder="Vendor" required style="width:140px;">
                <input type="number" name="amount" class="form-control" placeholder="Amount" step="0.01" required style="width:100px;">
                <select name="category" class="form-control" style="width:160px;">${CATEGORIES.map(c => `<option value="${c}">${c.replace(/_/g,' ')}</option>`).join('')}</select>
                <input type="text" name="description" class="form-control" placeholder="Description" style="width:150px;">
                <label style="display:flex;align-items:center;gap:4px;"><input type="checkbox" name="tax_deductible"> Deductible</label>
                <button type="submit" class="btn btn-primary">Add</button>
            </form>
        </div>
        <div style="overflow-x:auto;">
            <table class="data-table"><thead><tr><th>Date</th><th>Vendor</th><th>Amount</th><th>Category</th><th>Deductible</th><th>Actions</th></tr></thead>
            <tbody>${expenses.map(e => `<tr>
                <td>${e.date || '—'}</td><td>${e.vendor}</td><td>$${(e.amount||0).toFixed(2)}</td>
                <td>${(e.category||'').replace(/_/g,' ')}</td><td>${e.tax_deductible ? '✓' : '✗'}</td>
                <td><button class="btn-sm btn-danger btn-del" data-id="${e.id}">×</button></td>
            </tr>`).join('') || '<tr><td colspan="6" style="opacity:0.6">No expenses yet.</td></tr>'}</tbody></table>
        </div>`;
    bindEvents();
}

function bindEvents() {
    const form = document.getElementById('expense-form');
    if (form) form.onsubmit = async (ev) => {
        ev.preventDefault();
        const fd = new FormData(form);
        const data = Object.fromEntries(fd.entries());
        data.tax_deductible = !!fd.get('tax_deductible');
        data.amount = parseFloat(data.amount);
        try { await api.post(API, data); await load(); } catch(e) { alert(e.message); }
    };
    document.querySelectorAll('.btn-del').forEach(b => b.onclick = async () => {
        await api.request('DELETE', `${API}/${b.dataset.id}`); load();
    });
}

export default {
    render() {
        return `<div class="page-container">
            <div class="page-description">Track and categorize business expenses. Add receipts, mark tax-deductible items, and view spending summaries.</div>
            <h1>💸 Expenses</h1>
            <div id="expenses-content"><p style="opacity:0.6">Loading...</p></div>
        </div>`;
    },
    init() { load(); }
};
