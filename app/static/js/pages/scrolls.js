/* 
  SCROLLS.JS
  Document Generator Interface
*/

import { api } from '../app.js';

export default {
    render() {
        return `
            <div class="scrolls-container grid grid-2">
                
                <!-- Generator Forms -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Scribe's Desk</span>
                        <div class="tabs" style="display: flex; gap: 10px;">
                            <button class="btn btn-sm btn-primary" id="tab-memo">Tax Memo</button>
                            <button class="btn btn-sm btn-outline" id="tab-irs">IRS Response</button>
                        </div>
                    </div>

                    <!-- Memo Form -->
                    <form id="memo-form">
                        <div class="input-group">
                            <label class="input-label">Subject</label>
                            <input type="text" name="subject" class="form-control" placeholder="e.g. Taxability of Crypto Staking Rewards">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Client Name</label>
                            <input type="text" name="client_name" class="form-control" placeholder="Client Name">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Facts & Context</label>
                            <textarea name="facts" class="form-control" rows="6" placeholder="Describe the client's situation..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Generate Memo</button>
                    </form>

                    <!-- IRS Response Form (Hidden initially) -->
                    <form id="irs-form" style="display: none;">
                        <div class="grid grid-2" style="gap: var(--spacing-md);">
                            <div class="input-group">
                                <label class="input-label">Notice Type</label>
                                <input type="text" name="notice_type" class="form-control" placeholder="e.g. CP2000">
                            </div>
                            <div class="input-group">
                                <label class="input-label">Case Number</label>
                                <input type="text" name="case_number" class="form-control" placeholder="e.g. 123-456-789">
                            </div>
                        </div>
                        <div class="input-group">
                            <label class="input-label">Issues Raised</label>
                            <textarea name="issues" class="form-control" rows="3" placeholder="List the issues (comma separated)..."></textarea>
                        </div>
                        <div class="input-group">
                            <label class="input-label">Supporting Facts</label>
                            <textarea name="supporting_facts" class="form-control" rows="4" placeholder="Why is the IRS wrong?"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Generate Response</button>
                    </form>
                </div>

                <!-- Document Preview (The Scroll) -->
                <div class="card" style="background: var(--color-parchment); border: 2px solid var(--color-gold);">
                    <div class="card-header">
                        <span class="card-title">The Scroll</span>
                        <button class="btn btn-sm btn-outline" onclick="navigator.clipboard.writeText(document.getElementById('doc-content').innerText)">Copy</button>
                    </div>
                    
                    <div id="doc-preview" class="scroll-content" style="padding: 20px; font-family: 'Georgia', serif; line-height: 1.8; color: #333; height: 600px; overflow-y: auto;">
                        <div class="empty-state" style="text-align: center; color: #999; margin-top: 100px;">
                            <div style="font-size: 40px; margin-bottom: 10px;">✍️</div>
                            <p>Instruct the scribe to begin.</p>
                        </div>
                    </div>
                </div>

            </div>
        `;
    },

    async init() {
        const memoForm = document.getElementById('memo-form');
        const irsForm = document.getElementById('irs-form');
        const tabMemo = document.getElementById('tab-memo');
        const tabIrs = document.getElementById('tab-irs');
        const preview = document.getElementById('doc-preview');

        // Tab Switching
        tabMemo.addEventListener('click', () => {
            memoForm.style.display = 'block';
            irsForm.style.display = 'none';
            tabMemo.classList.add('btn-primary');
            tabMemo.classList.remove('btn-outline');
            tabIrs.classList.remove('btn-primary');
            tabIrs.classList.add('btn-outline');
        });

        tabIrs.addEventListener('click', () => {
            memoForm.style.display = 'none';
            irsForm.style.display = 'block';
            tabIrs.classList.add('btn-primary');
            tabIrs.classList.remove('btn-outline');
            tabMemo.classList.remove('btn-primary');
            tabMemo.classList.add('btn-outline');
        });

        // Memo Generation
        memoForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(memoForm);
            
            this.renderLoading();

            try {
                const res = await api.post('/api/v1/audit/memo', {
                    subject: formData.get('subject'),
                    client_name: formData.get('client_name'),
                    facts: formData.get('facts'),
                    tax_year: 2024
                });

                if (res) {
                    this.renderDocument(res.content);
                } else {
                    this.renderError('The scribe broke their quill (Error).');
                }
            } catch (err) {
                this.renderError(err.message);
            }
        });

        // IRS Response Generation
        irsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(irsForm);
            
            this.renderLoading();

            try {
                const res = await api.post('/api/v1/audit/irs-response', {
                    notice_type: formData.get('notice_type'),
                    case_number: formData.get('case_number'),
                    notice_date: new Date().toISOString().split('T')[0], // Today
                    issues: formData.get('issues').split(','),
                    taxpayer_name: "Client Name", // Placeholder
                    tax_years: "2023",
                    supporting_facts: formData.get('supporting_facts')
                });

                if (res) {
                    this.renderDocument(res.content);
                } else {
                    this.renderError('The scribe broke their quill (Error).');
                }
            } catch (err) {
                this.renderError(err.message);
            }
        });
    },

    renderLoading() {
        const preview = document.getElementById('doc-preview');
        preview.innerHTML = '<div class="spinner" style="margin: 100px auto;"></div><p style="text-align: center;">Drafting the sacred scroll...</p>';
    },

    renderError(msg) {
        const preview = document.getElementById('doc-preview');
        preview.innerHTML = `<div style="color: var(--color-danger); text-align: center; margin-top: 100px;">${msg}</div>`;
    },

    renderDocument(content) {
        const preview = document.getElementById('doc-preview');
        // Simple markdown-ish to HTML
        const html = content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        preview.innerHTML = `<div id="doc-content">${html}</div>`;
    }
};
