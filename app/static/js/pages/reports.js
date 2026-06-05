import { api } from '../app.js';

let activeTab = 'pnl';
let invoices = [], expenses = [], summary = {};

async function loadData() {
    try { const r = await api.get('/api/v1/invoices'); invoices = r.items || r || []; } catch(e) { invoices = []; }
    try { const r = await api.get('/api/v1/expenses'); expenses = r.items || r || []; } catch(e) { expenses = []; }
    try { summary = await api.get('/api/v1/expenses/summary') || {}; } catch(e) { summary = {}; }
    renderContent();
}

function renderContent() {
    const c = document.getElementById('reports-content');
    if (!c) return;
    const tabs = [['pnl','P&L'],['expenses','Expenses'],['deductions','Tax Deductions']];
    let body = '';

    if (activeTab === 'pnl') {
        const revenue = invoices.reduce((a, i) => a + (i.amount || i.total || 0), 0);
        const totalExp = expenses.reduce((a, e) => a + (e.amount || 0), 0);
        const profit = revenue - totalExp;
        body = `<div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:16px;">
            <div class="card" style="padding:16px;min-width:150px;"><h3 style="color:#4ade80;">Revenue</h3><p style="font-size:1.5rem;">$${revenue.toFixed(2)}</p></div>
            <div class="card" style="padding:16px;min-width:150px;"><h3 style="color:#f87171;">Expenses</h3><p style="font-size:1.5rem;">$${totalExp.toFixed(2)}</p></div>
            <div class="card" style="padding:16px;min-width:150px;"><h3 style="color:${profit>=0?'#4ade80':'#f87171'};">Profit</h3><p style="font-size:1.5rem;">$${profit.toFixed(2)}</p></div>
        </div>`;
    } else if (activeTab === 'expenses') {
        const cats = Object.entries(summary).sort((a, b) => b[1] - a[1]);
        const max = cats[0]?.[1] || 1;
        body = `<div style="margin-top:16px;">${cats.map(([cat, amt]) => `
            <div style="margin:8px 0;display:flex;align-items:center;gap:8px;">
                <span style="width:140px;font-size:0.85rem;">${cat.replace(/_/g,' ')}</span>
                <div style="flex:1;background:#333;border-radius:4px;height:20px;"><div style="width:${(amt/max*100).toFixed(1)}%;height:100%;background:#60a5fa;border-radius:4px;"></div></div>
                <span style="font-size:0.85rem;">$${amt.toFixed(2)}</span>
            </div>`).join('') || '<p style="opacity:0.6">No data.</p>'}</div>`;
    } else {
        const deductible = expenses.filter(e => e.tax_deductible);
        const grouped = {};
        deductible.forEach(e => { grouped[e.category] = (grouped[e.category] || 0) + (e.amount || 0); });
        const total = deductible.reduce((a, e) => a + (e.amount || 0), 0);
        body = `<div style="margin-top:16px;">
            <table class="data-table"><thead><tr><th>Category</th><th>Total</th></tr></thead><tbody>
            ${Object.entries(grouped).sort((a,b)=>b[1]-a[1]).map(([cat,amt]) => `<tr><td>${cat.replace(/_/g,' ')}</td><td>$${amt.toFixed(2)}</td></tr>`).join('')}
            </tbody></table>
            <p style="margin-top:12px;font-weight:bold;">Total Deductions: $${total.toFixed(2)}</p>
        </div>`;
    }

    c.innerHTML = `<div class="card"><div class="card-header" style="display:flex;gap:8px;">
        ${tabs.map(([k,l]) => `<button class="btn ${k===activeTab?'btn-primary':''}" data-tab="${k}">${l}</button>`).join('')}
    </div><div style="padding:16px;">${body}</div></div>`;

    c.querySelectorAll('[data-tab]').forEach(b => b.onclick = () => { activeTab = b.dataset.tab; renderContent(); });
}

export default {
    render() {
        return `<div class="page-container">
            <div class="page-description">View auto-generated financial reports based on your data — P&L, expense summaries, and tax deduction totals.</div>
            <h1>📊 Reports</h1>
            <div id="reports-content"><p style="opacity:0.6">Loading...</p></div>
        </div>`;
    },
    init() { loadData(); }
};
