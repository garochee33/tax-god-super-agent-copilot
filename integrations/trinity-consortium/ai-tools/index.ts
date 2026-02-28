import { oracleTools } from "./oracle-tools";
import { liaisonTools } from "./liaison-tools";
import { wardenTools } from "./warden-tools";
import { engineerTools } from "./engineer-tools";
import { prophetTools } from "./prophet-tools";
import { auditorTools } from "./auditor-tools";
import { architectTools } from "./architect-tools";
import { curatorTools } from "./curator-tools";
import { emissaryTools } from "./emissary-tools";
import { scribeTools } from "./scribe-tools";
import { sentinelTools } from "./sentinel-tools";
import { chancellorTools } from "./chancellor-tools";
import { designerTools } from "./designer-tools";
import { producerTools } from "./producer-tools";
import { presenterTools } from "./presenter-tools";
import { researcherTools } from "./researcher-tools";
import { directorTools } from "./director-tools";
import { linguistTools } from "./linguist-tools";
import { reporterTools } from "./reporter-tools";

export const allTools = [
  ...oracleTools,
  ...liaisonTools,
  ...wardenTools,
  ...engineerTools,
  ...prophetTools,
  ...auditorTools,
  ...architectTools,
  ...curatorTools,
  ...emissaryTools,
  ...scribeTools,
  ...sentinelTools,
  ...chancellorTools,
  ...designerTools,
  ...producerTools,
  ...presenterTools,
  ...researcherTools,
  ...directorTools,
  ...linguistTools,
  ...reporterTools
];

export const toolsByAgent = {
  oracle: oracleTools,
  liaison: liaisonTools,
  warden: wardenTools,
  engineer: engineerTools,
  prophet: prophetTools,
  auditor: auditorTools,
  architect: architectTools,
  curator: curatorTools,
  emissary: emissaryTools,
  scribe: scribeTools,
  sentinel: sentinelTools,
  chancellor: chancellorTools,
  designer: designerTools,
  producer: producerTools,
  presenter: presenterTools,
  researcher: researcherTools,
  director: directorTools,
  linguist: linguistTools,
  reporter: reporterTools
};

export const agentInfo = {
  oracle: {
    name: "The Oracle",
    role: "Data Room Intelligence & RAG Search",
    description: "Semantic search, document summarization, cross-referencing, and knowledge graph queries.",
    toolCount: oracleTools.length,
    icon: "Search"
  },
  liaison: {
    name: "The Liaison",
    role: "Operations & Investor Relations",
    description: "Email communications, calendar management, CRM operations, and member onboarding.",
    toolCount: liaisonTools.length,
    icon: "Users"
  },
  warden: {
    name: "The Warden",
    role: "Security & Access Control",
    description: "Permission management, session control, watermarking, and breach detection.",
    toolCount: wardenTools.length,
    icon: "Shield"
  },
  engineer: {
    name: "The Engineer",
    role: "Technical Operations & Development",
    description: "System diagnostics, code generation, performance profiling, and deployment.",
    toolCount: engineerTools.length,
    icon: "Wrench"
  },
  prophet: {
    name: "The Prophet",
    role: "Strategic Analysis & Forecasting",
    description: "Market impact modeling, scenario analysis, ROI calculations, and risk assessment.",
    toolCount: prophetTools.length,
    icon: "TrendingUp"
  },
  auditor: {
    name: "The Auditor",
    role: "Compliance & Quality Assurance",
    description: "NI 43-101 scanning, brand consistency, code security, and document auditing.",
    toolCount: auditorTools.length,
    icon: "CheckCircle"
  },
  architect: {
    name: "The Architect",
    role: "System Design & Technical Planning",
    description: "Schema design, API specifications, dependency analysis, and tech debt tracking.",
    toolCount: architectTools.length,
    icon: "Layout"
  },
  curator: {
    name: "The Curator",
    role: "Content & Asset Management",
    description: "Object storage, file organization, versioning, thumbnails, and media transcoding.",
    toolCount: curatorTools.length,
    icon: "FolderOpen"
  },
  emissary: {
    name: "The Emissary",
    role: "External Integrations & API Orchestration",
    description: "Google Drive sync, Opus Clip, ElevenLabs voice, webhooks, and integration health.",
    toolCount: emissaryTools.length,
    icon: "Globe"
  },
  scribe: {
    name: "The Scribe",
    role: "Documentation & Content Creation",
    description: "Reports, presentations, newsletters, changelogs, investor decks, and FAQs.",
    toolCount: scribeTools.length,
    icon: "FileText"
  },
  sentinel: {
    name: "The Sentinel",
    role: "Monitoring & Alerting",
    description: "Health dashboards, alert dispatch, anomaly detection, and SLA monitoring.",
    toolCount: sentinelTools.length,
    icon: "Activity"
  },
  chancellor: {
    name: "The Chancellor",
    role: "Financial Operations & Treasury",
    description: "Investor ledger, capital stack, distributions, fee processing, and treasury.",
    toolCount: chancellorTools.length,
    icon: "DollarSign"
  },
  designer: {
    name: "The Designer",
    role: "Creative Design & Visual Assets",
    description: "Web design, UI mockups, image generation, branding, infographics, and social media assets.",
    toolCount: designerTools.length,
    icon: "Palette"
  },
  producer: {
    name: "The Producer",
    role: "Media Production & Video",
    description: "Video creation, editing, clipping, captions, thumbnails, animation, and storyboards.",
    toolCount: producerTools.length,
    icon: "Film"
  },
  presenter: {
    name: "The Presenter",
    role: "Presentations & Slideshows",
    description: "Slideshows, pitch decks, webinar slides, animations, and speaker notes.",
    toolCount: presenterTools.length,
    icon: "Presentation"
  },
  researcher: {
    name: "The Researcher",
    role: "Intelligence & Deep Search",
    description: "Multi-agent web search, topic research, fact-checking, competitive analysis, and knowledge mapping.",
    toolCount: researcherTools.length,
    icon: "Radar"
  },
  director: {
    name: "The Director",
    role: "Project Management & Organization",
    description: "Project planning, milestones, task assignment, sprints, risk assessment, and roadmaps.",
    toolCount: directorTools.length,
    icon: "Target"
  },
  linguist: {
    name: "The Linguist",
    role: "Voice & Language Processing",
    description: "Text-to-speech, speech-to-text, voice transformation, translation, and content moderation.",
    toolCount: linguistTools.length,
    icon: "Languages"
  },
  reporter: {
    name: "The Reporter",
    role: "Analytics & Detailed Reporting",
    description: "Detailed reports, spreadsheets, dashboards, financial analysis, market reports, and data exports.",
    toolCount: reporterTools.length,
    icon: "FileSpreadsheet"
  }
};

export type AgentId = keyof typeof toolsByAgent;

export type { AgentContext, ToolDefinition } from "./types";
