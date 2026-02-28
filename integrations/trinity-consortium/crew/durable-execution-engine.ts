import { db } from "../../db";
import { durableWorkflows, durableActivities, workflowSignals, taskQueues } from "@shared/schema";
import { eq, desc, and, lte, sql } from "drizzle-orm";

type ActivityDefinition = {
  name: string;
  activityType: string;
  input?: Record<string, any>;
  maxRetries?: number;
  retryBackoff?: string;
  timeoutSeconds?: number;
  metadata?: Record<string, any>;
};

type StartWorkflowData = {
  name: string;
  workflowType: string;
  input?: Record<string, any>;
  taskQueueId?: string;
  retryPolicy?: Record<string, any>;
  activities: ActivityDefinition[];
  memo?: Record<string, any>;
  searchAttributes?: Record<string, any>;
  projectId?: string;
  parentWorkflowId?: string;
};

type PresetDefinition = {
  id: string;
  name: string;
  description: string;
  workflowType: string;
  activities: ActivityDefinition[];
};

export class DurableExecutionEngine {

  async createTaskQueue(data: { name: string; description?: string; maxConcurrency?: number; metadata?: Record<string, any> }) {
    const [queue] = await db.insert(taskQueues).values({
      name: data.name,
      description: data.description,
      maxConcurrency: data.maxConcurrency ?? 10,
      metadata: data.metadata ?? {},
      status: "active",
      workerCount: 0,
    }).returning();
    return queue;
  }

  async listTaskQueues() {
    return db.select().from(taskQueues);
  }

  async getTaskQueue(id: string) {
    const [queue] = await db.select().from(taskQueues).where(eq(taskQueues.id, id));
    return queue || null;
  }

  async updateTaskQueue(id: string, data: Partial<{ name: string; description: string; maxConcurrency: number; status: string; metadata: Record<string, any> }>) {
    const [updated] = await db.update(taskQueues).set(data).where(eq(taskQueues.id, id)).returning();
    return updated || null;
  }

