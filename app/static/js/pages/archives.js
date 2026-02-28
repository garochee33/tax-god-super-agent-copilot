/* 
  ARCHIVES.JS
  Citation Search Interface
*/

import { api } from '../app.js';

export default {
    render() {
        return `
            <div class="archives-container">
                <div class="card" style="margin-bottom: var(--spacing-lg);">
                    <div class="card-header">
                        <span class="card-title">Search the Sacred Texts</span>
                    </div>
                    <form id="search-form" style="display: flex; gap: var(--spacing-md);">
                        <input type="text" id="search-input" class="form-control" placeholder="Search for tax law, IRC sections, or IRS publications..." autocomplete="off">
                        <button type="submit" class="btn btn-primary">
                            <svg viewBox="0 0 24 24" style="width: 20px; height: 20px; fill: currentColor;"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                            Search
                        </button>
                    </form>
                </div>

                <div id="search-results" class="grid grid-2">
                    <!-- Results will appear here -->
                    <div class="empty-state" style="grid-column: span 2; text-align: center; color: #999; margin-top: 40px;">
                        <div style="font-size: 40px; margin-bottom: 10px;">📚</div>
                        <p>Enter a query to search the archives.</p>
                    </div>
                </div>
            </div>
        `;
    },

    async init() {
        const form = document.getElementById('search-form');
        const input = document.getElementById('search-input');
        const resultsContainer = document.getElementById('search-results');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = input.value.trim();
            if (!query) return;
            if (query.length > 500) {
                resultsContainer.innerHTML = '<div class="error" style="grid-column: span 2; text-align: center;">Query too long (max 500 characters).</div>';
                return;
            }

            resultsContainer.innerHTML = '<div class="spinner" style="grid-column: span 2; margin: 0 auto;"></div>';

            try {
                const res = await api.post('/api/v1/chat/citations/search', {
                    query: query,
                    max_results: 10
                });

                if (res && res.citations) {
                    this.renderResults(res.citations);
                } else {
                    resultsContainer.innerHTML = '<div class="error" style="grid-column: span 2; text-align: center;">No scrolls found.</div>';
                }
            } catch (err) {
                console.error(err);
                const msg = err && err.message ? err.message : 'The archives are closed (Error).';
                resultsContainer.innerHTML = `<div class="error" style="grid-column: span 2; text-align: center;">${msg} <button class="btn btn-sm btn-outline" style="margin-top: 8px;">Retry</button></div>`;
                resultsContainer.querySelector('button')?.addEventListener('click', () => { input.focus(); });
            }
        });
    },

    renderResults(citations) {
        const container = document.getElementById('search-results');
        container.innerHTML = '';

        if (citations.length === 0) {
            container.innerHTML = '<div class="empty-state" style="grid-column: span 2; text-align: center;">No matching scrolls found.</div>';
            return;
        }

        citations.forEach(cit => {
            const card = document.createElement('div');
            card.className = 'card citation-result';
            card.innerHTML = `
                <div class="card-header">
                    <span class="citation-ref" style="font-size: 14px; color: var(--color-primary-dark); font-weight: bold;">${cit.reference}</span>
                    <span class="badge badge-gold">${cit.type}</span>
                </div>
                <div class="citation-title" style="font-weight: 600; margin-bottom: 8px;">${cit.title}</div>
                <div class="citation-summary" style="font-size: 13px; color: #555;">${cit.summary}</div>
                <div class="citation-meta" style="margin-top: 10px; font-size: 11px; color: #999;">Year: ${cit.year}</div>
            `;
            container.appendChild(card);
        });
    }
};
