import { db } from "../../db";
import { automationWorkflows, automationExecutions } from "@shared/schema";
import { eq } from "drizzle-orm";

export type AutomationNode = {
  id: string;
  type: string;
  label: string;
  config: Record<string, any>;
  position?: { x: number; y: number };
};

export type AutomationEdge = {
  id: string;
  source: string;
  target: string;
  label?: string;
};

export type AutomationStepResult = {
  nodeId: string;
  nodeType: string;
  label: string;
  status: "success" | "failed" | "skipped";
  input: Record<string, any>;
  output: Record<string, any>;
  duration: number;
  error?: string;
};

export class AutomationEngine {
  async execute(
    workflow: { id?: string; name?: string; nodes: AutomationNode[]; edges: AutomationEdge[] },
    input: Record<string, any> = {}
  ) {
    const workflowId = workflow.id || workflow.name || "preset";
    const [execution] = await db
      .insert(automationExecutions)
      .values({
        workflowId,
        status: "running",
        steps: [],
        input,
      })
      .returning();

    const steps: AutomationStepResult[] = [];
    let state: Record<string, any> = { ...input };
    let finalError: string | undefined;

    try {
      const targetSet = new Set(workflow.edges.map((e) => e.target));
      const startNodes = workflow.nodes.filter((n) => !targetSet.has(n.id));

      const order = this.topologicalSort(workflow.nodes, workflow.edges, startNodes);

      for (const node of order) {
        const stepStart = Date.now();
        const inputSnapshot = { ...state };
        let output: Record<string, any> = {};
        let status: "success" | "failed" = "success";
        let error: string | undefined;

        try {
          output = await this.executeNode(node, state, workflow.edges);
          state = { ...state, ...output };
        } catch (err: any) {
          status = "failed";
          error = err.message || String(err);
          finalError = error;
        }

        steps.push({
          nodeId: node.id,
          nodeType: node.type,
          label: node.label,
          status,
          input: inputSnapshot,
          output,
          duration: Date.now() - stepStart,
          error,
        });

        if (status === "failed") break;
      }

      const executionStatus = finalError ? "failed" : "completed";

      await db
        .update(automationExecutions)
        .set({
          status: executionStatus,
          finishedAt: new Date(),
          steps,
          output: state,
          error: finalError,
        })
        .where(eq(automationExecutions.id, execution.id));

      if (workflow.id) {
        await db
          .update(automationWorkflows)
          .set({
            lastRunAt: new Date(),
            lastRunResult: {
              executionId: execution.id,
              status: executionStatus,
              stepsCompleted: steps.filter((s) => s.status === "success").length,
              totalSteps: steps.length,
              error: finalError,
            },
            updatedAt: new Date(),
          })
          .where(eq(automationWorkflows.id, workflow.id));
      }

      return {
        executionId: execution.id,
        status: executionStatus,
        steps,
        output: state,
        error: finalError,
      };
    } catch (err: any) {
      await db
        .update(automationExecutions)
        .set({
          status: "failed",
          finishedAt: new Date(),
          steps,
          error: err.message || String(err),
        })
        .where(eq(automationExecutions.id, execution.id));

      throw err;
    }
  }

  private topologicalSort(
    nodes: AutomationNode[],
    edges: AutomationEdge[],
    startNodes: AutomationNode[]
  ): AutomationNode[] {
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const adjacency = new Map<string, string[]>();
    const inDegree = new Map<string, number>();

    for (const node of nodes) {
      adjacency.set(node.id, []);
      inDegree.set(node.id, 0);
    }

    for (const edge of edges) {
      adjacency.get(edge.source)?.push(edge.target);
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    }

    const queue: string[] = [];
    for (const node of nodes) {
      if ((inDegree.get(node.id) || 0) === 0) {
        queue.push(node.id);
      }
    }

    const sorted: AutomationNode[] = [];
    const visited = new Set<string>();

    while (queue.length > 0) {
      const id = queue.shift()!;
      if (visited.has(id)) continue;
      visited.add(id);

      const node = nodeMap.get(id);
      if (node) sorted.push(node);

      for (const neighbor of adjacency.get(id) || []) {
        const deg = (inDegree.get(neighbor) || 1) - 1;
        inDegree.set(neighbor, deg);
        if (deg === 0) {
          queue.push(neighbor);
        }
      }
    }

    return sorted;
  }

