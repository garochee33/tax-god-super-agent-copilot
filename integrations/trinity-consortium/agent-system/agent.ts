import { chat, ChatMessage } from "../../integrations/ai-models";
import { AgentContext } from "../types";
import {
  AgentRole,
  AgentStep,
  ToolCall,
  TaskResult,
  DelegationRequest,
  CrewAgentId,
  ExecutionStatus,
  ThoughtType,
  ExecutionPolicy,
  AgentCommand,
  AgentCommandResult,
} from "./types";
import { memoryManager } from "./memory";

export const DEFAULT_EXECUTION_POLICY: ExecutionPolicy = {
  mode: "controlled",
  allowDelegation: false,
  maxIterations: 5,
  requireApproval: false,
};

export class AutonomousAgent {
  private role: AgentRole;
  private context: AgentContext;
  private steps: AgentStep[] = [];
  private maxIterations: number;
  private totalTokens: number = 0;
  private delegationHandler?: (request: DelegationRequest) => Promise<TaskResult>;
  private policy: ExecutionPolicy;

  constructor(role: AgentRole, context: AgentContext) {
    this.role = role;
    this.context = context;
    this.policy = { ...DEFAULT_EXECUTION_POLICY };
    this.maxIterations = this.policy.maxIterations;
  }

  setPolicy(policy: ExecutionPolicy): void {
    this.policy = { ...policy };
    this.maxIterations = this.policy.maxIterations;
  }

  setDelegationHandler(handler: (request: DelegationRequest) => Promise<TaskResult>): void {
    this.delegationHandler = handler;
  }

