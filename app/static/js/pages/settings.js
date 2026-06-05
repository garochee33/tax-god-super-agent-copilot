import { api } from '../app.js';

const TABS = ['general', 'integrations', 'apikeys', 'customization'];

export default {
    render() {
        return `
            <div class="page-description">Configure your application preferences, manage integrations, API keys, and display settings.</div>
            <div class="card" style="margin-bottom: var(--spacing-lg);">
                <div style="display: flex; gap: var(--spacing-md); border-bottom: 1px solid #eee; padding-bottom: var(--spacing-sm);">
                    <button class="btn btn-sm settings-tab active" data-tab="general">General</button>
                    <button class="btn btn-sm settings-tab" data-tab="integrations">Integrations</button>
                    <button class="btn btn-sm settings-tab" data-tab="apikeys">API Keys</button>
                    <button class="btn btn-sm settings-tab" data-tab="customization">Customization</button>
                </div>
            </div>
            <div id="settings-content"><div class="spinner"></div></div>
        `;
    },

    async init() {
        document.querySelectorAll('.settings-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.settings-tab').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.showTab(btn.dataset.tab);
            });
        });
        this.showTab('general');
    },

    async showTab(tab) {
        const container = document.getElementById('settings-content');
        container.innerHTML = '<div class="spinner"></div>';
        if (tab === 'general') await this.renderGeneral(container);
        else if (tab === 'integrations') await this.renderIntegrations(container);
        else if (tab === 'apikeys') await this.renderApiKeys(container);
        else if (tab === 'customization') await this.renderCustomization(container);
    },

    async renderGeneral(container) {
        try {
            const s = await api.get('/api/v1/settings');
            container.innerHTML = `
                <div class="card">
                    <div class="card-header"><span class="card-title">General Settings</span></div>
                    <form id="general-form">
                        <div style="margin-bottom: var(--spacing-md); display: flex; align-items: center; gap: 12px;">
                            <label style="font-weight: 600; min-width: 140px;">Theme</label>
                            <select id="set-theme" class="form-control" style="max-width: 200px;">
                                <option value="light" ${s.theme === 'light' ? 'selected' : ''}>Light</option>
                                <option value="dark" ${s.theme === 'dark' ? 'selected' : ''}>Dark</option>
                            </select>
                        </div>
                        <div style="margin-bottom: var(--spacing-md); display: flex; align-items: center; gap: 12px;">
                            <label style="font-weight: 600; min-width: 140px;">Default AI Model</label>
                            <select id="set-model" class="form-control" style="max-width: 200px;">
                                <option value="gpt-4o" ${s.default_model === 'gpt-4o' ? 'selected' : ''}>GPT-4o</option>
                                <option value="gpt-4o-mini" ${s.default_model === 'gpt-4o-mini' ? 'selected' : ''}>GPT-4o Mini</option>
                                <option value="claude-sonnet" ${s.default_model === 'claude-sonnet' ? 'selected' : ''}>Claude Sonnet</option>
                                <option value="claude-haiku" ${s.default_model === 'claude-haiku' ? 'selected' : ''}>Claude Haiku</option>
                            </select>
                        </div>
                        <div style="margin-bottom: var(--spacing-md); display: flex; align-items: center; gap: 12px;">
                            <label style="font-weight: 600; min-width: 140px;">Notifications</label>
                            <input type="checkbox" id="set-notif" ${s.notifications_enabled ? 'checked' : ''}>
                            <span style="font-size: 13px;">Enable notifications</span>
                        </div>
                        <button type="submit" class="btn btn-primary">Save</button>
                        <span id="general-msg" style="margin-left: 12px; font-size: 13px;"></span>
                    </form>
                </div>
            `;
            document.getElementById('general-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const msg = document.getElementById('general-msg');
                try {
                    await api.request('PATCH', '/api/v1/settings', {
                        theme: document.getElementById('set-theme').value,
                        default_model: document.getElementById('set-model').value,
                        notifications_enabled: document.getElementById('set-notif').checked
                    });
                    msg.style.color = 'green';
                    msg.textContent = 'Saved!';
                } catch (err) {
                    msg.style.color = 'red';
                    msg.textContent = err.message;
                }
            });
        } catch (err) {
            container.innerHTML = `<p style="color: red;">${err.message}</p>`;
        }
    },

    async renderIntegrations(container) {
        try {
            const data = await api.get('/api/v1/settings/integrations');
            const integrations = data.integrations || data;
            container.innerHTML = `
                <div class="card">
                    <div class="card-header"><span class="card-title">Connected Services</span></div>
                    <div id="integrations-list">
                        ${(Array.isArray(integrations) ? integrations : []).map(i => `
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eee;">
                                <div><strong>${i.name || i.provider}</strong><span style="margin-left: 8px; font-size: 12px; color: ${i.connected ? 'green' : '#999'};">${i.connected ? '● Connected' : '○ Not connected'}</span></div>
                                <button class="btn btn-sm ${i.connected ? 'btn-outline' : 'btn-primary'}" data-provider="${i.provider || i.name}">${i.connected ? 'Disconnect' : 'Connect'}</button>
                            </div>
                        `).join('')}
                        ${(!integrations || integrations.length === 0) ? '<p style="color: #999;">No integrations available.</p>' : ''}
                    </div>
                </div>
            `;
        } catch (err) {
            container.innerHTML = `<p style="color: red;">${err.message}</p>`;
        }
    },

    async renderApiKeys(container) {
        let savedKeys = [];
        try {
            const res = await api.get('/api/v1/settings/secrets');
            savedKeys = res.key_names || res.keys || res || [];
        } catch (_) {}

        const hasOpenAI = savedKeys.includes('OPENAI_API_KEY');
        const hasAnthropic = savedKeys.includes('ANTHROPIC_API_KEY');

        container.innerHTML = `
            <div class="card">
                <div class="card-header"><span class="card-title">API Keys</span></div>
                <p style="font-size: 13px; color: #666; margin-bottom: var(--spacing-md);">Keys are encrypted at rest. Values are never displayed after saving.</p>
                <form id="apikeys-form">
                    <div style="margin-bottom: var(--spacing-md);">
                        <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">OpenAI API Key ${hasOpenAI ? '<span style="color: green;">✓ saved</span>' : ''}</label>
                        <input type="password" id="key-openai" class="form-control" placeholder="${hasOpenAI ? '••••••••••••' : 'sk-...'}">
                    </div>
                    <div style="margin-bottom: var(--spacing-md);">
                        <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">Anthropic API Key ${hasAnthropic ? '<span style="color: green;">✓ saved</span>' : ''}</label>
                        <input type="password" id="key-anthropic" class="form-control" placeholder="${hasAnthropic ? '••••••••••••' : 'sk-ant-...'}">
                    </div>
                    <button type="submit" class="btn btn-primary">Save Keys</button>
                    <span id="keys-msg" style="margin-left: 12px; font-size: 13px;"></span>
                </form>
            </div>
        `;
        document.getElementById('apikeys-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const msg = document.getElementById('keys-msg');
            const secrets = {};
            const openai = document.getElementById('key-openai').value.trim();
            const anthropic = document.getElementById('key-anthropic').value.trim();
            if (openai) secrets['OPENAI_API_KEY'] = openai;
            if (anthropic) secrets['ANTHROPIC_API_KEY'] = anthropic;
            if (!Object.keys(secrets).length) { msg.style.color = 'red'; msg.textContent = 'Enter at least one key.'; return; }
            try {
                await api.post('/api/v1/settings/secrets', { secrets });
                msg.style.color = 'green';
                msg.textContent = 'Keys saved!';
                document.getElementById('key-openai').value = '';
                document.getElementById('key-anthropic').value = '';
            } catch (err) {
                msg.style.color = 'red';
                msg.textContent = err.message;
            }
        });
    },

    async renderCustomization(container) {
        try {
            const s = await api.get('/api/v1/settings');
            container.innerHTML = `
                <div class="card">
                    <div class="card-header"><span class="card-title">Customization</span></div>
                    <form id="custom-form">
                        <div style="margin-bottom: var(--spacing-md); display: flex; align-items: center; gap: 12px;">
                            <label style="font-weight: 600; min-width: 140px;">Timezone</label>
                            <select id="set-tz" class="form-control" style="max-width: 250px;">
                                ${['America/New_York','America/Chicago','America/Denver','America/Los_Angeles','America/Anchorage','Pacific/Honolulu','UTC','Europe/London','Europe/Paris','Asia/Tokyo'].map(tz => `<option value="${tz}" ${s.timezone === tz ? 'selected' : ''}>${tz}</option>`).join('')}
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary">Save</button>
                        <span id="custom-msg" style="margin-left: 12px; font-size: 13px;"></span>
                    </form>
                </div>
            `;
            document.getElementById('custom-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const msg = document.getElementById('custom-msg');
                try {
                    await api.request('PATCH', '/api/v1/settings', { timezone: document.getElementById('set-tz').value });
                    msg.style.color = 'green';
                    msg.textContent = 'Saved!';
                } catch (err) {
                    msg.style.color = 'red';
                    msg.textContent = err.message;
                }
            });
        } catch (err) {
            container.innerHTML = `<p style="color: red;">${err.message}</p>`;
        }
    }
};
