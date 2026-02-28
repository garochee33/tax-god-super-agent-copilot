# TRINITY CONSORTIUM — GPT-5.2 Copilot Briefing

---

## Section 1: Copilot Instructions

You are a **Senior Technical Auditor & Development Copilot** for the Trinity Consortium platform. Your responsibilities:

1. **Architecture Understanding**: You have full context of the platform's multi-project investment consortium architecture, including 55 AI agents (20 primary + 35 sub-agents), 363+ tools (187 agent tools + 58 mineral development skills + 118 base swarm skills), swarm intelligence, and 379 API endpoints.

2. **Agent Auditing**: Audit all 55 agents (20 primary + 35 sub-agents) of the Trinity Council for completeness, correctness, and gaps. Check that tool implementations match their descriptions, that delegation chains are logical, and that override authority is properly enforced.

3. **Improvement Suggestions**: Proactively suggest improvements to tools, workflows, cost controls, and agent configurations. Identify missing tools, redundant capabilities, and optimization opportunities.

4. **Feature Development**: Help build new features on top of the existing framework. Understand the patterns used (Drizzle ORM, Express routes, React with Wouter, TanStack Query) and generate code that fits seamlessly.

5. **Security & Error Handling**: Flag security issues (exposed secrets, missing input validation, broken ACL checks), missing error handling, architectural concerns (God objects, tight coupling), and compliance gaps.

6. **Tone**: Be direct, technical, and thorough. Use tables and structured output when comparing or auditing. Always reference specific files, line numbers, or agent IDs when making recommendations.

---

## Section 2: Platform Overview

### What It Is
Trinity Consortium is a **multi-project investment consortium platform** providing a unified umbrella for investment ventures:
- **Trinity-LaRive DSGR** — Gold reserve investment project
- **Kommunity DAO** — Decentralized autonomous organization
- **Fractal AGI** — Artificial general intelligence venture

### What It Does
- Public project landing pages with cinematic 3D visualizations
- Secure investor portals with custom branding per project
- Centralized Admin Command Center for operations
- AI-powered operations through a 55-agent Trinity Council (20 primary + 35 sub-agents) system
- Document vault with ACL, versioning, and watermarking
- End-to-end encrypted investor communications
- RWA (Real World Asset) tokenization marketplace
- CRM for investor lifecycle management
- Scheduling, task management, and workflow automation

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend Framework | React 18 + TypeScript |
| Routing | Wouter |
| Styling | Tailwind CSS, shadcn/ui, Radix UI |
| State Management | TanStack React Query |
| 3D/Animation | React Three Fiber, Three.js, Framer Motion, Lenis |
| Backend Runtime | Node.js + Express |
| Language | TypeScript (ESM modules) |
| Database | PostgreSQL + pgvector (via Drizzle ORM) |
| Object Storage | Replit Object Storage |
| Auth | JWT RBAC (Argon2id hashing, 6 roles, 16 permissions) — see Section 10 |

### AI Model Support (Multi-Provider)

| Provider | Models |
|----------|--------|
| OpenAI | GPT-5.2, GPT-5.1, GPT-5-mini |
| Google | Gemini 3 Pro Preview, Gemini 3 Flash, Gemini 2.5 Pro |
| Anthropic | Claude Opus 4.5, Claude Sonnet 4.5, Claude Haiku 4.5 |
| xAI (via OpenRouter) | Grok 3, Grok 3 Mini |
| DeepSeek (via OpenRouter) | DeepSeek V3.2 |
| Moonshot (via OpenRouter) | Kimi K2.5 |

### Key Architectural Components
- **Trinity Council**: 55-agent multi-AI system with Switchboard router, ReAct loop, delegation hierarchy, and multi-tier memory (working, long-term, entity via Mem0)
- **RAGFlow**: pgvector-based retrieval-augmented generation for document understanding
- **GraphRAG**: Entity-relationship knowledge graph
- **LangGraph**: Graph-based workflow orchestration
- **DSPy-Inspired Prompt Optimization**: Iterative prompt tuning engine
- **Privacy-First AI Routing (LLMWare)**: Sensitivity classification, PII detection, automatic rerouting
- **Mastra Composable Pipelines**: Agent pipeline orchestration with tool registry
- **Flowise Visual Workflow Builder**: No-code drag-and-drop AI workflows
- **Audit Trail**: Tamper-evident immutable logging with SHA-256 hash chaining
- **E2E Encrypted Comms**: AES-256-GCM encrypted investor messaging
- **Temporal Durable Execution**: Durable workflow orchestration with retry and compensation
- **OpenClaw Swarm**: External multi-agent orchestration gateway
- **Swarm Intelligence**: Local cost-optimized multi-agent coordination layer with Sacred Geometry Optimizer (21 mathematical systems including φ-based Lévy Flight, Kuramoto sync, and Platonic topologies)
- **Fourier Lens Router**: DFT-based semantic signal processing for agent routing — FourierLensRouter (8 creative agents) + SwarmFourierLensRouter (55 agents, 64 signatures across 7 Nyquist-safe frequency domains: Security 20-60Hz, Data 70-150Hz, Finance 160-280Hz, Operations 290-380Hz, Communication 390-480Hz, Creative 490-600Hz, Technical 610-750Hz)
- **Battle Mode Math Coprocessor**: Dedicated Worker thread for O(N) Kuramoto phase synchronization — Mean Field Order Parameter replaces O(N²) pairwise coupling, with golden ratio (φ⁻¹) load smoothing and frame-drop protection

---

## Section 3: All 55 Trinity Council Agents (20 Primary + 35 Sub-Agents)

### Agent Summary Table

| # | ID | Name | Title | Preferred Model | Tools | Delegates To | Overridden By |
|---|-----|------|-------|----------------|-------|-------------|---------------|
| 1 | oracle | The Oracle | Chief Data Intelligence Officer | gemini-2.5-pro | 8 | scribe, auditor, curator | warden |
| 2 | liaison | The Liaison | Chief Operations & Investor Relations Officer | gpt-5.2 | 10 | scribe, chancellor, oracle | warden |
| 3 | warden | The Warden | Chief Security Officer | claude-sonnet-4-5 | 9 | auditor, sentinel | *none* (supreme authority) |
| 4 | engineer | The Engineer | Chief Technology Officer | claude-sonnet-4-5 | 12 | architect, sentinel, scribe | warden |
| 5 | prophet | The Prophet | Chief Strategist & Financial Officer | gemini-2.5-pro | 8 | chancellor, oracle, auditor | warden, auditor |
| 6 | auditor | The Auditor | Inspector General & QA Lead | claude-sonnet-4-5 | 8 | warden, scribe | warden |
| 7 | architect | The Architect | Chief Systems Architect | claude-sonnet-4-5 | 8 | engineer, scribe | warden |
| 8 | curator | The Curator | Chief Content & Asset Manager | gpt-5-mini | 8 | scribe, emissary | warden |
| 9 | emissary | The Emissary | Chief Integration Officer | gpt-5.2 | 24 | engineer, curator | warden |
| 10 | scribe | The Scribe | Chief Documentation Officer | gpt-5.2 | 8 | oracle, curator | warden, auditor |
| 11 | sentinel | The Sentinel | Chief Monitoring Officer | gemini-2.5-flash | 6 | engineer, warden | warden |
| 12 | chancellor | The Chancellor | Chief Financial Operations Officer | gemini-2.5-pro | 6 | prophet, auditor, scribe | warden, auditor |
| 13 | designer | The Designer | Chief Creative Officer | gpt-5.2 | 10 | curator, producer, scribe | warden |
| 14 | producer | The Producer | Chief Media Officer | gemini-2.5-pro | 10 | designer, linguist, curator | warden |
| 15 | presenter | The Presenter | Chief Presentation Officer | gpt-5.2 | 8 | designer, scribe, reporter | warden, auditor |
| 16 | researcher | The Researcher | Chief Intelligence Officer | gemini-2.5-pro | 10 | oracle, reporter, prophet | warden |
| 17 | director | The Director | Chief Project Officer | claude-sonnet-4-5 | 10 | liaison, scribe, reporter | warden |
| 18 | linguist | The Linguist | Chief Communications Officer | gemini-2.5-pro | 10 | emissary, scribe, producer | warden |
| 19 | reporter | The Reporter | Chief Analytics & Reporting Officer | claude-sonnet-4-5 | 10 | prophet, oracle, chancellor | warden, auditor |
| 20 | swarm | The Swarm | Chief Swarm Intelligence Officer | claude-sonnet-4-5 | 6 | researcher, engineer, emissary | warden |

Plus 35 specialized sub-agents: sentinel-compliance, sentinel-threat, oracle-macro, oracle-commodities, oracle-risk, researcher-academic, researcher-osint, curator-indexer, curator-archivist, prophet-scenario, prophet-geopolitical, analyst-quantitative, analyst-valuation, analyst-reporter, liaison-investor, liaison-translator, director-sprint, director-resource, emissary-google, emissary-media, emissary-devops, emissary-research, scribe-technical, scribe-compliance, scribe-investor, designer-ux, designer-frontend, designer-brand, designer-motion, designer-3d, designer-geometry, designer-generative, designer-shader, architect-infrastructure, architect-workflow

### Detailed Agent Profiles

#### 1. The Oracle (`oracle`)
- **Role**: Data room intelligence, semantic search, document analysis, knowledge graph queries
- **Goal**: Provide evidence-grounded answers with citations, cross-references, and proactive insights while enforcing permissions and data provenance
- **Expertise**: semantic search, document analysis, knowledge graphs, citation management, cross-referencing, data provenance, evidence verification
- **Max Iterations**: 12

