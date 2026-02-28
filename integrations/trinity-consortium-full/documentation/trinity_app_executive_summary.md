# TRINITY CONSORTIUM — Executive Summary

**Last Updated:** February 14, 2026  
**Version:** 2.0  
**Classification:** Internal Development Reference

---

## 1. Project Overview

TRINITY CONSORTIUM is an invitation-only, private multi-project consortium focused on sovereign-grade asset stewardship and strategic ventures. The platform provides secure investor access, custom branding, project-specific CRM, document management, and activity tracking, all managed from a centralized Admin Command Center enhanced with AI tools.

**Key Principle:** This is NOT a public investment platform. It maintains a minimal public web presence, directing invited participants to a secure portal.

### Active Projects
1. **TRINITY-LARIVE Digital Sovereign Gold Reserve** — 49.9 acres of patented gold mining claims, 2.29M oz indicated gold resources, 1909 patent, 50/50 JV structure
2. **Kommunity DAO** — Decentralized community governance venture
3. **Fractal AGI Web of Life** — Artificial general intelligence exploration

---

## 2. Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Wouter, Tailwind CSS, shadcn/ui, Radix UI |
| **3D/Animation** | React Three Fiber, Three.js, Framer Motion, Lenis |
| **Backend** | Node.js, Express, TypeScript (ESM) |
| **Database** | PostgreSQL (63 tables), Drizzle ORM, pgvector |
| **Object Storage** | Replit Object Storage |
| **Auth** | JWT (HS256) + RBAC, Argon2id password hashing |
| **AI Providers** | OpenAI, Google Gemini, Anthropic Claude, xAI Grok, DeepSeek, Moonshot Kimi, Genspark, OpenClaw, Replit AI (9 providers, 27 models) |

---

## 3. Architecture Summary

### Frontend (153 TypeScript/TSX files)
- **Public Pages (5):** Homepage (`/`), Trinity-LaRive (`/trinity-larive`), Request Access, Kommunity DAO, Fractal AGI
- **Portal Pages (17):** Dashboard, Data Room, Admin CRM, Admin Console, Command Center, Flow Builder, Agentic Constellation, Agent Management, Tools Catalog, Knowledge Base, Sentinel Dashboard, Execution Dashboard, Infrastructure Report, Effects Showcase, Our Projects, Q&A, Contact
- **Component Groups:** admin, ai, constellation, effects, icons, layout, motion, premium, sacred, ui

### Backend (163 TypeScript files)
- **13 Domain Modules:** ai, auth, constellation, crm, governance, integrations, marketplace, notifications, projects, swarm, tenants, vault, workflows
- **19 Route Files** serving 468 API endpoints
- **Service Layer Pattern** with domain-driven organization

### Database (63 tables, 1698 lines of schema)
Core table groups: tenants, projects, users, investors, members, vault_documents, constellation_nodes/edges, notifications, tasks, meetings, workflows, agent_memories, embeddings, knowledge_files, graph_entities/relationships, marketplace_connectors, background_tasks, and more.

---

## 4. AI Multi-Agent System ("Trinity Council")

### 20 Specialized Agents

| Agent | Role | Key Tools / Capabilities |
|-------|------|--------------------------|
| Oracle | Strategic intelligence & document analysis | `analyzeDocument`, `strategicBriefing`, `riskAssessment`, sentiment analysis, executive summaries |
| Liaison | CRM & investor relations management | `manageInvestor`, `scheduleMeeting`, investor scoring, communication logs, follow-up automation |
| Warden | Security, access control & compliance | `auditAccess`, `revokeToken`, permission scanning, threat assessment, compliance reports |
| Engineer | Technical infrastructure & development | `runDiagnostics`, `deployService`, system health checks, dependency audits, performance profiling |
| Prophet | Financial forecasting & predictive analysis | `forecastRevenue`, `modelScenario`, Monte Carlo simulations, trend detection, risk quantification |
| Auditor | Compliance verification & security scanning | `scanVulnerabilities`, `verifyCompliance`, SOC 2 checklists, penetration test reports, audit trails |
| Architect | System design & infrastructure planning | `designSchema`, `planMigration`, capacity planning, architecture diagrams, tech debt analysis |
| Curator | Document management & knowledge organization | `classifyDocument`, `buildTaxonomy`, auto-tagging, version control, knowledge graph updates |
| Emissary | External integrations (GitHub, Genspark) | `syncGitHub`, `queryGenspark`, webhook management, API bridge, external data ingestion |
| Scribe | Document generation & content authoring | `generateReport`, `draftProposal`, PDF/DOCX export, template engine, multi-format output |
| Sentinel | Real-time monitoring & threat detection | `monitorEndpoints`, `detectAnomaly`, uptime tracking, alert escalation, incident response |
| Chancellor | Investor ledger & capital stack tracking | `trackCapital`, `recordDistribution`, ledger reconciliation, waterfall calculations, cap table management |
| Designer | Creative direction, UI/UX, 3D, brand systems | `generateMockup`, `create3DAsset`, brand guidelines, color palette generation, sacred geometry visuals |
| Director | Project planning & milestone tracking | `createMilestone`, `assignTask`, Gantt scheduling, dependency mapping, progress dashboards |
| Linguist | Text-to-speech & speech-to-text | `synthesizeSpeech`, `transcribeAudio`, ElevenLabs integration, multi-language support, voice cloning |
| Presenter | Slideshow & pitch deck generation | `buildDeck`, `exportSlides`, Gamma.app integration, template selection, speaker notes |
| Producer | Video creation & editing | `createClip`, `editVideo`, Opus Clip integration, storyboard generation, subtitle rendering |
| Reporter | Report generation (PDF, DOCX, HTML) | `compileReport`, `formatExport`, chart embedding, data visualization, scheduled report delivery |
| Researcher | Deep web search & topic research | `deepSearch`, `synthesizeFindings`, source ranking, citation management, competitive analysis |
| Swarm | OpenClaw multi-agent orchestration | `orchestrateCrew`, `delegateTask`, cost-aware routing, consensus voting, parallel execution |

