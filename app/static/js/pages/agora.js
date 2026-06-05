/**
 * Agora — Client Management Interface
 */

import { session } from '../app.js';

const API = '/api/v1/clients';

function headers() {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${session.getAccessToken()}` };
}

let currentPage = 1;

async function fetchClients(page = 1, search = '') {
  const params = new URLSearchParams({ page, per_page: 20 });
  if (search) params.set('search', search);
  const res = await fetch(`${API}?${params}`, { headers: headers() });
  if (!res.ok) throw new Error('Failed to load clients');
  return res.json();
}

async function createClient(data) {
  const res = await fetch(API, { method: 'POST', headers: headers(), body: JSON.stringify(data) });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Create failed'); }
  return res.json();
}

async function updateClient(id, data) {
  const res = await fetch(`${API}/${id}`, { method: 'PATCH', headers: headers(), body: JSON.stringify(data) });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Update failed'); }
  return res.json();
}

async function deleteClient(id) {
  const res = await fetch(`${API}/${id}`, { method: 'DELETE', headers: headers() });
  if (!res.ok) throw new Error('Delete failed');
}

function statusBadge(status) {
  return `<span class="status-badge status-${status || 'inactive'}">${status}</span>`;
}

function renderList(data) {
  const { clients, total, page, per_page } = data;
  const totalPages = Math.ceil(total / per_page);
  if (!clients.length) return '<p style="opacity:0.6">No clients yet. Use the form above to add your first client.</p>';
  let html = `<table class="data-table"><thead><tr><th>Name</th><th>Email</th><th>Company</th><th>Filing</th><th>Status</th><th>Actions</th></tr></thead><tbody>`;
  for (const c of clients) {
    html += `<tr data-id="${c.id}">
      <td>${c.name}</td><td>${c.email || '—'}</td><td>${c.company || '—'}</td>
      <td>${c.filing_type || '—'}</td><td>${statusBadge(c.status)}</td>
      <td><button class="btn-sm btn-edit" data-id="${c.id}">Edit</button> <button class="btn-sm btn-danger btn-delete" data-id="${c.id}">×</button></td>
    </tr>`;
  }
  html += '</tbody></table>';
  if (totalPages > 1) {
    html += `<div class="pagination">Page ${page}/${totalPages} `;
    if (page > 1) html += `<button class="btn-sm btn-prev">← Prev</button> `;
    if (page < totalPages) html += `<button class="btn-sm btn-next">Next →</button>`;
    html += '</div>';
  }
  return html;
}

function formHtml(client = null) {
  const c = client || {};
  return `<form id="client-form" class="agora-form">
    <input type="hidden" name="id" value="${c.id || ''}">
    <div class="form-row">
      <div class="form-group"><label>Name *</label><input name="name" class="form-control" value="${c.name || ''}" required maxlength="255"></div>
      <div class="form-group"><label>Email</label><input name="email" type="email" class="form-control" value="${c.email || ''}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Phone</label><input name="phone" class="form-control" value="${c.phone || ''}" maxlength="50"></div>
      <div class="form-group"><label>Company</label><input name="company" class="form-control" value="${c.company || ''}" maxlength="255"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Tax ID</label><input name="tax_id" class="form-control" value="${c.tax_id || ''}" maxlength="50"></div>
      <div class="form-group"><label>Filing Type</label>
        <select name="filing_type" class="form-control">
          <option value="">—</option>
          <option value="individual" ${c.filing_type === 'individual' ? 'selected' : ''}>Individual</option>
          <option value="business" ${c.filing_type === 'business' ? 'selected' : ''}>Business</option>
          <option value="trust" ${c.filing_type === 'trust' ? 'selected' : ''}>Trust</option>
          <option value="nonprofit" ${c.filing_type === 'nonprofit' ? 'selected' : ''}>Nonprofit</option>
        </select>
      </div>
      <div class="form-group"><label>Status</label>
        <select name="status" class="form-control">
          <option value="active" ${c.status === 'active' ? 'selected' : ''}>Active</option>
          <option value="prospect" ${c.status === 'prospect' ? 'selected' : ''}>Prospect</option>
          <option value="inactive" ${c.status === 'inactive' ? 'selected' : ''}>Inactive</option>
        </select>
      </div>
    </div>
    <div class="form-group"><label>Notes</label><textarea name="notes" class="form-control" rows="3" maxlength="5000">${c.notes || ''}</textarea></div>
    <div class="form-actions">
      <button type="submit" class="btn btn-primary">${client ? 'Update' : 'Add Client'}</button>
      ${client ? '<button type="button" class="btn btn-secondary btn-cancel">Cancel</button>' : ''}
    </div>
  </form>`;
}

function getContainer() {
  return document.querySelector('.agora-page');
}

async function refresh() {
  const container = getContainer();
  if (!container) return;
  const search = container.querySelector('#agora-search')?.value || '';
  try {
    const data = await fetchClients(currentPage, search);
    container.querySelector('#client-list').innerHTML = renderList(data);
    bindListEvents();
  } catch (err) {
    container.querySelector('#client-list').innerHTML = `<p class="error">${err.message}</p>`;
  }
}

function bindListEvents() {
  const container = getContainer();
  if (!container) return;
  container.querySelectorAll('.btn-delete').forEach(btn => {
    btn.onclick = async () => {
      if (!confirm('Delete this client?')) return;
      await deleteClient(btn.dataset.id);
      await refresh();
    };
  });
  container.querySelectorAll('.btn-edit').forEach(btn => {
    btn.onclick = async () => {
      const res = await fetch(`${API}/${btn.dataset.id}`, { headers: headers() });
      const client = await res.json();
      container.querySelector('#client-form-area').innerHTML = formHtml(client);
      bindFormEvents();
    };
  });
  const prev = container.querySelector('.btn-prev');
  const next = container.querySelector('.btn-next');
  if (prev) prev.onclick = () => { currentPage--; refresh(); };
  if (next) next.onclick = () => { currentPage++; refresh(); };
}

function bindFormEvents() {
  const container = getContainer();
  if (!container) return;
  const form = container.querySelector('#client-form');
  if (!form) return;
  form.onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const data = Object.fromEntries(fd.entries());
    const id = data.id; delete data.id;
    Object.keys(data).forEach(k => { if (!data[k]) delete data[k]; });
    try {
      if (id) await updateClient(id, data);
      else await createClient(data);
      container.querySelector('#client-form-area').innerHTML = formHtml();
      bindFormEvents();
      currentPage = 1;
      await refresh();
    } catch (err) { alert(err.message); }
  };
  const cancel = form.querySelector('.btn-cancel');
  if (cancel) cancel.onclick = () => { container.querySelector('#client-form-area').innerHTML = formHtml(); bindFormEvents(); };
}

export default {
  render() {
    currentPage = 1;
    return `<div class="page-container agora-page">
      <div class="page-description">Manage your client roster — add, edit, search, and organize clients by filing type and status. Client data is used across the platform for personalized queries and audits.</div>
      <h1>⚖️ Agora — Client Management</h1>
      <div class="agora-controls">
        <input type="text" id="agora-search" class="form-control" placeholder="Search clients by name, email, or company..." style="max-width:300px;">
      </div>
      <div id="client-form-area">${formHtml()}</div>
      <div id="client-list"><p style="opacity:0.6">Loading...</p></div>
    </div>`;
  },

  init() {
    const container = getContainer();
    if (!container) return;
    const searchInput = container.querySelector('#agora-search');
    let debounce;
    searchInput.oninput = () => { clearTimeout(debounce); debounce = setTimeout(() => { currentPage = 1; refresh(); }, 300); };
    bindFormEvents();
    refresh();
  }
};
