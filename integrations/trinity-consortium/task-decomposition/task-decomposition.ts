/**
 * DTDA-lite: Dynamic Task Decomposition (Tax God–inspired).
 * Classifies Council requests, scores complexity, and returns an execution plan.
 */

export type RequestCategory =
  | "document_review"
  | "risk_compliance"
  | "summary_report"
  | "crm_ops"
  | "system_diagnostics"
  | "analytics_forecast"
  | "general";

export interface DecomposedSubtask {
  task: string;
  priority: number;
  description?: string;
}

export interface ExecutionPlan {
  executionPlan: "direct" | "sequential";
  category: RequestCategory;
  complexity: number;
  subtasks?: DecomposedSubtask[];
  suggestedAgents?: string[];
  estimatedMaxTurns?: number;
}

const CATEGORY_KEYWORDS: Record<RequestCategory, string[]> = {
  document_review: ["document", "vault", "summary", "analyze", "read", "file", "report", "pdf"],
  risk_compliance: ["compliance", "audit", "NI 43-101", "disclosure", "risk", "warden", "permission"],
  summary_report: ["summarize", "summary", "overview", "brief", "executive", "high-level"],
  crm_ops: ["meeting", "schedule", "email", "contact", "investor", "crm", "liaison"],
  system_diagnostics: ["health", "log", "diagnostic", "status", "engineer", "error"],
  analytics_forecast: ["forecast", "predict", "analytics", "trend", "prophet", "churn"],
  general: [],
};

function classifyRequest(message: string): RequestCategory {
  const lower = message.toLowerCase();
  const scores: Record<RequestCategory, number> = {
    document_review: 0,
    risk_compliance: 0,
    summary_report: 0,
    crm_ops: 0,
    system_diagnostics: 0,
    analytics_forecast: 0,
    general: 0,
  };

  for (const [cat, keywords] of Object.entries(CATEGORY_KEYWORDS) as [RequestCategory, string[]][]) {
    if (cat === "general") continue;
    scores[cat] = keywords.filter((kw) => lower.includes(kw)).length;
  }

  const best = (Object.entries(scores) as [RequestCategory, number][])
    .filter(([c]) => c !== "general")
    .sort((a, b) => b[1] - a[1])[0];

  return best && best[1] > 0 ? best[0] : "general";
}

function analyzeComplexity(message: string, category: RequestCategory): number {
  const words = message.split(/\s+/).length;
  const hasMultiPart = /(?:and|also|then|next|first|second)/i.test(message);
  const hasNumbers = /\d{2,}/.test(message);
  let score = 1;
  score += Math.min(words / 25, 2.5);
  if (hasMultiPart) score += 1.5;
  if (hasNumbers) score += 0.5;
  return Math.min(10, Math.round(score * 10) / 10);
}

function breakIntoSubtasks(message: string, category: RequestCategory): DecomposedSubtask[] {
  switch (category) {
    case "document_review":
      return [
        { task: "locate_documents", priority: 1, description: "Find relevant vault/knowledge documents" },
        { task: "extract_summarize", priority: 2, description: "Summarize and extract key points" },
        { task: "report_findings", priority: 3, description: "Present findings to user" },
      ];
    case "risk_compliance":
      return [
        { task: "check_permissions", priority: 1, description: "Warden permission check if needed" },
        { task: "run_compliance_scan", priority: 2, description: "Auditor compliance scan" },
        { task: "report_risks", priority: 3, description: "Report risks and recommendations" },
      ];
    case "summary_report":
      return [
        { task: "gather_sources", priority: 1, description: "Gather data room and activity context" },
        { task: "synthesize_summary", priority: 2, description: "Produce executive summary" },
      ];
    default:
      return [{ task: "execute", priority: 1, description: "Handle with Council tools" }];
  }
}

export function getExecutionPlan(message: string): ExecutionPlan {
  const category = classifyRequest(message);
  const complexity = analyzeComplexity(message, category);

  if (complexity < 3) {
    return {
      executionPlan: "direct",
      category,
      complexity,
      estimatedMaxTurns: 3,
    };
  }

  const subtasks = breakIntoSubtasks(message, category);
  const suggestedAgents: string[] = [];
  if (category === "document_review") suggestedAgents.push("oracle");
  if (category === "risk_compliance") suggestedAgents.push("warden", "auditor");
  if (category === "crm_ops") suggestedAgents.push("liaison");
  if (category === "system_diagnostics") suggestedAgents.push("engineer");
  if (category === "analytics_forecast") suggestedAgents.push("prophet");

  return {
    executionPlan: subtasks.length > 1 ? "sequential" : "direct",
    category,
    complexity,
    subtasks: subtasks.length > 1 ? subtasks : undefined,
    suggestedAgents: suggestedAgents.length > 0 ? suggestedAgents : undefined,
    estimatedMaxTurns: Math.min(8, 3 + subtasks.length),
  };
}
