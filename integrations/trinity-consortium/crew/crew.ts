import {
  CrewAgentId,
  CrewConfig,
  MissionResult,
  TaskResult,
  DelegationRequest,
  AgentStep,
  AgentCommand,
  AgentCommandResult,
} from "./types";
import { AutonomousAgent } from "./agent";
import { getAgentRole } from "./agent-definitions";
import { AgentContext } from "../types";
import { chat, ChatMessage, AIModel } from "../../integrations/ai-models";
import { memoryManager } from "./memory";

export class Crew {
  private config: CrewConfig;
  private context: AgentContext;
  private agents: Map<CrewAgentId, AutonomousAgent> = new Map();
  private executionTrace: AgentStep[] = [];
  private totalTokens: number = 0;

  constructor(config: CrewConfig, context: AgentContext) {
    this.config = config;
    this.context = context;
    this.initializeAgents();
  }

  private initializeAgents(): void {
    for (const agentId of this.config.agents) {
      const role = getAgentRole(agentId);
      const agent = new AutonomousAgent(role, this.context);
      agent.setDelegationHandler(this.handleDelegation.bind(this));
      this.agents.set(agentId, agent);
    }
  }

  private async handleDelegation(request: DelegationRequest): Promise<TaskResult> {
    const targetRole = getAgentRole(request.toAgent);
    if (!targetRole) {
      return {
        taskId: `delegation_failed_${Date.now()}`,
        agentId: request.toAgent,
        status: "failed",
        goal: request.task,
        result: `Agent ${request.toAgent} not found`,
        steps: [],
        delegations: [],
        startTime: Date.now(),
        endTime: Date.now(),
        totalDuration: 0,
        tokensUsed: 0,
        toolsUsed: [],
        iterations: 0,
        success: false,
        error: `Agent ${request.toAgent} not available`,
      };
    }

    let agent = this.agents.get(request.toAgent);
    if (!agent) {
      agent = new AutonomousAgent(targetRole, this.context);
      agent.setDelegationHandler(this.handleDelegation.bind(this));
      this.agents.set(request.toAgent, agent);
    }

    const result = await agent.execute(
      request.task,
      `Delegated from ${request.fromAgent}: ${request.context}`
    );

    this.totalTokens += result.tokensUsed;
    this.executionTrace.push(...result.steps);

    return result;
  }

