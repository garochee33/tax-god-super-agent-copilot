/* 
  TRIBUNAL.JS
  Audit Interface (Gabriel's Tribunal)
*/

import { api } from '../app.js';
import { escapeHtml, safeMarkdown } from '../utils.js';

export default {
    render() {
        return `
            <div class="tribunal-container grid grid-2">
                
                <!-- Input Form (The Plea) -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">The Plea (Tax Return Data)</span>
                        <div class="actions">
                            <button id="load-sample" class="btn btn-outline btn-sm">Load Sample</button>
                        </div>
                    </div>
                    
                    <form id="audit-form">
                        <div class="grid grid-2" style="gap: var(--spacing-md);">
                            <div class="input-group">
                                <label class="input-label">Client ID</label>
                                <input type="text" name="client_id" class="form-control" value="client-001">
                            </div>
                            <div class="input-group">
                                <label class="input-label">Tax Year</label>
                                <select name="tax_year" class="form-control">
                                    <option value="2024">2024</option>
                                    <option value="2023">2023</option>
                                </select>
                            </div>
                        </div>

                        <div class="greek-border-top" style="margin: var(--spacing-md) 0;"></div>

                        <div class="grid grid-2" style="gap: var(--spacing-md);">
                            <div class="input-group">
                                <label class="input-label">Filing Status</label>
                                <select name="filing_status" class="form-control">
                                    <option value="single">Single</option>
                                    <option value="married_joint">Married Filing Jointly</option>
                                    <option value="head_household">Head of Household</option>
                                </select>
                            </div>
                            <div class="input-group">
                                <label class="input-label">Wages (W-2)</label>
                                <input type="number" name="wages" class="form-control" placeholder="0">
                            </div>
                            <div class="input-group">
                                <label class="input-label">Schedule C Income</label>
                                <input type="number" name="schedule_c" class="form-control" placeholder="0">
                            </div>
                            <div class="input-group">
                                <label class="input-label">Total Itemized Deductions</label>
                                <input type="number" name="itemized" class="form-control" placeholder="0">
                            </div>
                        </div>

                        <div class="input-group" style="margin-top: var(--spacing-md);">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" name="home_office">
                                <span style="font-size: 14px;">Works from Home (Home Office)</span>
                            </label>
                        </div>

                        <div style="margin-top: var(--spacing-lg); text-align: right;">
                            <button type="submit" class="btn btn-primary">
                                <svg viewBox="0 0 24 24" style="width: 20px; height: 20px; fill: currentColor;"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>
                                Submit to Tribunal
                            </button>
                        </div>
                    </form>
                </div>

                <!-- Results (The Decree) -->
                <div class="card" id="results-panel" style="background: var(--color-parchment-dark); border: 2px solid var(--color-gold);">
                    <div class="card-header">
                        <span class="card-title">The Decree (Audit Report)</span>
                        <span class="badge badge-gold" id="score-badge">Score: --</span>
                    </div>
                    
                    <div id="results-content" style="text-align: center; padding: 40px; color: #666;">
                        <div style="font-size: 48px; margin-bottom: 20px; opacity: 0.5;">⚖️</div>
                        <p>Submit a plea to receive judgment.</p>
                    </div>
                </div>

            </div>
        `;
    },

    async init() {
        const form = document.getElementById('audit-form');
        const loadBtn = document.getElementById('load-sample');

        loadBtn.addEventListener('click', () => {
            form.querySelector('[name="wages"]').value = 85000;
            form.querySelector('[name="schedule_c"]').value = 45000;
            form.querySelector('[name="itemized"]').value = 18000;
            form.querySelector('[name="home_office"]').checked = true;
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);

            const clientId = (formData.get('client_id') || '').trim();
            if (!clientId) {
                this.renderError('Client ID is required.');
                return;
            }
            const wages = parseFloat(formData.get('wages') || 0);
            const scheduleC = parseFloat(formData.get('schedule_c') || 0);
            const itemized = parseFloat(formData.get('itemized') || 0);
            if (wages < 0 || scheduleC < 0 || itemized < 0) {
                this.renderError('Wages, Schedule C, and Itemized must be non-negative.');
                return;
            }

            const data = {
                client_id: clientId,
                tax_year: parseInt(formData.get('tax_year'), 10),
                return_data: {
                    filing_status: formData.get('filing_status'),
                    wages_reported: wages,
                    schedule_c_income: scheduleC,
                    total_itemized: itemized,
                    works_from_home: formData.get('home_office') === 'on',
                    deduction_type: itemized > 14600 ? 'itemized' : 'standard',
                    agi: wages + scheduleC
                }
            };

            this.renderLoading();

            try {
                const res = await api.post('/api/v1/audit/run', data);
                if (res) {
                    this.renderResults(res);
                } else {
                    this.renderError('Judgment could not be rendered.');
                }
            } catch (err) {
                this.renderError(err.message);
            }
        });
    },

    renderLoading() {
        const panel = document.getElementById('results-content');
        panel.innerHTML = '<div class="spinner" style="margin: 0 auto;"></div><p style="margin-top: 20px;">Agent Gabriel is weighing the evidence...</p>';
    },

    renderError(msg) {
        const panel = document.getElementById('results-content');
        panel.innerHTML = `<div style="color: var(--color-danger);">${escapeHtml(msg)}</div>`;
    },

    renderResults(report) {
        const panel = document.getElementById('results-content');
        const badge = document.getElementById('score-badge');
        
        badge.textContent = `Score: ${report.overall_score}/100`;
        badge.className = `badge ${report.overall_score > 80 ? 'badge-success' : 'badge-warning'}`;

        let savingsHtml = '';
        if (report.total_savings > 0) {
            savingsHtml = `
                <div class="savings-banner" style="background: var(--color-gold-light); color: var(--color-gold-dark); padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid var(--color-gold); font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 10px;">
                    <span style="font-size: 20px;">💰</span>
                    Potential Savings Identified: $${report.total_savings.toLocaleString()}
                </div>
            `;
        }

        let flagsHtml = '';
        report.all_flags.forEach(flag => {
            let icon = 'ℹ️';
            let colorClass = 'badge-primary';
            
            if (flag.severity === 'red') { icon = '🛡️'; colorClass = 'badge-danger'; }
            if (flag.severity === 'yellow') { icon = '⚠️'; colorClass = 'badge-warning'; }
            if (flag.severity === 'green') { icon = '✅'; colorClass = 'badge-success'; }

            flagsHtml += `
                <div class="flag-item" style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid ${flag.severity === 'red' ? 'var(--color-danger)' : (flag.severity === 'green' ? 'var(--color-success)' : 'var(--color-warning)')}; text-align: left;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="font-weight: 600; display: flex; align-items: center; gap: 8px;">${icon} ${escapeHtml(flag.title)}</span>
                        <span class="badge ${colorClass}">${escapeHtml(flag.category)}</span>
                    </div>
                    <div style="font-size: 13px; color: #444; margin-bottom: 8px;">${escapeHtml(flag.description)}</div>
                    <div style="font-size: 12px; font-style: italic; color: #666;">Recommendation: ${escapeHtml(flag.recommendation)}</div>
                </div>
            `;
        });

        panel.innerHTML = `
            ${savingsHtml}
            <div class="summary" style="text-align: left; margin-bottom: 20px; font-style: italic;">
                "${escapeHtml(report.summary)}"
            </div>
            <div class="flags-list">
                ${flagsHtml}
            </div>
        `;
    }
};
