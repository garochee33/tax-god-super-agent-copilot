# Trinity Consortium Knowledge Base (Index-First)

> Purpose: a fast, grep-friendly map that lets contributors (and agents) jump to the right files without broad repo scans.
> Rule: if you change a pattern (auth, tiers, middleware, storage), you must update this index.

---

## 0. Start Here — Canonical Files

**Auth + Tiers (look here first)**
- `shared/tier-constants.ts` — canonical tiers (PUBLIC/L1/L2/L3 + A1/A2/A3/A4), labels, upgrade proofs, confidentiality mapping
- `server/auth/middleware.ts` — Express guards: requireAuth(), requireAdminTier(n), requireMemberTier(n), requirePermission()
- `server/auth/jwt.ts` — JWT sign/verify, claims: {sub, email, roles, perms, memberTier, adminTier}
- `server/auth/rbac.ts` — 6 roles (admin, investor, operator, qp, collaborator, legal), 16 permissions
- `client/src/lib/auth-context.tsx` — client auth state + role/tier interpretation
- `client/src/components/PortalGuard.tsx` — portal auth gating

**Routes**
- `server/routes.ts` — master route registration (global hooks + all domain routers)
- `server/domains/**` — 19 domain directories, 25 route files
- `client/src/App.tsx` — frontend routing map (all Route definitions)

**DB Schema**
- `shared/schema.ts` — Drizzle ORM, 85 pgTable definitions

**Storage + Vault**
- `server/storage.ts` — IStorage interface + Drizzle implementation
- `server/domains/vault/*` — document vault, ingestion, ACL, knowledge graphs

---

## 1. Canonical Access Model

```
Member tiers:  PUBLIC(0) → L1_CONFIDENTIAL(1) → L2_RESTRICTED(2) → L3_CLASSIFIED(3)
Admin tiers:   NONE(0) → A1_TEAM(1) → A2_PARTNER(2) → A3_OWNER(3) → A4_DEV(4)
```

**Single source of truth**
- Enums/constants: `shared/tier-constants.ts`
- Server enforcement: `server/auth/middleware.ts`
- Client gating: `client/src/components/PortalGuard.tsx` + `client/src/lib/auth-context.tsx`
- AI agent context: `server/ai/types.ts` → AgentContext.memberTier / AgentContext.adminTier

**Forbidden patterns (do not reintroduce)**
- `user.role === "admin"` or `roles.includes("admin")` in routes/components
- Duplicated admin guard logic outside `server/auth/*`
- Only exception: `server/domains/auth/auth.service.ts:72` (legacy safety net)
- `req.user.id` or `req.user.userId` — JWT claims use `req.user.sub` for user ID
- `parseInt(someId)` on any table ID — all IDs are varchar/string, never numeric
- `activityLog.details` — correct column is `activityLog.description`
- `documentAcl.userId` — correct column is `documentAcl.memberId`
- `documentAcl.permission` (string) — use boolean flags: `canView`, `canDownload`, `canShare`

**Document confidentiality → tier mapping**
| Confidentiality | Required |
|---|---|
| PUBLIC | memberTier ≥ 0 |
| INTERNAL | memberTier ≥ 1 |
| CONFIDENTIAL | memberTier ≥ 2 |
| STRICTLY_CONFIDENTIAL | memberTier ≥ 3 |
| TECHNICAL_RESTRICTED | adminTier ≥ 1 |

**Tier upgrade requirements**
- L1→L2: proofOfScope, proofOfRecord, proofOfIntent
- L2→L3: proofOfApproval, proofOfCompletion, proofOfCommitment
- L3→Active: proofOfStake, proofOfFunds

---

## 2. API Domain Map (server/domains/)

Each domain exposes `*.routes.ts` and optionally `*.service.ts`.

