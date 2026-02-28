/**
 * Tax God Agent Registration for Trinity Consortium
 *
 * This file defines how Tax God integrates as an agent within the Trinity Consortium's
 * 55-agent system. Tax God becomes the tax/finance/legal specialist among the Trinity Council.
 */

import { taxGodAgent, taxGodAgentSchema, TaxGodAgent } from './tax-god-agent';

// Trinity Consortium Agent Registry Entry
export const TAX_GOD_AGENT_CONFIG = {
  // Basic Agent Information
  id: "tax-god",
  name: "Tax God",
  title: "Chief Tax, Financial & Legal Advisor",
  description: "AI-powered tax co-pilot providing comprehensive tax, financial, and legal advisory services",

  // Model Configuration
  primaryModel: "gpt-5.2",
  fallbackModels: ["claude-sonnet-4.5", "gemini-2.5-pro"],
  costPerTask: 0.15, // $0.15 per task

  // Authority & Permissions
  authorityLevel: 4, // High authority for financial/tax decisions
  clearanceLevel: "financial", // Access to financial data and decisions
  canDelegate: true,
  canSpawn: true, // Can spawn specialized sub-agents
  canOverride: false, // Cannot override Warden

  // Specialization Areas
  specializations: [
    "tax_preparation",
    "tax_planning",
    "tax_optimization",
    "financial_analysis",
    "legal_counsel",
    "entity_structuring",
    "audit_defense",
    "compliance",
    "multi_jurisdiction_tax",
    "estate_planning"
  ],

  // Capabilities
  capabilities: [
    "dtda_decomposition",      // Dynamic Task Decomposition Algorithm
    "imra_memory",             // Intelligent Memory Retrieval Algorithm
    "shva_validation",         // Self-Healing Validation Algorithm
    "agent_spawning",          // Can spawn specialized sub-agents
    "cross_jurisdiction",      // Multi-state/international tax
    "real_time_monitoring",    // Tax law change monitoring
    "confidence_scoring",      // Quality assurance scoring
    "citation_management",     // IRC/regulation citations
    "risk_assessment",         // Tax risk evaluation
    "strategy_optimization"    // Tax strategy optimization
  ],

  // Communication Protocols
  supportedMessageTypes: [
    "request", "response", "delegate", "broadcast", "spawn"
  ],

  // Integration Points
  apiEndpoints: {
    taxAnalysis: "/api/v1/advanced/query",
    taskDecomposition: "/api/v1/advanced/decompose",
    memoryRetrieval: "/api/v1/advanced/memory",
    validation: "/api/v1/advanced/validate",
    health: "/api/v1/advanced/health"
  },

  // Sub-Agent Templates (for spawning)
  subAgentTemplates: {
    state_specialist: {
      specialization: "state_tax_{jurisdiction}",
      model: "claude-sonnet-4.5",
      costPerTask: 0.12,
      capabilities: ["state_specific_tax", "nexus_analysis"],
      lifespan: 24 * 60 * 60 * 1000 // 24 hours
    },

    audit_defense: {
      specialization: "audit_defense",
      model: "gpt-4.1",
      costPerTask: 0.08,
      capabilities: ["audit_response", "penalty_abatement", "idrs"],
      lifespan: 7 * 24 * 60 * 60 * 1000 // 1 week
    },

    entity_specialist: {
      specialization: "entity_structuring",
      model: "claude-opus-4.5",
      costPerTask: 0.20,
      capabilities: ["llc_formation", "corporate_structure", "compliance"],
      lifespan: 30 * 24 * 60 * 60 * 1000 // 30 days
    }
  },

  // Trinity Council Integration
  delegationRules: {
    // Can receive delegations from these agents
    acceptsFrom: ["oracle", "prophet", "chancellor", "warden", "liaison"],

    // Will delegate to these agents when appropriate
    delegatesTo: ["oracle", "researcher", "auditor", "engineer"],

    // Override authority (Tax God cannot be overridden except by Warden)
    canBeOverriddenBy: ["warden"]
  },

  // Monitoring & Reporting
  reporting: {
    metrics: ["queries_processed", "confidence_average", "agents_spawned", "cost_total"],
    alerts: ["low_confidence_responses", "spawned_agent_failures", "api_unavailable"],
    dashboards: ["tax_performance", "agent_utilization", "cost_analysis"]
  }
};

// Agent Health Check Function
export async function checkTaxGodHealth(): Promise<{
  status: "healthy" | "degraded" | "unhealthy";
  details: any;
}> {
  try {
    // Check Tax God API health
    const response = await fetch('http://localhost:8000/api/v1/advanced/health');

    if (response.ok) {
      const health = await response.json();
      return {
        status: health.status === "healthy" ? "healthy" : "degraded",
        details: health
      };
    } else {
      return {
        status: "unhealthy",
        details: { error: `HTTP ${response.status}` }
      };
    }
  } catch (error) {
    return {
      status: "unhealthy",
      details: { error: error.message }
    };
  }
}

// Agent Registration Function
export async function registerTaxGodAgent(): Promise<boolean> {
  try {
    // Health check first
    const health = await checkTaxGodHealth();
    if (health.status !== "healthy") {
      console.error("Tax God agent health check failed:", health.details);
      return false;
    }

    // Register with Trinity Consortium
    const registration = {
      ...TAX_GOD_AGENT_CONFIG,
      agentInstance: taxGodAgent,
      registrationTime: new Date().toISOString(),
      version: "3.0.0"
    };

    // In a real implementation, this would send to Trinity registration service
    console.log("Tax God agent registered with Trinity Consortium:", registration.id);

    return true;
  } catch (error) {
    console.error("Failed to register Tax God agent:", error);
    return false;
  }
}

// Message Routing Handler
export async function handleTrinityMessage(message: any): Promise<any> {
  return await taxGodAgent.receiveMessage(message);
}

// Export the configured agent
export { taxGodAgent };
export default taxGodAgent;