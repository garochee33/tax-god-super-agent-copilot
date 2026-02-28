import { chat, ChatMessage, AIModel } from "../../integrations/ai-models";
import { AgentContext } from "../types";
import { CrewAgentId } from "./types";

export type WorkflowNodeType = "prompt" | "tool" | "agent" | "decision" | "transform" | "parallel" | "input" | "output";

export type WorkflowNode = {
  id: string;
  type: WorkflowNodeType;
  label: string;
  config: Record<string, any>;
};

export type WorkflowEdge = {
  id: string;
  from: string;
  to: string;
  condition?: string;
  label?: string;
};

export type WorkflowState = Record<string, any>;

export type WorkflowDefinition = {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  initialState: WorkflowState;
  model?: AIModel;
};

export type WorkflowStepResult = {
  nodeId: string;
  nodeType: WorkflowNodeType;
  input: WorkflowState;
  output: WorkflowState;
  duration: number;
  success: boolean;
  error?: string;
};

export type WorkflowExecutionResult = {
  workflowId: string;
  status: "completed" | "failed" | "paused";
  steps: WorkflowStepResult[];
  finalState: WorkflowState;
  totalDuration: number;
  tokensUsed: number;
};

const MAX_ITERATIONS = 50;

export class WorkflowEngine {
  private definition: WorkflowDefinition;
  private context: AgentContext;
  private state: WorkflowState;
  private steps: WorkflowStepResult[];
  private tokensUsed: number;
  private iterations: number;
  private nodeMap: Map<string, WorkflowNode>;

  constructor(definition: WorkflowDefinition, context: AgentContext) {
    this.definition = definition;
    this.context = context;
    this.state = { ...definition.initialState };
    this.steps = [];
    this.tokensUsed = 0;
    this.iterations = 0;
    this.nodeMap = new Map(definition.nodes.map(n => [n.id, n]));
  }

  async execute(input?: WorkflowState): Promise<WorkflowExecutionResult> {
    const startTime = Date.now();

    if (input) {
      this.state = { ...this.state, ...input };
    }

    const inputNode = this.definition.nodes.find(n => n.type === "input");
    if (!inputNode) {
      return {
        workflowId: this.definition.id,
        status: "failed",
        steps: [],
        finalState: this.state,
        totalDuration: Date.now() - startTime,
        tokensUsed: 0,
      };
    }

    const queue: string[] = [inputNode.id];
    const visited = new Set<string>();

    while (queue.length > 0 && this.iterations < MAX_ITERATIONS) {
      const currentNodeId = queue.shift()!;
      this.iterations++;

      const node = this.nodeMap.get(currentNodeId);
      if (!node) continue;

      if (visited.has(currentNodeId) && node.type !== "decision") {
        continue;
      }
      visited.add(currentNodeId);

      const stepStart = Date.now();
      const inputSnapshot = { ...this.state };
      let stepOutput: WorkflowState = {};
      let success = true;
      let error: string | undefined;

      try {
        switch (node.type) {
          case "input":
            stepOutput = this.executeInputNode(node);
            break;
          case "output":
            stepOutput = this.executeOutputNode(node);
            break;
          case "prompt":
            stepOutput = await this.executePromptNode(node);
            break;
          case "tool":
            stepOutput = this.executeToolNode(node);
            break;
          case "agent":
            stepOutput = this.executeAgentNode(node);
            break;
          case "decision":
            stepOutput = await this.executeDecisionNode(node);
            break;
          case "transform":
            stepOutput = this.executeTransformNode(node);
            break;
          case "parallel":
            stepOutput = await this.executeParallelNode(node);
            break;
        }
        this.state = { ...this.state, ...stepOutput };
      } catch (err: any) {
        success = false;
        error = err.message || String(err);
      }

      this.steps.push({
        nodeId: currentNodeId,
        nodeType: node.type,
        input: inputSnapshot,
        output: stepOutput,
        duration: Date.now() - stepStart,
        success,
        error,
      });

      if (!success) {
        return {
          workflowId: this.definition.id,
          status: "failed",
          steps: this.steps,
          finalState: this.state,
          totalDuration: Date.now() - startTime,
          tokensUsed: this.tokensUsed,
        };
      }

      if (node.type === "decision" && stepOutput._nextNodeId) {
        queue.push(stepOutput._nextNodeId);
        delete this.state._nextNodeId;
      } else {
        const nextNodes = this.getNextNodes(currentNodeId);
        for (const nextId of nextNodes) {
          queue.push(nextId);
        }
      }
    }

    return {
      workflowId: this.definition.id,
      status: "completed",
      steps: this.steps,
      finalState: this.state,
      totalDuration: Date.now() - startTime,
      tokensUsed: this.tokensUsed,
    };
  }

  private executeInputNode(node: WorkflowNode): WorkflowState {
    return { _inputReceived: true };
  }