  private async executeNode(
    node: AutomationNode,
    state: Record<string, any>,
    edges: AutomationEdge[]
  ): Promise<Record<string, any>> {
    switch (node.type) {
      case "trigger":
        return this.executeTrigger(node, state);
      case "http_request":
        return this.executeHttpRequest(node, state);
      case "code":
        return this.executeCode(node, state);
      case "set_data":
        return this.executeSetData(node, state);
      case "if_condition":
        return this.executeIfCondition(node, state);
      case "switch":
        return this.executeSwitch(node, state);
      case "merge":
        return this.executeMerge(node, state);
      case "wait":
        return this.executeWait(node, state);
      case "email":
        return this.executeEmail(node, state);
      case "calendar":
        return this.executeCalendar(node, state);
      case "spreadsheet":
        return this.executeSpreadsheet(node, state);
      default:
        return { [`${node.id}_result`]: `Unknown node type: ${node.type}` };
    }
  }

  private executeTrigger(
    node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    const triggerType = node.config.triggerType || "manual";
    return {
      _triggerType: triggerType,
      _triggeredAt: new Date().toISOString(),
      ...state,
    };
  }

  private async executeHttpRequest(
    node: AutomationNode,
    state: Record<string, any>
  ): Promise<Record<string, any>> {
    const { url, method = "GET", headers = {}, body } = node.config;

    if (!url) {
      throw new Error("http_request node requires a url in config");
    }

    const resolvedUrl = this.interpolate(url, state);
    const resolvedHeaders: Record<string, string> = {};
    for (const [key, value] of Object.entries(headers)) {
      resolvedHeaders[key] = this.interpolate(String(value), state);
    }

    const fetchOptions: RequestInit = {
      method: method.toUpperCase(),
      headers: resolvedHeaders,
    };

    if (body && ["POST", "PUT", "PATCH"].includes(method.toUpperCase())) {
      fetchOptions.body =
        typeof body === "string"
          ? this.interpolate(body, state)
          : JSON.stringify(body);
      if (!resolvedHeaders["Content-Type"]) {
        resolvedHeaders["Content-Type"] = "application/json";
      }
    }

    const response = await fetch(resolvedUrl, fetchOptions);
    let responseData: any;

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      responseData = await response.json();
    } else {
      responseData = await response.text();
    }

