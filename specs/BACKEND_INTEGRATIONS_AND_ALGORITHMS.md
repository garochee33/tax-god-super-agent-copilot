# Tax God Backend: Integrations + Algorithms

## What is implemented

### OAuth Integrations
- Google Workspace OAuth URL generation, code exchange, token refresh, profile test, Gmail list endpoint.
- QuickBooks OAuth URL generation, code exchange, token refresh, connection test, Profit & Loss report endpoint.
- In-memory credential lifecycle with expiration-aware refresh in `IntegrationManager`.
- OAuth callback supported for:
  - Programmatic POST callback: `/api/v1/integrations/callback`
  - Browser GET callback: `/api/v1/integrations/callback?provider=...&code=...&state=...`

### Integration API Endpoints
- `GET /api/v1/integrations/list?user_id=...`
- `POST /api/v1/integrations/connect`
- `POST /api/v1/integrations/callback`
- `GET /api/v1/integrations/callback`
- `POST /api/v1/integrations/disconnect`
- `GET /api/v1/integrations/status/{provider}?user_id=...`
- `GET /api/v1/integrations/google/emails?user_id=...`
- `GET /api/v1/integrations/quickbooks/company?user_id=...`
- `GET /api/v1/integrations/quickbooks/profit-loss?user_id=...&year=2024`
- `GET /api/v1/integrations/quickbooks/balance-sheet?user_id=...&as_of=YYYY-MM-DD` (optional; default end of prior month)
- `GET /api/v1/integrations/quickbooks/vendors?user_id=...&max_results=100`
- `GET /api/v1/integrations/roadmap` — 2026 roadmap categories and tools (research, compliance, documents, planning, connectivity). See `specs/INTEGRATION_ROADMAP_2026.md`.

### ROI Algorithms
- `compute_roi` and `project_incremental_revenue` added in `app/services/roi_engine.py`.
- ROI endpoints added:
  - `POST /api/v1/analytics/roi/calculate`
  - `POST /api/v1/analytics/roi/project`

### Document intelligence (Trinity GEM)
- **PDF ingest:** `POST /api/v1/documents/ingest` — upload a PDF (multipart `file` or JSON `content_base64`); returns extracted text, page count, tables (pipe-style), metadata, and optional tax-doc entity hints (SSN/EIN/year patterns). Max 20 MB. See `app/services/document_intelligence.py` (pypdf + table extraction).

### Cost Governance Upgrades
- Routing metadata exposed by estimate endpoint:
  - `routing_path`, `budget_mode`, `estimated_swarm_agents`, `downgrade_reason`
- Swarm-lane estimate support via context:
  - `parallelizable_score`, `batch_size`

## Required environment variables for real OAuth

Set in `.env`:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI` (default is `/api/v1/integrations/callback`)
- `QUICKBOOKS_CLIENT_ID`
- `QUICKBOOKS_CLIENT_SECRET`
- `QUICKBOOKS_REDIRECT_URI` (default is `/api/v1/integrations/callback`)

If credentials are missing, `/connect` now returns a clear configuration error.

## QuickBooks production & deploy

- **Sandbox vs Production:** Use Intuit Developer Sandbox for testing; switch to production keys and redirect URI for live deploy.
- **Rate limits:** Intuit caps at ~500 requests per minute per company. The API maps 429 to HTTP 503 with message "QuickBooks rate limit exceeded. Try again in a minute."; the Hermes UI shows a friendly rate-limit message.
- **Balance sheet:** `as_of` must be `YYYY-MM-DD`; validated server-side. Omitted `as_of` defaults to end of prior month.
- **Logging:** QuickBooks failures (including 429) are logged without secrets (user_id, endpoint, status).

## Extension/Web integration note

`/api/v1/chat/query` now returns a stable `conversation_id` even in model-error paths, so browser clients can persist conversation state consistently.
