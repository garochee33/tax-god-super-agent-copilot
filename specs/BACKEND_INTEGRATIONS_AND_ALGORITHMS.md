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
- `GET /api/v1/integrations/quickbooks/profit-loss?user_id=...&year=2024`

### ROI Algorithms
- `compute_roi` and `project_incremental_revenue` added in `app/services/roi_engine.py`.
- ROI endpoints added:
  - `POST /api/v1/analytics/roi/calculate`
  - `POST /api/v1/analytics/roi/project`

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

## Extension/Web integration note

`/api/v1/chat/query` now returns a stable `conversation_id` even in model-error paths, so browser clients can persist conversation state consistently.