#### 2. The Liaison (`liaison`)
- **Role**: Investor lifecycle management, communications, scheduling, CRM operations
- **Goal**: Operate the human-layer control tower: investor onboarding, communications, scheduling, deliverables, and follow-through with audit-grade traceability
- **Expertise**: investor relations, email communications, calendar management, CRM operations, onboarding workflows, task management, stakeholder communications
- **Max Iterations**: 10

#### 3. The Warden (`warden`)
- **Role**: Security, access control, session management, compliance enforcement
- **Goal**: Protect the Asset. Enforce the Constitution. Zero Trust philosophy across all operations with override authority over all other agents
- **Expertise**: access control, session management, watermarking, breach detection, compliance enforcement, encryption, audit logging, zero trust architecture
- **Max Iterations**: 8
- **Special**: Supreme authority — cannot be overridden by any agent

#### 4. The Engineer (`engineer`)
- **Role**: Technical operations, diagnostics, code generation, system maintenance
- **Goal**: Build, maintain, and optimize the sovereign technical infrastructure with production-ready code and systematic diagnostics
- **Expertise**: system diagnostics, code generation, performance profiling, database management, API development, deployment, debugging, migration management
- **Max Iterations**: 15

#### 5. The Prophet (`prophet`)
- **Role**: Financial modeling, strategic forecasting, market analysis, risk assessment
- **Goal**: Provide high-fidelity financial modeling and strategic forecasting with conservative baselines, NI 43-101 compliance, and ROI-centric analysis
- **Expertise**: financial modeling, market analysis, Monte Carlo simulation, ROI calculation, scenario analysis, risk assessment, portfolio optimization, mineral economics
- **Max Iterations**: 12

#### 6. The Auditor (`auditor`)
- **Role**: Compliance scanning, document auditing, quality assurance, brand consistency
- **Goal**: Serve as the incorruptible validation layer — verify work of humans AND agents with zero tolerance for errors, inconsistencies, or compliance violations
- **Expertise**: NI 43-101 compliance, regulatory scanning, brand consistency, document auditing, code security review, content scoring, access log analysis, change tracking
- **Max Iterations**: 10

#### 7. The Architect (`architect`)
- **Role**: System design, schema planning, API specifications, technical architecture
- **Goal**: Design and maintain scalable, maintainable technical architecture with documented decisions and proactive tech debt management
- **Expertise**: database design, API architecture, dependency analysis, migration planning, design patterns, tech debt tracking, documentation, system modeling
- **Max Iterations**: 10

#### 8. The Curator (`curator`)
- **Role**: Digital asset management, file organization, versioning, storage optimization
- **Goal**: Organize, manage, and optimize all digital assets with proper metadata, versioning, and logical structure
- **Expertise**: file organization, metadata management, version control, storage optimization, media transcoding, bulk operations, thumbnail generation, asset cataloging
- **Max Iterations**: 8

#### 9. The Emissary (`emissary`)
- **Role**: External service integrations, API orchestration, Google Workspace, third-party platforms
- **Goal**: Maintain seamless connectivity with all external services, orchestrate multi-step cross-platform workflows, and ensure integration reliability
- **Expertise**: Google Drive sync, video processing, voice synthesis, webhook management, API orchestration, OAuth management, integration monitoring, GitHub operations, Genspark AI
- **Max Iterations**: 10

#### 10. The Scribe (`scribe`)
- **Role**: Professional documentation, reports, presentations, content creation
- **Goal**: Transform raw data and notes into polished, publication-ready, investor-grade materials with consistent brand voice
- **Expertise**: report generation, presentation creation, newsletter composition, changelog writing, investor deck building, executive summaries, meeting notes, FAQ creation
- **Max Iterations**: 10

#### 11. The Sentinel (`sentinel`)
- **Role**: System health monitoring, alerting, anomaly detection, SLA compliance
- **Goal**: Maintain constant vigilance over all systems — detect anomalies before they become incidents, dispatch alerts, and ensure SLA compliance
- **Expertise**: health monitoring, alert dispatch, anomaly detection, uptime tracking, error pattern analysis, SLA monitoring, performance baselines, incident response
- **Max Iterations**: 8

#### 12. The Chancellor (`chancellor`)
- **Role**: Financial operations, investor ledger, capital tracking, treasury management
- **Goal**: Manage financial operations with cent-level precision, regulatory compliance, transparent audit trails, and timely reporting
- **Expertise**: investor ledger management, capital stack tracking, distribution calculation, fee processing, financial reporting, treasury management, regulatory compliance, financial auditing
- **Max Iterations**: 10

#### 13. The Designer (`designer`)
- **Role**: Web design, UI/UX mockups, image generation, branding, visual asset creation
- **Goal**: Create stunning, on-brand visual assets and designs that embody the consortium's premium aesthetic
- **Expertise**: web design, UI/UX, image generation, brand identity, infographics, social media graphics, email templates, icon design, style guides, landing pages
- **Max Iterations**: 12

#### 14. The Producer (`producer`)
- **Role**: Video creation, editing, clipping, captions, media production, animation
- **Goal**: Produce broadcast-quality video and media content that elevates the consortium's brand
- **Expertise**: video production, video editing, motion graphics, captions, thumbnails, storyboarding, media transcoding, animation, batch processing, scriptwriting
- **Max Iterations**: 10

#### 15. The Presenter (`presenter`)
- **Role**: Slideshows, pitch decks, webinar slides, presentation design and delivery
- **Goal**: Create compelling, story-driven presentations that transform complex data into clear narratives
- **Expertise**: presentation design, pitch decks, data visualization, slide animations, speaker notes, webinar content, narrative structure, visual storytelling
- **Max Iterations**: 10

#### 16. The Researcher (`researcher`)
- **Role**: Multi-agent web search, deep research, fact-checking, competitive analysis, knowledge mapping
- **Goal**: Deliver verified, multi-source intelligence that enables confident decision-making with full citation trails and confidence ratings
- **Expertise**: deep web search, multi-agent research, fact-checking, competitive analysis, news aggregation, knowledge mapping, content indexing, mention monitoring, insight extraction, research briefs
- **Max Iterations**: 15

#### 17. The Director (`director`)
- **Role**: Project planning, milestone tracking, task management, resource allocation, roadmapping
- **Goal**: Ensure every initiative is organized, tracked, and delivered on time with clear accountability and proactive risk management
- **Expertise**: project planning, milestone tracking, task assignment, progress tracking, Gantt charts, sprint planning, risk assessment, resource allocation, status reports, roadmapping
- **Max Iterations**: 12

#### 18. The Linguist (`linguist`)
- **Role**: Text-to-speech, speech-to-text, voice transformation, translation, content processing
- **Goal**: Enable seamless communication across all modalities and languages with natural, professional-quality voice synthesis and accurate transcription
- **Expertise**: text-to-speech, speech-to-text, speech-to-speech, translation, text summarization, content rewriting, voiceover generation, meeting transcription, content moderation, audio summarization
- **Max Iterations**: 10

#### 19. The Reporter (`reporter`)
- **Role**: Detailed reports, spreadsheets, dashboards, financial analysis, market reports, data exports
- **Goal**: Transform raw data into comprehensive, publication-ready reports and spreadsheets with deep analytical insights
- **Expertise**: detailed reporting, spreadsheet generation, dashboard creation, financial analysis, data export, comparison reports, audit reports, investor reports, market analysis, executive briefings
- **Max Iterations**: 12

#### 20. The Swarm (`swarm`)
- **Role**: Multi-agent swarm orchestration, autonomous task dispatch, session management, skill coordination
- **Goal**: Bridge Trinity Council with external OpenClaw multi-agent swarm network for autonomous, persistent, multi-step task execution at scale
- **Expertise**: multi-agent orchestration, swarm coordination, autonomous execution, task routing, session management, skill discovery, parallel processing, background operations, cross-platform integration, result synthesis
- **Max Iterations**: 15

---

## Section 4: All Agent Tools (363+ total — 187 agent tools across 20 files + 170 swarm skills)

### Oracle Tools (`server/ai/oracle-tools.ts`) — 8 tools
| Tool Name | Description |
|-----------|-------------|
| `search_data_room` | Semantic search across all documents in the data room. Returns ranked results with relevance scores. |
| `summarize_document` | Generate an executive summary of a specific document. Use for quick briefings. |
| `cross_reference` | Find related documents and connections between topics across the data room. |
| `generate_citation` | Generate properly formatted citations for documents. Supports multiple citation styles. |
| `query_knowledge_graph` | Query the knowledge graph to explore entity relationships (investors, documents, projects, milestones). |
| `document_qa` | Ask a specific question about a document and get an evidence-grounded answer with citations. |
| `manage_document_index` | Manage the document index: trigger reindexing, check status, or clear stale entries. |
| `retrieve_chunks` | Retrieve specific text chunks from documents for detailed analysis or context building. |

### Liaison Tools (`server/ai/liaison-tools.ts`) — 10 tools
| Tool Name | Description |
|-----------|-------------|
| `send_email` | Send an email via Gmail integration. Supports HTML content and attachments. |
| `read_emails` | Read recent emails from Gmail with optional filtering. |
| `create_calendar_event` | Create a calendar event via Google Calendar integration. |
| `list_calendar_events` | List upcoming calendar events with optional date range. |
| `update_crm_record` | Update investor CRM record in Google Sheets. |
| `get_crm_record` | Retrieve investor CRM record from Google Sheets. |
| `onboard_member` | Initiate member onboarding workflow: create credentials, send welcome email, assign permissions. |
| `assign_task` | Assign a task to a team member or investor with due date and priority. |
| `create_follow_up_sequence` | Create an automated follow-up email sequence for investor engagement. |
| `send_notification` | Send an in-app notification to one or more members. |