  async startWorkflow(data: StartWorkflowData) {
    const [workflow] = await db.insert(durableWorkflows).values({
      name: data.name,
      workflowType: data.workflowType,
      status: "running",
      input: data.input ?? {},
      taskQueueId: data.taskQueueId,
      retryPolicy: data.retryPolicy ?? {},
      totalActivities: data.activities.length,
      currentActivityIndex: 0,
      memo: data.memo ?? {},
      searchAttributes: data.searchAttributes ?? {},
      projectId: data.projectId,
      parentWorkflowId: data.parentWorkflowId,
      startedAt: new Date(),
      state: {},
    }).returning();

    for (let i = 0; i < data.activities.length; i++) {
      const act = data.activities[i];
      await db.insert(durableActivities).values({
        workflowId: workflow.id,
        name: act.name,
        activityType: act.activityType,
        status: "pending",
        input: act.input ?? {},
        sequenceNumber: i,
        maxRetries: act.maxRetries ?? 3,
        retryBackoff: act.retryBackoff ?? "exponential",
        timeoutSeconds: act.timeoutSeconds ?? 300,
        metadata: act.metadata ?? {},
        attempt: 1,
      });
    }

    await this.executeNextActivity(workflow.id);

    const [updated] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, workflow.id));
    return updated;
  }

  async getWorkflow(id: string) {
    const [workflow] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, id));
    if (!workflow) return null;

    const activities = await db.select().from(durableActivities).where(eq(durableActivities.workflowId, id));
    const completed = activities.filter(a => a.status === "completed").length;
    const failed = activities.filter(a => a.status === "failed").length;
    const pending = activities.filter(a => a.status === "pending").length;
    const running = activities.filter(a => a.status === "running").length;

    return {
      ...workflow,
      activitySummary: { total: activities.length, completed, failed, pending, running },
    };
  }

  async listWorkflows(filters?: { status?: string }) {
    if (filters?.status) {
      return db.select().from(durableWorkflows)
        .where(eq(durableWorkflows.status, filters.status))
        .orderBy(desc(durableWorkflows.createdAt));
    }
    return db.select().from(durableWorkflows).orderBy(desc(durableWorkflows.createdAt));
  }

  async pauseWorkflow(id: string) {
    const [workflow] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, id));
    if (!workflow || workflow.status !== "running") return null;

    const [updated] = await db.update(durableWorkflows)
      .set({ status: "paused", updatedAt: new Date() })
      .where(eq(durableWorkflows.id, id))
      .returning();
    return updated;
  }

  async resumeWorkflow(id: string) {
    const [workflow] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, id));
    if (!workflow || workflow.status !== "paused") return null;

    const [updated] = await db.update(durableWorkflows)
      .set({ status: "running", updatedAt: new Date() })
      .where(eq(durableWorkflows.id, id))
      .returning();

    await this.executeNextActivity(id);

    const [refreshed] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, id));
    return refreshed;
  }

  async cancelWorkflow(id: string) {
    const [workflow] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, id));
    if (!workflow) return null;

    await db.update(durableActivities)
      .set({ status: "cancelled" })
      .where(and(
        eq(durableActivities.workflowId, id),
        eq(durableActivities.status, "pending")
      ));

    const [updated] = await db.update(durableWorkflows)
      .set({ status: "cancelled", updatedAt: new Date(), completedAt: new Date() })
      .where(eq(durableWorkflows.id, id))
      .returning();
    return updated;
  }

  async retryWorkflow(id: string) {
    const [workflow] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, id));
    if (!workflow || workflow.status !== "failed") return null;

    await db.update(durableActivities)
      .set({ status: "pending", attempt: 1, error: null, output: null, startedAt: null, completedAt: null, nextRetryAt: null })
      .where(and(
        eq(durableActivities.workflowId, id),
        sql`${durableActivities.status} IN ('failed', 'retrying')`
      ));

    const [updated] = await db.update(durableWorkflows)
      .set({ status: "running", error: null, currentActivityIndex: 0, updatedAt: new Date(), completedAt: null })
      .where(eq(durableWorkflows.id, id))
      .returning();

    await this.executeNextActivity(id);

    const [refreshed] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, id));
    return refreshed;
  }

  async executeNextActivity(workflowId: string) {
    const [workflow] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, workflowId));
    if (!workflow || workflow.status !== "running") return null;

    const pendingActivities = await db.select().from(durableActivities)
      .where(and(
        eq(durableActivities.workflowId, workflowId),
        eq(durableActivities.status, "pending")
      ))
      .orderBy(durableActivities.sequenceNumber)
      .limit(1);

    if (pendingActivities.length === 0) {
      await db.update(durableWorkflows)
        .set({
          status: "completed",
          completedAt: new Date(),
          updatedAt: new Date(),
          output: { completedActivities: workflow.totalActivities },
        })
        .where(eq(durableWorkflows.id, workflowId));
      return null;
    }

    const activity = pendingActivities[0];

    await db.update(durableActivities)
      .set({ status: "running", startedAt: new Date() })
      .where(eq(durableActivities.id, activity.id));

    try {
      const output = await this.executeActivityByType(activity.activityType, activity.input as Record<string, any>);

      await db.update(durableActivities)
        .set({ status: "completed", output, completedAt: new Date() })
        .where(eq(durableActivities.id, activity.id));

      const newIndex = (activity.sequenceNumber ?? 0) + 1;
      await db.update(durableWorkflows)
        .set({ currentActivityIndex: newIndex, updatedAt: new Date() })
        .where(eq(durableWorkflows.id, workflowId));

      if (newIndex >= (workflow.totalActivities ?? 0)) {
        await db.update(durableWorkflows)
          .set({
            status: "completed",
            completedAt: new Date(),
            updatedAt: new Date(),
            output,
          })
          .where(eq(durableWorkflows.id, workflowId));
      }

      return { activityId: activity.id, status: "completed", output };
    } catch (err: any) {
      const currentAttempt = activity.attempt ?? 1;
      const maxRetries = activity.maxRetries ?? 3;

      if (currentAttempt < maxRetries) {
        const backoff = activity.retryBackoff ?? "exponential";
        const nextRetryMs = this.calculateNextRetry(currentAttempt, backoff);
        const nextRetryAt = new Date(Date.now() + nextRetryMs);

        await db.update(durableActivities)
          .set({
            status: "retrying",
            error: err.message || String(err),
            attempt: currentAttempt + 1,
            nextRetryAt,
          })
          .where(eq(durableActivities.id, activity.id));

        return { activityId: activity.id, status: "retrying", error: err.message };
      } else {
        await db.update(durableActivities)
          .set({
            status: "failed",
            error: err.message || String(err),
            completedAt: new Date(),
          })
          .where(eq(durableActivities.id, activity.id));

        await db.update(durableWorkflows)
          .set({
            status: "failed",
            error: `Activity "${activity.name}" failed: ${err.message || String(err)}`,
            updatedAt: new Date(),
          })
          .where(eq(durableWorkflows.id, workflowId));

        return { activityId: activity.id, status: "failed", error: err.message };
      }
    }
  }

  private async executeActivityByType(activityType: string, input: Record<string, any>): Promise<Record<string, any>> {
    switch (activityType) {
      case "http_call": {
        const url = input.url || "https://api.example.com";
        console.log(`[DurableEngine] HTTP call to: ${url}`);
        return { status: 200, url, response: { success: true }, executedAt: new Date().toISOString() };
      }
      case "transform": {
        const transformed = { ...input, _transformed: true, transformedAt: new Date().toISOString() };
        return transformed;
      }
      case "ai_inference": {
        const model = input.model || "gpt-4";
        const prompt = input.prompt || "default prompt";
        console.log(`[DurableEngine] AI inference with model: ${model}`);
        return { model, result: `AI inference result for ${prompt}`, executedAt: new Date().toISOString() };
      }
      case "notification": {
        const channel = input.channel || "email";
        const message = input.message || "Notification sent";
        console.log(`[DurableEngine] Notification via ${channel}: ${message}`);
        return { sent: true, channel, message, executedAt: new Date().toISOString() };
      }
      case "data_query": {
        const query = input.query || "SELECT * FROM data";
        console.log(`[DurableEngine] Data query: ${query}`);
        return { query, rows: 42, duration: "120ms", executedAt: new Date().toISOString() };
      }
      case "timer": {
        const durationMs = input.durationMs || 1000;
        console.log(`[DurableEngine] Timer: waiting ${durationMs}ms`);
        return { waited: durationMs, executedAt: new Date().toISOString() };
      }
      case "child_workflow": {
        console.log(`[DurableEngine] Child workflow placeholder`);
        return { childWorkflowId: "pending", executedAt: new Date().toISOString() };
      }
      default:
        return { result: `Unknown activity type: ${activityType}`, executedAt: new Date().toISOString() };
    }
  }

  async retryActivity(activityId: string) {
    const [activity] = await db.select().from(durableActivities).where(eq(durableActivities.id, activityId));
    if (!activity) return null;
    if (activity.status !== "failed" && activity.status !== "retrying") return null;

    await db.update(durableActivities)
      .set({ status: "pending", attempt: 1, error: null, output: null, startedAt: null, completedAt: null, nextRetryAt: null })
      .where(eq(durableActivities.id, activityId));

    const [workflow] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, activity.workflowId));
    if (workflow && workflow.status === "failed") {
      await db.update(durableWorkflows)
        .set({ status: "running", error: null, updatedAt: new Date() })
        .where(eq(durableWorkflows.id, activity.workflowId));
    }

    return this.executeNextActivity(activity.workflowId);
  }

  async getActivityHistory(workflowId: string) {
    return db.select().from(durableActivities)
      .where(eq(durableActivities.workflowId, workflowId))
      .orderBy(durableActivities.sequenceNumber);
  }

  async getActivity(id: string) {
    const [activity] = await db.select().from(durableActivities).where(eq(durableActivities.id, id));
    return activity || null;
  }

  async sendSignal(data: { workflowId: string; signalName: string; payload?: Record<string, any>; senderId?: string; senderType?: string }) {
    const [signal] = await db.insert(workflowSignals).values({
      workflowId: data.workflowId,
      signalName: data.signalName,
      payload: data.payload ?? {},
      senderId: data.senderId,
      senderType: data.senderType ?? "system",
      status: "delivered",
      deliveredAt: new Date(),
    }).returning();

    if (data.signalName === "resume") {
      const [workflow] = await db.select().from(durableWorkflows).where(eq(durableWorkflows.id, data.workflowId));
      if (workflow && workflow.status === "paused") {
        await this.resumeWorkflow(data.workflowId);
      }
    }

    return signal;
  }

  async getSignals(workflowId: string) {
    return db.select().from(workflowSignals)
      .where(eq(workflowSignals.workflowId, workflowId))
      .orderBy(desc(workflowSignals.createdAt));
  }

  async processSignal(signalId: string) {
    const [updated] = await db.update(workflowSignals)
      .set({ status: "processed", processedAt: new Date() })
      .where(eq(workflowSignals.id, signalId))
      .returning();
    return updated || null;
  }

  getPresets(): PresetDefinition[] {
    return [
      {
        id: "investor_onboarding_saga",
        name: "Investor Onboarding Saga",
        description: "Complete investor onboarding with identity verification, credit check, risk assessment, welcome notification, and portfolio setup",
        workflowType: "saga",
        activities: [
          { name: "verify_identity", activityType: "http_call", input: { url: "https://api.kyc-provider.com/verify", method: "POST" } },
          { name: "credit_check", activityType: "data_query", input: { query: "SELECT credit_score FROM credit_bureau WHERE investor_id = ?" } },
          { name: "risk_assessment", activityType: "ai_inference", input: { model: "gpt-4", prompt: "Assess investment risk profile based on provided financial data" } },
          { name: "send_welcome", activityType: "notification", input: { channel: "email", message: "Welcome to the platform! Your account has been verified." } },
          { name: "setup_portfolio", activityType: "transform", input: { template: "default_portfolio", allocation: "balanced" } },
        ],
      },
      {
        id: "document_processing_pipeline",
        name: "Document Processing Pipeline",
        description: "Ingest, extract entities, store results, and notify upon document processing completion",
        workflowType: "sequential",
        activities: [
          { name: "ingest_document", activityType: "http_call", input: { url: "https://api.document-service.com/ingest", method: "POST" } },
          { name: "extract_entities", activityType: "ai_inference", input: { model: "gpt-4", prompt: "Extract key entities and metadata from the ingested document" } },
          { name: "store_results", activityType: "data_query", input: { query: "INSERT INTO document_results (entities, metadata) VALUES (?, ?)" } },
          { name: "notify_completion", activityType: "notification", input: { channel: "email", message: "Document processing completed successfully." } },
        ],
      },
      {
        id: "compliance_check_workflow",
        name: "Compliance Check Workflow",
        description: "Gather compliance data, analyze against regulations, and generate a compliance report",
        workflowType: "state_machine",
        activities: [
          { name: "gather_data", activityType: "data_query", input: { query: "SELECT * FROM compliance_records WHERE status = 'pending'" } },
          { name: "analyze_compliance", activityType: "ai_inference", input: { model: "gpt-4", prompt: "Analyze gathered data for regulatory compliance violations" } },
          { name: "generate_report", activityType: "transform", input: { template: "compliance_report", format: "pdf" } },
        ],
      },
    ];
  }

  async executePreset(presetId: string, input?: Record<string, any>) {
    const presets = this.getPresets();
    const preset = presets.find(p => p.id === presetId);
    if (!preset) {
      throw new Error(`Preset not found: ${presetId}`);
    }

    return this.startWorkflow({
      name: preset.name,
      workflowType: preset.workflowType,
      input: input ?? {},
      activities: preset.activities,
    });
  }

  private calculateNextRetry(attempt: number, backoff: string, baseMs: number = 1000): number {
    let delayMs: number;
    switch (backoff) {
      case "fixed":
        delayMs = baseMs;
        break;
      case "linear":
        delayMs = baseMs * attempt;
        break;
      case "exponential":
        delayMs = baseMs * Math.pow(2, attempt - 1);
        break;
      default:
        delayMs = baseMs * Math.pow(2, attempt - 1);
    }
    return Math.min(delayMs, 5 * 60 * 1000);
  }
}

export const durableEngine = new DurableExecutionEngine();