### 245+ Tools across 13 categories

Tool categories: Document Management, CRM & Investor Relations, Security & Compliance, Financial Analysis, Infrastructure & DevOps, Knowledge Management, External Integrations, Communication, Research & Intelligence, Creative & Design, Audio & Video, Reporting, and Orchestration.

### 18 Sub-Agents mirroring primary agents

Each primary agent has a corresponding sub-agent that can be delegated to for specialized subtasks. Sub-agents inherit the parent's tools but operate with narrower context windows and lower cost budgets, enabling efficient task decomposition.

---

## 5. AI Infrastructure

| System | Purpose | Details |
|--------|---------|---------|
| **Adaptive Execution Engine** | ReAct-style observe→decide→act loop | Replaces rigid workflows with dynamic decision trees; supports multi-step tool chains with state tracking |
| **Circuit Breaker** | Per-agent error rate tracking | Three states: closed→open→half-open; auto-recovery with configurable thresholds per agent |
| **Governance Gatekeeper** | Pre-execution cost check | SSE approval workflow for high-cost operations; budget enforcement before tool invocation |
| **Sacred Geometry Optimizer** | Geometric math for AI tuning | 21 systems: golden ratio scoring, Fibonacci retry, fractal clustering, toroidal scheduling + Lévy Flight, Kuramoto sync, Golden Section Search, Platonic solids, Vesica Piscis consensus, Spiral optimizer |
| **Continuous Improvement Loop** | Reinforcement learning system | SessionEvaluator + PolicyStore + FractalLearningEngine + DailyTrainingPipeline; learns from every interaction |
| **Cost Tracker** | Centralized spend tracking | Daily and per-session caps; per-agent and per-model cost attribution; real-time budget alerts |
| **Batch Tool Executor** | Concurrency-limited parallel execution | Max 6 concurrent tool calls, 30s timeout per tool, automatic retry with exponential backoff |
| **Sentinel Service** | System-wide health monitoring | Continuous endpoint monitoring, anomaly detection, automated incident escalation, uptime SLA tracking |
| **Streaming Analytics** | Real-time dashboard broadcasting | WebSocket push every 5s; agent activity, cost burn rate, tool usage heatmaps, session metrics |
| **Council Bus** | Inter-agent communication backbone | Per-request context sharing between agents; message routing, priority queuing, broadcast channels |
| **Document Intelligence** | Automated document processing | PDF/DOCX parsing, entity extraction, auto-classification, embedding generation, semantic search indexing |
| **Daily Briefing** | Automated daily summary generation | Aggregates overnight activity, pending tasks, cost summaries, anomaly alerts into executive briefing |
| **Federated Knowledge Graph** | Domain-partitioned graph | Cross-domain entity matching, relationship inference, graph traversal queries, knowledge fusion |
| **Agent Marketplace** | Automation integrations | Zapier/Make/n8n/Custom webhook connectors; trigger-action workflows with external services |
| **Multi-Tenant Architecture** | Tenant isolation | Slug-based tenant resolution with plan/usage tracking; data partitioning per tenant |
| **Background Task Queue** | Async worker system | Priority-ordered execution, configurable retry logic, dead-letter handling, progress reporting |
| **Composable Tool Engine** | Dynamic tool composition | 245+ tools with compatibility scoring, composition templates, and runtime tool chain assembly |
| **Context Engineering** | Prompt optimization | Role-based context filtering with token budgets; dynamic prompt construction per agent persona |
| **Bayesian Optimizer** | Agent parameter tuning | GP-UCB acquisition function for hyperparameter optimization; temperature, top-p, tool selection weights |
| **Dual Decomposition Router** | Task decomposition | Splits complex multi-domain tasks into localized subproblems; coordinates parallel agent execution |
| **Execution Tracker** | Operation audit trail | Full execution history with timing, cost, input/output logging; queryable via Execution Dashboard |
| **Importance Scorer** | Message prioritization | ML-based scoring of incoming requests; routes high-priority items for immediate processing |
| **Conversation Memory** | Session context persistence | Short-term and long-term memory stores; RAG-powered retrieval for conversation continuity |