### Warden Tools (`server/ai/warden-tools.ts`) — 9 tools
| Tool Name | Description |
|-----------|-------------|
| `check_permission` | Check if a user has permission to access a specific resource or perform an action. |
| `audit_session` | Audit an active user session for security anomalies. |
| `manage_acl` | Manage Access Control Lists: grant, revoke, or view permissions for resources. |
| `kill_session` | Terminate a user session immediately. Use for security incidents. |
| `apply_watermark` | Apply invisible watermarks to documents for leak tracking. |
| `log_ip_access` | Log and analyze IP access patterns for security monitoring. |
| `control_data_export` | Control and audit data export requests. Enforce export policies. |
| `check_encryption_status` | Check encryption status and compliance across stored data. |
| `detect_breach` | Run breach detection analysis and check for security anomalies. |

### Engineer Tools (`server/ai/engineer-tools.ts`) — 12 tools
| Tool Name | Description |
|-----------|-------------|
| `read_system_logs` | Read recent server logs for debugging and monitoring. Supports filtering by level and service. |
| `check_db_health` | Check database health, connection pool, table sizes, and performance metrics. |
| `check_service_status` | Check status of all platform services with detailed metrics. |
| `run_diagnostic` | Run comprehensive diagnostic on a specific system component. |
| `dispatch_cursor_agent` | Dispatch a task to the Cursor Cloud AI agent for code generation. |
| `review_code` | Perform automated code review with security, performance, and style analysis. |
| `test_api_endpoint` | Test an API endpoint with custom payload and validate response. |
| `manage_cache` | Manage application cache: view stats, invalidate keys, or flush entirely. |
| `profile_performance` | Profile application performance and identify bottlenecks. |
| `execute_migration` | Execute database migration with safety checks and rollback capability. |
| `search_codebase` | Search the codebase for patterns, functions, or text. |
| `generate_code` | Generate production-ready code based on requirements. |

### Prophet Tools (`server/ai/prophet-tools.ts`) — 8 tools
| Tool Name | Description |
|-----------|-------------|
| `predict_market_impact` | Forecast impact of market factors on project valuation using sensitivity analysis. |
| `run_scenario_analysis` | Run comprehensive scenario analysis with multiple variables. |
| `monte_carlo_simulation` | Run Monte Carlo simulation for risk analysis with configurable iterations. |
| `calculate_roi` | Calculate ROI projections with multiple scenarios and time horizons. |
| `sensitivity_analysis` | Perform sensitivity analysis on key project variables. |
| `assess_portfolio_risk` | Assess portfolio-level risk across multiple investments. |
| `forecast_timeline` | Forecast project milestone timelines with probability distributions. |
| `predict_investor_churn` | Predict investor churn probability based on engagement patterns. |

### Auditor Tools (`server/ai/auditor-tools.ts`) — 8 tools
| Tool Name | Description |
|-----------|-------------|
| `scan_compliance` | Deep scan text for NI 43-101 violations, promissory language, and regulatory issues. |
| `check_brand_consistency` | Check content against brand guidelines for consistency. |
| `lint_code_security` | Lint code for security vulnerabilities and best practice violations. |
| `audit_document` | Comprehensive document audit for accuracy, completeness, and compliance. |
| `track_document_changes` | Track and diff document changes with version comparison. |
| `validate_regulatory_checklist` | Validate against regulatory compliance checklists. |
| `score_content` | Score content quality on multiple dimensions (clarity, accuracy, tone, completeness). |
| `audit_access_logs` | Audit access logs for suspicious patterns and policy violations. |

### Architect Tools (`server/ai/architect-tools.ts`) — 8 tools
| Tool Name | Description |
|-----------|-------------|
| `design_schema` | Design database schema with tables, relationships, and constraints. |
| `generate_api_spec` | Generate OpenAPI/Swagger specification for API endpoints. |
| `analyze_dependencies` | Analyze project dependencies for vulnerabilities, updates, and conflicts. |
| `plan_migration` | Plan database or system migration with steps and rollback procedures. |
| `detect_code_patterns` | Detect design patterns, anti-patterns, and code smells in the codebase. |
| `track_tech_debt` | Track and prioritize technical debt items with effort estimation. |
| `recommend_refactor` | Recommend code refactoring with impact analysis and implementation plan. |
| `generate_documentation` | Generate technical documentation from code analysis. |

### Curator Tools (`server/ai/curator-tools.ts`) — 8 tools
| Tool Name | Description |
|-----------|-------------|
| `manage_storage` | List, upload, download, and delete files in object storage. |
| `organize_files` | Organize files into logical folder structures with renaming. |
| `generate_thumbnails` | Generate thumbnail previews for documents and media. |
| `tag_metadata` | Add, update, or search metadata tags on files. |
| `manage_versions` | Manage file versions: list history, restore, or compare versions. |
| `bulk_upload` | Bulk upload multiple files with metadata and organization. |
| `analyze_storage` | Analyze storage usage, find duplicates, and recommend cleanup. |
| `transcode_media` | Transcode media files between formats with quality control. |

### Emissary Tools (`server/ai/emissary-tools.ts`) — 24 tools
| Tool Name | Description |
|-----------|-------------|
| `github_list_repos` | List GitHub repositories for the authenticated user. |
| `github_get_repo` | Get detailed information about a specific GitHub repository. |
| `github_list_pull_requests` | List pull requests for a repository with optional filtering. |
| `github_create_pull_request` | Create a new pull request on a GitHub repository. |
| `github_list_issues` | List issues for a repository with optional filtering. |
| `github_create_issue` | Create a new issue on a GitHub repository. |
| `github_get_file` | Get the content of a file from a GitHub repository. |
| `github_search_code` | Search for code across GitHub repositories. |
| `sync_google_drive` | Sync files between Object Storage and Google Drive. |
| `process_video_opus` | Process video content with Opus Clip for AI-powered clipping and captions. |
| `synthesize_voice` | Synthesize speech using ElevenLabs text-to-speech. |
| `transcribe_audio` | Transcribe audio to text using ElevenLabs speech-to-text. |
| `manage_webhooks` | Manage webhook integrations for external services. |
| `orchestrate_api` | Orchestrate calls to multiple external APIs in sequence or parallel. |
| `check_integration_health` | Check the health status of all external integrations. |
| `refresh_oauth` | Refresh OAuth tokens for external service connections. |
| `genspark_search` | Perform AI-powered web search using Genspark. |
| `genspark_chat` | Have a conversational chat with Genspark AI with multi-turn context. |
| `genspark_deep_research` | Conduct deep AI-powered research on a topic (especially mining/finance). |
| `genspark_analyze_document` | Analyze a document with AI-powered extraction of key data, financials, and risks. |
| `genspark_market_insights` | Get real-time market insights and forecasts for commodities. |
| `genspark_analyze_code` | Analyze code for issues, suggestions, and quality metrics. |
| `genspark_generate_code` | Generate code based on a natural language prompt. |
| `genspark_vision` | Analyze an image using AI vision capabilities. |

*Note: Additional Genspark tools exist in the file (genspark_explain_code, genspark_debug_code, genspark_stakeholder_briefing, genspark_due_diligence) — total tool functions in the file exceed 24 when counting all named exports.*

### Scribe Tools (`server/ai/scribe-tools.ts`) — 8 tools
| Tool Name | Description |
|-----------|-------------|
| `generate_report` | Generate professional reports: investor updates, quarterly reports, executive summaries. |
| `create_presentation` | Create presentations using Gamma.app AI for professional slides. |
| `compose_newsletter` | Compose investor newsletters with customizable templates and content blocks. |
| `write_changelog` | Generate changelog entries from commits, PRs, or manual input. |
| `build_investor_deck` | Build comprehensive investor deck with all required sections and data. |
| `create_executive_summary` | Create a concise executive summary from documents or raw data. |
| `format_meeting_notes` | Format and structure meeting notes with action items and summaries. |
| `generate_faq` | Generate FAQ content from documents, past Q&A, or topics. |

### Sentinel Tools (`server/ai/sentinel-tools.ts`) — 6 tools
| Tool Name | Description |
|-----------|-------------|
| `get_health_dashboard` | Get comprehensive health dashboard aggregating all system metrics. |
| `dispatch_alert` | Dispatch alerts to configured channels (Slack, email, SMS). |
| `detect_anomaly` | Run anomaly detection on system metrics and user behavior. |
| `track_uptime` | Track and report uptime metrics for all services. |
| `analyze_error_patterns` | Analyze error patterns to identify systemic issues. |
| `monitor_sla` | Monitor SLA compliance and generate violation alerts. |

### Chancellor Tools (`server/ai/chancellor-tools.ts`) — 6 tools
| Tool Name | Description |
|-----------|-------------|
| `manage_investor_ledger` | Manage investor ledger: track investments, distributions, and ownership. |
| `track_capital_stack` | Track and visualize the capital stack structure. |
| `calculate_distribution` | Calculate investor distributions based on waterfall structure. |
| `process_fees` | Calculate and process management fees, carry, and other fees. |
| `generate_financial_report` | Generate detailed financial reports for investors or auditors. |
| `treasury_dashboard` | View treasury dashboard with cash positions and forecasts. |

### Designer Tools (`server/ai/designer-tools.ts`) — 10 tools
| Tool Name | Description |
|-----------|-------------|
| `generate_web_mockup` | Create web page mockup/wireframe with layout specifications. |
| `generate_image` | AI image generation for design assets, illustrations, and visual content. |
| `design_ui_component` | Design UI component specs with styling, interactions, and accessibility. |
| `create_brand_kit` | Generate comprehensive brand identity kit with colors, typography, and visual elements. |
| `design_email_template` | Design responsive email template layouts with content blocks and styling. |
| `generate_icon_set` | Create icon set specifications with consistent style and sizing. |
| `create_infographic` | Design data infographic layouts with visual data representation. |
| `design_landing_page` | Full landing page design specification with sections, CTAs, and responsive layout. |
| `generate_social_media_assets` | Generate social media graphics specifications for various platforms. |
| `create_style_guide` | Generate comprehensive style guide with typography, colors, spacing. |

