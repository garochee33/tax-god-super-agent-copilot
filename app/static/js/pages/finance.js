import { api } from '../app.js';

let activeTab = 'accounts';
let data = { accounts: [], invoices: [], projects: [], spreadsheets: [], notes: [] };
let showForm = false;
let editId = null;

const TABS = ['accounts', 'invoices', 'projects', 'spreadsheets', 'notes'];

export default {
    render() {
        return `
            <div class="page-description">Manage your finances — accounts, invoices, projects, spreadsheets, and notes all in one place.</div>
            <div class="card">
                <div class="card-header" style="display:flex;gap:8px;flex-wrap:wrap;">
                    ${TABS.map(t => `<button class="btn ${t === activeTab ? 'btn-primary' : ''}" data-tab="${t}">${t.charAt(0).toUpperCase() + t.slice(1)}</button>`).join('')}
                </div>
                <div id="finance-content"></div>
            </div>`;
    },
    async init() {
        document.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', e => { activeTab = e.target.dataset.tab; showForm = false; editId = null; load(); }));
        await load();
    }
};

async function load() {
    try { const r = await api.get(`/api/v1/${activeTab}`); data[activeTab] = r.items || r || []; } catch(e) { data[activeTab] = []; }
    renderTab();
}

function renderTab() {
    document.querySelectorAll('[data-tab]').forEach(b => b.classList.toggle('btn-primary', b.dataset.tab === activeTab));
    const c = document.getElementById('finance-content');
    if (!c) return;
    c.innerHTML = `<div style="padding:16px;"><button class="btn btn-primary" id="add-btn">+ Add New</button>
        <div id="form-area" style="margin:12px 0;${showForm ? '' : 'display:none;'}">${getForm()}</div>
        <div style="overflow-x:auto;margin-top:12px;">${getTable()}</div></div>`;
    document.getElementById('add-btn').addEventListener('click', () => { showForm = !showForm; editId = null; renderTab(); });
    bindForm();
    bindActions();
}

function getTable() {
    const items = data[activeTab];
    if (!items.length) return '<p style="color:#999;">No items yet.</p>';
    const cols = { accounts: ['name','account_type','provider','balance','status'], invoices: ['invoice_number','client','total_amount','status','due_date'], projects: ['name','client','status','budget','spent'], spreadsheets: ['name','sheet_type','created_at'], notes: ['title','tags','client_id','project_id'] };
    const headers = cols[activeTab];
    return `<table style="width:100%;border-collapse:collapse;"><thead><tr>${headers.map(h => `<th style="text-align:left;padding:8px;border-bottom:1px solid #333;">${h.replace(/_/g,' ')}</th>`).join('')}<th style="padding:8px;border-bottom:1px solid #333;">Actions</th></tr></thead><tbody>${items.map(item => `<tr>${headers.map(h => `<td style="padding:8px;border-bottom:1px solid #222;">${fmt(item[h])}</td>`).join('')}<td style="padding:8px;border-bottom:1px solid #222;">
        <button class="btn" data-edit="${item.id}">Edit</button> <button class="btn" data-del="${item.id}">Del</button>
        ${activeTab === 'invoices' && item.status !== 'paid' ? `<button class="btn" data-paid="${item.id}">Mark Paid</button>` : ''}
        ${activeTab === 'spreadsheets' ? `<button class="btn" data-view="${item.id}">View</button>` : ''}
    </td></tr>`).join('')}</tbody></table>`;
}

function fmt(v) { if (v == null) return '-'; if (Array.isArray(v)) return v.join(', '); return String(v); }