  private executeOutputNode(node: WorkflowNode): WorkflowState {
    const format = node.config.format as string | undefined;
    if (format === "json") {
      return { _output: JSON.stringify(this.state) };
    }
    return { _output: this.state };
  }

  private async executePromptNode(node: WorkflowNode): Promise<WorkflowState> {
    const template = node.config.template as string;
    const model: AIModel = (node.config.model as AIModel) || this.definition.model || "gemini-2.5-flash";

    let prompt = template;
    for (const [key, value] of Object.entries(this.state)) {
      prompt = prompt.replace(new RegExp(`\\{\\{${key}\\}\\}`, "g"), String(value));
    }

    const messages: ChatMessage[] = [
      { role: "system", content: "You are a workflow processing agent. Respond with clear, structured output." },
      { role: "user", content: prompt },
    ];

    const response = await chat({ model, messages, maxTokens: 2048, temperature: 0.7 });

    if (response.usage) {
      this.tokensUsed += response.usage.totalTokens;
    }

    return { [node.id + "_result"]: response.content };
  }

  private executeToolNode(node: WorkflowNode): WorkflowState {
    const toolName = node.config.toolName as string;
    const args = (node.config.args as Record<string, any>) || {};
    return {
      [node.id + "_result"]: {
        toolName,
        args,
        status: "pending",
        message: `Tool '${toolName}' execution is handled by the agent layer`,
      },
    };
  }

  private executeAgentNode(node: WorkflowNode): WorkflowState {
    const agentId = node.config.agentId as CrewAgentId;
    const command = node.config.command as string;
    return {
      [node.id + "_result"]: {
        agentId,
        command,
        status: "pending",
        message: `Agent '${agentId}' command '${command}' is delegated to the crew system`,
      },
    };
  }

  private async executeDecisionNode(node: WorkflowNode): Promise<WorkflowState> {
    const conditions = node.config.conditions as Array<{ condition: string; targetNodeId: string }>;
    const defaultTarget = node.config.defaultTarget as string;

    const stateDescription = Object.entries(this.state)
      .filter(([k]) => !k.startsWith("_"))
      .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
      .join("\n");

    const conditionDescriptions = conditions
      .map((c, i) => `${i + 1}. "${c.condition}" -> go to node "${c.targetNodeId}"`)
      .join("\n");

    const messages: ChatMessage[] = [
      {
        role: "system",
        content: "You are a decision engine. Given the current state and conditions, respond with ONLY the number of the matching condition. If none match, respond with 0.",
      },
      {
        role: "user",
        content: `Current state:\n${stateDescription}\n\nConditions:\n${conditionDescriptions}\n\nWhich condition is met? Respond with the number only.`,
      },
    ];

    const model: AIModel = this.definition.model || "gemini-2.5-flash";
    const response = await chat({ model, messages, maxTokens: 16, temperature: 0 });

    if (response.usage) {
      this.tokensUsed += response.usage.totalTokens;
    }

    const choiceNum = parseInt(response.content.trim(), 10);
    let targetNodeId = defaultTarget;

    if (choiceNum > 0 && choiceNum <= conditions.length) {
      targetNodeId = conditions[choiceNum - 1].targetNodeId;
    }

    return { _nextNodeId: targetNodeId, [node.id + "_decision"]: targetNodeId };
  }

  private executeTransformNode(node: WorkflowNode): WorkflowState {
    const transformFn = node.config.transformFn as string;
    try {
      const fn = new Function("state", `return (${transformFn})(state)`);
      const result = fn(this.state);
      if (typeof result === "object" && result !== null) {
        return result as WorkflowState;
      }
      return { [node.id + "_result"]: result };
    } catch (err: any) {
      return { [node.id + "_error"]: err.message };
    }
  }

  private async executeParallelNode(node: WorkflowNode): Promise<WorkflowState> {
    const nodeIds = node.config.nodeIds as string[];
    const results = await Promise.all(
      nodeIds.map(async (id) => {
        const parallelNode = this.nodeMap.get(id);
        if (!parallelNode) return { [id + "_error"]: "Node not found" };

        switch (parallelNode.type) {
          case "prompt":
            return this.executePromptNode(parallelNode);
          case "tool":
            return this.executeToolNode(parallelNode);
          case "agent":
            return this.executeAgentNode(parallelNode);
          case "transform":
            return this.executeTransformNode(parallelNode);
          default:
            return { [id + "_result"]: "Unsupported parallel node type: " + parallelNode.type };
        }
      })
    );

    let merged: WorkflowState = {};
    for (const r of results) {
      merged = { ...merged, ...r };
    }
    return merged;
  }

  getNextNodes(currentNodeId: string): string[] {
    return this.definition.edges
      .filter(e => e.from === currentNodeId)
      .map(e => e.to);
  }
}