---

## 6. Security & Access Control

### Role-Based Access Control (RBAC)
| Role | Description | Access Level |
|------|-------------|-------------|
| Admin | Full platform control, all settings and data | Unrestricted |
| Investor | Portfolio view, data room, limited portal access | Read + limited write |
| Operator | Day-to-day operations, CRM, task management | Read/write operational data |
| QP (Qualified Purchaser) | Enhanced investor with accredited access | Extended data room |
| Collaborator | External partner with scoped access | Project-specific only |
| Legal | Compliance review, document access | Read-only + audit |

### Security Stack
- **16 Fine-Grained Permissions** mapped to roles via `server/auth/rbac.ts`
- **JWT Authentication** with HS256 signing and server-side token revocation
- **Argon2id Password Hashing** with configurable memory/time cost parameters
- **E2E Encryption** (`server/ai/crew/e2e-encryption.ts`) for secure inter-agent and user messaging
- **Privacy Router** (`server/ai/crew/privacy-router.ts`) with PII detection, redaction, and data classification
- **Document ACL** with per-document access controls and audit logging
- **Compliance Middleware** (`server/ai/middleware/compliance.ts`) for regulatory checks on AI operations
- **Cost Governor** with daily spending limits, per-operation caps, and SSE-based admin approval flows

---

## 7. Responsive Design

### Approach
Mobile-first responsive design implemented across all portal and public pages using Tailwind CSS utility classes.

### Breakpoint Strategy
| Breakpoint | Min Width | Usage |
|-----------|-----------|-------|
| `sm:` | 640px | Stack to 2-column transition |
| `md:` | 768px | Tablet-optimized layouts |
| `lg:` | 1024px | Desktop 3-column grids |
| `xl:` | 1280px | Wide desktop enhancements |
| `2xl:` | 1536px | Ultra-wide layouts |