function getForm() {
    const item = editId ? data[activeTab].find(i => i.id === editId) : {};
    const v = (k) => item?.[k] ?? '';
    if (activeTab === 'accounts') return formWrap(`<input class="form-control" name="name" placeholder="Name" value="${v('name')}"><select class="form-control" name="account_type"><option value="">Type...</option>${['personal','business','bank','stripe','paypal','crypto','other'].map(o => `<option ${v('account_type')===o?'selected':''}>${o}</option>`).join('')}</select><input class="form-control" name="provider" placeholder="Provider" value="${v('provider')}"><input class="form-control" name="currency" placeholder="Currency" value="${v('currency') || 'USD'}"><textarea class="form-control" name="notes" placeholder="Notes">${v('notes')}</textarea>`);
    if (activeTab === 'invoices') return formWrap(`<input class="form-control" name="invoice_number" placeholder="Invoice #" value="${v('invoice_number')}"><input class="form-control" name="client" placeholder="Client" value="${v('client')}"><input class="form-control" name="amount" type="number" step="0.01" placeholder="Amount" value="${v('amount') || ''}"><input class="form-control" name="tax_amount" type="number" step="0.01" placeholder="Tax" value="${v('tax_amount') || ''}"><input class="form-control" name="due_date" type="date" value="${v('due_date') || ''}"><textarea class="form-control" name="items" placeholder='Items JSON'>${v('items') ? JSON.stringify(v('items')) : ''}</textarea><textarea class="form-control" name="notes" placeholder="Notes">${v('notes')}</textarea>`);
    if (activeTab === 'projects') return formWrap(`<input class="form-control" name="name" placeholder="Name" value="${v('name')}"><input class="form-control" name="client" placeholder="Client" value="${v('client')}"><input class="form-control" name="budget" type="number" step="0.01" placeholder="Budget" value="${v('budget') || ''}"><input class="form-control" name="start_date" type="date" value="${v('start_date') || ''}"><input class="form-control" name="end_date" type="date" value="${v('end_date') || ''}"><textarea class="form-control" name="description" placeholder="Description">${v('description')}</textarea>`);
    if (activeTab === 'spreadsheets') return formWrap(`<input class="form-control" name="name" placeholder="Name" value="${v('name')}"><select class="form-control" name="sheet_type"><option value="">Type...</option>${['pnl','balance_sheet','budget','tax_summary','custom'].map(o => `<option ${v('sheet_type')===o?'selected':''}>${o}</option>`).join('')}</select>${editId ? `<textarea class="form-control" name="data" placeholder="Data JSON" rows="6">${v('data') ? JSON.stringify(v('data')) : ''}</textarea>` : ''}`);
    if (activeTab === 'notes') return formWrap(`<input class="form-control" name="title" placeholder="Title" value="${v('title')}"><textarea class="form-control" name="content" placeholder="Content">${v('content')}</textarea><input class="form-control" name="tags" placeholder="Tags (comma-sep)" value="${Array.isArray(v('tags')) ? v('tags').join(',') : v('tags')}"><input class="form-control" name="client_id" placeholder="Client ID" value="${v('client_id') || ''}"><input class="form-control" name="project_id" placeholder="Project ID" value="${v('project_id') || ''}">`);
    return '';
}

function formWrap(fields) {
    return `<form id="item-form" style="display:flex;flex-direction:column;gap:8px;max-width:500px;">${fields}<button type="submit" class="btn btn-primary">${editId ? 'Update' : 'Create'}</button></form>`;
}

function bindForm() {
    const form = document.getElementById('item-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        let body = Object.fromEntries(fd);
        // Parse special fields
        if (body.items) try { body.items = JSON.parse(body.items); } catch(_) {}
        if (body.data) try { body.data = JSON.parse(body.data); } catch(_) {}
        if (body.tags && typeof body.tags === 'string') body.tags = body.tags.split(',').map(t => t.trim()).filter(Boolean);
        ['amount','tax_amount','budget'].forEach(k => { if (body[k]) body[k] = parseFloat(body[k]); });
        // Remove empty strings
        Object.keys(body).forEach(k => { if (body[k] === '') delete body[k]; });
        try {
            if (editId) await api.request('PATCH', `/api/v1/${activeTab}/${editId}`, body);
            else await api.post(`/api/v1/${activeTab}`, body);
            showForm = false; editId = null; await load();
        } catch(err) { alert(err.message); }
    });
}

function bindActions() {
    document.querySelectorAll('[data-del]').forEach(b => b.addEventListener('click', async () => {
        if (!confirm('Delete?')) return;
        await api.request('DELETE', `/api/v1/${activeTab}/${b.dataset.del}`); load();
    }));
    document.querySelectorAll('[data-edit]').forEach(b => b.addEventListener('click', () => {
        editId = b.dataset.edit; showForm = true; renderTab();
    }));
    document.querySelectorAll('[data-paid]').forEach(b => b.addEventListener('click', async () => {
        await api.post(`/api/v1/invoices/${b.dataset.paid}/mark-paid`, {}); load();
    }));
    document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => {
        editId = b.dataset.view; showForm = true; renderTab();
    }));
}