  async execute(goal: string, additionalContext?: string): Promise<TaskResult> {
    const taskId = `task_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const startTime = Date.now();
    const toolsUsed: string[] = [];
    const delegationResults: any[] = [];

    const workingMemory = memoryManager.createWorkingMemory(taskId, goal);

    const relevantMemories = memoryManager.recall(this.role.id, goal, 5);
    const memoryContext =
      relevantMemories.length > 0
        ? `\n\nRELEVANT MEMORIES FROM PAST TASKS:\n${relevantMemories.map(m => `- [${m.type}] ${m.key}: ${m.value} (confidence: ${m.confidence})`).join("\n")}`
        : "";

    try {
      const plan = await this.plan(goal, additionalContext || "", memoryContext);
      workingMemory.plan = plan;

      let iteration = 0;
      let finalResult = "";
      let completed = false;

      while (iteration < this.maxIterations && !completed) {
        iteration++;

        const reasoningResult = await this.reason(goal, workingMemory, iteration);

        if (reasoningResult.completed) {
          finalResult = reasoningResult.result || "";
          completed = true;
          this.addStep({
            type: "reflection",
            content: `Task completed after ${iteration} iterations.`,
          });
          break;
        }

        if (reasoningResult.toolCall) {
          const toolName = reasoningResult.toolCall.name;
          if (this.policy.blockedTools?.includes(toolName)) {
            this.addStep({
              type: "error",
              content: `Tool "${toolName}" is blocked by execution policy.`,
            });
            continue;
          }
          if (this.policy.allowedTools && !this.policy.allowedTools.includes(toolName)) {
            this.addStep({
              type: "error",
              content: `Tool "${toolName}" is not in the allowed tools list.`,
            });
            continue;
          }

          const toolResult = await this.executeTool(
            toolName,
            reasoningResult.toolCall.args
          );
          toolsUsed.push(toolName);

          const observation =
            typeof toolResult.result === "string"
              ? toolResult.result
              : JSON.stringify(toolResult.result, null, 2);

          memoryManager.addObservation(
            taskId,
            `[${reasoningResult.toolCall.name}]: ${observation.slice(0, 500)}`
          );
          workingMemory.completedSteps.push(`Executed ${reasoningResult.toolCall.name}`);

          this.addStep(
            {
              type: "observation",
              content: `Tool ${reasoningResult.toolCall.name} returned: ${observation.slice(0, 1000)}`,
            },
            toolResult
          );

          if (!toolResult.success) {
            const correction = await this.selfCorrect(
              goal,
              reasoningResult.toolCall.name,
              toolResult.error || "Unknown error",
              workingMemory
            );
            this.addStep({ type: "correction", content: correction });
          }
        }

        if (reasoningResult.delegation) {
          if (!this.policy.allowDelegation) {
            this.addStep({
              type: "error",
              content: `Delegation to ${reasoningResult.delegation.toAgent} blocked by execution policy (allowDelegation: false).`,
            });
            continue;
          }

          if (this.policy.allowedAgents && !this.policy.allowedAgents.includes(reasoningResult.delegation.toAgent)) {
            this.addStep({
              type: "error",
              content: `Delegation to ${reasoningResult.delegation.toAgent} blocked: agent not in allowedAgents list.`,
            });
            continue;
          }

          const delegationReq: DelegationRequest = {
            fromAgent: this.role.id,
            toAgent: reasoningResult.delegation.toAgent,
            task: reasoningResult.delegation.task,
            context: reasoningResult.delegation.context,
            priority: reasoningResult.delegation.priority || "medium",
          };

          this.addStep({
            type: "delegation",
            content: `Delegating to ${delegationReq.toAgent}: ${delegationReq.task}`,
          });

          if (this.delegationHandler) {
            const delegationResult = await this.delegationHandler(delegationReq);
            delegationResults.push({ request: delegationReq, result: delegationResult });
            memoryManager.addObservation(
              taskId,
              `Delegation to ${delegationReq.toAgent} completed: ${delegationResult.result.slice(0, 500)}`
            );
            workingMemory.completedSteps.push(`Delegated to ${delegationReq.toAgent}`);
          }
        }
      }

      if (!completed) {
        finalResult = await this.synthesize(goal, workingMemory);
        this.addStep({
          type: "reflection",
          content: `Reached max iterations (${this.maxIterations}). Synthesizing best available result.`,
        });
      }

      this.extractAndStoreMemories(goal, finalResult, workingMemory);
      memoryManager.clearWorkingMemory(taskId);

      return {
        taskId,
        agentId: this.role.id,
        status: "completed" as ExecutionStatus,
        goal,
        result: finalResult,
        steps: this.steps,
        delegations: delegationResults,
        startTime,
        endTime: Date.now(),
        totalDuration: Date.now() - startTime,
        tokensUsed: this.totalTokens,
        toolsUsed: Array.from(new Set(toolsUsed)),
        iterations: this.steps.length,
        success: true,
      };
    } catch (error: any) {
      memoryManager.clearWorkingMemory(taskId);
      return {
        taskId,
        agentId: this.role.id,
        status: "failed" as ExecutionStatus,
        goal,
        result: "",
        steps: this.steps,
        delegations: delegationResults,
        startTime,
        endTime: Date.now(),
        totalDuration: Date.now() - startTime,
        tokensUsed: this.totalTokens,
        toolsUsed: Array.from(new Set(toolsUsed)),
        iterations: this.steps.length,
        success: false,
        error: error.message,
      };
    }
  }

  private async plan(goal: string, additionalContext: string, memoryContext: string): Promise<string[]> {
    const toolDescriptions = this.role.tools
      .map(t => `- ${t.name}: ${t.description}`)
      .join("\n");
    const delegationOptions =
      this.role.delegatesTo.length > 0
        ? `\nYou can delegate subtasks to: ${this.role.delegatesTo.join(", ")}`
        : "";

    const messages: ChatMessage[] = [
      {
        role: "system",
        content: `You are ${this.role.name} (${this.role.title}) — an autonomous AI agent in the Trinity Council.

ROLE: ${this.role.role}
GOAL: ${this.role.goal}
BACKSTORY: ${this.role.backstory}

You are creating an execution plan. Think step by step about how to accomplish the given goal.

AVAILABLE TOOLS:
${toolDescriptions}
${delegationOptions}
${memoryContext}

Output a JSON array of step strings. Each step should be a clear, actionable instruction.
Example: ["Step 1: Use search_data_room to find relevant documents", "Step 2: Analyze results", "Step 3: Synthesize findings"]

Output ONLY the JSON array, no other text.`,
      },
      {
        role: "user",
        content: `GOAL: ${goal}\n${additionalContext ? `\nADDITIONAL CONTEXT: ${additionalContext}` : ""}`,
      },
    ];

    const response = await chat({
      model: this.role.preferredModel,
      messages,
      maxTokens: 1024,
      temperature: 0.3,
    });
    this.totalTokens += response.usage?.totalTokens || 0;

    try {
      const cleaned = response.content
        .replace(/```json\n?/g, "")
        .replace(/```\n?/g, "")
        .trim();
      const parsed = JSON.parse(cleaned);
      const plan = Array.isArray(parsed) ? parsed : [response.content];
      this.addStep({
        type: "planning",
        content: `Created execution plan with ${plan.length} steps:\n${plan.map((s: string, i: number) => `${i + 1}. ${s}`).join("\n")}`,
      });
      return plan;
    } catch {
      const plan = [goal];
      this.addStep({ type: "planning", content: `Single-step plan: ${goal}` });
      return plan;
    }
  }

  private async reason(
    goal: string,
    workingMemory: any,
    iteration: number
  ): Promise<{
    completed: boolean;
    result?: string;
    toolCall?: { name: string; args: Record<string, any> };
    delegation?: {
      toAgent: CrewAgentId;
      task: string;
      context: string;
      priority?: "low" | "medium" | "high" | "critical";
    };
  }> {
    const toolDescriptions = this.role.tools
      .map(t => `- ${t.name}: ${t.description}`)
      .join("\n");

    const recentObservations = workingMemory.observations
      .slice(-10)
      .map((o: string, i: number) => `  ${i + 1}. ${o}`)
      .join("\n");
    const completedSteps = workingMemory.completedSteps
      .map((s: string, i: number) => `  ${i + 1}. ${s}`)
      .join("\n");
    const planSteps = workingMemory.plan
      .map((s: string, i: number) => `  ${i + 1}. ${s}`)
      .join("\n");

    const delegationOptions =
      this.role.delegatesTo.length > 0
        ? `\nDELEGATION: You can delegate subtasks to these specialists: ${this.role.delegatesTo.join(", ")}`
        : "";

    const messages: ChatMessage[] = [
      {
        role: "system",
        content: `You are ${this.role.name} (${this.role.title}) — an autonomous agent executing a task.

${this.role.systemPrompt}

You are in iteration ${iteration}/${this.maxIterations} of your ReAct loop.

EXECUTION PLAN:
${planSteps || "  (no plan yet)"}

COMPLETED STEPS:
${completedSteps || "  (none yet)"}

RECENT OBSERVATIONS:
${recentObservations || "  (none yet)"}

AVAILABLE TOOLS:
${toolDescriptions}
${delegationOptions}

INSTRUCTIONS:
Analyze the current state and decide your next action. You MUST respond with a JSON object in ONE of these formats:

1. To use a tool:
{"action": "tool", "tool": "tool_name", "args": {...}, "reasoning": "why this tool"}

2. To delegate to another agent:
{"action": "delegate", "toAgent": "agent_id", "task": "what to do", "context": "relevant context", "priority": "medium", "reasoning": "why delegate"}

3. To complete the task (you have enough information):
{"action": "complete", "result": "your comprehensive final answer in markdown", "reasoning": "why complete now"}

Think carefully: Do you have enough information to provide a complete answer? If yes, use "complete". If not, use a tool or delegate.

Output ONLY the JSON object.`,
      },
      {
        role: "user",
        content: `GOAL: ${goal}`,
      },
    ];

    const response = await chat({
      model: this.role.preferredModel,
      messages,
      maxTokens: 4096,
      temperature: 0.4,
    });
    this.totalTokens += response.usage?.totalTokens || 0;

    try {
      const content = response.content
        .replace(/```json\n?/g, "")
        .replace(/```\n?/g, "")
        .trim();
      const decision = JSON.parse(content);

      this.addStep({
        type: "reasoning",
        content: decision.reasoning || `Iteration ${iteration}: Decided to ${decision.action}`,
      });

      if (decision.action === "complete") {
        return { completed: true, result: decision.result };
      }

      if (decision.action === "tool") {
        return {
          completed: false,
          toolCall: { name: decision.tool, args: decision.args || {} },
        };
      }

      if (decision.action === "delegate") {
        return {
          completed: false,
          delegation: {
            toAgent: decision.toAgent as CrewAgentId,
            task: decision.task,
            context: decision.context || "",
            priority: decision.priority || "medium",
          },
        };
      }

      return { completed: true, result: response.content };
    } catch {
      return { completed: true, result: response.content };
    }
  }

  private async executeTool(toolName: string, args: Record<string, any>): Promise<ToolCall> {
    const startTime = Date.now();
    const tool = this.role.tools.find(t => t.name === toolName);

    if (!tool) {
      return {
        toolName,
        args,
        result: null,
        duration: Date.now() - startTime,
        success: false,
        error: `Tool "${toolName}" not found in ${this.role.name}'s toolkit`,
        timestamp: startTime,
      };
    }

    try {
      const validationResult = tool.schema.safeParse(args);
      if (!validationResult.success) {
        return {
          toolName,
          args,
          result: null,
          duration: Date.now() - startTime,
          success: false,
          error: `Validation failed: ${validationResult.error.issues.map(i => i.message).join(", ")}`,
          timestamp: startTime,
        };
      }

      const result = await tool.execute(validationResult.data, this.context);
      return {
        toolName,
        args: validationResult.data,
        result,
        duration: Date.now() - startTime,
        success: true,
        timestamp: startTime,
      };
    } catch (error: any) {
      return {
        toolName,
        args,
        result: null,
        duration: Date.now() - startTime,
        success: false,
        error: error.message,
        timestamp: startTime,
      };
    }
  }

  private async selfCorrect(
    goal: string,
    failedTool: string,
    error: string,
    _workingMemory: any
  ): Promise<string> {
    const messages: ChatMessage[] = [
      {
        role: "system",
        content: `You are ${this.role.name}. A tool execution failed. Analyze the error and suggest a correction strategy.

FAILED TOOL: ${failedTool}
ERROR: ${error}
CURRENT GOAL: ${goal}

Provide a brief correction strategy (1-2 sentences).`,
      },
      { role: "user", content: "What should we try differently?" },
    ];

    const response = await chat({
      model: this.role.preferredModel,
      messages,
      maxTokens: 256,
      temperature: 0.3,
    });
    this.totalTokens += response.usage?.totalTokens || 0;
    return response.content;
  }

  private async synthesize(goal: string, workingMemory: any): Promise<string> {
    const observations = workingMemory.observations.join("\n");
    const messages: ChatMessage[] = [
      {
        role: "system",
        content: `You are ${this.role.name} (${this.role.title}). Synthesize all gathered information into a comprehensive final response.

${this.role.systemPrompt}`,
      },
      {
        role: "user",
        content: `GOAL: ${goal}\n\nGATHERED INFORMATION:\n${observations}\n\nProvide a comprehensive, well-structured response in markdown.`,
      },
    ];

    const response = await chat({
      model: this.role.preferredModel,
      messages,
      maxTokens: 4096,
      temperature: 0.5,
    });
    this.totalTokens += response.usage?.totalTokens || 0;
    return response.content;
  }

  private extractAndStoreMemories(goal: string, result: string, workingMemory: any): void {
    memoryManager.store(
      this.role.id,
      "skill",
      `completed_task_${Date.now()}`,
      `Goal: ${goal.slice(0, 200)} | Result: ${result.slice(0, 200)}`,
      0.8,
      "task_execution"
    );

    for (const obs of workingMemory.observations) {
      const investorMatch = obs.match(/investor[:\s]+(\w+)/i);
      if (investorMatch) {
        memoryManager.upsertEntity({
          entityId: `investor_${investorMatch[1].toLowerCase()}`,
          entityType: "investor",
          name: investorMatch[1],
          attributes: { mentionedIn: goal },
          relationships: [],
        });
      }

      const projectMatch = obs.match(/project[:\s]+(\w+)/i);
      if (projectMatch) {
        memoryManager.upsertEntity({
          entityId: `project_${projectMatch[1].toLowerCase()}`,
          entityType: "project",
          name: projectMatch[1],
          attributes: { mentionedIn: goal },
          relationships: [],
        });
      }
    }
  }

  private addStep(thought: { type: ThoughtType; content: string }, toolCall?: ToolCall): void {
    this.steps.push({
      stepNumber: this.steps.length + 1,
      thought: {
        type: thought.type,
        content: thought.content,
        timestamp: Date.now(),
      },
      action: toolCall,
      timestamp: Date.now(),
    });
  }

  async executeCommand(command: AgentCommand): Promise<AgentCommandResult> {
    const commandId = `cmd_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const startTime = Date.now();

    if (command.policy) {
      this.setPolicy({ ...DEFAULT_EXECUTION_POLICY, ...command.policy });
    }

    this.steps = [];
    this.totalTokens = 0;

    try {
      const taskResult = await this.execute(command.command, command.context);

      return {
        commandId,
        agentId: this.role.id,
        command: command.command,
        response: taskResult.result,
        steps: taskResult.steps,
        toolsUsed: taskResult.toolsUsed,
        delegations: taskResult.delegations,
        tokensUsed: taskResult.tokensUsed,
        duration: Date.now() - startTime,
        success: taskResult.success,
        error: taskResult.error,
      };
    } catch (error: any) {
      return {
        commandId,
        agentId: this.role.id,
        command: command.command,
        response: "",
        steps: this.steps,
        toolsUsed: [],
        delegations: [],
        tokensUsed: this.totalTokens,
        duration: Date.now() - startTime,
        success: false,
        error: error.message,
      };
    }
  }

  getSteps(): AgentStep[] {
    return this.steps;
  }

  getRole(): AgentRole {
    return this.role;
  }
}