| Domain | Files | Routes | Lines | Auth Pattern |
|---|---|---|---|---|
| ai/ | ai.routes.ts, conversation.routes.ts, execution.routes.ts, sentinel.routes.ts | 176 | 4348 | adminTier(1), auth-only for conversations |
| ai (battle-mode) | `GET /api/ai/battle-mode/status` | 1 | — | adminTier(1) — Battle Mode coprocessor status and metrics |
| integrations/ | integration.routes.ts, rwa.routes.ts | 162 | 2178 | auth |
| workflows/ | workflow.routes.ts | 34 | 445 | auth |
| swarm/ | swarm.routes.ts | 37 | 960 | requirePermission("swarm:dispatch") |
| swarm (fourier-lens) | `POST /api/swarm/fourier-lens/route` | 1 | — | auth — Fourier Lens creative routing (8 agents) |
| swarm (fourier-lens) | `GET /api/swarm/fourier-lens/metrics` | 1 | — | auth — Creative router metrics |
| swarm (fourier-lens) | `POST /api/swarm/fourier-lens/route-all` | 1 | — | auth — Full-spectrum routing (all 55 agents, 7 domains) |
| swarm (fourier-lens) | `GET /api/swarm/fourier-lens/metrics-all` | 1 | — | auth — Full-spectrum metrics |
| crm/ | crm.routes.ts | 18 | 314 | adminTier(1) |
| vault/ | vault.routes.ts, federated-graph.routes.ts, knowledge-graph.routes.ts | 26 | 1181 | mixed (auth + inline adminTier) |
| marketplace/ | marketplace.routes.ts | 13 | 158 | adminTier(1) |
| agent-cost/ | agent-cost.routes.ts, agent-cost.service.ts | 12 | 129 | adminTier(1) |
| tiers/ | tier.routes.ts, ai-audit-engine.ts | 8 | 207 | mixed (adminTier 1-3 + memberTier 1) |
| auth/ | auth.routes.ts, auth.service.ts | 7 | 88 | adminTier(3) for user mgmt |
| sentinel/ | sentinel.routes.ts | 7 | 84 | adminTier(1) |
| conversation/ | conversation.routes.ts | 7 | 102 | auth |
| tenants/ | tenant.routes.ts | 6 | 108 | adminTier(1) |
| constellation/ | constellation.routes.ts | 5 | 56 | auth |
| execution/ | execution.routes.ts | 5 | 158 | inline adminTier |
| projects/ | project.routes.ts | 4 | 43 | auth |
| reporting/ | reporting.routes.ts | 4 | 165 | adminTier(1) |
| governance/ | governance.routes.ts | 4 | 91 | adminTier(1) |
| agent-executions/ | agent-executions.routes.ts | 4 | 71 | adminTier(1) |
| oracle-copilot/ | oracle-copilot.routes.ts | 2 | 303 | auth + memberTier(1) |
| compute/ | compute.routes.ts, compute-broker.service.ts | 24 | 473 | mixed (auth + adminTier(1)) |
| notifications/ | notification.routes.ts | 2 | 31 | auth |

**Non-domain routes**
- `server/routes.ts` — Stripe webhooks, daily briefing, AI learning, terrain elevation, health check
- `server/routes/data-room.ts` — 10 data room routes
- `server/replit_integrations/` — audio (1), chat (1), image (1), investor-ai (3), object_storage (2)

---

## 3. File-Purpose Index

### server/ (root)
- `index.ts` — Express bootstrap, middleware (helmet, rate-limit, compression)
- `routes.ts` — Master route registration + Stripe webhooks + health check
- `storage.ts` — IStorage interface + Drizzle implementation
- `db.ts` — PostgreSQL connection pool via Drizzle
- `seed.ts` — DB seeding (admin founder EGD33, adminTier=4, memberTier=3)
- `static.ts` — Static file serving
- `vite.ts` — Vite dev server integration

### server/auth/
- `middleware.ts` — requireAuth(), requireAdminTier(n), requireMemberTier(n), requirePermission(), requireRole()
- `jwt.ts` — JWT sign/verify, claims structure
- `rbac.ts` — Role & permission constants, role→permission mapping