### Producer Tools (`server/ai/producer-tools.ts`) — 10 tools
| Tool Name | Description |
|-----------|-------------|
| `create_video` | Generate video content with AI-powered production. |
| `edit_video` | Edit existing video with AI-powered instructions. |
| `clip_video` | Extract highlights and clips from video using AI scene detection. |
| `add_captions` | Generate and add captions/subtitles using AI speech recognition. |
| `generate_thumbnail` | Create eye-catching video thumbnails with AI-powered composition. |
| `create_video_script` | Write video script with scene descriptions, dialogue, and timing. |
| `transcode_media` | Transcode media files between formats with quality control. |
| `create_animation` | Generate motion graphics animation specifications. |
| `batch_process_media` | Batch process multiple media files with consistent operations. |
| `generate_storyboard` | Create visual storyboard for video production. |

### Presenter Tools (`server/ai/presenter-tools.ts`) — 8 tools
| Tool Name | Description |
|-----------|-------------|
| `create_slideshow` | Create full presentation slideshow with themed slides and transitions. |
| `generate_deck` | Generate investor, pitch, or strategy deck with structured sections. |
| `design_slide` | Design individual slide with specific content, layout, and animations. |
| `create_pitch_deck` | Build startup pitch deck with problem, solution, market, and financial slides. |
| `export_presentation` | Export presentation to various formats with quality options. |
| `add_slide_animations` | Add transitions and animations to presentation slides. |
| `create_webinar_slides` | Create webinar presentation with interactive elements and speaker notes. |
| `generate_presentation_notes` | Generate detailed speaker notes for presentation slides. |

### Researcher Tools (`server/ai/researcher-tools.ts`) — 10 tools
| Tool Name | Description |
|-----------|-------------|
| `deep_web_search` | Multi-agent deep web search across multiple sources with relevance ranking. |
| `research_topic` | Comprehensive topic research with multiple sources, citations, and findings. |
| `index_content` | Index content for searchability with metadata tagging and priority ranking. |
| `competitive_analysis` | Analyze competitors and market landscape with structured intelligence. |
| `aggregate_news` | Aggregate and analyze news from multiple sources with sentiment analysis. |
| `fact_check` | Verify claims against multiple authoritative sources with confidence scoring. |
| `build_research_brief` | Compile research into a structured brief with citations and executive summary. |
| `monitor_mentions` | Monitor web mentions of entities across platforms with sentiment tracking. |
| `extract_insights` | Extract actionable insights from data sources using AI analysis. |
| `create_knowledge_map` | Build knowledge map from research showing entity relationships. |

### Director Tools (`server/ai/director-tools.ts`) — 10 tools
| Tool Name | Description |
|-----------|-------------|
| `create_project_plan` | Create detailed project plan with goals, timeline, milestones, and team assignments. |
| `manage_milestones` | Create, update, and track project milestones with dependencies. |
| `assign_tasks` | Assign and distribute tasks across team members with priority and deadlines. |
| `track_progress` | Get comprehensive project progress overview with metrics and status. |
| `generate_gantt` | Generate Gantt chart data with task dependencies and timeline visualization. |
| `create_sprint` | Create sprint or iteration plan with goals, capacity, and task allocation. |
| `risk_assessment` | Assess project risks with categorization, likelihood, and mitigation strategies. |
| `resource_allocation` | Optimize resource allocation across project tasks and team members. |
| `generate_status_report` | Generate project status report for stakeholders. |
| `create_roadmap` | Build product or project roadmap with horizons, themes, and milestones. |

### Linguist Tools (`server/ai/linguist-tools.ts`) — 10 tools
| Tool Name | Description |
|-----------|-------------|
| `text_to_speech` | Convert text to natural speech audio with voice selection and language options. |
| `speech_to_text` | Transcribe audio to text with language detection and timestamp support. |
| `speech_to_speech` | Real-time voice transformation converting speech with different voice characteristics. |
| `translate_text` | Translate text between languages with tone and context awareness. |
| `summarize_text` | AI-powered text summarization with configurable length and style. |
| `rewrite_content` | Rewrite content with different tone, style, or audience targeting. |
| `generate_voiceover` | Generate professional voiceover audio from script with pacing and background options. |
| `transcribe_meeting` | Transcribe meeting audio with speaker diarization and identification. |
| `content_moderation` | Moderate text content for policy compliance and safety. |
| `generate_audio_summary` | Create audio summary from text content with voice narration. |

### Reporter Tools (`server/ai/reporter-tools.ts`) — 10 tools
| Tool Name | Description |
|-----------|-------------|
| `generate_detailed_report` | Generate fully detailed analytical report with data-driven insights. |
| `create_spreadsheet` | Generate spreadsheet with structured data, formulas, and multiple sheets. |
| `build_dashboard_report` | Build dashboard-style report with KPIs, charts, and real-time metrics. |
| `generate_financial_analysis` | Generate detailed financial analysis with metrics, ratios, and projections. |
| `create_data_export` | Export data to various formats with filtering, aggregation, and transformation. |
| `generate_comparison_report` | Generate side-by-side comparison report between entities across metrics. |
| `create_audit_report` | Generate compliance and audit report with findings and recommendations. |
| `build_investor_report` | Build comprehensive investor report with performance and highlights. |
| `generate_market_report` | Generate comprehensive market analysis report with trends and indicators. |
| `create_executive_briefing` | Create concise one-page executive briefing with key topics and recommendations. |

### Swarm Tools (`server/ai/swarm-tools.ts`) — 6 tools
| Tool Name | Description |
|-----------|-------------|
| `dispatch_openclaw_task` | Dispatch a task to the OpenClaw multi-agent swarm for autonomous execution. |
| `dispatch_openclaw_swarm` | Deploy a multi-agent swarm for complex operations (parallel, sequential, or hierarchical). |
| `get_openclaw_status` | Check the OpenClaw gateway connection status, health, and active session count. |
| `list_openclaw_skills` | List all available skills/capabilities installed on the connected OpenClaw instance. |
| `get_openclaw_sessions` | Retrieve recent OpenClaw task sessions with their status and results. |
| `get_openclaw_session_result` | Get the detailed result of a specific OpenClaw session by its ID. |

---

## Section 5: Swarm Intelligence Architecture

Source files: `server/ai/swarm/orchestrator.ts`, `server/ai/swarm/cost-optimizer.ts`, `server/ai/swarm/communication-bus.ts`, `server/ai/swarm/skills-library.ts`, `server/ai/swarm/sacred-geometry-optimizer.ts`

### 8 Swarm Agents

| Agent ID | Capabilities | Cost/Task | Avg Response | Success Rate |
|----------|-------------|-----------|-------------|-------------|
| `oracle` | forecasting, analysis, market-intelligence, risk-assessment | $0.15 | 8s | 94% |
| `researcher` | web-search, data-gathering, academic-research, verification | $0.08 | 12s | 96% |
| `scribe` | documentation, summarization, report-writing, formatting | $0.05 | 5s | 98% |
| `architect` | system-design, planning, optimization, modeling | $0.12 | 15s | 91% |
| `analyst` | financial-modeling, data-analysis, valuation, forecasting | $0.10 | 10s | 95% |
| `sentinel` | monitoring, alerts, compliance-checking, security | $0.03 | 3s | 99% |
| `curator` | knowledge-management, data-organization, search, indexing | $0.04 | 4s | 97% |
| `liaison` | communication, stakeholder-management, coordination, translation | $0.06 | 6s | 93% |

### 12 Pre-Built Skills

| Skill ID | Name | Category | Description |
|----------|------|----------|-------------|
| `deep-market-research` | Deep Market Research | research | Multi-source market analysis covering trends, pricing, demand drivers, and competitive landscape |
| `geological-data-analysis` | Geological Data Analysis | research | Analyze geological surveys, mineral assays, and resource estimation data |
| `competitive-intelligence` | Competitive Intelligence | research | Competitor analysis, industry benchmarking, and strategic intelligence gathering |
| `financial-modeling` | Financial Modeling | analysis | NPV, IRR, sensitivity analysis, cash flow modeling, and valuation |
| `risk-assessment` | Risk Assessment | analysis | Comprehensive risk evaluation covering operational, financial, regulatory, and strategic risks |
| `due-diligence` | Due Diligence | analysis | Full due diligence checklist including legal, financial, operational, and technical verification |
| `investor-report` | Investor Report | creative | Generate polished, professional investor reports with data visualization guidance |
| `executive-summary` | Executive Summary | creative | Create concise executive-level summaries from complex data and analyses |
| `presentation-deck` | Presentation Deck | creative | Build structured presentation content with slide outlines and speaker notes |
| `compliance-audit` | Compliance Audit | technical | Regulatory compliance verification against relevant frameworks and standards |
| `system-architecture-review` | System Architecture Review | technical | Technical architecture analysis covering scalability, security, and reliability |
| `stakeholder-briefing` | Stakeholder Briefing | communication | Prepare targeted stakeholder communications, updates, and briefing materials |

### 58 Mineral Development Skills (TRINITY-LARIVE Project)

