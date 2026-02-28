import type { Express } from "express";
import { db } from "../../db";
import { eq } from "drizzle-orm";
import { visualWorkflows, insertVisualWorkflowSchema, automationWorkflows, automationExecutions } from "@shared/schema";
import { WorkflowEngine, WORKFLOW_PRESETS, automationEngine, AUTOMATION_PRESETS, schedulingService, durableEngine } from "../../ai/crew";
import { auditTrailService } from "../../ai/crew";
import type { WorkflowNodeType } from "../../ai/crew/langgraph";
import { errorMessage } from "../../core/errors";
import { requireAuth } from "../../auth/middleware";

export function registerWorkflowRoutes(app: Express): void {
  /**
   * DOMAIN: Workflows
   * Purpose: Durable workflow execution, visual workflows, automation
   *
   * Auth:
   * - All routes: requireAuth() only
   *
   * Middleware chain: requireAuth()
   *
   * Key tables: workflows, durableWorkflows, durableActivities, workflowSignals, automationWorkflows, visualWorkflows
   *
   * Grep hooks: requireAuth(, /api/workflows/, /api/automation/, /api/durable/, /api/scheduling/
   */

  // ============================================
  // FLOWISE: VISUAL WORKFLOW BUILDER
  // ============================================

  app.get("/api/workflows/visual", requireAuth(), async (req, res) => {
    try {
      const { projectId, status } = req.query;
      let query = db.select().from(visualWorkflows);
      if (projectId) {
        query = query.where(eq(visualWorkflows.projectId, projectId as string)) as any;
      }
      if (status) {
        query = query.where(eq(visualWorkflows.status, status as string)) as any;
      }
      const workflows = await query;
      res.json(workflows);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/workflows/visual/presets", requireAuth(), async (_req, res) => {
    const presets = Object.entries(WORKFLOW_PRESETS).map(([key, def]) => ({
      id: key,
      name: def.name,
      description: def.description,
      nodes: def.nodes.map(n => ({
        id: n.id,
        type: "custom",
        position: { x: 0, y: 0 },
        data: { nodeType: n.type, label: n.label, config: n.config },
      })),
      edges: def.edges.map(e => ({
        id: e.id,
        source: e.from,
        target: e.to,
        label: e.label,
        data: { condition: e.condition },
      })),
    }));
    res.json(presets);
  });

  app.get("/api/workflows/visual/:id", requireAuth(), async (req, res) => {
    try {
      const [workflow] = await db.select().from(visualWorkflows).where(eq(visualWorkflows.id, req.params.id));
      if (!workflow) return res.status(404).json({ error: "Workflow not found" });
      res.json(workflow);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/workflows/visual", requireAuth(), async (req, res) => {
    try {
      const parsed = insertVisualWorkflowSchema.parse(req.body);
      const [workflow] = await db.insert(visualWorkflows).values(parsed).returning();
      res.status(201).json(workflow);
    } catch (error: unknown) {
      res.status(400).json({ error: errorMessage(error) });
    }
  });

  app.put("/api/workflows/visual/:id", requireAuth(), async (req, res) => {
    try {
      const [existing] = await db.select().from(visualWorkflows).where(eq(visualWorkflows.id, req.params.id));
      if (!existing) return res.status(404).json({ error: "Workflow not found" });
      const [updated] = await db.update(visualWorkflows).set({
        ...req.body,
        updatedAt: new Date(),
      }).where(eq(visualWorkflows.id, req.params.id)).returning();
      res.json(updated);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.delete("/api/workflows/visual/:id", requireAuth(), async (req, res) => {
    try {
      const [existing] = await db.select().from(visualWorkflows).where(eq(visualWorkflows.id, req.params.id));
      if (!existing) return res.status(404).json({ error: "Workflow not found" });
      await db.delete(visualWorkflows).where(eq(visualWorkflows.id, req.params.id));
      res.json({ success: true });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/workflows/visual/:id/execute", requireAuth(), async (req, res) => {
    try {
      const [workflow] = await db.select().from(visualWorkflows).where(eq(visualWorkflows.id, req.params.id));
      if (!workflow) return res.status(404).json({ error: "Workflow not found" });

      const { input } = req.body;
      const nodes = workflow.nodes as Array<Record<string, unknown>>;
      const edges = workflow.edges as Array<Record<string, unknown>>;

      const definition = {
        id: workflow.id,
        name: workflow.name,
        description: workflow.description || "",
        nodes: (nodes as Array<Record<string, unknown>>).map((n) => ({
          id: n.id as string,
          type: ((n.data as Record<string, unknown>)?.nodeType || "prompt") as WorkflowNodeType,
          label: ((n.data as Record<string, unknown>)?.label || n.id) as string,
          config: ((n.data as Record<string, unknown>)?.config || {}) as Record<string, unknown>,
        })),
        edges: (edges as Array<Record<string, unknown>>).map((e) => ({
          id: e.id as string,
          from: e.source as string,
          to: e.target as string,
          condition: (e.data as Record<string, unknown>)?.condition as string | undefined,
          label: e.label as string | undefined,
        })),
        initialState: input || {},
        model: (req.body.model || "gpt-4o") as any,
      };

      const context = { userId: "1", userRole: "admin" as const, projectId: req.body.projectId };
      const engine = new WorkflowEngine(definition, context);
      const result = await engine.execute();

      auditTrailService.logWorkflowEvent("workflow_executed", workflow.id, `Workflow "${workflow.name}" executed (${result.status})`, undefined, req.body.projectId, { status: result.status, nodeCount: nodes.length }).catch(() => {});

      await db.update(visualWorkflows).set({
        lastRunAt: new Date(),
        lastRunResult: result as any,
        updatedAt: new Date(),
      }).where(eq(visualWorkflows.id, req.params.id));

      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  // ============================================
  // N8N WORKFLOW AUTOMATION
  // ============================================

  app.get("/api/automation/workflows", requireAuth(), async (req, res) => {
    try {
      const { projectId, status } = req.query;
      let query = db.select().from(automationWorkflows);
      const results = await query;
      res.json(results);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/automation/workflows/:id", requireAuth(), async (req, res) => {
    try {
      const [workflow] = await db.select().from(automationWorkflows).where(eq(automationWorkflows.id, req.params.id)).limit(1);
      if (!workflow) return res.status(404).json({ error: "Workflow not found" });
      res.json(workflow);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/automation/workflows", requireAuth(), async (req, res) => {
    try {
      const [workflow] = await db.insert(automationWorkflows).values(req.body).returning();
      res.json(workflow);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.put("/api/automation/workflows/:id", requireAuth(), async (req, res) => {
    try {
      const [workflow] = await db.update(automationWorkflows).set({ ...req.body, updatedAt: new Date() }).where(eq(automationWorkflows.id, req.params.id)).returning();
      if (!workflow) return res.status(404).json({ error: "Workflow not found" });
      res.json(workflow);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.delete("/api/automation/workflows/:id", requireAuth(), async (req, res) => {
    try {
      await db.delete(automationWorkflows).where(eq(automationWorkflows.id, req.params.id));
      res.json({ success: true });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/automation/execute", requireAuth(), async (req, res) => {
    try {
      const { workflowId, preset, input } = req.body;
      type AutomationWorkflowInput = Parameters<typeof automationEngine.execute>[0];
      let workflow: AutomationWorkflowInput | null = null;
      if (preset && (AUTOMATION_PRESETS as Record<string, unknown>)[preset]) {
        workflow = (AUTOMATION_PRESETS as Record<string, unknown>)[preset] as AutomationWorkflowInput;
      } else if (workflowId) {
        const [w] = await db.select().from(automationWorkflows).where(eq(automationWorkflows.id, workflowId)).limit(1);
        if (!w) return res.status(404).json({ error: "Workflow not found" });
        workflow = w as unknown as AutomationWorkflowInput;
      } else {
        return res.status(400).json({ error: "workflowId or preset required" });
      }
      const result = await automationEngine.execute(workflow!, input || {});
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/automation/executions", requireAuth(), async (req, res) => {
    try {
      const { workflowId } = req.query;
      let results;
      if (workflowId) {
        results = await db.select().from(automationExecutions).where(eq(automationExecutions.workflowId, workflowId as string));
      } else {
        results = await db.select().from(automationExecutions);
      }
      res.json(results);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/automation/presets", requireAuth(), (_req, res) => {
    const presets = Object.entries(AUTOMATION_PRESETS).map(([id, def]) => ({
      id,
      name: (def as any).name,
      description: (def as any).description,
      nodeCount: (def as any).nodes?.length || 0,
    }));
    res.json(presets);
  });

  // ============================================
  // CAL.COM SCHEDULING
  // ============================================

  app.get("/api/scheduling/event-types", requireAuth(), async (req, res) => {
    try {
      const result = await schedulingService.getEventTypes(req.query.projectId as string | undefined);
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/scheduling/event-types/:id", requireAuth(), async (req, res) => {
    try {
      const result = await schedulingService.getEventType(req.params.id);
      if (!result) return res.status(404).json({ error: "Event type not found" });
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/scheduling/event-types", requireAuth(), async (req, res) => {
    try {
      const result = await schedulingService.createEventType(req.body);
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.put("/api/scheduling/event-types/:id", requireAuth(), async (req, res) => {
    try {
      const result = await schedulingService.updateEventType(req.params.id, req.body);
      if (!result) return res.status(404).json({ error: "Event type not found" });
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.delete("/api/scheduling/event-types/:id", requireAuth(), async (req, res) => {
    try {
      await schedulingService.deleteEventType(req.params.id);
      res.json({ success: true });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/scheduling/availability", requireAuth(), async (req, res) => {
    try {
      const result = await schedulingService.getAvailability(req.query.projectId as string | undefined);
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.put("/api/scheduling/availability", requireAuth(), async (req, res) => {
    try {
      const result = await schedulingService.setAvailability(req.user?.sub || "system", req.body);
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/scheduling/slots", requireAuth(), async (req, res) => {
    try {
      const { eventTypeId, date, timezone } = req.query;
      if (!eventTypeId || !date) return res.status(400).json({ error: "eventTypeId and date required" });
      const slots = await schedulingService.getAvailableSlots(
        eventTypeId as string,
        date as string,
        (timezone as string) || "UTC"
      );
      res.json(slots);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/scheduling/bookings", requireAuth(), async (req, res) => {
    try {
      const booking = await schedulingService.createBooking(req.body);
      res.json(booking);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/scheduling/bookings", requireAuth(), async (req, res) => {
    try {
      const { eventTypeId, status } = req.query;
      const result = await schedulingService.getBookings({
        eventTypeId: eventTypeId as string | undefined,
        status: status as string | undefined,
      });
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.put("/api/scheduling/bookings/:id/cancel", requireAuth(), async (req, res) => {
    try {
      const result = await schedulingService.cancelBooking(req.params.id);
      if (!result) return res.status(404).json({ error: "Booking not found" });
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.put("/api/scheduling/bookings/:id/reschedule", requireAuth(), async (req, res) => {
    try {
      const result = await schedulingService.rescheduleBooking(req.params.id, req.body.newStartTime, req.body.newEndTime);
      if (!result) return res.status(404).json({ error: "Booking not found" });
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  // ============================================
  // TEMPORAL-STYLE DURABLE EXECUTION ENGINE
  // ============================================

  app.get("/api/durable/workflows", requireAuth(), async (req, res) => {
    try {
      const { status } = req.query;
      const workflows = durableEngine.listWorkflows({
        status: status as string | undefined,
      });
      res.json(workflows);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/durable/workflows/:id", requireAuth(), async (req, res) => {
    try {
      const workflow = durableEngine.getWorkflow(req.params.id);
      if (!workflow) return res.status(404).json({ error: "Workflow not found" });
      res.json(workflow);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/durable/workflows", requireAuth(), async (req, res) => {
    try {
      const result = await durableEngine.startWorkflow(req.body);
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/durable/workflows/:id/signal", requireAuth(), async (req, res) => {
    try {
      const { signalName } = req.body;
      if (!signalName) return res.status(400).json({ error: "signalName required" });
      res.status(501).json({ error: "Signal not yet implemented" });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/durable/workflows/:id/cancel", requireAuth(), async (req, res) => {
    try {
      await durableEngine.cancelWorkflow(req.params.id);
      res.json({ success: true });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/durable/task-queues", requireAuth(), async (_req, res) => {
    try {
      const queues = [durableEngine.getTaskQueue("default")].filter(Boolean);
      res.json(queues);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/durable/presets", requireAuth(), (_req, res) => {
    try {
      const presets = durableEngine.getPresets();
      res.json(presets);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });
}