### server/core/
- `errors.ts` — Error message extraction utility
- `governance.ts` — Governance rules: revenue splits, fees, fractional ownership limits

### server/integrations/ (25 files)
- `ai-models.ts` — AI model registry (9 providers, 27+ models)
- Google Workspace: `google-drive.ts`, `google-docs.ts`, `google-sheets.ts`, `google-calendar.ts`, `google-mail.ts`, `google-meet.ts`, `google-slides.ts`, `google-forms.ts`, `google-service-account.ts`
- Communication: `discord.ts`, `twilio.ts`, `sendgrid.ts`, `email-service.ts`
- Dev tools: `github.ts`, `linear.ts`, `notion.ts`, `cursor-agent.ts`
- AI/Media: `elevenlabs.ts`, `genspark.ts`, `gamma.ts`, `opus-clip.ts`
- Finance: `stripe.ts`
- Data: `data-room.ts`, `llamaindex-rag.ts`

### server/domains/compute/
- `compute.routes.ts` — 24 routes: node registration, heartbeat, task lifecycle, PBFT consensus (submit/vote/status), gossip (push/topology), CRDT (leaderboard/user stats), distributed algorithm stats
- `compute-broker.service.ts` — ComputeBrokerService: node registry, task scheduling (priority-based), trust scoring (0.98x decay), heartbeat (90s stale), PBFT/gossip/CRDT integration

### server/ai/consensus/ (3 files)
- `pbft-engine.ts` — PBFT Byzantine Fault Tolerance: HMAC-SHA256 signed votes, 3f+1 replicas, strict 2/3+ supermajority, pre-prepare/prepare/commit phases, trust adjustment (1.02x boost / 0.95x penalty)
- `gossip-engine.ts` — Push-pull gossip protocol: decentralized node discovery, monotonic version-gated state, random fanout (default 3), 10s loop, 5-min stale pruning
- `crdt-engine.ts` — CRDTs: GCounter (grow-only), PNCounter (pos/neg), LWWRegister (last-writer-wins), CRDTContributionLedger combining all for conflict-free distributed state

### server/ai/compute-integration.ts
- AI agent bridge to distributed compute pool with automatic local server fallback