export const WORKFLOW_PRESETS: Record<string, WorkflowDefinition> = {
  document_analysis: {
    id: "document_analysis",
    name: "Document Analysis",
    description: "Extracts, analyzes, and summarizes document content",
    model: "gemini-2.5-flash",
    initialState: {},
    nodes: [
      { id: "input", type: "input", label: "Document Input", config: { schema: { document: "string", title: "string" } } },
      { id: "extract", type: "prompt", label: "Extract Key Points", config: { template: "Extract all key facts, figures, and important points from the following document titled '{{title}}':\n\n{{document}}" } },
      { id: "analyze", type: "prompt", label: "Analyze Content", config: { template: "Analyze the following extracted points for themes, risks, and opportunities:\n\n{{extract_result}}" } },
      { id: "summarize", type: "prompt", label: "Summarize", config: { template: "Create a concise executive summary based on this analysis:\n\n{{analyze_result}}" } },
      { id: "output", type: "output", label: "Final Output", config: { format: "json" } },
    ],
    edges: [
      { id: "e1", from: "input", to: "extract" },
      { id: "e2", from: "extract", to: "analyze" },
      { id: "e3", from: "analyze", to: "summarize" },
      { id: "e4", from: "summarize", to: "output" },
    ],
  },

  investor_briefing: {
    id: "investor_briefing",
    name: "Investor Briefing",
    description: "Researches, analyzes, drafts, and reviews an investor briefing",
    model: "gemini-2.5-pro",
    initialState: {},
    nodes: [
      { id: "input", type: "input", label: "Briefing Input", config: { schema: { topic: "string", context: "string" } } },
      { id: "research", type: "prompt", label: "Research", config: { template: "Research the following investment topic and provide comprehensive findings:\n\nTopic: {{topic}}\nContext: {{context}}", model: "gemini-2.5-flash" as AIModel } },
      { id: "analyze", type: "prompt", label: "Analyze", config: { template: "Perform a deep analysis of these research findings for institutional investors:\n\n{{research_result}}" } },
      { id: "draft", type: "prompt", label: "Draft Briefing", config: { template: "Draft a professional investor briefing based on this analysis:\n\n{{analyze_result}}\n\nOriginal topic: {{topic}}" } },
      { id: "review", type: "prompt", label: "Review & Refine", config: { template: "Review this investor briefing for accuracy, completeness, and professional tone. Provide the final polished version:\n\n{{draft_result}}" } },
      { id: "output", type: "output", label: "Final Briefing", config: { format: "json" } },
    ],
    edges: [
      { id: "e1", from: "input", to: "research" },
      { id: "e2", from: "research", to: "analyze" },
      { id: "e3", from: "analyze", to: "draft" },
      { id: "e4", from: "draft", to: "review" },
      { id: "e5", from: "review", to: "output" },
    ],
  },

  due_diligence: {
    id: "due_diligence",
    name: "Due Diligence",
    description: "Parallel financial, legal, and market analysis merged into a comprehensive report",
    model: "gemini-2.5-pro",
    initialState: {},
    nodes: [
      { id: "input", type: "input", label: "Due Diligence Input", config: { schema: { company: "string", sector: "string", documents: "string" } } },
      { id: "financial_analysis", type: "prompt", label: "Financial Analysis", config: { template: "Perform a financial due diligence analysis for {{company}} in the {{sector}} sector. Available data:\n\n{{documents}}", model: "gemini-2.5-flash" as AIModel } },
      { id: "legal_analysis", type: "prompt", label: "Legal Analysis", config: { template: "Perform a legal due diligence review for {{company}} in the {{sector}} sector. Available data:\n\n{{documents}}", model: "gemini-2.5-flash" as AIModel } },
      { id: "market_analysis", type: "prompt", label: "Market Analysis", config: { template: "Perform a market due diligence analysis for {{company}} in the {{sector}} sector. Available data:\n\n{{documents}}", model: "gemini-2.5-flash" as AIModel } },
      { id: "parallel_exec", type: "parallel", label: "Parallel Analysis", config: { nodeIds: ["financial_analysis", "legal_analysis", "market_analysis"] } },
      { id: "merge", type: "transform", label: "Merge Results", config: { transformFn: "(state) => ({ merged_analysis: [state.financial_analysis_result, state.legal_analysis_result, state.market_analysis_result].filter(Boolean).join('\\n\\n---\\n\\n') })" } },
      { id: "report", type: "prompt", label: "Generate Report", config: { template: "Create a comprehensive due diligence report for {{company}} based on the following parallel analyses:\n\n{{merged_analysis}}" } },
      { id: "output", type: "output", label: "Final Report", config: { format: "json" } },
    ],
    edges: [
      { id: "e1", from: "input", to: "parallel_exec" },
      { id: "e2", from: "parallel_exec", to: "merge" },
      { id: "e3", from: "merge", to: "report" },
      { id: "e4", from: "report", to: "output" },
    ],
  },
};