| Domain | Count | Skill IDs |
|--------|-------|-----------|
| Geological Exploration & Modeling | 8 | `drill_program_planning`, `core_logging_analysis`, `geochemical_assay_interpretation`, `structural_geology_modeling`, `3d_geological_modeling`, `geophysical_survey_analysis`, `stratigraphic_correlation`, `alteration_mineral_mapping` |
| Resource Estimation & Classification | 6 | `ni_43_101_resource_estimate`, `jorc_resource_classification`, `variogram_modeling`, `kriging_grade_estimation`, `resource_sensitivity_analysis`, `reserve_conversion_analysis` |
| Mining Engineering & Operations | 8 | `open_pit_mine_design`, `underground_mine_planning`, `mine_production_scheduling`, `geotechnical_slope_analysis`, `hydrogeological_assessment`, `mine_equipment_selection`, `blast_pattern_optimization`, `mine_ventilation_design` |
| Metallurgy & Processing | 6 | `metallurgical_test_analysis`, `gold_recovery_optimization`, `comminution_circuit_design`, `flowsheet_development`, `reagent_consumption_analysis`, `tailings_characterization` |
| Environmental & Permitting | 6 | `environmental_impact_assessment`, `water_quality_monitoring`, `mine_closure_planning`, `biodiversity_impact_analysis`, `air_quality_assessment`, `environmental_permitting` |
| Gold Market & Economics | 6 | `gold_price_forecasting`, `mine_feasibility_study`, `mine_cashflow_modeling`, `operating_cost_estimation`, `capital_cost_estimation`, `gold_hedging_strategy` |
| Land & Rights Management | 4 | `mineral_rights_analysis`, `land_access_negotiation`, `stakeholder_community_engagement`, `indigenous_consultation_planning` |
| Health, Safety & Compliance | 5 | `mine_safety_audit`, `hazard_identification_assessment`, `emergency_response_planning`, `occupational_health_monitoring`, `regulatory_compliance_tracker` |
| Sovereign Gold Reserve Management | 4 | `sovereign_gold_custody`, `gold_provenance_chain`, `bullion_quality_assurance`, `reserve_diversification_strategy` |
| Advanced Mining Analytics | 5 | `ore_body_machine_learning`, `predictive_maintenance_mining`, `mine_digital_twin`, `drone_survey_analysis`, `lidar_point_cloud_processing` |

### Cost Control Configuration

```
Budget Caps:
  Per Task:    $0.50
  Per Session: $5.00
  Per Day:     $25.00
  Per Agent:   Configurable per-agent overrides

Override Rules:
  Critical Task Cap:      $5.00
  Requires Confirmation:  true
  Allowed Priorities:     ['critical', 'urgent']

Alert System:
  Warning Threshold:  80% of cap

Emergency Controls:
  Kill Switch:        $50.00 (auto-halt all operations)
  Cooldown Period:    24 hours (86400000ms)
  Daily Reset:        Midnight automatic reset
```

### Model Pricing Tiers

| Model | Input/1K tokens | Output/1K tokens | Tier |
|-------|----------------|-----------------|------|
| DeepSeek V3.2 | $0.00014 | $0.00028 | Economy |
| Gemini 3 Flash | $0.00015 | $0.00060 | Economy |
| Kimi K2.5 | $0.00018 | $0.00036 | Economy |
| Claude Haiku 4.5 | $0.00040 | $0.00200 | Standard |
| GPT-5-mini | $0.00050 | $0.00150 | Standard |
| Claude Sonnet 4.5 | $0.00200 | $0.01000 | Premium |
| GPT-5.2 | $0.00300 | $0.01200 | Premium |

### 4 Execution Strategies
1. **Solo** — Single agent handles the task end-to-end
2. **Parallel** — Multiple agents work simultaneously on subtasks
3. **Sequential** — Agents work in order, each building on prior output
4. **Collaborative** — Agents coordinate through the communication bus with shared context

### Communication Bus Architecture
- **Priority Queue**: Messages sorted by priority (high > normal > low)
- **Pub/Sub Pattern**: `on()`, `once()`, `broadcast()` handlers
- **Acknowledgment System**: `requiresAck` flag with timeout tracking
- **Message Types**: Typed payloads with sender/recipient routing
- **Processing Loop**: 100ms polling interval for queue processing
- **Timeout Handling**: 30s default timeout per message with configurable override

---

## Section 6: Database Schema (51 tables)

Source: `shared/schema.ts` — 1,385 lines, 51 tables

