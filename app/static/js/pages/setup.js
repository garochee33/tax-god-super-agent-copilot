import { api } from '../app.js';

let step = 0;
const STEPS = ['Welcome', 'Business Info', 'API Keys', 'First Client', 'Done'];

function renderStep() {
    const c = document.getElementById('setup-content');
    if (!c) return;
    const bodies = [
        `<h2>Welcome to Tax God ⚡</h2><p>Let's get your workspace set up in a few quick steps.</p>
         <button class="btn btn-primary" id="next-btn">Get Started →</button>`,

        `<h2>Business Info</h2>
         <form id="setup-biz" style="display:flex;flex-direction:column;gap:8px;max-width:360px;">
            <input type="text" name="name" class="form-control" placeholder="Business Name" required>
            <select name="business_type" class="form-control">
                <option value="llc">LLC</option><option value="corporation">Corporation</option>
                <option value="sole_prop">Sole Prop</option><option value="partnership">Partnership</option>
                <option value="nonprofit">Nonprofit</option><option value="trust">Trust</option>
            </select>
            <input type="text" name="ein" class="form-control" placeholder="EIN (optional)">
            <input type="text" name="currency" class="form-control" placeholder="USD" value="USD">
            <button type="submit" class="btn btn-primary">Next →</button>
         </form>`,

        `<h2>API Keys</h2>
         <p style="opacity:0.7;">Configure API keys in Settings later, or add your OpenAI key now:</p>
         <form id="setup-keys" style="display:flex;flex-direction:column;gap:8px;max-width:360px;">
            <input type="text" name="openai_key" class="form-control" placeholder="sk-... (optional)">
            <button type="submit" class="btn btn-primary">Next →</button>
         </form>`,

        `<h2>First Client</h2>
         <p style="opacity:0.7;">Add your first client or skip for now.</p>
         <form id="setup-client" style="display:flex;flex-direction:column;gap:8px;max-width:360px;">
            <input type="text" name="name" class="form-control" placeholder="Client Name">
            <input type="email" name="email" class="form-control" placeholder="Email (optional)">
            <div style="display:flex;gap:8px;">
                <button type="submit" class="btn btn-primary">Add & Finish</button>
                <button type="button" class="btn" id="skip-btn">Skip</button>
            </div>
         </form>`,

        `<h2>You're all set! 🎉</h2><p>Your workspace is ready.</p>
         <button class="btn btn-primary" id="go-dash">Go to Dashboard</button>`
    ];

    c.innerHTML = `<div class="card" style="padding:24px;max-width:500px;margin:40px auto;">
        <p style="opacity:0.5;font-size:0.8rem;">Step ${step + 1} of ${STEPS.length}: ${STEPS[step]}</p>
        ${bodies[step]}
    </div>`;
    bindStep();
}

function bindStep() {
    const next = document.getElementById('next-btn');
    if (next) next.onclick = () => { step++; renderStep(); };

    const bizForm = document.getElementById('setup-biz');
    if (bizForm) bizForm.onsubmit = async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(bizForm).entries());
        Object.keys(data).forEach(k => { if (!data[k]) delete data[k]; });
        try { await api.post('/api/v1/businesses', data); } catch(err) { alert(err.message); return; }
        step++; renderStep();
    };

    const keysForm = document.getElementById('setup-keys');
    if (keysForm) keysForm.onsubmit = async (e) => {
        e.preventDefault();
        const key = new FormData(keysForm).get('openai_key');
        if (key) { try { await api.post('/api/v1/settings', { openai_api_key: key }); } catch(e) {} }
        step++; renderStep();
    };

    const clientForm = document.getElementById('setup-client');
    if (clientForm) {
        clientForm.onsubmit = async (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(clientForm).entries());
            if (data.name) { try { await api.post('/api/v1/clients', data); } catch(e) {} }
            step = 4; renderStep();
        };
        const skip = document.getElementById('skip-btn');
        if (skip) skip.onclick = () => { step = 4; renderStep(); };
    }

    const dash = document.getElementById('go-dash');
    if (dash) dash.onclick = () => { window.location.hash = 'pantheon'; };
}

export default {
    render() {
        step = 0;
        return `<div class="page-container"><div id="setup-content"></div></div>`;
    },
    init() { renderStep(); }
};