    return {
      [`${node.id}_status`]: response.status,
      [`${node.id}_data`]: responseData,
      [`${node.id}_ok`]: response.ok,
    };
  }

  private executeCode(
    node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    const { code } = node.config;

    if (!code) {
      throw new Error("code node requires a code string in config");
    }

    try {
      const fn = new Function("data", code);
      const result = fn(state);
      if (typeof result === "object" && result !== null) {
        return result;
      }
      return { [`${node.id}_result`]: result };
    } catch (err: any) {
      throw new Error(`Code execution failed: ${err.message}`);
    }
  }

  private executeSetData(
    node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    const { fields = {} } = node.config;
    const resolved: Record<string, any> = {};

    for (const [key, value] of Object.entries(fields)) {
      if (typeof value === "string") {
        resolved[key] = this.interpolate(value, state);
      } else {
        resolved[key] = value;
      }
    }

    return resolved;
  }

  private executeIfCondition(
    node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    const { field, operator, value } = node.config;
    const fieldValue = state[field];
    let result = false;

    switch (operator) {
      case "eq":
        result = fieldValue == value;
        break;
      case "neq":
        result = fieldValue != value;
        break;
      case "gt":
        result = Number(fieldValue) > Number(value);
        break;
      case "lt":
        result = Number(fieldValue) < Number(value);
        break;
      case "contains":
        result = String(fieldValue).includes(String(value));
        break;
      case "exists":
        result = fieldValue !== undefined && fieldValue !== null;
        break;
      default:
        result = false;
    }

    return {
      [`${node.id}_result`]: result,
      _conditionResult: result,
      ...state,
    };
  }

  private executeSwitch(
    node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    const { field, cases = {} } = node.config;
    const fieldValue = String(state[field]);
    const matchedCase = (cases as Record<string, string>)[fieldValue] || "default";

    return {
      [`${node.id}_matched`]: matchedCase,
      [`${node.id}_value`]: fieldValue,
      _switchResult: matchedCase,
      ...state,
    };
  }

  private executeMerge(
    _node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    return { ...state };
  }

  private async executeWait(
    node: AutomationNode,
    state: Record<string, any>
  ): Promise<Record<string, any>> {
    const { seconds = 1 } = node.config;
    const waitMs = Math.min(Number(seconds) * 1000, 30000);

    await new Promise((resolve) => setTimeout(resolve, waitMs));

    return {
      [`${node.id}_waited`]: seconds,
      _waitedAt: new Date().toISOString(),
    };
  }

  private executeEmail(
    node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    const { to, subject, body } = node.config;
    const resolvedTo = this.interpolate(to || "", state);
    const resolvedSubject = this.interpolate(subject || "", state);
    const resolvedBody = this.interpolate(body || "", state);

    console.log(`[AutomationEngine] Email stub - To: ${resolvedTo}, Subject: ${resolvedSubject}, Body: ${resolvedBody.substring(0, 100)}...`);

    return {
      [`${node.id}_sent`]: true,
      [`${node.id}_to`]: resolvedTo,
      [`${node.id}_subject`]: resolvedSubject,
      _emailSent: true,
    };
  }

  private executeCalendar(
    node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    const { title, startTime, endTime } = node.config;
    const resolvedTitle = this.interpolate(title || "", state);
    const resolvedStart = this.interpolate(startTime || "", state);
    const resolvedEnd = this.interpolate(endTime || "", state);

    console.log(`[AutomationEngine] Calendar stub - Event: ${resolvedTitle}, Start: ${resolvedStart}, End: ${resolvedEnd}`);

    return {
      [`${node.id}_created`]: true,
      [`${node.id}_title`]: resolvedTitle,
      [`${node.id}_startTime`]: resolvedStart,
      [`${node.id}_endTime`]: resolvedEnd,
      _calendarEventCreated: true,
    };
  }

  private executeSpreadsheet(
    node: AutomationNode,
    state: Record<string, any>
  ): Record<string, any> {
    const { action = "read", range = "A1:Z100" } = node.config;
    const resolvedRange = this.interpolate(range, state);

    console.log(`[AutomationEngine] Spreadsheet stub - Action: ${action}, Range: ${resolvedRange}`);

    return {
      [`${node.id}_action`]: action,
      [`${node.id}_range`]: resolvedRange,
      [`${node.id}_result`]: action === "read" ? [] : { success: true },
      _spreadsheetProcessed: true,
    };
  }

  private interpolate(template: string, data: Record<string, any>): string {
    return template.replace(/\{\{(\w+)\}\}/g, (_, key) => {
      const val = data[key];
      if (val === undefined || val === null) return "";
      return String(val);
    });
  }
}

export const automationEngine = new AutomationEngine();