  async executeMission(goal: string): Promise<MissionResult> {
    const missionId = `mission_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const startTime = Date.now();
    const taskResults: TaskResult[] = [];
    const agentsUsed: CrewAgentId[] = [];

    try {
      if (this.config.process === "hierarchical") {
        return await this.executeHierarchical(missionId, goal, startTime);
      } else {
        return await this.executeSequential(missionId, goal, startTime);
      }
    } catch (error: any) {
      return {
        missionId,
        crewConfig: this.config,
        tasks: taskResults,
        finalOutput: `Mission failed: ${error.message}`,
        agentsUsed,
        totalDuration: Date.now() - startTime,
        totalTokens: this.totalTokens,
        success: false,
        executionTrace: this.executionTrace,
      };
    }
  }

  private async executeHierarchical(
    missionId: string,
    goal: string,
    startTime: number
  ): Promise<MissionResult> {
    const managerId = this.config.managerAgent || this.selectBestManager(goal);
    const taskResults: TaskResult[] = [];
    const agentsUsed: CrewAgentId[] = [managerId];

    const decomposition = await this.decomposeGoal(managerId, goal);

    for (const subTask of decomposition) {
      let agent = this.agents.get(subTask.agentId as CrewAgentId);
      if (!agent) {
        const role = getAgentRole(subTask.agentId as CrewAgentId);
        if (!role) continue;
        agent = new AutonomousAgent(role, this.context);
        agent.setDelegationHandler(this.handleDelegation.bind(this));
        this.agents.set(subTask.agentId as CrewAgentId, agent);
      }

      agentsUsed.push(subTask.agentId as CrewAgentId);
      const result = await agent.execute(subTask.task, subTask.context);
      taskResults.push(result);
      this.totalTokens += result.tokensUsed;
      this.executionTrace.push(...result.steps);
    }

    const finalOutput = await this.synthesizeMission(managerId, goal, taskResults);

    return {
      missionId,
      crewConfig: this.config,
      tasks: taskResults,
      finalOutput,
      agentsUsed: Array.from(new Set(agentsUsed)),
      totalDuration: Date.now() - startTime,
      totalTokens: this.totalTokens,
      success: taskResults.every(r => r.success),
      executionTrace: this.executionTrace,
    };
  }

  private async executeSequential(
    missionId: string,
    goal: string,
    startTime: number
  ): Promise<MissionResult> {
    const taskResults: TaskResult[] = [];
    const agentsUsed: CrewAgentId[] = [];

    const bestAgent = this.selectBestAgent(goal);
    agentsUsed.push(bestAgent);

    const agent = this.agents.get(bestAgent);
    if (!agent) {
      return {
        missionId,
        crewConfig: this.config,
        tasks: [],
        finalOutput: "No suitable agent found",
        agentsUsed: [],
        totalDuration: Date.now() - startTime,
        totalTokens: this.totalTokens,
        success: false,
        executionTrace: this.executionTrace,
      };
    }

    const result = await agent.execute(goal);
    taskResults.push(result);
    this.totalTokens += result.tokensUsed;
    this.executionTrace.push(...result.steps);

    for (const d of result.delegations) {
      agentsUsed.push(d.request.toAgent);
    }

    return {
      missionId,
      crewConfig: this.config,
      tasks: taskResults,
      finalOutput: result.result,
      agentsUsed: Array.from(new Set(agentsUsed)),
      totalDuration: Date.now() - startTime,
      totalTokens: this.totalTokens,
      success: result.success,
      executionTrace: this.executionTrace,
    };
  }

  private selectBestAgent(goal: string): CrewAgentId {
    const goalLower = goal.toLowerCase();
    const scores: Record<string, number> = {};

    for (const agentId of this.config.agents) {
      const role = getAgentRole(agentId);
      let score = 0;

      for (const kw of role.expertise) {
        if (goalLower.includes(kw.toLowerCase())) score += 10;
      }

      if (goalLower.includes(role.role.toLowerCase())) score += 5;

      const words = goalLower.split(/\s+/);
      for (const word of words) {
        if (role.goal.toLowerCase().includes(word) && word.length > 3) score += 2;
      }

      scores[agentId] = score;
    }

    const bestAgent = Object.entries(scores).sort(([, a], [, b]) => b - a)[0];
    return (bestAgent?.[0] || this.config.agents[0]) as CrewAgentId;
  }

  private selectBestManager(goal: string): CrewAgentId {
    const managerPriority: CrewAgentId[] = ["oracle", "engineer", "prophet", "liaison"];
    for (const id of managerPriority) {
      if (this.config.agents.includes(id)) return id;
    }
    return this.config.agents[0];
  }

  private async decomposeGoal(
    managerId: CrewAgentId,
    goal: string
  ): Promise<Array<{ agentId: string; task: string; context: string }>> {
    const availableAgents = this.config.agents
      .filter(id => id !== managerId)
      .map(id => {
        const role = getAgentRole(id);
        return `- ${id} (${role.name}): ${role.role}. Expertise: ${role.expertise.join(", ")}`;
      })
      .join("\n");

    const messages: ChatMessage[] = [
      {
        role: "system",
        content: `You are a mission manager. Decompose the given goal into sub-tasks and assign each to the most appropriate specialist agent.

AVAILABLE AGENTS:
${availableAgents}

Respond with a JSON array of objects:
[{"agentId": "agent_id", "task": "specific task", "context": "relevant context"}]

Rules:
1. Assign each sub-task to the single best agent
2. Keep sub-tasks focused and specific
3. Order them logically (dependencies first)
4. Use 1-5 sub-tasks maximum
5. Output ONLY the JSON array`,
      },
      {
        role: "user",
        content: `GOAL: ${goal}`,
      },
    ];

    const managerRole = getAgentRole(managerId);
    const response = await chat({
      model: managerRole.preferredModel,
      messages,
      maxTokens: 1024,
      temperature: 0.3,
    });
    this.totalTokens += response.usage?.totalTokens || 0;

    try {
      const content = response.content
        .replace(/```json\n?/g, "")
        .replace(/```\n?/g, "")
        .trim();
      const parsed = JSON.parse(content);
      return Array.isArray(parsed)
        ? parsed.filter((t: any) => this.config.agents.includes(t.agentId as CrewAgentId))
        : [{ agentId: this.config.agents[0], task: goal, context: "" }];
    } catch {
      return [{ agentId: this.config.agents[0], task: goal, context: "" }];
    }
  }

  private async synthesizeMission(
    managerId: CrewAgentId,
    goal: string,
    taskResults: TaskResult[]
  ): Promise<string> {
    const resultsSummary = taskResults
      .map(
        r =>
          `[${r.agentId} - ${r.success ? "SUCCESS" : "FAILED"}]: ${r.result.slice(0, 1000)}`
      )
      .join("\n\n---\n\n");

    const managerRole = getAgentRole(managerId);
    const messages: ChatMessage[] = [
      {
        role: "system",
        content: `You are ${managerRole.name}, synthesizing results from a multi-agent mission. Combine all agent outputs into a single, coherent, comprehensive response.

${managerRole.systemPrompt}`,
      },
      {
        role: "user",
        content: `ORIGINAL GOAL: ${goal}\n\nAGENT RESULTS:\n${resultsSummary}\n\nSynthesize into a comprehensive, well-structured final response.`,
      },
    ];

    const response = await chat({
      model: managerRole.preferredModel,
      messages,
      maxTokens: 4096,
      temperature: 0.5,
    });
    this.totalTokens += response.usage?.totalTokens || 0;
    return response.content;
  }

  async executeCommand(command: AgentCommand): Promise<AgentCommandResult> {
    const agentId = command.agentId;

    let agent = this.agents.get(agentId);
    if (!agent) {
      const role = getAgentRole(agentId);
      if (!role) {
        return {
          commandId: `cmd_failed_${Date.now()}`,
          agentId,
          command: command.command,
          response: "",
          steps: [],
          toolsUsed: [],
          delegations: [],
          tokensUsed: 0,
          duration: 0,
          success: false,
          error: `Agent "${agentId}" not found`,
        };
      }
      agent = new AutonomousAgent(role, this.context);
      agent.setDelegationHandler(this.handleDelegation.bind(this));
      this.agents.set(agentId, agent);
    }

    const result = await agent.executeCommand(command);
    this.totalTokens += result.tokensUsed;
    this.executionTrace.push(...result.steps);
    return result;
  }

  getExecutionTrace(): AgentStep[] {
    return this.executionTrace;
  }

  getMemoryStats() {
    return memoryManager.getStats();
  }
}

export const CREW_PRESETS: Record<string, CrewConfig> = {
  full_council: {
    id: "full_council",
    name: "Full Trinity Council",
    description: "All 12 agents working together on complex missions",
    agents: [
      "oracle", "liaison", "warden", "engineer", "prophet", "auditor",
      "architect", "curator", "emissary", "scribe", "sentinel", "chancellor",
    ],
    process: "hierarchical",
    managerAgent: "oracle",
    maxRounds: 5,
    verbose: true,
    memoryEnabled: true,
    model: "gpt-5.2" as AIModel,
  },
  due_diligence: {
    id: "due_diligence",
    name: "Due Diligence Crew",
    description: "Comprehensive investment due diligence analysis",
    agents: ["oracle", "prophet", "auditor", "chancellor", "warden"],
    process: "hierarchical",
    managerAgent: "oracle",
    maxRounds: 4,
    verbose: true,
    memoryEnabled: true,
    model: "gemini-2.5-pro" as AIModel,
  },
  content_creation: {
    id: "content_creation",
    name: "Content Creation Crew",
    description: "Professional content generation and publishing",
    agents: ["scribe", "curator", "auditor", "emissary"],
    process: "sequential",
    maxRounds: 3,
    verbose: true,
    memoryEnabled: true,
    model: "gpt-5.2" as AIModel,
  },
  security_audit: {
    id: "security_audit",
    name: "Security Audit Crew",
    description: "Comprehensive security and compliance review",
    agents: ["warden", "auditor", "sentinel", "engineer"],
    process: "hierarchical",
    managerAgent: "warden",
    maxRounds: 4,
    verbose: true,
    memoryEnabled: true,
    model: "claude-sonnet-4-5" as AIModel,
  },
  financial_analysis: {
    id: "financial_analysis",
    name: "Financial Analysis Crew",
    description: "Deep financial modeling and market analysis",
    agents: ["prophet", "chancellor", "oracle", "auditor"],
    process: "hierarchical",
    managerAgent: "prophet",
    maxRounds: 4,
    verbose: true,
    memoryEnabled: true,
    model: "gemini-2.5-pro" as AIModel,
  },
  ops_management: {
    id: "ops_management",
    name: "Operations Management Crew",
    description: "Day-to-day operations and investor management",
    agents: ["liaison", "scribe", "curator", "sentinel"],
    process: "sequential",
    maxRounds: 3,
    verbose: true,
    memoryEnabled: true,
    model: "gpt-5.2" as AIModel,
  },
  tech_ops: {
    id: "tech_ops",
    name: "Technical Operations Crew",
    description: "System maintenance, development, and monitoring",
    agents: ["engineer", "architect", "sentinel", "emissary"],
    process: "hierarchical",
    managerAgent: "engineer",
    maxRounds: 4,
    verbose: true,
    memoryEnabled: true,
    model: "claude-sonnet-4-5" as AIModel,
  },
};

export function createCrew(presetOrConfig: string | CrewConfig, context: AgentContext): Crew {
  const config =
    typeof presetOrConfig === "string"
      ? CREW_PRESETS[presetOrConfig] || CREW_PRESETS.full_council
      : presetOrConfig;
  return new Crew(config, context);
}