### Core Platform
| Table | Key Columns | Relationships |
|-------|-------------|---------------|
| `projects` | id (uuid PK), name, slug (unique), tagline, description, primaryColor (#D4AF37), accentColor, logoUrl, heroImageUrl, status (active/draft/archived), isPublic, portalEnabled, metadata (JSONB) | Parent for most entities |
| `users` | id (uuid PK), username (unique), email (unique), passwordHash (Argon2id), roles (text[]), extraPerms (text[]), isActive, lastLogin | Auth identity |
| `investors` | id (uuid PK), userId (FK→users), name, email (unique), company, status (pending/active), accessLevel (basic/premium) | Links to users |

### Document Management
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `documents` | id, name, category, type (PDF), size, restricted, accessLevel, url, description | Legacy document store |
| `vault_documents` | id, projectId (FK→projects), name, category (legal/geological/corporate/financial/marketing/technical), fileType, fileSize, url, description, summary (AI-generated), accessLevel (admin/investor), tags (text[]), indexed | Primary document vault |
| `document_folders` | id, name, description, parentId (self-referencing), isPersonal, memberId (FK→members), color, icon | Nested folder structure |
| `document_acl` | id, documentId (FK→vault_documents), workspaceId, memberId, canView, canDownload, canShare, grantedBy, expiresAt | Fine-grained access control |
| `knowledge_files` | id, name, category (index/data/config/code/text/markup), fileType, path, content (full text), contentHash, purpose, vectorized, metadata (JSONB) | AI knowledge source files |

### CRM & Members
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `members` | id, projectId, firstName, lastName, email (unique), phone, company, title, address/city/state/country, role (investor/advisor/partner/qp/admin), status (pending/active/suspended/archived), accessLevel (basic/standard/premium/full), ndaSigned, ndaSignedDate, kycVerified, tags (text[]), projectAccess (text[]), purpose, metrics (JSONB), notes | CRM member profiles |
| `member_credentials` | id, memberId (FK→members), username (unique), passwordHash, accessToken, tokenExpiresAt, emailSent/smsSent/linkShared booleans with timestamps, isActive | Member login credentials |
| `member_document_permissions` | id, memberId (FK), documentId (FK→vault_documents), folderId (FK→document_folders), canView, canDownload, expiresAt, grantedBy | Per-member doc permissions |
| `member_activity` | id, memberId (FK), action (login/document_view/download...), details, ipAddress, metadata (JSONB) | Activity audit log |

### Workspace & Access
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `investor_workspaces` | id, name, slug (unique), description, projectId (FK), accessType (private/restricted/public), requiresNda, isActive, metadata (JSONB) | Secure data rooms |
| `workspace_members` | id, workspaceId (FK), memberId (FK), role (viewer/contributor/admin), permissions (text[]), invitedAt, joinedAt, expiresAt, isActive | Workspace membership |

### Tasks & Meetings
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `tasks` | id, projectId, title, description, status (pending/in_progress/completed/cancelled), priority (low/medium/high/urgent), dueDate, assignedTo (FK→members), relatedMemberId, tags (text[]), createdBy, completedAt | Task management |
| `meetings` | id, projectId, title, description, meetingDate, duration (minutes), location, meetingLink, memberId (FK), agenda, notes, actionItems (text[]), status (scheduled/completed/cancelled), createdBy | Meeting tracking |

### Notifications & Activity
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `notifications` | id, type, category (system), title, message, severity (info/warn/error), recipientId, projectId, sourceAgent, metadata (JSONB), read, dismissed, actionUrl | In-app notifications |
| `activity_log` | id, projectId (FK), action, description, userId (FK→users), metadata (JSONB) | System-wide activity |

### Constellation (Graph Visualization)
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `constellation_nodes` | id, name, type, category, description, x, y (position), size, color, metadata (JSONB) | Interactive node map |
| `constellation_edges` | id, sourceId (FK→nodes), targetId (FK→nodes), relationship, strength, animated | Node connections |

### Drive Sync
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `drive_sync_configs` | id, name, driveFolderId, driveFolderName, projectId, targetCategory, accessLevel, workspaceId, autoSync, syncInterval (minutes), lastSyncAt/Status/Message, isActive | Google Drive sync config |
| `drive_synced_files` | id, syncConfigId (FK), driveFileId, driveFileName, vaultDocumentId (FK→vault_documents), driveModifiedTime | Sync tracking |

### AI & RAG
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `embeddings` | id, sourceType, sourceId, chunkIndex, content, chunkText, metadata (JSONB), projectId, accessLevel | Vector embeddings (pgvector) |
| `graph_entities` | id, type, name, description, attributes (JSONB), sourceDocumentId, communityId, projectId | GraphRAG entities |
| `graph_relationships` | id, sourceId, targetId, type, weight, attributes (JSONB) | GraphRAG relationships |
| `agent_memories` | id, agentId, memoryType (fact), category, key, value, entityId/Type/Name, projectId, confidence (0-100), importance (0-100), accessCount, source, expiresAt | Mem0 persistent memory |
| `prompt_optimizations` | id, name, description, originalPrompt, optimizedPrompt, status (pending/running/done), model, evalMetrics (JSONB), variants (JSONB), bestVariantIndex, iterations, maxIterations | DSPy prompt tuning |
| `privacy_audit_logs` | id, requestId, sensitivityLevel, detectedEntities (JSONB), originalModel, routedModel, reason, dataCategories (JSONB), redactionApplied, userId, projectId | Privacy routing log |
| `agent_preferences` | id, agentName (unique), enabled, model, tools (text[]) | Per-agent config |
| `agent_presets` | id, name, description, agents (text[]), isActive, isBuiltIn | Agent group presets |

### Workflows
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `workflows` | id, name, description, definition (JSONB), status (draft/active), projectId | LangGraph workflows |
| `visual_workflows` | id, name, description, nodes (JSONB), edges (JSONB), viewport (JSONB), status, lastRunAt/Result, projectId | Visual flow builder |
| `automation_workflows` | id, name, description, nodes (JSONB), edges (JSONB), status, triggerType (manual/schedule), schedule, lastRunAt/Result, projectId | n8n-style automation |
| `automation_executions` | id, workflowId, status (running/completed/failed), steps (JSONB), input (JSONB), output (JSONB), error | Execution log |

### Audit & Security
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `audit_trail` | id (serial PK), eventId (uuid), timestamp, category, action, severity, actor, actorType (system/user/agent), resourceType/Id, projectId, description, metadata (JSONB), ipAddress, previousHash, entryHash, immutable | SHA-256 hash-chained immutable log |
| `encryption_keys` | id, ownerId, ownerType (admin), publicKey, keyFingerprint, algorithm (RSA-OAEP), keySize (2048), active, expiresAt | E2E encryption keys |
| `encrypted_messages` | id, threadId, senderId/Type, recipientId/Type, subject, encryptedContent, encryptedAesKey, iv, contentHash, priority, category, status, readAt, expiresAt, projectId | AES-256-GCM encrypted messages |
| `message_threads` | id, subject, participantIds (text[]), projectId, category, priority, encrypted, lastMessageAt, messageCount | Message thread grouping |

### Scheduling (Cal.com-style)
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `event_types` | id, title, slug, description, durationMinutes (30), location (video), color (#D4AF37), active, projectId | Bookable event types |
| `availability_windows` | id, ownerId, dayOfWeek (0-6), startTime, endTime, timezone (UTC) | Available time slots |
| `bookings` | id, eventTypeId, inviteeName, inviteeEmail, startTime, endTime, status (confirmed/cancelled), notes, calendarEventId, projectId | Confirmed bookings |

### Durable Execution (Temporal-style)
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `task_queues` | id, name (unique), description, workerCount, maxConcurrency (10), status (active), metadata (JSONB) | Worker pool management |
| `durable_workflows` | id, name, workflowType, status (pending/running/completed/failed/cancelled), input/output/state (JSONB), taskQueueId, retryPolicy (JSONB), currentActivityIndex, totalActivities, parentWorkflowId, runId (uuid), memo/searchAttributes (JSONB), projectId | Fault-tolerant workflows |
| `durable_activities` | id, workflowId, activityType, name, status, input/output (JSONB), error, attempt, maxRetries (3), retryBackoff (exponential), nextRetryAt, heartbeatAt/Details, timeoutSeconds (300), sequenceNumber | Individual workflow steps |
| `workflow_signals` | id, workflowId, signalName, payload (JSONB), senderId/Type, status (pending/delivered/processed), deliveredAt/processedAt, expiresAt | External events to workflows |

### RWA Marketplace
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `rwa_assets` | id, name, slug, category (commodities), description, imageUrl, valuation, currency (USD), yieldRate, location, issuer, complianceStatus (pending/approved), status (draft/active), riskRating (low/medium/high), minimumInvestment, maturityDate, projectId, metadata (JSONB) | Tokenized real-world assets |
| `rwa_asset_tokens` | id, assetId, tokenSymbol, tokenName, totalSupply (1M), circulatingSupply, pricePerToken, decimals (2), fractionalized, blockchain (ethereum), contractAddress, metadata (JSONB) | Asset token specs |
| `rwa_orders` | id, assetId, investorId, orderType (market/limit), side (buy/sell), quantity, limitPrice, filledQuantity, averageFillPrice, status (open/filled/cancelled), expiresAt, metadata (JSONB) | Trading orders |
| `rwa_portfolios` | id, investorId, assetId, tokenBalance, averageCost, totalInvested, unrealizedPnl | Investor holdings |
| `rwa_transactions` | id, orderId, assetId, buyerId, sellerId, transactionType (buy/sell), quantity, pricePerToken, totalAmount, fee, status (completed), blockchainTxHash | Trade history |

### Swarm Ledger
| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `swarm_ledger` | id, traceId, sessionId, taskDescriptions (text[]), estimatedCost (numeric), actualCost (numeric), priority (normal/high/critical), status (pending/running/completed/failed) | OpenClaw cost tracking |

---

## Section 7: API Endpoint Map (379 endpoints)

Source: `server/routes.ts`

### Authentication & Users
- `POST /api/auth/login`
- `GET/POST /api/projects`

### Documents & Vault
- `GET/POST /api/documents`, `GET/PUT/DELETE /api/documents/:id`
- `GET/PUT /api/documents/category/:category`
- `GET/POST /api/vault/documents`, `GET/DELETE /api/vault/documents/:id`

### Constellation (Graph)
- `GET/POST /api/constellation/nodes`, `PUT/DELETE /api/constellation/nodes/:id`
- `GET/POST /api/constellation/edges`, `DELETE /api/constellation/edges/:id`

### Notifications
- `GET/POST /api/notifications`, `PUT /api/notifications/:id`
- `GET /api/notifications/unread-count`, `POST /api/notifications/read-all`
- `GET /api/notifications/stream` (SSE), `GET /api/notifications/stats`

### Admin CRM
- `GET/POST /api/admin/members`, `GET/PUT/DELETE /api/admin/members/:id`
- `GET/POST /api/admin/tasks`, `PUT /api/admin/tasks/:id`
- `GET/POST /api/admin/meetings`, `PUT/DELETE /api/admin/meetings/:id`
- `GET/POST /api/admin/documents`, `GET/POST /api/admin/permissions`
- `GET/POST /api/admin/workspaces`, `PUT/DELETE /api/admin/workspaces/:id`
- `GET/POST /api/admin/workspace-members`
- `GET/POST /api/admin/acl`
- `GET/POST /api/admin/drive/*`

### AI / Trinity Council
- `GET /api/council/agents`, `GET /api/council/models`
- `POST /api/council/chat`, `POST /api/council/stream`
- `POST /api/council/command`, `POST /api/council/mission`
- `POST /api/council/autonomous`
- `GET/POST/DELETE /api/council/memory`
- `GET/PUT /api/council/presets`
- `POST /api/ai/chat`, `GET /api/ai/status`, `GET /api/ai/models`
- `POST /api/ai-studio/generate`, `POST /api/ai-studio/generate-image`
- `GET/PUT /api/agents/preferences`, `GET/POST /api/agents/presets`
- `GET/PUT /api/agents/enabled`

### RAG & Knowledge
- `POST /api/rag/ingest`, `POST /api/rag/query`, `POST /api/rag/search`
- `GET /api/rag/stats`, `GET /api/rag/embeddings`
- `POST /api/ragflow/search`, `GET /api/ragflow/sources`, `GET /api/ragflow/stats`
- `POST /api/graphrag/ingest`, `POST /api/graphrag/query`, `GET /api/graphrag/stats`
- `GET/POST /api/knowledge/files`

### Memory (Mem0)
- `POST /api/mem0/store`, `POST /api/mem0/recall`, `POST /api/mem0/extract`
- `POST /api/mem0/context`, `POST /api/mem0/reinforce`, `POST /api/mem0/decay`
- `GET /api/mem0/entity/:entityId`, `GET /api/mem0/stats`
- `DELETE /api/mem0/memory/:id`

### Prompt Optimization (DSPy)
- `GET/POST /api/dspy/optimizations`, `POST /api/dspy/optimizations/:id/iterate`

### Privacy Router
- `POST /api/privacy/classify`, `POST /api/privacy/route`
- `GET /api/privacy/audit-logs`, `GET /api/privacy/stats`

### Multimodal (Gemini)
- `POST /api/multimodal/analyze`, `POST /api/multimodal/batch`
- `POST /api/multimodal/analyze-and-ingest`, `POST /api/multimodal/multi-document`
- `GET /api/multimodal/capabilities`

### Workflows (LangGraph / Visual / Automation)
- `GET/POST /api/workflows/visual`, `PUT/DELETE /api/workflows/visual/:id`
- `POST /api/workflows/execute`, `GET /api/workflows/presets`
- `GET/POST /api/automation/workflows`, `PUT/DELETE /api/automation/workflows/:id`
- `POST /api/automation/execute/:id`, `GET /api/automation/executions`
- `GET /api/automation/presets`

### Mastra Pipelines
- `GET/POST /api/mastra/pipelines`, `POST /api/mastra/pipelines/:id/run`
- `GET /api/mastra/agents`, `GET/POST /api/mastra/registry`

### MCP (Model Context Protocol)
- `GET /api/mcp/tools`, `POST /api/mcp/execute`, `GET /api/mcp/info`

### Audit Trail
- `GET/POST /api/audit-trail`, `GET /api/audit-trail/stats`
- `POST /api/audit-trail/verify`, `POST /api/audit-trail/export`

### Encrypted Communications
- `GET/POST /api/secure-messages/keys`, `GET /api/secure-messages/system-key`
- `POST /api/secure-messages/send`, `GET /api/secure-messages/threads`
- `GET /api/secure-messages/:messageId`, `GET /api/secure-messages/unread`

### Durable Execution (Temporal-style)
- `GET/POST /api/durable/workflows`, `GET /api/durable/workflows/:id`
- `POST /api/durable/workflows/:id/signal`, `POST /api/durable/workflows/:id/cancel`
- `GET/POST /api/durable/task-queues`
- `GET /api/durable/activities/:workflowId`, `POST /api/durable/signals`
- `GET /api/durable/presets`, `POST /api/durable/execute-preset`

### Scheduling (Cal.com-style)
- `GET/POST /api/scheduling/event-types`, `PUT/DELETE /api/scheduling/event-types/:id`
- `GET/POST /api/scheduling/availability`, `DELETE /api/scheduling/availability/:id`
- `GET/POST /api/scheduling/bookings`, `PUT /api/scheduling/bookings/:id`
- `GET /api/scheduling/slots`, `POST /api/scheduling/seed-defaults`
- `GET /api/scheduling/defaults`

### Drive Grounding
- `GET/POST /api/drive-grounding/configs`, `PUT/DELETE /api/drive-grounding/configs/:id`
- `POST /api/drive-grounding/sync/:configId`
- `GET /api/drive-grounding/status/:configId`
- `POST /api/drive-grounding/search`, `POST /api/drive-grounding/document/:driveFileId`
- `POST /api/drive-grounding/spreadsheet/:spreadsheetId`

### OpenClaw / Swarm
- `POST /api/openclaw/dispatch`, `GET /api/openclaw/sessions`
- `GET /api/openclaw/sessions/:sessionId`, `GET /api/openclaw/status`
- `GET /api/openclaw/skills`
- `POST /api/swarm/orchestrate`, `GET /api/swarm/agents`
- `GET /api/swarm/skills`, `GET /api/swarm/cost`, `GET /api/swarm/status`

### RWA Marketplace
- `GET/POST /api/rwa/assets`, `GET/PUT /api/rwa/assets/:id`
- `GET /api/rwa/tokens`, `GET /api/rwa/tokens/:tokenId`
- `POST /api/rwa/orders`, `GET /api/rwa/orders`
- `GET /api/rwa/order-book/:tokenId`
- `GET /api/rwa/portfolio/:investorId`
- `GET /api/rwa/transactions`, `GET /api/rwa/market-stats`
- `POST /api/rwa/seed`

### Integrations (30+ external services)
- `GET /api/integrations/status`
- `POST /api/integrations/google-drive/*` (list, upload, download, create-folder, search)
- `POST /api/integrations/gmail/*` (send, read, search)
- `POST /api/integrations/sheets/*` (read, write, append, create)
- `POST /api/integrations/calendar/*` (list-events, create-event, update-event, delete-event)
- `POST /api/integrations/docs/*` (create, read, append)
- `POST /api/integrations/slides/*` (create, read, add-slide)
- `POST /api/integrations/forms/*` (create, list-responses, get)
- `POST /api/integrations/meet/*` (create)
- `POST /api/integrations/github/*` (repos, pulls, issues, files, search)
- `POST /api/integrations/elevenlabs/*` (synthesize, transcribe, voices)
- `POST /api/integrations/genspark/*` (search, chat, research, analyze, market, code, vision)
- `POST /api/integrations/opus/*` (process)
- `POST /api/integrations/discord/*` (send, webhook)
- `POST /api/integrations/notion/*` (create, search, update)
- `POST /api/integrations/cursor/*` (dispatch, status)
- `POST /api/integrations/stripe/*` (create-checkout, subscriptions, invoices)
- `POST /api/integrations/sendgrid/*` (send, templates)
- `POST /api/integrations/twilio/*` (send-sms, make-call)
- `POST /api/integrations/linear/*` (create-issue, list-issues, projects)
- `POST /api/integrations/gamma/*` (create-presentation)

### Dev/System
- `GET /api/dev/health`, `GET /api/dev/stats`
- `GET /api/dev/endpoints`, `GET /api/dev/integrations`
- `GET /api/system/capabilities`

---

## Section 8: Frontend Pages & Routes (21 active)

Source: `client/src/App.tsx` — Updated February 13, 2026

### Public Routes (no auth required)
| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `ConsortiumHome` | Main consortium landing — alchemical symbol, three project cards, philosophy |
| `/trinity-larive` | `Home` | Trinity-LaRive hero page with scroll-driven cinematic chapters |
| `/trinity-larive/request-access` | `RequestAccess` | Portal access request form |
| `/kommunity-dao` | `KommunityDAO` | Kommunity DAO minimal public page |
| `/fractal-agi` | `FractalAGI` | Fractal AGI minimal public page |

### Portal Routes (auth-gated, JWT required)
| Route | Component | Description |
|-------|-----------|-------------|
| `/trinity-larive/portal` | `PortalDashboard` | Sovereign Vault dashboard overview |
| `/trinity-larive/portal/projects` | `OurProjects` (2,210 lines) | **Consolidated project content** — 7 tabs: Asset, Geology, Strategy, Governance, Compliance, Title & Patent, Reports (w/ AI brief generation) |
| `/trinity-larive/portal/data-room` | `DataRoom` | Document vault with upload/download/categorization |
| `/trinity-larive/portal/qa` | `QA` | Investor Q&A section |
| `/trinity-larive/portal/contact` | `Contact` | Contact form |
| `/trinity-larive/portal/admin` | `AdminConsole` | Admin overview console |
| `/trinity-larive/portal/admin/crm` | `AdminCRM` | CRM dashboard (members, tasks, meetings) |
| `/trinity-larive/portal/admin/knowledge-base` | `KnowledgeBase` | AI knowledge base management |

### Admin Routes (auth-gated, admin role)
| Route | Component | Description |
|-------|-----------|-------------|
| `/admin/command-center` | `CommandCenter` (7,248 lines) | Full AI command center — all 55 agents (20 primary + 35 sub-agents), integrations, system management |
| `/admin/agentic-constellation` | `AgenticConstellation` (1,579 lines) | Interactive agent constellation visualization |
| `/admin/flow-builder` | `FlowiseBuilder` | Visual drag-and-drop workflow builder |
| `/admin/agent-management` | `AgentManagement` | Per-agent configuration (model, tools, enabled/disabled) |
| `/admin/tools-catalog` | `ToolsCatalog` | Browsable catalog of all 363+ tools |
| `/admin/infrastructure-report` | `InfrastructureReport` | System infrastructure & health overview |
| `/admin/effects-showcase` | `EffectsShowcase` | 3D effects demo/preview gallery |

### Content Architecture Note
All detailed project content (Asset, Geology, Strategy, Governance, Compliance, Title & Patent, Reports) has been consolidated into the single `OurProjects.tsx` page with tab navigation. The standalone pages for these topics were removed on Feb 13, 2026. Public project pages (`/trinity-larive`, `/kommunity-dao`, `/fractal-agi`) are intentionally minimal hero+summary pages — the detailed content lives exclusively behind the authenticated portal.

---

## Section 9: Key Configuration & Environment

### Environment Variables (Shared)

| Variable | Purpose |
|----------|---------|
| `ENFORCE_WORKSPACE_ACL` | Toggle workspace ACL enforcement (currently `false`) |
| `NODE_ENV` | Runtime environment (`production`) |
| `PORT` | Server port (`3000`) |
| `VITE_API_BASE_URL` | Frontend API base URL |
| `OPENCLAW_GATEWAY_URL` | OpenClaw swarm gateway ngrok endpoint |
| `OPENCLAW_GATEWAY_TOKEN` | Authentication token for OpenClaw gateway |

### Secrets (Encrypted)

| Secret | Purpose |
|--------|---------|
| `SESSION_SECRET` | Express session signing key |
| `DATABASE_URL` | PostgreSQL connection string |
| `PGDATABASE`, `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD` | Individual PostgreSQL credentials |
| `AI_INTEGRATIONS_OPENAI_API_KEY` | OpenAI API key (GPT-5.2, GPT-5-mini) |
| `AI_INTEGRATIONS_OPENAI_BASE_URL` | OpenAI API base URL |
| `AI_INTEGRATIONS_OPENROUTER_API_KEY` | OpenRouter API key (DeepSeek, Grok, Kimi) |
| `AI_INTEGRATIONS_OPENROUTER_BASE_URL` | OpenRouter API base URL |
| `AI_INTEGRATIONS_GEMINI_API_KEY` | Google Gemini API key |
| `AI_INTEGRATIONS_GEMINI_BASE_URL` | Gemini API base URL |
| `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` | Anthropic API base URL |
| `CURSOR_API_KEY` | Cursor Cloud Agent API key |
| `DEFAULT_OBJECT_STORAGE_BUCKET_ID` | Replit Object Storage bucket ID |
| `PUBLIC_OBJECT_SEARCH_PATHS` | Object storage public search paths |
| `PRIVATE_OBJECT_DIR` | Object storage private directory |
| `REPLIT_DOMAINS`, `REPLIT_DEV_DOMAIN`, `REPL_ID` | Replit platform configuration |

### Installed Integrations (Replit-Managed)

| Integration | Version |
|-------------|---------|
| OpenAI AI Integrations | 2.0.0 |
| OpenRouter AI Integrations | 2.0.0 |
| Gemini AI Integrations | 2.0.0 |
| Anthropic AI Integrations | 2.0.0 |
| JavaScript Object Storage | 2.0.0 |
| Google Drive | 1.0.0 |
| Google Mail (Gmail) | 1.0.0 |
| Google Sheets | 1.0.0 |
| Google Calendar | 1.0.0 |
| Google Docs | 1.0.0 |
| ElevenLabs | 1.0.0 |
| GitHub | 1.0.0 |

---

## Section 10: Authentication & RBAC System

Source: `server/auth/rbac.ts`, `server/auth/jwt.ts`, `server/domains/auth/auth.routes.ts`

### Architecture
- **JWT-based** authentication with HS256 signing, configurable expiry, issuer/audience validation
- **Argon2id** password hashing (server-side, not bcrypt)
- **Server-side token revocation** support
- **Role-Based Access Control (RBAC)** with 6 roles and 16 fine-grained permissions

### 6 Roles
| Role | Description | Permission Count |
|------|-------------|-----------------|
| `admin` | Full platform access, all operations | 16 (all) |
| `operator` | Day-to-day management, docs/deals, swarm dispatch | 9 |
| `qp` | Qualified Person — approval authority, compliance | 7 |
| `legal` | Legal document management and compliance | 7 |
| `collaborator` | Content contribution, document editing | 3 |
| `investor` | Read-only portal, docs, and deals access | 3 |

### 16 Permissions
| Permission | Description |
|------------|-------------|
| `portal:read` | View portal dashboard and pages |
| `portal:write` | Modify portal content |
| `docs:read` | View documents in vault/data room |
| `docs:write` | Upload/edit documents |
| `docs:approve` | Approve document publication |
| `deals:read` | View deal pipeline and RWA marketplace |
| `deals:write` | Create/modify deals |
| `deals:approve` | Approve deals for execution |
| `compliance:read` | View compliance status and reports |
| `compliance:write` | Update compliance records |
| `legal:read` | View legal documents |
| `legal:write` | Modify legal documents |
| `swarm:dispatch` | Send tasks to AI swarm |
| `swarm:approve` | Approve swarm task execution |
| `swarm:audit` | View swarm cost and activity logs |
| `admin:users` | Manage user accounts and roles |

### Role→Permission Matrix
```
                portal:r  portal:w  docs:r  docs:w  docs:a  deals:r  deals:w  deals:a  comp:r  comp:w  legal:r  legal:w  swarm:d  swarm:a  swarm:au  admin:u
admin           ✓         ✓         ✓       ✓       ✓       ✓        ✓        ✓        ✓       ✓       ✓        ✓        ✓        ✓        ✓         ✓
operator        ✓         ✓         ✓       ✓               ✓        ✓                 ✓                                         ✓                  ✓
qp              ✓                   ✓               ✓       ✓                 ✓        ✓       ✓                                                     ✓
legal           ✓                   ✓       ✓       ✓                                  ✓       ✓       ✓        ✓                                    ✓
collaborator    ✓                   ✓       ✓
investor        ✓                   ✓                        ✓
```

### Auth Endpoints
| Endpoint | Purpose |
|----------|---------|
| `POST /api/auth/login` | Username/password login → JWT token |
| `POST /api/auth/logout` | Server-side token invalidation |
| `GET /api/auth/verify` | Validate current JWT, return user + roles |
| `GET /api/auth/roles` | List available roles (requires auth) |
| `GET /api/admin/users` | List all users (requires `admin:users`) |
| `POST /api/admin/users` | Create user with roles (requires `admin:users`) |
| `PATCH /api/admin/users/:id` | Update user roles/status (requires `admin:users`) |

### Default Admin Credentials (from `server/domains/auth/auth.service.ts` → `seedAdminUser()`)
- Username: `admin`
- Password: `admin2024` (or `ADMIN_DEFAULT_PASSWORD` env var override)
- Roles: `["admin"]`
- Seeded on first server start if no admin user exists

---

## Section 11: Trinity-LaRive Project Domain Knowledge

### Property & Claims
| Claim | Details |
|-------|---------|
| Saturday Night No. 1 | Primary claim — Lucin Mining District, Box Elder County, Utah |
| Saturday Night No. 2 | Adjacent claim — same district |
| U.S. Mineral Patent | Patent #86663, issued 1909 |
| Mining District | Lucin Mining District |
| County/State | Box Elder County, Utah |
| Coordinates | ~41.33°N, -113.92°W (Pilot Range, western Utah) |

### Geology
| Parameter | Value |
|-----------|-------|
| Deposit Type | Carlin-type disseminated gold mineralization |
| Host Rock | Paleozoic carbonate sequences (limestone/dolomite) |
| Alteration | Silicification, decalcification, sulfidation |
| Gold Form | Sub-microscopic (invisible) gold in arsenian pyrite/marcasite |
| Key Pathfinders | As, Sb, Hg, Tl — classic Carlin geochemical suite |
| Grade Model | 0.5–5+ g/t Au (disseminated zones) |
| Structural Controls | High-angle normal faults, fold hinges |
| Regional Context | Great Basin Province, Basin and Range extension |

### Visualization Infrastructure (see `client/src/lib/three/KNOWLEDGE_BASE.md`)
Five modules planned for geological visualization:
1. **Mineral Sample Viewer** — Interactive 3D samples with measurement/annotation tools
2. **Ore Grade Heat Map** — Color-coded concentration display with custom GLSL shaders
3. **Geological Data Overlay** — 2D/3D combined drill hole, structure, and cross-section views
4. **3D Terrain + Deposit Simulation** — DEM terrain with subsurface ore body rendering
5. **Investor Demo Microsite** — Guided geological walkthrough with curated viewpoints

### Brand & Visual Identity
| Element | Value |
|---------|-------|
| Primary Color | `#D4AF37` (sovereign gold) |
| Accent Color | `#1A1A2E` (deep navy/charcoal) |
| Typography | Inter (body), Playfair Display (headings) |
| Motifs | Alchemical symbols, sacred geometry, sovereign iconography |
| Tone | Private, sovereign, institutional — never "marketing" or "sales" |
| Copy Guidelines | Use "private consortium," "invited participants," "select partners," "by invitation" — never "invest," "returns," "profits" |

---

## Section 12: Current State & Known Areas for Improvement

*Updated: February 13, 2026*

### What's Working ✅
1. **Authentication**: Production-grade JWT RBAC with Argon2id hashing, 6 roles, 16 permissions, route-level guards in `server/auth/`
2. **Routes**: Decomposed into domain modules under `server/domains/` (auth, ai, constellation, crm, integrations, notifications, projects, swarm, vault, workflows)
3. **AI Council**: Multi-model chat/stream via 4 providers (OpenAI, Gemini, Anthropic, OpenRouter) with model switching
4. **Swarm Cost Governance**: CostGate enforcement, pluggable CostEstimator, non-linear estimation, two-phase settlement, adaptive throttling — 128/128 unit tests passing
5. **Google Integrations**: Drive, Gmail, Sheets, Calendar, Docs all connected via Replit integrations
6. **3D Sacred Geometry**: 18 presets, 5 GLSL shaders, parametric surfaces, preset materials — lazy-loadable
7. **Object Storage**: Connected for document upload/download
8. **OpenClaw Swarm**: External multi-agent dispatch with ed25519 device auth (dependent on ngrok tunnel)
9. **OurProjects Portal**: Consolidated 7-tab interface with AI-powered report generation

### Tool Implementation Status
**Most tools return simulated/mock data** in their `execute()` functions. They return realistic structured data but do not perform actual operations. This is by design for the prototype phase.

#### Tools with REAL Integrations:
| Tool | Agent | Integration |
|------|-------|------------|
| `send_email` / `read_emails` | Liaison | Gmail API |
| `create_calendar_event` / `list_calendar_events` | Liaison | Google Calendar API |
| `sync_google_drive` | Emissary | Google Drive API |
| `synthesize_voice` / `transcribe_audio` | Emissary | ElevenLabs API |
| `github_*` (8 tools) | Emissary | GitHub API |
| `dispatch_openclaw_task` / `dispatch_openclaw_swarm` | Swarm | OpenClaw Gateway |
| Council chat/stream | — | Multi-model AI (4 providers) |

#### Tools with MOCK Responses (need real implementation):
Oracle, Prophet, Auditor, Architect, Curator, Sentinel, Chancellor, Designer, Producer, Presenter, Researcher, Director, Linguist, Reporter — all ~170 agent tools return hardcoded structured data. Additionally, 58 mineral development skills (363+ total tools) are registered in the skills library.

### Integration Status
| Integration | Status | Notes |
|-------------|--------|-------|
| OpenAI | ✅ | GPT-5.2, GPT-5.1, GPT-5-mini |
| Gemini | ✅ | Gemini 3 Pro Preview, 3 Flash, 2.5 Pro |
| Anthropic | ✅ | Claude Opus 4.5, Sonnet 4.5, Haiku 4.5 |
| OpenRouter | ✅ | Grok 3, Grok 3 Mini, DeepSeek V3.2, Kimi K2.5 |
| Google Drive/Gmail/Sheets/Calendar/Docs | ✅ | Replit integrations |
| GitHub | ✅ | Replit integration |
| ElevenLabs | ✅ | Replit integration |
| Object Storage | ✅ | Replit integration |
| OpenClaw Swarm | ⚠️ | Depends on ngrok tunnel |
| Cursor Cloud | ⚠️ | API key exists, partial implementation |
| Stripe/SendGrid/Discord/Notion/Twilio/Linear | 🔲 | Endpoints exist, no API keys |
| Genspark/Opus Clip/Gamma.app | 🔲 | Endpoints exist, mock responses |
| n8n/Cal.com | 🔲 | Schema exists, no external connection |

### Testing Infrastructure
- **Framework**: Vitest with globals enabled, V8 coverage provider
- **Path Aliases**: `@/` → `server/`, `@shared/` → `shared/`
- **Test Files**: 6 cost governance test suites (128/128 tests passing)
- **Location**: `server/ai/swarm/__tests__/`
- **Run**: `npx vitest run` (all) or `npx vitest run --coverage` (with coverage)

### Priority Improvement Areas
1. **Implement real tool execute() functions** — Start with Oracle tools (search_data_room, document_qa) using existing RAG infrastructure
2. **Activate pgvector** — Store actual vector embeddings, not just text content
3. **Wire up stubbed integrations** — Stripe, SendGrid, Discord are high-value
4. **Add input validation** — Zod schemas on all POST/PUT endpoints
5. **Implement real-time cost tracking** — Connect cost optimizer to actual AI API usage
6. **Add error boundaries** — Both frontend (React) and backend (Express middleware)
7. **Enable workspace ACL** — Set `ENFORCE_WORKSPACE_ACL=true` and test access controls
8. **Expand test coverage** — Unit tests exist for swarm cost governance; add API route tests and integration tests

---

*Document last updated: February 13, 2026*
*Source: Direct codebase analysis of Trinity Consortium platform*
*Totals: 51 database tables, 379 API endpoints, 55 AI agents (20 primary + 35 sub-agents), 363+ tools (187 agent tools + 58 mineral development skills + 118 base skills), 21 frontend routes, 128 unit tests*
