# Tax God – Production Wiring Summary

This document summarizes the production-grade backend/frontend wiring and UI improvements applied to Tax God v3.0.

## Backend ↔ Frontend Wiring

| Area | What Was Done |
|------|----------------|
| **Oracle (Chat)** | Sends `client_id` and `conversation_id` on every query; persists `conversation_id` in sessionStorage for conversation resume; displays `model_used` in badge; surfaces API error message in UI. |
| **Scrolls (Memo/IRS)** | Memo: subject, client_name, facts, **tax_year** (dropdown) with required validation. IRS: **taxpayer_name** and **tax_years** form fields (no hardcoded placeholders); required validation and max lengths. |
| **Tribunal (Audit)** | Client-side validation: required client_id; non-negative wages, Schedule C, itemized. Error message shown in results panel. |
| **Archives (Citations)** | Query length limit (500 chars); error message + Retry on failure. |
| **Hermes (Integrations)** | Disconnect button when connected; in-page success/error messages (no `alert()`); `showMessage()` for connect/disconnect feedback. |
| **Pantheon (Dashboard)** | Loading skeleton on stat cards until metrics load; **Cost estimate** tool: input + “Estimate” calls `POST /api/v1/analytics/estimate`, shows cost and model. |
| **Agora (Clients)** | Full CRUD client management. Lists, creates, edits, deletes clients via `/api/v1/clients`. Paginated list with search and status filter. Form: name, email, phone, company, tax_id, filing_type, status, notes. |

## API Client (app.js)

- **Error normalization:** Array `detail` from backend is joined into a single string; `err.status` and `err.unauthorized` set for 401/403.
- **Optional retry:** `api.request(..., { retries: 1 })` for transient failures (no retry on 401/403).

## UI/UX

- **Pantheon:** Skeleton shimmer on stat values and trend lines until data loads; estimate result area for cost preview.
- **Hermes:** Message strip above grid for success/error/info; auto-hide after 5s.
- **Forms:** Required fields marked with red `*`; `maxlength` and validation before submit where applicable.
- **CSS:** `.pantheon-skeleton.loading` shimmer; `.required` for labels.

## Backend (unchanged but relied on)

- Chat: `client_id`, `conversation_id`, `require_citations` already supported.
- Audit memo: `subject`, `facts`, `client_name`, `tax_year`.
- Audit IRS response: `taxpayer_name`, `tax_years`, `issues`, `supporting_facts`, etc.
- Integrations: `POST /disconnect` with `provider`, `user_id`.
- Analytics: `POST /estimate` with `query`, `client_id`.

## Not Implemented (optional next)

- Full **Documents** page (batch-process, job status polling).
- **ROI** calculator UI (endpoints exist: `/roi/calculate`, `/roi/project`).
- **Advanced** pipeline UI (decompose/memory/validate).
- **Conversation resume** UI (e.g. “Load previous conversation”) using `GET /chat/conversations/{id}`.
- Auth (login/JWT); currently `client_id` from localStorage and optional API base.
