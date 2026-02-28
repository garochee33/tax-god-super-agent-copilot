import { z } from "zod";

const CURSOR_API_BASE = "https://api.cursor.com/v1";

export const cursorTaskSchema = z.object({
  goal: z.string().min(1, "Task goal is required"),
  repository: z.string().optional(),
  branch: z.string().optional(),
  context: z.string().optional(),
  priority: z.enum(["low", "medium", "high"]).default("medium"),
  enableNetwork: z.boolean().default(false),
  model: z.enum(["gpt-4o", "claude-sonnet-4.5", "auto"]).default("auto"),
});

export const cursorTaskStatusSchema = z.object({
  taskId: z.string(),
  status: z.enum(["queued", "running", "completed", "failed", "cancelled"]),
  progress: z.number().min(0).max(100).optional(),
  output: z.string().optional(),
  error: z.string().optional(),
  filesModified: z.array(z.string()).optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export type CursorTaskRequest = z.infer<typeof cursorTaskSchema>;
export type CursorTaskStatus = z.infer<typeof cursorTaskStatusSchema>;

export interface CursorAgentInfo {
  agentId: string;
  name: string;
  status: "idle" | "busy" | "offline";
  currentTask?: string;
  tasksCompleted: number;
}

class CursorAgentService {
  private apiKey: string | undefined;

  constructor() {
    this.apiKey = process.env.CURSOR_API_KEY;
  }

  private getHeaders() {
    if (!this.apiKey) {
      throw new Error("CURSOR_API_KEY is not configured");
    }
    return {
      "Authorization": `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
    };
  }

  isConfigured(): boolean {
    return !!this.apiKey;
  }

  async submitTask(request: CursorTaskRequest): Promise<{ taskId: string; status: string }> {
    const response = await fetch(`${CURSOR_API_BASE}/agents/tasks`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        goal: request.goal,
        repository: request.repository,
        branch: request.branch,
        context: request.context,
        priority: request.priority,
        enableNetwork: request.enableNetwork,
        model: request.model,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cursor API error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async getTaskStatus(taskId: string): Promise<CursorTaskStatus> {
    const response = await fetch(`${CURSOR_API_BASE}/agents/tasks/${taskId}`, {
      method: "GET",
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cursor API error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async cancelTask(taskId: string): Promise<{ success: boolean }> {
    const response = await fetch(`${CURSOR_API_BASE}/agents/tasks/${taskId}/cancel`, {
      method: "POST",
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cursor API error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async listTasks(limit: number = 20): Promise<CursorTaskStatus[]> {
    const response = await fetch(`${CURSOR_API_BASE}/agents/tasks?limit=${limit}`, {
      method: "GET",
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cursor API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return data.tasks || data;
  }

  async getAgentStatus(): Promise<CursorAgentInfo[]> {
    const response = await fetch(`${CURSOR_API_BASE}/agents`, {
      method: "GET",
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cursor API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return data.agents || data;
  }

  async testConnection(): Promise<{ connected: boolean; message: string }> {
    if (!this.apiKey) {
      return { connected: false, message: "API key not configured" };
    }
    return { 
      connected: true, 
      message: "Cursor Cloud Agent API key configured. Tasks will be submitted when triggered." 
    };
  }
}

export const cursorAgentService = new CursorAgentService();
