/* 
  SCROLLS.JS
  Document Generator Interface
*/

import { api } from '../app.js';
import { escapeHtml, safeMarkdown } from '../utils.js';

export default {
    render() {
        return `
            <div class="page-description">Generate professional tax memos and IRS response letters using AI. Fill in the details and the system drafts a complete document with proper legal structure and citations.</div>
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
                            <label class="input-label">Subject <span class="required">*</span></label>
                            <input type="text" name="subject" class="form-control" placeholder="e.g. Taxability of Crypto Staking Rewards" required maxlength="500">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Client Name <span class="required">*</span></label>
                            <input type="text" name="client_name" class="form-control" placeholder="Client or matter name" required maxlength="200">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Tax Year</label>
                            <select name="tax_year" class="form-control">
                                <option value="2025">2025</option>
                                <option value="2024" selected>2024</option>
                                <option value="2023">2023</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label class="input-label">Facts & Context <span class="required">*</span></label>
                            <textarea name="facts" class="form-control" rows="6" placeholder="Describe the client's situation..." required maxlength="10000"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Generate Memo</button>
                    </form>

                    <!-- IRS Response Form (Hidden initially) -->
                    <form id="irs-form" style="display: none;">
                        <div class="grid grid-2" style="gap: var(--spacing-md);">
                            <div class="input-group">
                                <label class="input-label">Taxpayer Name <span class="required">*</span></label>
                                <input type="text" name="taxpayer_name" class="form-control" placeholder="Full legal name" required maxlength="200">
                            </div>
                            <div class="input-group">
                                <label class="input-label">Tax Year(s) <span class="required">*</span></label>
                                <input type="text" name="tax_years" class="form-control" placeholder="e.g. 2023 or 2022, 2023" required maxlength="50">
                            </div>
                        </div>
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
                            <label class="input-label">Issues Raised <span class="required">*</span></label>
                            <textarea name="issues" class="form-control" rows="3" placeholder="List the issues (comma separated)..." required maxlength="2000"></textarea>
                        </div>
                        <div class="input-group">
                            <label class="input-label">Supporting Facts <span class="required">*</span></label>
                            <textarea name="supporting_facts" class="form-control" rows="4" placeholder="Why is the IRS wrong?" required maxlength="5000"></textarea>
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
                            <p style="font-size: 12px; margin-top: 8px;">Fill out the form on the left and submit — the AI will generate a formatted document here.</p>
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

            const subject = (formData.get('subject') || '').trim();
            const clientName = (formData.get('client_name') || '').trim();
            const facts = (formData.get('facts') || '').trim();
            if (!subject || !clientName || !facts) {
                this.renderError('Subject, Client Name, and Facts are required.');
                return;
            }
            try {
                const res = await api.post('/api/v1/audit/memo', {
                    subject,
                    client_name: clientName,
                    facts,
                    tax_year: parseInt(formData.get('tax_year') || '2024', 10)
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

            const taxpayerName = (formData.get('taxpayer_name') || '').trim();
            const taxYears = (formData.get('tax_years') || '').trim();
            const issuesRaw = (formData.get('issues') || '').trim();
            const supportingFacts = (formData.get('supporting_facts') || '').trim();
            if (!taxpayerName || !taxYears || !issuesRaw || !supportingFacts) {
                this.renderError('Taxpayer Name, Tax Year(s), Issues Raised, and Supporting Facts are required.');
                return;
            }
            try {
                const res = await api.post('/api/v1/audit/irs-response', {
                    notice_type: formData.get('notice_type') || '',
                    case_number: formData.get('case_number') || '',
                    notice_date: new Date().toISOString().split('T')[0],
                    issues: issuesRaw.split(',').map((s) => s.trim()).filter(Boolean),
                    taxpayer_name: taxpayerName,
                    tax_years: taxYears,
                    supporting_facts: supportingFacts
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
        preview.innerHTML = `<div style="color: var(--color-danger); text-align: center; margin-top: 100px;">${escapeHtml(msg)}</div>`;
    },

    renderDocument(content) {
        const preview = document.getElementById('doc-preview');
        preview.innerHTML = `<div id="doc-content">${safeMarkdown(content)}</div>`;
    }
};
