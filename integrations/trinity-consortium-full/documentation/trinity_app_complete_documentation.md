# TRINITY CONSORTIUM — Complete Technical Documentation

**Last Updated:** February 17, 2026
**Version:** 1.1
**Purpose:** Developer reference for auditing, maintenance, and feature development

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Database Schema](#2-database-schema)
3. [Authentication & Authorization](#3-authentication--authorization)
4. [API Endpoints Reference](#4-api-endpoints-reference)
5. [AI Multi-Agent System](#5-ai-multi-agent-system)
6. [AI Infrastructure Components](#6-ai-infrastructure-components)
7. [Frontend Architecture](#7-frontend-architecture)
8. [SEO & Crawl Control](#8-seo--crawl-control)
9. [External Integrations](#9-external-integrations)
10. [Configuration & Environment](#10-configuration--environment)
11. [Deployment & Operations](#11-deployment--operations)
12. [Known Considerations](#12-known-considerations)

---

## 1. System Architecture

### Overview
- **Monorepo** with `client/` (React), `server/` (Express), and `shared/` (schema)
- **Single-port deployment** on port 5000 (frontend + API)
- **Domain-driven backend** with 14 domain modules (ai, auth, command-center, constellation, crm, governance, integrations, marketplace, notifications, projects, swarm, tenants, vault, workflows)
- **Service layer pattern** separating business logic from routes

### Technology Stack

#### Frontend
| Technology | Purpose |
|-----------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Wouter | Client-side routing |
| Tailwind CSS | Utility-first styling |
| shadcn/ui + Radix UI | Component library |
| TanStack React Query | Server state management |
| Framer Motion | Animations |
| Lenis (@studio-freight/lenis) | Smooth scrolling |
| React Three Fiber + Drei | 3D visualizations |
| @xyflow/react | Flow diagram builder |
| cmdk | Command palette |

#### Backend
| Technology | Purpose |
|-----------|---------|
| Node.js + Express | Server runtime |
| TypeScript (ESM) | Type-safe server code |
| Drizzle ORM | Database queries |
| drizzle-zod | Schema validation |
| jsonwebtoken | JWT auth |
| argon2 | Password hashing |
| compression | Response compression |
| Zod | Runtime validation |

#### AI SDKs
| Package | Provider |
|---------|----------|
| @ai-sdk/openai | OpenAI |
| @google/genai | Google Gemini |
| @anthropic-ai/sdk | Anthropic Claude |
| openrouter (via OpenAI SDK) | xAI Grok, DeepSeek, Moonshot Kimi |
| Custom REST | Genspark AI |
| Custom WebSocket | OpenClaw Swarm |
| Replit AI (built-in) | Code Intelligence |

### Request Flow
```
Client (React) → Express Server (port 5000)
  → Middleware (compression, JSON parsing, tenant resolution, logging)
  → Route Handler (domain module)
  → Storage Interface (Drizzle ORM)
  → PostgreSQL Database
```

### Development vs Production
- **Development:** Vite HMR dev server proxied through Express
- **Production:** Static build served via `express.static()` from `server/public/`

---

## 2. Database Schema

### Schema Location
`shared/schema.ts` — 79 tables

### Table Reference

#### Multi-Tenant
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `tenants` | Tenant organizations | id, name, slug, domain, plan, status, maxProjects, maxMembers |

#### Projects
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `projects` | Consortium projects | id, tenantId, name, slug, primaryColor, status, isPublic, portalEnabled |

#### Authentication
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | User accounts | id, tenantId, username, email, passwordHash, roles[], extraPerms[], isActive |
| `investors` | Investor profiles | id, userId, name, email, company, status, accessLevel |

#### CRM
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `members` | CRM member records | id, firstName, lastName, email, role, status, ndaSigned, company |
| `member_credentials` | Access credentials | id, memberId, portalPassword, inviteToken, inviteExpires |
| `member_document_permissions` | Doc access | id, memberId, documentId, canView, canDownload |
| `member_activity` | Activity tracking | id, memberId, action, metadata |
| `tasks` | Task management | id, title, status, priority, assignedTo, dueDate |
| `meetings` | Meeting records | id, title, date, status, attendees, notes |
| `technical_glossary` | Term definitions | id, term, definition, category |

#### Document Vault
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `vault_documents` | Vault documents | id, name, fileType, category, fileSize, indexed, summary, storageKey |
| `document_folders` | Folder hierarchy | id, name, parentId, description |
| `document_acl` | Access control lists | id, documentId, entityType, entityId, permission |
| `document_visual_metadata` | Visual metadata | id, documentId, charts, tables, maps, entities |
| `knowledge_files` | Knowledge base files | id, name, content, source, indexed |

#### Constellation (Interactive Visualization)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `constellation_nodes` | Graph nodes | id, label, type, category, x, y, size, color |
| `constellation_edges` | Graph edges | id, sourceId, targetId, relationship, strength, animated |

#### Notifications & Activity
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `notifications` | System notifications | id, type, category, title, message, severity, recipientId |
| `activity_log` | Audit log | id, action, entity, entityId, userId, details, timestamp |

#### AI System
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `agent_memories` | Agent memory store | id, agentId, type, content, importance, embedding |
| `agent_performance_metrics` | Performance tracking | id, agentId, metric, value, period |
| `agent_preferences` | Agent preferences | id, agentName, temperature, maxTokens, enabled |
| `agent_presets` | Agent config presets | id, name, description, config |
| `embeddings` | Vector embeddings | id, sourceType, sourceId, embedding, metadata |
| `prompt_optimizations` | DSPy optimizations | id, agentId, prompt, optimizedPrompt, score |
| `session_evaluations` | RL session evals | id, sessionId, scores, overallScore |
| `learning_generations` | Learning generations | id, generation, metrics, fibonacciLevel |
| `tool_selection_policies` | Tool selection | id, situationHash, toolName, score, selections |
| `graph_entities` | Knowledge graph | id, name, type, properties, projectId |
| `graph_relationships` | Graph relations | id, sourceId, targetId, type, properties |

#### Workflows & Automation
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `workflows` | Workflow definitions | id, name, trigger, steps, status |
| `visual_workflows` | Visual flow builder | id, name, nodes, edges, description |
| `workflow_signals` | Workflow signals | id, workflowId, signalType, payload |
| `automation_workflows` | Automation defs | id, name, trigger, actions, schedule |
| `automation_executions` | Execution history | id, workflowId, status, result, duration |
| `durable_workflows` | Durable workflows | id, workflowId, state, currentStep |
| `durable_activities` | Durable activities | id, workflowId, activityName, status, result |
| `background_tasks` | Background tasks | id, type, priority, status, progress, result |

#### Marketplace
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `marketplace_connectors` | Available integrations | id, name, type, config, webhookUrl |
| `marketplace_installs` | Installed connectors | id, connectorId, tenantId, status, config |
| `marketplace_webhook_events` | Webhook logs | id, installId, eventType, payload, status |

#### Security & Encryption
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `encryption_keys` | E2E encryption keys | id, ownerId, ownerType, publicKey, fingerprint |
| `encrypted_messages` | Encrypted messages | id, senderId, recipientId, encryptedContent |
| `message_threads` | Message threads | id, subject, participants, lastMessage |
| `privacy_audit_logs` | Privacy audit trail | id, action, classification, piiDetected |
| `audit_trail` | Compliance audit trail | id, agentId, action, input, output, toolsUsed |

#### Scheduling
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `event_types` | Calendar event types | id, title, duration, color |
| `bookings` | Scheduled bookings | id, eventTypeId, startTime, endTime, attendeeName |
| `availability_windows` | Availability slots | id, dayOfWeek, startTime, endTime |

#### Other
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `sentinel_healing_events` | Self-healing events | id, agentId, errorType, healingAction |
| `swarm_ledger` | Cost tracking ledger | id, taskId, estimatedCost, actualCost, status |
| `investor_workspaces` | Investor workspaces | id, name, ownerId, settings |
| `workspace_members` | Workspace members | id, workspaceId, memberId, role |
| `documents` | General documents | id, title, content, folderId |
| `drive_sync_configs` | Google Drive sync | id, driveId, folderId, syncEnabled |
| `drive_synced_files` | Synced files | id, configId, driveFileId, localPath |
| `task_queues` | Task queue entries | id, taskType, priority, payload |
| `rwa_assets` | Real-world assets | id, name, type, value, tokenized |
| `rwa_asset_tokens` | Asset tokens | id, assetId, tokenId, holder |
| `rwa_orders` | Asset orders | id, assetId, type, amount, status |
| `rwa_portfolios` | Portfolio tracking | id, investorId, totalValue |
| `rwa_transactions` | Asset transactions | id, orderId, type, amount, timestamp |

### Schema Conventions
- Primary keys: `varchar` with `gen_random_uuid()` default
- Timestamps: `timestamp` with `.defaultNow()`
- Arrays: `text().array()` pattern
- JSON: `jsonb()` for flexible metadata
- Foreign keys: `.references(() => table.id)`
- Insert schemas: `createInsertSchema(table).omit({ id, createdAt, ... })`

---

## 3. Authentication & Authorization

### Auth Flow
1. User submits credentials to `POST /api/auth/login`
2. Server verifies password with Argon2id
3. JWT token issued with claims: `{ id, username, roles[], permissions[] }`
4. Token validated on each request via middleware
5. Route-level guards check role/permission requirements

### RBAC Roles
| Role | Description |
|------|-------------|
| `admin` | Full system access |
| `investor` | Portal access, document viewing |
| `operator` | Operational management |
| `qp` | Qualified purchaser with elevated access |
| `collaborator` | Limited collaboration access |
| `legal` | Legal document access |

### 16 Permissions
`view_documents`, `download_documents`, `upload_documents`, `manage_members`, `manage_tasks`, `manage_meetings`, `view_analytics`, `manage_settings`, `manage_projects`, `manage_notifications`, `view_audit_log`, `manage_workflows`, `manage_ai`, `manage_marketplace`, `manage_tenants`, `manage_security`

### Auth Routes
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| GET | `/api/auth/verify` | Verify JWT token |
| GET | `/api/auth/roles` | List available roles |

---

## 4. API Endpoints Reference

### Authentication (`auth.routes.ts`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/verify` | Verify token |
| GET | `/api/auth/roles` | List roles |

### CRM (`crm.routes.ts`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/members` | List all members |
| GET | `/api/admin/members/:id` | Get member by ID |
| POST | `/api/admin/members` | Create member |
| PUT | `/api/admin/members/:id` | Update member |
| DELETE | `/api/admin/members/:id` | Delete member |
| GET | `/api/admin/members/:id/credentials` | Get member credentials |
| GET | `/api/admin/members/:id/permissions` | Get member permissions |
| GET | `/api/admin/members/:id/workspaces` | Get member workspaces |
| GET | `/api/admin/tasks` | List tasks |
| POST | `/api/admin/tasks` | Create task |
| PUT | `/api/admin/tasks/:id` | Update task |
| DELETE | `/api/admin/tasks/:id` | Delete task |
| GET | `/api/admin/meetings` | List meetings |
| POST | `/api/admin/meetings` | Create meeting |
| DELETE | `/api/admin/meetings/:id` | Delete meeting |
| GET | `/api/admin/workspaces` | List workspaces |
| POST | `/api/admin/workspaces` | Create workspace |
| GET | `/api/admin/workspaces/:id` | Get workspace |
| DELETE | `/api/admin/workspaces/:id` | Delete workspace |

### Projects (`project.routes.ts`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List projects |
| GET | `/api/projects/:slug` | Get project by slug |
| POST | `/api/projects` | Create project |
| PUT | `/api/projects/:id` | Update project |

### Vault / Documents (`vault.routes.ts`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vault/documents` | List documents |
| POST | `/api/vault/documents` | Upload document |
| POST | `/api/vault/documents/:id/summarize` | AI summarize |
| GET | `/api/admin/documents/:id/acl` | Document ACL |
| GET | `/api/knowledge/files` | Knowledge files |
| POST | `/api/knowledge/files` | Create knowledge file |

### Constellation (`constellation.routes.ts`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/constellation/nodes` | List nodes |
| GET | `/api/constellation/edges` | List edges |
| POST | `/api/constellation/nodes` | Create node |
| POST | `/api/constellation/edges` | Create edge |

### AI System (`ai.routes.ts` — 149 endpoints)

#### Core AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai/status` | AI system status |
| GET | `/api/ai/providers` | List AI providers |
| GET | `/api/ai/models` | List available models |
| POST | `/api/council/query` | Query Trinity Council |
| GET | `/api/council/stream` | SSE stream for council |
| POST | `/api/council/batch` | Batch tool execution |

#### Agent Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents/enabled` | List enabled agents |
| GET | `/api/agents/preferences` | Agent preferences |
| PUT | `/api/agents/preferences/:agentName` | Update preferences |
| GET | `/api/agents/presets` | List presets |
| POST | `/api/agents/presets` | Create preset |
| DELETE | `/api/agents/presets/:id` | Delete preset |
| GET | `/api/agent-profiles` | Performance profiles |
| GET | `/api/agent-profiles/:agentId` | Single profile |

#### Adaptive Execution
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/adaptive/execute` | Execute adaptive task |
| GET | `/api/adaptive/status/:executionId` | Execution status |
| GET | `/api/adaptive/active` | Active executions |
| GET | `/api/adaptive/philosophy` | Engine philosophy |

#### Cost & Governance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai/spend` | Current spend |
| GET | `/api/ai/spend/alerts` | Spend alerts |
| GET | `/api/ai/cost/pending` | Pending approvals |
| POST | `/api/governance/submit` | Submit for approval |
| GET | `/api/governance/approvals/stream` | SSE approval stream |

#### Circuit Breaker
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/circuit-breaker/status` | All circuit states |
| GET | `/api/circuit-breaker/agent/:agentId` | Agent circuit state |
| POST | `/api/circuit-breaker/reset/:agentId` | Reset circuit |

#### Memory & RAG
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/mem0/store` | Store memory |
| POST | `/api/mem0/recall` | Recall memories |
| POST | `/api/mem0/extract` | Extract entities |
| POST | `/api/mem0/context` | Get context |
| DELETE | `/api/mem0/memory/:id` | Delete memory |
| POST | `/api/rag/ingest` | Ingest document |
| POST | `/api/rag/query` | Query RAG |
| POST | `/api/rag/search` | Search embeddings |
| POST | `/api/ragflow/search` | RAGFlow search |

#### Analytics & Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/dashboard` | Dashboard data |
| GET | `/api/analytics/agents` | Agent analytics |
| GET | `/api/analytics/tools` | Tool analytics |
| GET | `/api/audit-trail` | Audit trail |
| GET | `/api/audit-trail/stats` | Audit stats |

#### Learning System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai/learning/status` | Learning status |
| POST | `/api/ai/learning/train` | Manual training |
| GET | `/api/ai/learning/generations` | Generation history |
| GET | `/api/ai/learning/policies` | Policy inspection |
| POST | `/api/ai/learning/auto-training` | Toggle auto-training |

#### Composable Tools
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/composable/tools` | All tools |
| GET | `/api/composable/categories` | Tool categories |
| GET | `/api/composable/templates` | Composition templates |
| GET | `/api/composable/score/:toolA/:toolB` | Compatibility score |
| GET | `/api/composable/stats` | Engine stats |

#### Swarm
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/swarm/orchestrate` | Orchestrate swarm |
| POST | `/api/swarm/cost/estimate` | Cost estimate |
| PUT | `/api/swarm/cost/limits` | Set cost limits |
| POST | `/api/swarm/skills/:skillId/execute` | Execute skill |
| POST | `/api/swarm/subagents/:id/toggle` | Toggle subagent |

#### Multimodal
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/multimodal/analyze` | Analyze document |
| POST | `/api/multimodal/analyze-and-ingest` | Analyze + ingest |
| POST | `/api/multimodal/batch` | Batch analysis |
| POST | `/api/multimodal/multi-document` | Multi-doc analysis |

### Integrations (`integration.routes.ts`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/integrations/generate` | AI content generation |
| GET | `/api/integrations/generate-stream` | Streaming generation |
| POST | `/api/integrations/gamma/generate` | Gamma presentations |
| POST | `/api/integrations/sendgrid/send` | Send email |
| POST | `/api/integrations/stripe/customers` | Create Stripe customer |
| POST | `/api/integrations/stripe/payment-intents` | Payment intent |
| POST | `/api/integrations/twilio/sms` | Send SMS |
| Various | `/api/integrations/sheets/*` | Google Sheets |
| Various | `/api/integrations/slides/*` | Google Slides |
| Various | `/api/integrations/calendar/*` | Google Calendar |
| Various | `/api/integrations/meet/*` | Google Meet |

### Notifications (`notification.routes.ts`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | List notifications |
| POST | `/api/notifications` | Create notification |
| PUT | `/api/notifications/:id/read` | Mark read |
| PUT | `/api/notifications/read-all` | Mark all read |
| DELETE | `/api/notifications/:id` | Delete |
| GET | `/api/notifications/stream` | SSE stream |

### Other Domains
| Domain | Key Endpoints |
|--------|--------------|
| Tenants | CRUD at `/api/tenants/*` |
| Marketplace | CRUD + webhooks at `/api/marketplace/*` |
| Governance | Approvals at `/api/governance/*` |
| Scheduling | Event types, bookings, availability at `/api/scheduling/*` |
| Knowledge Graph | Entities, relationships at `/api/knowledge-graph/*` |
| Federated Graph | Cross-project graph at `/api/federated-graph/*` |
| Workflows | Visual workflows at `/api/workflows/*` |
| Automation | Automation workflows at `/api/automation/*` |
| Conversations | Chat history at `/api/conversations/*` |

---

## 5. AI Multi-Agent System

### Agent Definitions
Located in `server/ai/crew/agent-definitions.ts`

Each agent has: Name, Role, Goal, Backstory, Tools array, Model preference

### 20 Primary Agents

1. **Oracle** (`oracle-tools.ts`) — Strategic intelligence, document analysis, data room management, deep research with RAG
2. **Liaison** (`liaison-tools.ts`) — CRM operations, member management, meeting scheduling, activity tracking, glossary management
3. **Warden** (`warden-tools.ts`) — Security audits, access control, credential management, privacy audit logging, document ACL
4. **Engineer** (`engineer-tools.ts`) — System architecture analysis, performance optimization, infrastructure planning
5. **Prophet** (`prophet-tools.ts`) — Financial modeling, market analysis, risk assessment, Monte Carlo simulations
6. **Auditor** (`auditor-tools.ts`) — Compliance verification, document scanning, security assessment, PII detection
7. **Architect** (`architect-tools.ts`) — System design, route mapping, database analysis, tech stack evaluation
8. **Curator** (`curator-tools.ts`) — Document organization, folder management, knowledge file curation, metadata management
9. **Emissary** (`emissary-tools.ts`) — GitHub integration, Genspark research, external API management
10. **Scribe** (`scribe-tools.ts`) — Document generation (reports, memos, briefs), content authoring, template management
11. **Sentinel** (`sentinel-tools.ts`) — Real-time monitoring, anomaly detection, health checks, self-healing
12. **Chancellor** (`chancellor-tools.ts`) — Investor ledger, capital stack tracking, allocation management
13. **Designer** (`designer-tools.ts`) — UI/UX design, 3D assets, sacred geometry, brand systems, motion design
14. **Director** (`director-tools.ts`) — Project planning, milestone tracking, task delegation, timeline management
15. **Linguist** (`linguist-tools.ts`) — Text-to-speech (ElevenLabs), speech-to-text, language translation
16. **Presenter** (`presenter-tools.ts`) — Slide deck generation (Gamma.app), pitch deck creation
17. **Producer** (`producer-tools.ts`) — Video creation (Opus Clip), editing, format conversion
18. **Reporter** (`reporter-tools.ts`) — Report generation (PDF, DOCX, HTML), data visualization, spreadsheets
19. **Researcher** (`researcher-tools.ts`) — Multi-source web search, topic analysis, citation management
20. **Swarm** (`swarm-tools.ts`) — OpenClaw multi-agent orchestration, task dispatch, skill library

### 18 Sub-Agents
Defined in `server/ai/swarm/orchestrator.ts` — mirror primary agents, activated based on load, specialization match, or primary agent availability.

### Tool System
- **ToolDefinition** interface in `server/ai/types.ts`
- Each tool has: name, description, Zod input schema, execute function
- **ToolResult<T>** envelope with: success, data, error, citations, audit metadata
- Permission checks via `checkPermission()` helper
- 363+ tools total: 187 agent tools across 13 categories + 58 mineral development skills + 118 base swarm skills

### Mineral Development Skills (58 skills, 10 domains)
Registered in `server/ai/swarm/skills-library.ts` for the TRINITY-LARIVE Mineral Development Project:
- **Geological Exploration & Modeling** (8): drill program planning, core logging, geochemical assay interpretation, structural geology, 3D modeling, geophysical survey, stratigraphic correlation, alteration mapping
- **Resource Estimation & Classification** (6): NI 43-101, JORC classification, variogram modeling, kriging, sensitivity analysis, reserve conversion
- **Mining Engineering & Operations** (8): open pit design, underground planning, production scheduling, geotechnical slope, hydrogeology, equipment selection, blast optimization, ventilation
- **Metallurgy & Processing** (6): metallurgical testing, gold recovery, comminution circuit, flowsheet development, reagent analysis, tailings characterization
- **Environmental & Permitting** (6): EIA, water quality monitoring, mine closure, biodiversity, air quality, environmental permitting
- **Gold Market & Economics** (6): price forecasting, feasibility study, cashflow modeling, OpEx/CapEx estimation, hedging strategy
- **Land & Rights Management** (4): mineral rights analysis, land access negotiation, stakeholder engagement, indigenous consultation
- **Health, Safety & Compliance** (5): safety audit, hazard ID, emergency response, occupational health, regulatory compliance
- **Sovereign Gold Reserve Management** (4): custody, provenance chain, bullion QA, diversification strategy
- **Advanced Mining Analytics** (5): ML ore body analysis, predictive maintenance, digital twin, drone survey, LiDAR processing

### Council Query Flow
1. User sends prompt to `POST /api/council/query`
2. **Switchboard Router** analyzes intent and selects agent(s)
3. **Context Engineering** filters context by role with token budgets
4. **Adaptive Execution Engine** runs observe→decide→act loop
5. Agent calls tools as needed (with Circuit Breaker checks)
6. **Inter-Agent Bus** shares results between agents
7. **Cost Tracker** records spend
8. **Compliance Middleware** scans output
9. Response streamed via SSE to client

---

## 6. AI Infrastructure Components

### Adaptive Execution Engine (`adaptive-execution-engine.ts`)
- **ReAct loop:** observe → decide → act (replaces rigid workflows)
- **Self-healing:** retry / substitute / skip / abort strategies
- **Dynamic tool discovery** from goals
- **Circuit breaker-aware** tool selection
- **Policy-informed** confidence adjustment from Continuous Improvement Loop

### Circuit Breaker (`circuit-breaker.ts`)
- Per-agent error rate tracking
- States: closed → open → half-open
- 50% error rate threshold → 5-minute pause
- Limited probe recovery in half-open state

### Governance Gatekeeper (`governance-gatekeeper.ts`)
- Pre-execution cost check
- SSE-based approval workflow for tasks exceeding threshold
- Approval/rejection via admin interface

### Cost System
- **Cost Estimator** (`cost-estimator.ts`) — Token-based cost estimation per model
- **Cost Governor** (`cost-governor.ts`) — Budget enforcement with pluggable gate
- **Cost Tracker** (`cost-tracker.ts`) — Centralized spend tracking, daily/session caps
- **Swarm Cost** — Non-linear estimation, two-phase settlement, runtime guardrails

### Continuous Improvement Loop (`continuous-improvement/`)
- **SessionEvaluator** — LLM-as-Judge scoring across 6 dimensions (tool selection, recovery, cost efficiency, goal achievement, adaptation, collaboration)
- **ToolSelectionPolicyStore** — UCB-style contextual bandits with SHA-256 situation hashing and 0.95 decay
- **FractalLearningEngine** — Fibonacci spiral growth metrics tracking
- **DailyTrainingPipeline** — Scheduled batch evaluation and policy updates
- Golden-ratio (PHI-based) dimension weights for evaluation scoring

### Memory Systems
- **Mem0** (`crew/mem0.ts`) — Self-improving persistent memory with entity extraction
- **Conversation Memory** (`conversation-memory.ts`) — Full database-backed chat history
- **Agent Memories** table — Vector embeddings for semantic recall

### Knowledge & RAG
- **RAGFlow** (`crew/ragflow.ts`) — Retrieval-Augmented Generation
- **GraphRAG** (`crew/graphrag.ts`) — Knowledge Graph-based retrieval
- **Gemini Multimodal** (`crew/multimodal.ts`) — Document vision analysis
- **Drive Grounding** (`crew/drive-grounding.ts`) — Google Drive document grounding

### Agent Performance
- **Agent Profiles** (`agent-profiles.ts`) — Auto-tuning (temperature, tokens, priority)
- **Agent Evaluator** (`swarm/agent-evaluator.ts`) — Execution/Planning/Domain/Coordination scoring
- **Bayesian Optimizer** (`swarm/bayesian-optimizer.ts`) — GP-UCB parameter tuning

### Orchestration
- **LangGraph** (`crew/langgraph.ts`) — Workflow orchestration
- **Mastra** (`crew/mastra.ts`) — Composable pipeline orchestration
- **Durable Execution** (`crew/durable-execution-engine.ts`) — Temporal-style durable workflows
- **Sacred Geometry Optimizer** (`swarm/sacred-geometry-optimizer.ts`) — 21 mathematical systems: geometric scoring/scheduling + Lévy Flight, Kuramoto sync, Golden Section Search, Platonic solid topologies, Vesica Piscis consensus, Spiral optimizer

### Security
- **Privacy Router** (`crew/privacy-router.ts`) — Sensitivity classification, PII detection, redaction
- **E2E Encryption** (`crew/e2e-encryption.ts`) — RSA key pairs for message encryption
- **Compliance Middleware** (`middleware/compliance.ts`) — Output scanning and classification
- **Audit Trail** (`crew/audit-trail.ts`) — Every agent action logged with verification

### Monitoring & Analytics
- **Sentinel Service** (`sentinel-service.ts`) — Self-healing monitoring with automatic error detection and recovery
- **Streaming Analytics** (`streaming-analytics.ts`) — WebSocket-based real-time dashboard broadcasting agent metrics every 5s
- **Agent Analytics** (`agent-analytics.ts`) — Analytics aggregation for agent performance

### Communication & Context
- **Council Bus** (`council-bus.ts`) — Inter-agent communication bus for per-request context sharing

### Document & Knowledge Processing
- **Document Intelligence** (`document-intelligence.ts`) — Automated multimodal analysis on vault uploads using Gemini 2.5 Flash
- **Daily Briefing** (`daily-briefing.ts`) — Automated daily briefing generation

### Memory & Execution
- **Importance Scorer** (`importance-scorer.ts`) — Memory importance scoring for agent recall
- **Execution Tracker** (`execution-tracker.ts`) — Tracks adaptive execution state and history

### Production Infrastructure (Phase 1-4 Upgrade — Feb 2026)

#### Phase 1: Database Optimization
- 7 B-Tree indexes on `agent_executions` (agent_id, status, started_at, session_id) and `agent_tool_calls` (execution_id, tool_type, timestamp)
- Paginated storage methods: `getAgentExecutions`, `countAgentExecutions`, `getAgentToolCallsByExecution` with limit/offset

#### Phase 2: Swarm Core
- **GeometricCheckpointSystem** (`server/ai/swarm/geometric-checkpoint.ts`): DB-backed vertex anchoring via `agentExecutions.meta` jsonb with SHA-256 integrity verification
- **SacredDeltaSync** (`server/ai/swarm/sacred-delta-sync.ts`): Diff-based agent state sync with entropy threshold (auto full-state fallback at 70%), delta stats tracking
- **CreativeOrchestrator** (`server/ai/engines/creative-orchestrator.ts`): TF-IDF routing, dynamic skill acquisition, pipelined wave DAG execution

#### Phase 3: API Resilience
- Exponential backoff with jitter on all AI model API calls (OpenAI, Anthropic, Gemini, OpenRouter) — max 5 retries, 2^attempt × 1000ms + random jitter for 429/5xx errors
- Circuit breaker per-agent error rate tracking with adaptive state machine

#### Phase 4: Frontend Performance
- `useSwarmTelemetry` hook with REST polling and visualization parameter derivation
- Three.js `.dispose()` cleanup in PlatonicDance component, memoized Vector3 in other components
- Zero memory leak architecture for WebGL components

### Cost Projection Calculator
- **Backend**: `POST /api/command-center/cost-projection` — projects future costs based on historical data, model mix multipliers (economy/balanced/premium/flagship), daily task volume, and weekly growth rate
- **Frontend**: `ProjectedCostCalculator` component with interactive sliders, Recharts bar chart, and budget status warnings
- Integrated into Command Center Cost Control tab

---

## 7. Frontend Architecture

### Routing (`client/src/App.tsx`)

#### Public Routes (indexed by search engines)
| Path | Component | Description |
|------|-----------|-------------|
| `/` | ConsortiumHome | Main consortium homepage |
| `/trinity-larive` | Home | Trinity-LaRive project page |
| `/trinity-larive/request-access` | RequestAccess | Access request / login |
| `/kommunity-dao` | KommunityDAO | Kommunity DAO page |
| `/fractal-agi` | FractalAGI | Fractal AGI page |

#### Portal Routes (noindex, auth required)
| Path | Component | Description |
|------|-----------|-------------|
| `/trinity-larive/portal` | PortalDashboard | Investor dashboard |
| `/trinity-larive/portal/projects` | OurProjects | Project listing |
| `/trinity-larive/portal/data-room` | DataRoom | Document vault |
| `/trinity-larive/portal/qa` | QA | Q&A section |
| `/trinity-larive/portal/contact` | Contact | Contact form |
| `/trinity-larive/portal/admin` | AdminConsole | Admin console |
| `/trinity-larive/portal/admin/crm` | AdminCRM | Investor CRM |
| `/trinity-larive/portal/admin/knowledge-base` | KnowledgeBase | Knowledge management |

#### Admin Routes (noindex, admin only)
| Path | Component | Description |
|------|-----------|-------------|
| `/admin/command-center` | CommandCenter | Central command hub |
| `/admin/agentic-constellation` | AgenticConstellation | Agent visualization |
| `/admin/flow-builder` | FlowiseBuilder | Visual workflow builder |
| `/admin/agent-management` | AgentManagement | Agent configuration |
| `/admin/tools-catalog` | ToolsCatalog | Tool browser |
| `/admin/infrastructure-report` | InfrastructureReport | System report |
| `/admin/effects-showcase` | EffectsShowcase | UI effects demo |
| `/admin/sentinel-dashboard` | SentinelDashboard | Security monitoring |
| `/admin/execution-dashboard` | ExecutionDashboard | Execution tracking |

### Component Organization
```
client/src/components/
├── admin/        # Admin components (CouncilTerminal, KnowledgeMapGraph, etc.)
├── ai/           # AI components (InvestorChatbot, floating assistant)
├── constellation/ # Constellation chart components
├── effects/      # 21 3D visual effects (sacred geometry, fractals, neural fields, portals)
├── icons/        # Custom icon components
├── layout/       # Layout (Navigation, PortalLayout, Footer)
├── motion/       # Animation (AnimatedSection, ScrollProgress, etc.)
├── premium/      # Premium UI elements
├── sacred/       # Sacred geometry 3D components
└── ui/           # 56 shadcn/ui components
```

### Key Patterns
- **useSEO hook** — Per-page title, description, robots meta, OG tags
- **useAuth hook** — Authentication context and JWT management
- **PortalLayout** — Responsive layout with sidebar, mobile hamburger menu, context panel
- **Navigation** — Project-aware navigation with Sheet-based mobile menu
- **TanStack React Query** — All API calls use useQuery/useMutation with `/api/` query keys

### File Counts
- **Frontend:** 153 TSX/TS files across `client/src/`
- **Backend:** 163 TS files across `server/`

### Responsive Design
- Mobile-first with Tailwind breakpoints: `sm:` (640px), `md:` (768px), `lg:` (1024px)
- PortalLayout detects `isMobile` at 768px breakpoint
- Grid layouts use `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` pattern
- Decorative elements hidden on mobile: `hidden sm:flex`
- FlowiseBuilder panels hidden on mobile: `hidden md:flex`
- WCAG-compliant touch targets (`min-h-[44px]`) for accessibility
- Mobile-first breakpoints with progressive enhancement
- Overflow handling with `break-words` / `overflow-wrap` for long content

---

## 8. SEO & Crawl Control

### robots.txt (Dynamic — `server/index.ts`)
```
User-agent: *
Allow: /
Allow: /trinity-larive
Allow: /trinity-larive/request-access
Allow: /kommunity-dao
Allow: /fractal-agi

Disallow: /trinity-larive/portal/
Disallow: /admin/
Disallow: /api/

Sitemap: https://{host}/sitemap.xml
```

### sitemap.xml (Dynamic — `server/index.ts`)
5 public pages with:
- `lastmod: 2026-02-14`
- `changefreq: monthly`
- Priority: 1.0 (homepage), 0.8 (projects), 0.6 (request-access)

### Meta Tags (`client/src/hooks/useSEO.ts`)
- **Public pages:** `<meta name="robots" content="index, follow">`
- **Portal/Admin pages:** `<meta name="robots" content="noindex, nofollow">`
- Dynamic document title with " | TRINITY CONSORTIUM" suffix
- OG and Twitter Card tags per page

### index.html Head
Valid elements only per Google guidelines: title, meta, link, script. No iframe or img in head.

---

## 9. External Integrations

25 integration files in `server/integrations/`:

| Integration | File | Purpose |
|------------|------|---------|
| AI Models | `ai-models.ts` | Multi-provider AI model routing |
| Cursor Agent | `cursor-agent.ts` | Cursor Cloud agent integration |
| Data Room | `data-room.ts` | Secure data room management |
| Discord | `discord.ts` | Notifications and webhooks |
| ElevenLabs | `elevenlabs.ts` | Text-to-speech |
| Email Service | `email-service.ts` | Transactional email |
| Gamma | `gamma.ts` | Presentation generation |
| Genspark | `genspark.ts` | AI research |
| GitHub | `github.ts` | Repository management |
| Google Calendar | `google-calendar.ts` | Event management |
| Google Docs | `google-docs.ts` | Document creation |
| Google Drive | `google-drive.ts` | Document sync |
| Google Forms | `google-forms.ts` | Form management |
| Google Mail | `google-mail.ts` | Email sending |
| Google Meet | `google-meet.ts` | Meeting scheduling |
| Google Service Account | `google-service-account.ts` | Service account auth |
| Google Sheets | `google-sheets.ts` | Spreadsheet operations |
| Google Slides | `google-slides.ts` | Presentation creation |
| Linear | `linear.ts` | Issue tracking |
| LlamaIndex RAG | `llamaindex-rag.ts` | RAG pipeline |
| Notion | `notion.ts` | Knowledge management |
| Opus Clip | `opus-clip.ts` | Video processing |
| SendGrid | `sendgrid.ts` | Transactional email |
| Stripe | `stripe.ts` | Payment processing |
| Twilio | `twilio.ts` | SMS messaging |

---

## 10. Configuration & Environment

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | JWT signing secret |
| `GAMMA_APP_API_KEY` | Gamma.app API key |
| `GOLDAPI_API_KEY` | Gold price API |
| `GENSPARK_API_KEY` | Genspark AI API key |
| `OPENCLAW_GATEWAY_URL` | OpenClaw WebSocket gateway |
| `OPENCLAW_GATEWAY_TOKEN` | OpenClaw auth token |
| `CURSOR_API_KEY` | Cursor Cloud Agent |
| `OPUS_CLIP_API_KEY` | Opus Clip video API |
| `SERVICE_ACCOUNT_JSON` | Google service account |

### AI Provider Keys (Replit Integrations — auto-managed)
- `AI_INTEGRATIONS_OPENAI_API_KEY` — OpenAI
- `AI_INTEGRATIONS_ANTHROPIC_API_KEY` — Anthropic
- `AI_INTEGRATIONS_GEMINI_API_KEY` — Google Gemini
- `AI_INTEGRATIONS_OPENROUTER_API_KEY` — OpenRouter (Grok, DeepSeek, Kimi)

### Build Configuration
- `vite.config.ts` — Frontend build config
- `tsconfig.json` — TypeScript configuration
- `drizzle.config.ts` — Database migration config
- `tailwind.config.ts` — Tailwind CSS configuration

---

## 11. Deployment & Operations

### Commands
```bash
npm run dev           # Development with Vite HMR (port 5000)
npm run build         # Production build
npm run start         # Run production build
npm run db:push       # Push schema changes to database
npm run db:push --force  # Force push (destructive)
```

### Production Serving
1. Vite builds client to `dist/public/`
2. Express serves static files from `dist/public/`
3. Catch-all route serves `index.html` for SPA routing
4. API routes registered before static serving

### WebSocket Endpoints
- `/ws/analytics` — Real-time agent metrics (broadcasts every 5s)
- Various SSE endpoints for streaming responses

### Health Monitoring
- Sentinel Dashboard for real-time system monitoring
- Circuit Breaker status for agent health
- Background task queue with progress tracking
- Cost alerts when approaching budget limits

### Database Operations
- See `docs/DB_NOTES.md` for full database operational rules and guidelines

---

## 12. Known Considerations

### Architecture Notes
- Single-server deployment (API + frontend on same port)
- AI provider keys managed via Replit integrations (auto-rotated)
- Database schema uses UUID primary keys (varchar with gen_random_uuid())
- Some agent tools are "simulated" (return structured mock data) for agents that integrate with external services not yet connected

### Security Notes
- Portal routes require JWT authentication
- Admin routes require admin role
- Document access controlled via ACL system
- PII detection and redaction in AI outputs
- All agent actions logged to audit trail

### Performance Notes
- Circuit Breaker prevents cascading agent failures
- Batch Tool Executor limits concurrency to 6
- Background Task Queue handles long-running operations
- Adaptive throttling for API rate limiting
- Streaming responses for large AI outputs

### Database Notes
- 79 tables with pgvector extension for embeddings
- Schema managed via Drizzle ORM (not raw migrations)
- Use `npm run db:push` for schema sync (never manual ALTER TABLE)
- Foreign key relationships between core tables
- See `docs/DB_NOTES.md` for full database operational guidelines