export const AUTOMATION_PRESETS = {
  data_collection_pipeline: {
    name: "Data Collection Pipeline",
    description: "Collects data from an API endpoint, transforms it, and sends a notification",
    triggerType: "manual",
    status: "draft",
    nodes: [
      {
        id: "trigger_1",
        type: "trigger",
        label: "Start",
        config: { triggerType: "manual" },
        position: { x: 100, y: 200 },
      },
      {
        id: "http_1",
        type: "http_request",
        label: "Fetch Data",
        config: {
          url: "https://jsonplaceholder.typicode.com/posts/1",
          method: "GET",
          headers: {},
        },
        position: { x: 350, y: 200 },
      },
      {
        id: "set_data_1",
        type: "set_data",
        label: "Transform Data",
        config: {
          fields: {
            processed: true,
            processedAt: "{{_triggeredAt}}",
            source: "api_collection",
          },
        },
        position: { x: 600, y: 200 },
      },
      {
        id: "email_1",
        type: "email",
        label: "Send Notification",
        config: {
          to: "admin@example.com",
          subject: "Data Collection Complete",
          body: "Data has been collected and processed at {{processedAt}}.",
        },
        position: { x: 850, y: 200 },
      },
    ] as AutomationNode[],
    edges: [
      { id: "e1", source: "trigger_1", target: "http_1" },
      { id: "e2", source: "http_1", target: "set_data_1" },
      { id: "e3", source: "set_data_1", target: "email_1" },
    ] as AutomationEdge[],
  },

  conditional_alert: {
    name: "Conditional Alert",
    description: "Evaluates a condition and sends an alert or logs data based on the result",
    triggerType: "manual",
    status: "draft",
    nodes: [
      {
        id: "trigger_1",
        type: "trigger",
        label: "Start",
        config: { triggerType: "manual" },
        position: { x: 100, y: 200 },
      },
      {
        id: "condition_1",
        type: "if_condition",
        label: "Check Threshold",
        config: {
          field: "value",
          operator: "gt",
          value: 100,
        },
        position: { x: 350, y: 200 },
      },
      {
        id: "email_1",
        type: "email",
        label: "Send Alert",
        config: {
          to: "alerts@example.com",
          subject: "Threshold Exceeded",
          body: "Value {{value}} has exceeded the threshold of 100.",
        },
        position: { x: 600, y: 100 },
      },
      {
        id: "set_data_1",
        type: "set_data",
        label: "Log Normal",
        config: {
          fields: {
            status: "normal",
            checkedAt: "{{_triggeredAt}}",
          },
        },
        position: { x: 600, y: 300 },
      },
    ] as AutomationNode[],
    edges: [
      { id: "e1", source: "trigger_1", target: "condition_1" },
      { id: "e2", source: "condition_1", target: "email_1", label: "true" },
      { id: "e3", source: "condition_1", target: "set_data_1", label: "false" },
    ] as AutomationEdge[],
  },

  multi_step_processing: {
    name: "Multi-Step Processing",
    description: "Processes data through code transformation, API call, merge, and email notification",
    triggerType: "manual",
    status: "draft",
    nodes: [
      {
        id: "trigger_1",
        type: "trigger",
        label: "Start",
        config: { triggerType: "manual" },
        position: { x: 100, y: 200 },
      },
      {
        id: "code_1",
        type: "code",
        label: "Transform Input",
        config: {
          code: 'return { transformedData: JSON.stringify(data), itemCount: Object.keys(data).length, timestamp: new Date().toISOString() };',
        },
        position: { x: 350, y: 200 },
      },
      {
        id: "http_1",
        type: "http_request",
        label: "API Call",
        config: {
          url: "https://jsonplaceholder.typicode.com/posts",
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: { title: "Processed Data", body: "{{transformedData}}", userId: 1 },
        },
        position: { x: 600, y: 200 },
      },
      {
        id: "merge_1",
        type: "merge",
        label: "Merge Results",
        config: {},
        position: { x: 850, y: 200 },
      },
      {
        id: "email_1",
        type: "email",
        label: "Send Report",
        config: {
          to: "team@example.com",
          subject: "Processing Complete",
          body: "Multi-step processing completed. Items processed: {{itemCount}}. Timestamp: {{timestamp}}.",
        },
        position: { x: 1100, y: 200 },
      },
    ] as AutomationNode[],
    edges: [
      { id: "e1", source: "trigger_1", target: "code_1" },
      { id: "e2", source: "code_1", target: "http_1" },
      { id: "e3", source: "http_1", target: "merge_1" },
      { id: "e4", source: "merge_1", target: "email_1" },
    ] as AutomationEdge[],
  },
};