### Key Patterns
- **WCAG-compliant touch targets** with minimum `min-h-[44px]` on all interactive elements (buttons, links, form inputs)
- **Fluid grid layouts** using responsive column patterns (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`)
- **Responsive patterns applied across 30+ files** including portal pages, admin panels, and public pages
- **Overflow handling** with `overflow-x-auto` on tables/data grids, `overflow-hidden` on cards, and `truncate` for long text
- **Text wrapping** using `break-words`, `whitespace-normal`, and responsive font sizing (`text-sm md:text-base lg:text-lg`)
- **Flexible layouts** with `flex-wrap`, `gap-*`, and min-width constraints for adaptive component sizing
- **Hidden/visible toggling** with `hidden md:block` and `md:hidden` for device-appropriate content
- **Responsive navigation** with mobile hamburger menu and desktop horizontal nav bar

---

## 8. SEO & Crawl Control

- **robots.txt:** Dynamic server-side endpoint with explicit blocking rules:
  ```
  User-agent: *
  Disallow: /trinity-larive/portal/
  Disallow: /admin/
  Disallow: /api/
  Allow: /
  Sitemap: https://trinity-consortium.replit.app/sitemap.xml
  ```
- **sitemap.xml:** Dynamic XML sitemap (5 public pages only)
- **`useSEO` hook:** Custom React hook (`client/src/hooks/useSEO.ts`) providing per-page title, description, robots directive, Open Graph tags, and Twitter Card meta — applied on every page component
- **Portal/Admin pages:** `noindex, nofollow` directive via useSEO
- **Valid `<head>`** per Google guidelines with structured meta tags

---

## 9. External Integrations

| # | Integration | Status | Purpose |
|---|-------------|--------|---------|
| 1 | Google Drive | Full | Document storage, sharing, folder management |
| 2 | Google Gmail | Full | Email communication, notification delivery |
| 3 | Google Sheets | Full | Spreadsheet data import/export, investor tracking |
| 4 | Google Calendar | Full | Meeting scheduling, event management |
| 5 | Google Docs | Full | Collaborative document editing |
| 6 | Google Slides | Partial | Presentation generation and export |
| 7 | Google Meet | Partial | Video conference scheduling and links |
| 8 | Google Forms | Partial | Survey and form data collection |
| 9 | Google Service Account | Full | Server-to-server Google API authentication |
| 10 | GitHub | Full | Repository sync, issue tracking, CI/CD triggers |
| 11 | Stripe | Full | Payment processing, subscription management |
| 12 | SendGrid | Full | Transactional email delivery |
| 13 | Discord | Partial | Community notifications, webhook alerts |
| 14 | Notion | Partial | External knowledge base sync |
| 15 | Twilio | Partial | SMS notifications, phone verification |
| 16 | Linear | Partial | Project management and issue tracking |
| 17 | ElevenLabs | Full | Text-to-speech, voice cloning, audio generation |
| 18 | Gamma.app | Full | AI-powered presentation and deck creation |
| 19 | Opus Clip | Partial | Video clip extraction and editing |
| 20 | Cursor Cloud Agent | Full | AI-assisted code generation and review |
| 21 | LlamaIndex RAG | Full | Retrieval-augmented generation pipeline |
| 22 | Genspark | Partial | AI research and web intelligence |
| 23 | Data Room | Full | Secure document sharing for investors |
| 24 | Email Service | Full | Unified email abstraction layer |
| 25 | AI Models Hub | Full | Multi-provider model routing (9 providers, 27 models) |

---

## 10. File Structure Overview

```
/
├── client/                    # Frontend React app (153 files)
│   ├── index.html            # Entry point with SEO meta tags
│   ├── public/               # Static assets (favicon, robots.txt, sitemap.xml)
│   └── src/
│       ├── App.tsx           # Router with all routes
│       ├── pages/            # Page components (5 public + 17 portal)
│       ├── components/       # Shared components (admin, ai, layout, ui, etc.)
│       ├── hooks/            # Custom hooks (useSEO, useAuth, useVoice, etc.)
│       └── lib/              # Utilities, auth context, Three.js helpers
├── server/                   # Backend Express server (163 files)
│   ├── index.ts             # Server entry, middleware, robots.txt, sitemap.xml
│   ├── routes.ts            # Route registration hub
│   ├── storage.ts           # IStorage interface + Drizzle implementation
│   ├── db.ts                # Database connection
│   ├── seed.ts              # Database seeding
│   ├── domains/             # Domain-driven route modules
│   │   ├── ai/              # AI routes (149 endpoints)
│   │   ├── auth/            # Authentication routes
│   │   ├── crm/             # CRM routes
│   │   ├── vault/           # Vault + knowledge graph routes
│   │   └── ...              # 13 domain modules total
│   ├── ai/                  # AI agent system
│   │   ├── *-tools.ts       # 20 agent tool files
│   │   ├── crew/            # Agent crew (definitions, memory, RAG, etc.)
│   │   ├── swarm/           # Swarm orchestration
│   │   ├── continuous-improvement/ # RL learning system
│   │   └── middleware/       # Compliance middleware
│   └── integrations/        # External service integrations (25 files)
├── shared/
│   └── schema.ts            # Database schema (63 tables, 1698 lines)
├── Trinity_Documentation/   # Project documentation
├── docs/                    # Developer notes (DB_NOTES.md, portal_readme.md)
├── security-audit/          # Security audit reports and remediation
└── package.json             # Dependencies
```

---

## 11. Running the Project

```bash
npm run dev          # Start development server (port 5000)
npm run build        # Build for production
npm run start        # Run production build
npm run db:push      # Push schema to database
```

**Environment:** Node.js on NixOS (Replit), PostgreSQL (Neon-backed)

---

## 12. Database Operations

- **Reference:** See `docs/DB_NOTES.md` for full database conventions and operational procedures

### Key Rules
1. **Never use manual `ALTER TABLE`** — all schema changes must go through **Drizzle ORM** (`npm run db:push`)
2. **Schema source of truth:** `shared/schema.ts` — all 63 tables defined in a single file
3. **Test migrations locally** before pushing to production database
4. **Use transactions** for multi-table operations via `db.transaction()`

### Schema Conventions
| Convention | Implementation |
|-----------|---------------|
| **Primary Keys** | UUID type with `defaultRandom()` generation |
| **Timestamps** | `createdAt` / `updatedAt` columns with `defaultNow()` |
| **Arrays** | `text().array()` method syntax (not wrapper) |
| **JSON Data** | `jsonb` columns for metadata, config, tool parameters |
| **Relations** | Foreign keys with `references()` and cascade rules |
| **Enums** | PostgreSQL native enums via `pgEnum` |
| **Soft Deletes** | `deletedAt` timestamp where applicable |
| **Indexing** | Composite indexes on frequently queried column pairs |

### Common Table Groups
- **Core:** tenants, projects, users, investors, members
- **Documents:** vault_documents, knowledge_files, embeddings
- **AI:** agent_memories, conversation_sessions, execution_logs
- **Graph:** constellation_nodes, constellation_edges, graph_entities, graph_relationships
- **Operations:** tasks, meetings, workflows, background_tasks, notifications
- **Marketplace:** marketplace_connectors, marketplace_listings
