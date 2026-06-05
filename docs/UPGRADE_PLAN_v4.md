# Tax God v4.0 — Platform Upgrade Plan

## Research Summary

Based on analysis of **Stripe**, **QuickBooks Online**, **FreshBooks**, and **Wave**, here are the key features that make a financial platform feel complete:

### What Top Platforms Have That We Need

| Feature | Stripe | QuickBooks | FreshBooks | Tax God Status |
|---------|--------|------------|------------|---------------|
| Multi-business/sandbox | ✅ Test/Live modes | ✅ Multi-company | ❌ | 🔴 Missing |
| Guided setup wizard | ✅ | ✅ | ✅ | 🔴 Missing |
| Dashboard with KPIs | ✅ Revenue, MRR | ✅ P&L snapshot | ✅ | 🟡 Partial (Pantheon) |
| Expense tracking | ❌ | ✅ | ✅ | 🔴 Missing |
| Receipt capture | ❌ | ✅ | ✅ | 🔴 Missing |
| Recurring invoices | ✅ | ✅ | ✅ | 🔴 Missing |
| Payment acceptance | ✅ | ✅ | ✅ | 🔴 Missing (link only) |
| Bank reconciliation | ❌ | ✅ | ❌ | 🔴 Missing |
| Chart of accounts | ❌ | ✅ | ❌ | 🔴 Missing |
| Financial reports (P&L, Balance Sheet, Cash Flow) | ✅ | ✅ | ✅ | 🟡 Partial (spreadsheet) |
| Tax categories/deductions | ❌ | ✅ | ✅ | 🟡 (AI handles this) |
| Time tracking | ❌ | ❌ | ✅ | 🔴 Missing |
| Contacts/vendors | ❌ | ✅ | ✅ | 🟡 (clients only) |
| Icon-based nav with badges | ✅ | ✅ | ✅ | 🔴 Missing |
| Mobile-friendly | ✅ | ✅ | ✅ | 🟡 (responsive CSS needed) |

---

## Phase 1: Navigation & UX Overhaul (Priority: HIGH)

### 1.1 Icon-Based Sidebar Navigation
Replace text nav with icon+label tabs like Stripe/QuickBooks:

```
🏠 Dashboard      — KPI cards, quick actions
💬 AI Assistant   — Oracle (tax chat)
👥 Clients        — Agora
💰 Finance        — Accounts, Invoices, Expenses
📊 Reports        — P&L, Balance Sheet, Cash Flow, Tax Summary
📁 Projects       — Active projects + time tracking
📝 Documents      — Scrolls + Archives combined
🛡️ Audit          — Tribunal (Gabriel)
⚙️ Settings       — Profile, integrations, API keys
```

### 1.2 Multi-Business Sandbox
- Business switcher dropdown in sidebar header
- Each "business" = isolated data context (accounts, invoices, clients, projects)
- Default business created on signup
- "Add Business" flow: name, type (LLC/Corp/Sole Prop), EIN, fiscal year

### 1.3 Guided Setup Wizard (First-Run)
When user has no data, show step-by-step:
1. Welcome — set timezone, currency, fiscal year
2. Business Info — name, type, EIN/tax ID, address
3. Add API Keys — OpenAI/Anthropic for AI features
4. Connect Bank — link account (manual for now)
5. Create First Client — or skip
6. Done — redirect to dashboard

---

## Phase 2: Financial Core (Priority: HIGH)

### 2.1 Expenses & Transactions
- Expense model: date, vendor, amount, category, receipt_url, tax_deductible, account_id
- Categories: Office, Travel, Meals, Auto, Insurance, Professional Services, Utilities, etc.
- Auto-categorization via AI
- Monthly/yearly expense summaries

### 2.2 Recurring Invoices
- Frequency: weekly, monthly, quarterly, annually
- Auto-send on schedule
- Late payment reminders

### 2.3 Financial Reports (Auto-Generated)
- **Profit & Loss** — Revenue minus expenses by period
- **Balance Sheet** — Assets, liabilities, equity
- **Cash Flow Statement** — Operating, investing, financing
- **Tax Summary** — Deductible expenses grouped by IRS category
- Export to PDF/CSV

### 2.4 Chart of Accounts
- Standard chart (Assets, Liabilities, Equity, Revenue, Expenses)
- Custom sub-accounts
- Each transaction tagged to an account

---

## Phase 3: Business Intelligence (Priority: MEDIUM)

### 3.1 Dashboard KPIs
- Revenue this month (vs last month)
- Outstanding invoices (count + total)
- Expenses this month
- Net profit
- Upcoming due dates
- AI insights ("You spent 30% more on travel this quarter")

### 3.2 Contacts & Vendors
- Extend clients to support vendors/suppliers
- Track payments to vendors
- 1099 prep for contractors

### 3.3 Time Tracking
- Per-project hour logging
- Billable vs non-billable
- Auto-generate invoices from time entries

---

## Phase 4: Integrations & Payment (Priority: MEDIUM)

### 4.1 Stripe Connect
- Accept payments on invoices via Stripe
- Auto-reconcile payments
- Track Stripe balance

### 4.2 Bank Import (CSV/OFX)
- Upload bank statements
- Auto-match to expenses
- Reconciliation workflow

### 4.3 Receipt Scanning
- Upload photo/PDF of receipt
- AI extracts vendor, amount, date, category

---

## Implementation Order (Next Sprint)

| # | Task | Effort |
|---|------|--------|
| 1 | Redesign sidebar with icons + badges | 2h |
| 2 | Multi-business model + switcher | 3h |
| 3 | Guided setup wizard (first-run) | 2h |
| 4 | Expenses model + CRUD + categories | 2h |
| 5 | Dashboard page with real KPI cards | 2h |
| 6 | Financial reports (P&L auto-gen from data) | 3h |
| 7 | Recurring invoices | 1h |
| 8 | Combined Documents page (Scrolls + Archives) | 1h |

**Total: ~16h of focused implementation**
