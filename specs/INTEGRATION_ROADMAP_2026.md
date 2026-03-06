# Tax God Integration Roadmap 2026

This roadmap captures specialized tools to evolve the AI Tax Copilot: research, multi-state compliance, document management, strategic planning, and connectivity. Use it to prioritize which integrations to build next and how they map to the existing Hermes (integrations) and Oracle (chat) flows.

---

## 1. Advanced Tax Research & Case Law

Give the agent **expert-level reasoning and citation** grounded in IRC, IRS regulations, and court cases.

| Tool | Purpose | Integration notes |
|------|---------|--------------------|
| **TaxGPT** | "AI Tax OS" — structured, source-backed responses (IRC, IRS regs, court cases) | API/key or partner; cite sources in Oracle responses |
| **Blue J Tax** | Predictive tax research and case law analysis; complex interpretations | API; use for high-complexity research tool calls |
| **Lamo** | Generative AI for tough tax research with instant, cited answers | API; alternative or fallback to TaxGPT |
| **Thomson Reuters Tax** | Enterprise tax research and compliance | API/key; premium tier for firms |

**Backend fit:** New provider type `research` (API-key based, not OAuth). Single endpoint e.g. `POST /api/v1/research/query` that routes to configured provider(s). Oracle or a dedicated "Research" tool can call it; responses include citations.

**Config:** `TAX_RESEARCH_PROVIDER`, `TAXGPT_API_KEY` / `BLUEJ_API_KEY` / etc. (one active).

---

## 2. Indirect Tax & Global Compliance

For **multi-state and international** sales: nexus, rates, and transaction-level compliance.

| Tool | Purpose | Integration notes |
|------|---------|-------------------|
| **ChatFin** | Transaction intelligence — review every invoice against global tax rules in real time; pre-audit compliance | API; webhook or batch for invoice review |
| **Anrok** | SaaS-focused: global sales tax and VAT; economic nexus; integrates with billing engines | API/OAuth; sync with Stripe/QuickBooks billing |
| **Vertex** | Enterprise transaction tax — retail, leasing, high-volume determination | API; rate/nexus lookups |

**Backend fit:** New category `compliance`. Endpoints such as `POST /api/v1/compliance/nexus-check`, `GET /api/v1/compliance/rates?jurisdiction=...`. Can reuse `IntegrationManager` for OAuth (e.g. Anrok) or API-key storage per provider.

**Config:** `CHATFIN_API_KEY`, `ANROK_CLIENT_ID`/`ANROK_CLIENT_SECRET`, `VERTEX_*` (or similar).

---

## 3. AI Document Extraction & Practice Management

Automate **intake and workpaper assembly** so the agent can "read" client source documents.

| Tool | Purpose | Integration notes |
|------|---------|-------------------|
| **TaxDome AI** | Practice management: auto-tag, categorize, rename (e.g. `435345.pdf` → `2025_W2_John_Doe.pdf`) | API/OAuth; webhook for new documents |
| **1040SCAN (SurePrep)** | Scan, organize, assemble tax workpapers; reduce data entry for individual returns | API/integration; bulk or per-client |
| **Holistiplan** | OCR and analysis of uploaded returns in ~45s; planning opportunities and projections | API; upload → structured output for Oracle |
| **Rightworks** | Practice management and workflow (cited as +2 in source) | API; document and workflow hooks |

**Backend fit:** Category `documents`. Endpoints: `POST /api/v1/documents/ingest` (upload → provider), `GET /api/v1/documents/{id}/extracted`. Existing S3/storage can hold blobs; provider returns structured metadata and text for RAG or tool use.

**Config:** `TAXDOME_*`, `SUREPREP_*`, `HOLISTIPLAN_*`, `RIGHTWORKS_*`.

---

## 4. Strategic Planning & Forecasting

Upgrade the agent from **reporter to advisor** with what-if modeling and multi-year plans.

| Tool | Purpose | Integration notes |
|------|---------|-------------------|
| **Corvee Tax Planning** | Tax savings calculation, proactive plans, multi-year strategy modeling | API; call from Pantheon or Oracle for "tax plan" tool |
| **Abacum** | Mid-market FP&A; scenario and what-if budgets; can sync to QuickBooks | API/OAuth; link to existing QuickBooks data |
| **FP Alpha** | AI over wills, trusts, insurance; holistic tax and estate planning advice | API; estate-planning tool for Oracle |

**Backend fit:** Category `planning`. Endpoints: `POST /api/v1/planning/scenario`, `POST /api/v1/planning/estate-review`. ROI engine already exists; these become additional data sources or calculation backends.

**Config:** `CORVEE_*`, `ABACUM_*`, `FPALPHA_*`.

---

## 5. Connectivity & Automation Layers

**Glue** to talk to many backends (QuickBooks, CRMs, etc.) through a single, stable API layer.

| Tool | Purpose | Integration notes |
|------|---------|-------------------|
| **MuleSoft Anypoint** | Single API layer for agent ↔ dozens of systems; centralize security and transforms | Agent calls Anypoint APIs; map existing QuickBooks/Google to Anypoint assets |
| **CData Connect AI** | Connect QuickBooks (and others) to AI platforms (e.g. Copilot, custom agents) without duplicating data | Use as alternative or complement to direct QuickBooks API for sync/read |

**Backend fit:** Category `connectivity`. Either (a) route some Hermes/QuickBooks traffic through MuleSoft/CData, or (b) add a "connector gateway" that the agent calls (e.g. `GET /api/v1/connector/quickbooks/...`) and the gateway delegates to MuleSoft or CData. Reduces brittle, direct API calls.

**Config:** `MULESOFT_*`, `CDATA_*` (connection strings or API keys).

---

## Implementation order (suggested)

1. **Catalog & UI** — Expose integration categories and "planned" tools in API + Hermes so the roadmap is visible and extensible.
2. **Research** — One research provider (e.g. TaxGPT or Blue J) behind `POST /api/v1/research/query`; wire as Oracle tool for cited answers.
3. **Documents** — One document provider (e.g. Holistiplan or 1040SCAN) for ingest + extracted metadata; wire to Scrolls/Archives and Oracle.
4. **Compliance** — One compliance provider (e.g. Anrok for SaaS or Vertex) for nexus/rates; optional Hermes panel or Oracle tool.
5. **Planning** — Corvee or FP Alpha as first planning backend; Pantheon or Oracle tool.
6. **Connectivity** — Evaluate MuleSoft/CData once multiple backends are in place; add connector gateway if needed.

---

## References

- Current integrations: `specs/BACKEND_INTEGRATIONS_AND_ALGORITHMS.md`
- Hermes (UI): `app/static/js/pages/hermes.js`
- Integration manager: `app/services/integrations/manager.py` (OAuth); new categories can use API-key storage or same DB with different `provider` namespace.
