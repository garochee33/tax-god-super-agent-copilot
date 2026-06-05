/**
 * Tax Estimates Page - Quarterly estimates, deadlines & scenario calculator
 */
window.TaxEstimatesPage = {
  async render(container) {
    container.innerHTML = `<div class="spinner"></div>`;
    const content = `
      <div class="page-header"><h1>Tax Estimates</h1></div>
      <div class="grid grid-2">
        <div class="card" id="quarterly-card">
          <h3>Quarterly Estimate</h3>
          <div id="quarterly-data">Loading...</div>
        </div>
        <div class="card" id="deadline-card">
          <h3>Next Deadline</h3>
          <div id="deadline-data">Loading...</div>
        </div>
      </div>
      <div class="card" style="margin-top:1rem">
        <h3>Scenario Calculator</h3>
        <form id="scenario-form" class="form-grid">
          <label>Income<input type="number" id="sc-income" step="0.01" required></label>
          <label>Expenses<input type="number" id="sc-expenses" step="0.01" required></label>
          <label>Filing Status
            <select id="sc-status">
              <option value="single">Single</option>
              <option value="married_filing_jointly">Married Filing Jointly</option>
              <option value="married_filing_separately">Married Filing Separately</option>
              <option value="head_of_household">Head of Household</option>
            </select>
          </label>
          <button type="submit" class="btn btn-primary">Calculate</button>
        </form>
        <div id="scenario-result"></div>
      </div>`;
    container.innerHTML = content;
    this.loadQuarterly();
    this.loadDeadlines();
    document.getElementById('scenario-form').addEventListener('submit', e => { e.preventDefault(); this.runScenario(); });
  },

  async loadQuarterly() {
    try {
      const r = await fetch('/api/v1/estimates/quarterly', {headers: window.authHeaders()});
      const d = await r.json();
      document.getElementById('quarterly-data').innerHTML = `
        <p><strong>Estimated Tax:</strong> $${d.estimated_tax.toLocaleString()}</p>
        <p><strong>Quarterly Payment:</strong> $${d.quarterly_payment.toLocaleString()}</p>
        <p><strong>Effective Rate:</strong> ${d.effective_rate}%</p>`;
    } catch { document.getElementById('quarterly-data').textContent = 'Error loading data'; }
  },

  async loadDeadlines() {
    try {
      const r = await fetch('/api/v1/estimates/deadlines');
      const d = await r.json();
      const next = d.deadlines.find(dl => !dl.passed);
      document.getElementById('deadline-data').innerHTML = next
        ? `<p class="big-date">${next.date}</p>`
        : '<p>All deadlines passed for this year</p>';
    } catch { document.getElementById('deadline-data').textContent = 'Error'; }
  },

  async runScenario() {
    const body = {
      income: parseFloat(document.getElementById('sc-income').value),
      expenses: parseFloat(document.getElementById('sc-expenses').value),
      filing_status: document.getElementById('sc-status').value,
    };
    const r = await fetch('/api/v1/estimates/scenario', {method:'POST', headers:{'Content-Type':'application/json', ...window.authHeaders()}, body: JSON.stringify(body)});
    const d = await r.json();
    document.getElementById('scenario-result').innerHTML = `
      <p><strong>Estimated Tax:</strong> $${d.estimated_tax.toLocaleString()}</p>
      <p><strong>Quarterly Payment:</strong> $${d.quarterly_payment.toLocaleString()}</p>
      <p><strong>Effective Rate:</strong> ${d.effective_rate}%</p>`;
  }
};