### server/ai/ (110 files total)
- **21 agent tool files**: `{role}-tools.ts` pattern (analyst, architect, auditor, chancellor, curator, designer, director, emissary, engineer, liaison, linguist, oracle, presenter, producer, prophet, reporter, researcher, scribe, sentinel, swarm, warden)
- **Core infra** (~40 files): types.ts, index.ts, prompts.ts, execution-tracker.ts, cost-governor.ts, cost-estimator.ts, cost-tracker.ts, adaptive-execution-engine.ts, circuit-breaker.ts, consensus-algorithm.ts, trust-scoring.ts, frequency-router.ts, harmonic-load-balancer.ts, algorithm-engine.ts, performance-metrics.ts, governance-gatekeeper.ts, council-bus.ts, batch-executor.ts, background-task-queue.ts, importance-scorer.ts, sentinel-service.ts, structural-audit.ts, document-intelligence.ts, cloud-compute-service.ts, composable-tool-engine.ts, context-retrieval.ts, task-decomposition.ts, output-validation.ts, conversation-memory.ts, streaming-analytics.ts, agent-analytics.ts, agent-marketplace.ts, agent-profiles.ts, daily-briefing.ts, design-live-backends.ts, federated-knowledge-graph.ts, openclaw-service.ts, openclaw-cost-estimator.ts, execution-logger.ts
- **Swarm cost**: swarm-adaptive-throttle.ts, swarm-cost-instrumentation.ts, swarm-cost-planner.ts, swarm-guardrails.ts
- **crew/** (23 files): agent-definitions.ts, agent.ts, crew.ts, ragflow.ts, multimodal.ts, graphrag.ts, mem0.ts, langgraph.ts, mastra.ts, dspy-optimizer.ts, mcp-server.ts, memory.ts, scheduling-service.ts, marketplace-service.ts, drive-grounding.ts, durable-execution-engine.ts, automation-engine.ts, e2e-encryption.ts, audit-trail.ts, notifications.ts, privacy-router.ts, index.ts, types.ts
- **engines/** (5): generative-art-engine.ts, sacred-geometry-engine.ts, shader-library.ts, creative-orchestrator.ts (v3.0 — dynamic skill acquisition with pipelined wave execution; agents learn new keywords from successful tasks and persist them to DB via `agent_skill_profiles` table; stream-based DAG execution replaces blocking wave batches — tasks start as soon as their dependencies resolve; TF-IDF routing upgraded to Fourier Lens semantic signal processing using DFT on OpenAI text-embedding-3-small (1536-dim → 768 Nyquist limit) with φ-harmonic agent resonance signatures; 7 Nyquist-safe domains: Security (20-60Hz), Data (70-150Hz), Finance (160-280Hz), Operations (290-380Hz), Communication (390-480Hz), Creative (490-600Hz), Technical (610-750Hz)), fourier-lens-router.ts — DFT-based semantic signal processing for agent routing; SwarmFourierLensRouter — 64 agent signatures (55 unique agents with dual-ID aliases) across 7 frequency domains
- **swarm/** (13): orchestrator.ts, bayesian-optimizer.ts, genetic-optimizer.ts, sacred-geometry-optimizer.ts, agent-evaluator.ts, communication-bus.ts, cost-optimizer.ts, skills-library.ts, delta-sync.ts, sacred-delta-sync.ts, checkpoint-manager.ts, battle-mode-coprocessor.ts, geometry-worker.ts
- **Battle Mode Math Coprocessor**: `battle-mode-coprocessor.ts` — Worker thread manager for O(N) Kuramoto sync; `geometry-worker.ts` — Dedicated Worker thread for Mean Field Order Parameter computation. O(N) Mean Field Kuramoto synchronization via dedicated Worker thread, replacing O(N²) pairwise coupling for real-time 55-agent coordination
- **Incremental Delta Sync**: `server/ai/swarm/delta-sync.ts` — versioned agent state with diff-based updates, circular changelog (100 entries), subscriber model, auto-fallback to full resync. Enhanced by `server/ai/swarm/sacred-delta-sync.ts` — sacred harmonic delta engine with deep recursive diffing, SHA-256 resonance signatures, entropy reset threshold, and null-signal deletion handling
- **Checkpoint-Based Recovery**: `server/ai/swarm/checkpoint-manager.ts` — task state checkpointing with TTL (30 min), phase-aware resume for collaborative/delegated/sequential/parallel strategies, cost tracking
- **continuous-improvement/** (5): session-evaluator.ts, policy-store.ts, daily-training-pipeline.ts, fractal-learning-engine.ts, index.ts
- **middleware/**: compliance.ts (PII redaction)

### shared/
- `schema.ts` — 85 Drizzle table definitions + insert schemas + types
- `tier-constants.ts` — Tier enums, labels, metals, colors, upgrade requirements, access helpers
- `models/chat.ts` — Chat message types

---

## 4. Database Tables (85 tables in shared/schema.ts)

**Core**: members, users, investors, projects, projectMemberships, tenants, workspaceMembers
**Auth**: memberCredentials, aiAuditScores, tierUpgradeRequests, auditTrail, privacyAuditLogs
**Vault**: documents, vaultDocuments, documentAcl, documentAccessLog, documentFolders, documentIngestionJobs, documentViewerSessions, documentVisualMetadata, memberDocumentPermissions, embeddings, knowledgeFiles
**AI agents**: agentExecutions, agentToolCalls, agentMemories, agentPerformanceMetrics, agentPreferences, agentPresets, agentTrustScores, agentCostSessions, agentCostUsers, agentCostActions, agentCostAlerts, promptOptimizations, sessionEvaluations, toolSelectionPolicies, sentinelHealingEvents, agentSkillProfiles
**Graph**: graphEntities, graphRelationships, constellationNodes, constellationEdges
**CRM**: tasks, taskQueues, meetings, bookings, availabilityWindows, eventTypes, notifications, messageThreads, encryptedMessages, encryptionKeys, memberActivity, activityLog
**Marketplace**: marketplaceConnectors, marketplaceInstalls, marketplaceWebhookEvents
**Workflows**: workflows, durableWorkflows, durableActivities, workflowSignals, automationWorkflows, automationExecutions, visualWorkflows, backgroundTasks
**RWA**: rwaAssets, rwaAssetTokens, rwaOrders, rwaPortfolios, rwaTransactions
**Integrations**: driveSyncConfigs, driveSyncedFiles, investorWorkspaces
**Governance**: swarmLedger, reportingDashboards, learningGenerations
**Compute**: computeNodes, computeTasks, computeContributions, computeNetworkStats (4 tables, 11 indexes)
**Content**: technicalGlossary

---

## 5. Frontend Route Map

**Router**: `client/src/App.tsx`
**Auth guard**: `client/src/components/PortalGuard.tsx`

### Public (no auth)
- `/` → ConsortiumHome
- `/trinity-larive` → Home
- `/trinity-larive/request-access` → RequestAccess
- `/kommunity-dao` → KommunityDAO
- `/fractal-agi` → FractalAGI

### Portal (auth + PortalGuard)
- `/trinity-larive/portal` → PortalDashboard
- `/trinity-larive/portal/projects` → OurProjects
- `/trinity-larive/portal/data-room` → DataRoom
- `/trinity-larive/portal/parcel-map` → ParcelMap
- `/trinity-larive/portal/geological` → GeologicalPortal
- `/trinity-larive/portal/qa` → QA
- `/trinity-larive/portal/contact` → Contact
- `/trinity-larive/portal/compute` → ComputeSettingsPage

### Admin Portal (auth + admin)
- `/trinity-larive/portal/admin` → AdminConsole
- `/trinity-larive/portal/admin/crm` → AdminCRM
- `/trinity-larive/portal/admin/knowledge-base` → KnowledgeBase

### Command Center (auth + admin)
- `/admin/command-center` → CommandCenter
- `/admin/tier-management` → TierManagement
- `/admin/agent-management` → AgentManagement
- `/admin/tools-catalog` → ToolsCatalog
- `/admin/agent-cost-monitor` → AgentCostMonitor
- `/admin/reporting-dashboard` → ReportingDashboard
- `/admin/sentinel-dashboard` → SentinelDashboard
- `/admin/execution-dashboard` → ExecutionDashboard
- `/admin/infrastructure-report` → InfrastructureReport
- `/admin/agentic-constellation` → AgenticConstellation
- `/admin/sacred-constellation` → SacredConstellation
- `/admin/document-constellation` → DocumentConstellation
- `/admin/flow-builder` → FlowiseBuilder
- `/admin/fractal-orchestration` → FractalOrchestration
- `/admin/infographic-dashboard` → InfographicDashboard
- `/admin/generative-art` → GenerativeArtGallery
- `/admin/sacred-geometry` → SacredGeometryGallery
- `/admin/fourier-lens` → FourierLensVisualization
- `/admin/effects-showcase` → EffectsShowcase

---

## 6. Grep Hooks (exact patterns for fast lookup)

**Security**
- `requireAdminTier(` — admin tier enforcement
- `requireMemberTier(` — member tier enforcement
- `requireAuth()` — JWT auth guard
- `requirePermission(` — permission-based guard
- `adminTier` — tier references in any file
- `memberTier` — tier references in any file
- `PortalGuard` — client auth gating
- `canAccessConfidentiality` — document access check

**Vault**
- `/api/vault/` — vault API endpoints
- `documentAcl` — document access control
- `memberDocumentPermissions` — member doc permissions
- `documentAccessLog` — access logging

**AI**
- `/api/ai/` — AI API endpoints
- `AgentContext` — agent execution context type
- `governance-gatekeeper` — cost approval
- `cost-governor` — budget enforcement
- `switchboard` — agent routing
- `swarmFourierRouter` — full-spectrum Fourier routing
- `fourierRouter` — creative Fourier routing
- `battle-mode-coprocessor` — O(N) Kuramoto sync

**Compute Cooperative**
- `computeBroker` — distributed compute broker service
- `pbftEngine` — PBFT consensus engine singleton
- `gossipEngine` — gossip protocol engine singleton
- `contributionLedger` — CRDT contribution ledger singleton
- `/api/compute/` — compute cooperative API endpoints
- `compute-integration.ts` — AI agent bridge to compute pool

**Database**
- `pgTable` — table definitions in schema.ts
- `createInsertSchema` — insert schema generation

---

## 7. Update Rules

When you modify:
- **Tiers / RBAC** → update sections 0–1 + add grep hooks if new helpers introduced
- **Domains / routes** → update section 2 (domain table) + section 6 (grep hooks)
- **DB schema** → update section 4 (table list), note new tables
- **AI agents** → update section 3 (server/ai/ listing)
- **Frontend pages** → update section 5 (route map)
- **Auth middleware** → update sections 0–1

---

## 8. AI Providers (9 Providers, 27+ Models)

- OpenAI (GPT-5.2, GPT-5.1, GPT-5, GPT-5-mini, O4 Mini, GPT-4.1, GPT-4.1 Mini)
- Google Gemini (Gemini 3 Pro Preview, Gemini 3 Flash Preview, Gemini 2.5 Pro, Gemini 2.5 Flash)
- Anthropic Claude (Claude Opus 4.5, Claude Sonnet 4.5, Claude Haiku 4.5)
- xAI Grok (Grok 3, Grok 3 Mini via OpenRouter)
- DeepSeek (DeepSeek V3.2 via OpenRouter)
- Moonshot Kimi (Kimi K2.5 via OpenRouter)
- Genspark AI (Deep Research, Document AI, Code Ops, Vision AI)
- OpenClaw Swarm (Task Dispatch, Multi-Agent Swarm, Skill Library)
- Replit AI (Code Intelligence, Replit Agent)

---

## 9. KOMMUNITY DAO Integration

**Vault**: White Paper 2025 ingested (Doc ID: e6eb0e7a-5a75-4329-8fba-f00b8b196117, Project: 704ff0f5-dbb4-48b0-9c79-cf65f8a7cd71). PDF at `.private/KOMMUNITY_WHITE_PAPER_2025.pdf` (11.3 MB).

**Public page** (`/kommunity-dao`): Sanitized — wellness/sustainability/community only. NO blockchain/token supply/RFID/DAO governance.

**Portal sections** (9 tabs at `/trinity-larive/portal/projects`): Full white paper content — overview, tokenomics, ecosystem, sustainability, governance, rewards, strategy, mission, CTA.

**Internal data** (portal only): Dual-token LIFE+HUB, Ethereum DAO governance, RFID Key membership, 12+ global hubs.

---

## 10. Data Room Inventory (23 documents, 7 categories)

**Corporate** (5): Board Composition, Governance Framework, JV Agreement Summary, Executive Summary, Trust Structure Overview
**Financial** (3): Capital Structure Overview, Cost Estimates, Use of Funds Summary
**Geological** (6): 1997 QP Report, 2006 CPG Report, 2023 Topographic Survey, 2024 Independent Review, LaRive Parcels KML, USGS Geologic Maps M-77/M-78
**Legal** (4): Chain of Title Summary, Survey No. 5797, Title Insurance Policy, U.S. Mineral Patent #86663
**Marketing** (1): KOMMUNITY White Paper 2025
**Reference** (2): ALS Geochemistry Fee Schedule 2025, Documentation Transfer Guide
**Technical** (2): Sprint Planning Quick Reference, NI 43-101 Technical Report

**Features**: 9 categories, 3 view modes (list/grid/master index), admin upload + auto-ingestion, full-text search, ACL, session-based secure viewer with watermarking.
