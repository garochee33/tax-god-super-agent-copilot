import { type Express, type Request, type Response } from "express";
import { z } from "zod";
import { requireAuth, requirePermission } from "../../auth/middleware";
import { errorMessage } from "../../core/errors";

export async function registerSwarmRoutes(app: Express): Promise<void> {
  /**
   * DOMAIN: Swarm
   * Purpose: Multi-agent swarm orchestration, cost governance, OpenClaw dispatch
   *
   * Auth:
   * - requireAuth() + requirePermission("swarm:dispatch") for OpenClaw routes
   * - Mixed auth for other routes
   *
   * Middleware chain: requireAuth() → requirePermission("swarm:dispatch")
   *
   * Key tables: swarmLedger, agentExecutions
   *
   * Grep hooks: requirePermission(, /api/openclaw/, /api/swarm/, /api/cost-governance/
   */

  const auth = [requireAuth()] as const;
  const swarmAdmin = [requireAuth(), requirePermission("swarm:dispatch")] as const;

  // ============================================
  // OpenClaw Secured Swarm Dispatch (TC-002)
  // ============================================

  const { OpenClawCostGate, BUDGET_LIMITS } = await import("../../ai/cost-governor");
  const { OpenClawCostEstimator } = await import("../../ai/openclaw-cost-estimator");
  const { createSwarmCostPlan } = await import("../../ai/swarm-cost-planner");
  const { calculateThrottleDecision, THROTTLE_THRESHOLDS } = await import("../../ai/swarm-adaptive-throttle");
  const { SwarmCostInstrumentation } = await import("../../ai/swarm-cost-instrumentation");
  const swarmCostGate = new OpenClawCostGate(new OpenClawCostEstimator());
  const globalInstrumentation = new SwarmCostInstrumentation("global", "global");

  app.post("/api/openclaw/swarm", ...swarmAdmin, async (req: Request, res: Response) => {
    try {
      const { z } = await import("zod");
      const { openClawService } = await import("../../ai/openclaw-service");

      const SwarmRequest = z.object({
        traceId: z.string().min(1).max(128),
        sessionId: z.string().min(1).max(128),
        tasks: z.array(z.object({
          description: z.string().min(1).max(500),
          model: z.string().optional(),
          swarmSize: z.number().int().min(1).max(19).optional(),
        })).min(1).max(10),
        priority: z.enum(["normal", "critical"]),
        approvalToken: z.string().optional(),
      });

      const parsed = SwarmRequest.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({ error: "Invalid request", details: parsed.error.issues });
        return;
      }
      const body = parsed.data;

      const totalSwarmSize = body.tasks.reduce((sum, t) => sum + (t.swarmSize ?? 1), 0);

      const estimation = swarmCostGate.evaluate({
        traceId: body.traceId,
        sessionId: body.sessionId,
        toolName: "openclaw_swarm",
        priority: body.priority,
        task: {
          description: body.tasks[0].description,
          swarmSize: totalSwarmSize,
        },
        approvalToken: body.approvalToken,
      });

      if (!estimation.allowed) {
        res.status(402).json(estimation);
        return;
      }

      const taskPrompt = body.tasks.map(t => t.description).join(" | ");
      const session = await openClawService.dispatchSwarm({
        task: taskPrompt,
        agentCount: totalSwarmSize,
        priority: body.priority,
        strategy: "parallel",
        metadata: {
          traceId: body.traceId,
          sessionId: body.sessionId,
          estimatedCost: estimation.details.estimatedCost,
          costGatePreApproved: true,
        },
      });

      swarmCostGate.recordSpend(estimation.details.estimatedCost);

      try {
        const { db } = await import("../../db");
        const { swarmLedger } = await import("@shared/schema");
        await db.insert(swarmLedger).values({
          traceId: body.traceId,
          sessionId: body.sessionId,
          taskDescriptions: body.tasks.map(t => t.description),
          estimatedCost: estimation.details.estimatedCost.toFixed(4),
          priority: body.priority,
          status: "dispatched",
        });
      } catch (ledgerErr: unknown) {
        console.log(`[OpenClaw] Ledger write warning: ${errorMessage(ledgerErr)}`);
      }

      (res as any).json({ ok: true, ...estimation.details, session });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/openclaw/off", ...swarmAdmin, async (_req: Request, res: Response) => {
    try {
      const { costOptimizer } = await import("../../ai/swarm/cost-optimizer");
      swarmCostGate.engageKillSwitch();
      costOptimizer.updateLimits({
        caps: { perTask: 0, perSession: 0, perDay: 0, perAgent: {} },
      });
      res.json({ ok: true, message: "OpenClaw swarm dispatch disabled — kill switch engaged and all budgets zeroed" });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/openclaw/ledger", ...swarmAdmin, async (_req: Request, res: Response) => {
    try {
      const { db } = await import("../../db");
      const { swarmLedger } = await import("@shared/schema");
      const { desc } = await import("drizzle-orm");
      const entries = await db.select().from(swarmLedger).orderBy(desc(swarmLedger.createdAt)).limit(50);
      res.json({ entries, count: entries.length });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  // ============================================
  // Cost Governance Budget Transparency (TC-002)
  // ============================================

  app.get("/api/cost-governance/dashboard", ...swarmAdmin, async (_req: Request, res: Response) => {
    try {
      const stats = swarmCostGate.getStats();
      const settlement = swarmCostGate.getSettlementSummary();
      const sessionRemaining = Math.max(0, BUDGET_LIMITS.perSession - stats.sessionSpend);
      const dailyRemaining = Math.max(0, BUDGET_LIMITS.perDay - stats.dailySpend);

      res.json({
        budgets: {
          perTask: { limit: BUDGET_LIMITS.perTask, unit: "USD" },
          perSession: { limit: BUDGET_LIMITS.perSession, spent: stats.sessionSpend, remaining: sessionRemaining, unit: "USD" },
          perDay: { limit: BUDGET_LIMITS.perDay, spent: stats.dailySpend, remaining: dailyRemaining, unit: "USD" },
        },
        settlement,
        stats,
        throttleThresholds: THROTTLE_THRESHOLDS,
        killSwitchEngaged: stats.killSwitchEngaged,
        timestamp: new Date().toISOString(),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/cost-governance/simulate-plan", ...swarmAdmin, async (req: Request, res: Response) => {
    try {
      const SimulatePlanRequest = z.object({
        workerCount: z.number().int().min(1).max(20),
        modelTier: z.enum(["premium", "standard", "economy"]).optional(),
        delegationDepth: z.number().int().min(0).optional(),
        expectedToolCalls: z.number().int().min(0).optional(),
      });

      const parsed = SimulatePlanRequest.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({ error: "Invalid request", details: parsed.error.issues });
        return;
      }

      const { workerCount, modelTier, delegationDepth, expectedToolCalls } = parsed.data;

      const plan = createSwarmCostPlan({
        workerCount,
        modelTier: modelTier ?? "standard",
        delegationDepth: delegationDepth ?? 1,
        expectedToolCalls: expectedToolCalls ?? 2,
      });

      const stats = swarmCostGate.getStats();
      const remainingBudget = Math.max(0, BUDGET_LIMITS.perSession - stats.sessionSpend);

      const throttleDecision = calculateThrottleDecision(
        {
          remainingBudget,
          originalWorkerCount: workerCount,
          originalModelTier: modelTier ?? "standard",
          originalMaxTokens: 4096,
          delegationDepth: delegationDepth ?? 1,
          expectedToolCalls: expectedToolCalls ?? 2,
        },
        BUDGET_LIMITS.perSession,
      );

      res.json({ plan, throttleDecision });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/cost-governance/instrumentation", ...swarmAdmin, async (_req: Request, res: Response) => {
    try {
      const breakdown = globalInstrumentation.getBreakdown();
      res.json(breakdown);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  // ============================================
  // OpenClaw Multi-Agent Swarm Integration
  // ============================================

  app.get("/api/openclaw/status", ...auth, async (_req, res) => {
    try {
      const { openClawService } = await import("../../ai/openclaw-service");
      const status = openClawService.getStatus();
      const health = await openClawService.checkHealth();
      res.json({ ...status, ...health });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/openclaw/dispatch", ...swarmAdmin, async (req, res) => {
    try {
      const { openClawService } = await import("../../ai/openclaw-service");
      const { task, model, skills, priority, agentCount, strategy, metadata } = req.body;
      
      if (!task) {
        return res.status(400).json({ error: "Task description is required" });
      }

      let session;
      if (agentCount && agentCount > 1) {
        session = await openClawService.dispatchSwarm({
          task,
          model,
          skills,
          priority,
          agentCount,
          strategy: strategy || "parallel",
          metadata,
        });
      } else {
        session = await openClawService.dispatchTask({ task, model, skills, priority, metadata });
      }

      res.json(session);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/openclaw/sessions", ...auth, async (req, res) => {
    try {
      const { openClawService } = await import("../../ai/openclaw-service");
      const limit = parseInt(req.query.limit as string) || 50;
      const sessions = openClawService.getSessions(limit);
      res.json({
        sessions,
        total: sessions.length,
        active: sessions.filter((s) => s.status === "running" || s.status === "pending").length,
        completed: sessions.filter((s) => s.status === "completed").length,
        failed: sessions.filter((s) => s.status === "failed").length,
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/openclaw/sessions/:sessionId", ...auth, async (req, res) => {
    try {
      const { openClawService } = await import("../../ai/openclaw-service");
      const session = openClawService.getSession(req.params.sessionId);
      if (!session) {
        return res.status(404).json({ error: "Session not found" });
      }
      res.json(session);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/openclaw/skills", ...auth, async (_req, res) => {
    try {
      const { openClawService } = await import("../../ai/openclaw-service");
      const skills = await openClawService.listSkills();
      res.json({ skills, count: skills.length });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  // ============================================
  // Swarm Intelligence & Cost Optimization
  // ============================================

  app.post("/api/swarm/orchestrate", ...swarmAdmin, async (req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const { id, type, priority, requiredCapabilities, preferredAgents, budget, context, dependencies, subtasks, override } = req.body;

      if (!type || !requiredCapabilities || !Array.isArray(requiredCapabilities)) {
        return res.status(400).json({ error: "type and requiredCapabilities[] are required" });
      }

      const task = {
        id: id || `task-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
        type: type as any,
        priority: priority || "normal",
        requiredCapabilities,
        preferredAgents,
        budget,
        context: context || {},
        dependencies,
        subtasks,
        override: override || false,
      };

      const result = await swarmOrchestrator.orchestrate(task);
      res.json(result);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/status", ...auth, async (_req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const status = swarmOrchestrator.getSwarmStatus();
      res.json(status);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/geometry", ...auth, async (_req, res) => {
    try {
      const { sacredGeometryOptimizer } = await import("../../ai/swarm/sacred-geometry-optimizer");
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const { WORKFLOW_PRESETS } = await import("../../ai/crew/langgraph");

      const metrics = sacredGeometryOptimizer.getMetrics();

      const agents = swarmOrchestrator.getAgents();
      const clusters = sacredGeometryOptimizer.formAgentClusters(
        agents.map(a => ({
          id: a.id,
          capabilities: a.capabilities,
          load: a.load,
          successRate: a.successRate,
        }))
      );

      const workflowAnalyses = Object.entries(WORKFLOW_PRESETS).slice(0, 6).map(([id, def]) => {
        const symmetry = sacredGeometryOptimizer.analyzeWorkflowSymmetry(
          def.nodes.map(n => ({ id: n.id, type: n.type })),
          def.edges.map(e => ({ from: e.from, to: e.to }))
        );
        const schedule = sacredGeometryOptimizer.generateGeometricSchedule(
          def.nodes.map(n => ({ id: n.id, type: n.type })),
          def.edges.map(e => ({ from: e.from, to: e.to }))
        );
        return {
          workflowId: id,
          name: def.name,
          symmetryScore: symmetry.overallScore,
          branchSymmetry: symmetry.branchSymmetry,
          layerCount: symmetry.layerCount,
          topology: schedule.topology,
          efficiencyGain: schedule.efficiencyGain,
          suggestions: symmetry.optimizationSuggestions,
        };
      });

      const agentsForSymmetry = agents.map(a => ({
        id: a.id,
        capabilities: a.capabilities,
        load: a.load,
        successRate: a.successRate,
        type: a.type,
      }));
      const agentEdges = agents.flatMap((a, i) =>
        agents.slice(i + 1)
          .filter(b => a.capabilities.some(c => b.capabilities.includes(c)))
          .map(b => ({ from: a.id, to: b.id }))
      );

      const symmetryAnalysis = sacredGeometryOptimizer.analyzeSymmetryTypes(agentsForSymmetry, agentEdges);
      const equitablePartition = sacredGeometryOptimizer.computeEquitablePartition(
        agentsForSymmetry,
        agentEdges
      );

      res.json({
        metrics,
        clusters,
        workflowAnalyses,
        fibonacciRetryIntervals: Array.from({ length: 8 }, (_, i) => sacredGeometryOptimizer.getFibonacciRetryInterval(i)),
        symmetryAnalysis,
        equitablePartition,
        advancedSystems: [
          "Lévy Flight Exploration (Mantegna algorithm)",
          "Kuramoto Phase Synchronization",
          "Golden Section Search",
          "Platonic Solid Topologies (tetrahedron/octahedron/icosahedron/dodecahedron)",
          "Vesica Piscis Consensus Metric",
          "Golden Spiral Optimizer",
        ],
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/geometry/advanced", ...swarmAdmin, async (req: Request, res: Response) => {
    try {
      const { sacredGeometryOptimizer } = await import("../../ai/swarm/sacred-geometry-optimizer");

      const AdvancedGeometryRequest = z.object({
        method: z.enum(["levyFlight", "kuramotoSync", "kuramotoSyncFast", "goldenSectionSearch", "platonicCluster", "vesicaPiscisOverlap", "spiralOptimize"]),
        params: z.record(z.unknown()).optional(),
      });

      const parsed = AdvancedGeometryRequest.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({ error: "Invalid request", details: parsed.error.issues });
        return;
      }

      const { method, params } = parsed.data;
      let result: unknown;

      switch (method) {
        case "levyFlight": {
          const agents = (params?.agents as Array<{ id: string; load: number; successRate: number }>) || [];
          const threshold = (params?.stagnationThreshold as number) || 5;
          result = sacredGeometryOptimizer.levyFlightExplore(agents, threshold);
          break;
        }
        case "kuramotoSync": {
          const agents = (params?.agents as Array<{ id: string; naturalFrequency: number; currentPhase: number }>) || [];
          const coupling = (params?.couplingStrength as number) || 0.5;
          const dt = (params?.dt as number) || 0.1;
          const steps = (params?.steps as number) || 50;
          result = sacredGeometryOptimizer.kuramotoSync(agents, coupling, dt, steps);
          break;
        }
        case "kuramotoSyncFast": {
          const agents = (params?.agents as Array<{ id: string; naturalFrequency: number; currentPhase: number; queueDepth?: number }>) || [];
          const coupling = (params?.couplingStrength as number) || 0.5;
          result = await sacredGeometryOptimizer.kuramotoSyncFast(agents, coupling);
          break;
        }
        case "goldenSectionSearch": {
          const presets: Record<string, (x: number) => number> = {
            quadratic: (x) => x * x,
            cubic: (x) => x * x * x - 2 * x,
            sinusoidal: (x) => Math.sin(x),
            exponential: (x) => Math.exp(-x) + x * x,
            rosenbrock1d: (x) => (1 - x) * (1 - x),
          };
          const fname = (params?.function as string) || "quadratic";
          const f = presets[fname];
          if (!f) {
            res.status(400).json({ error: `Unknown function preset: ${fname}. Available: ${Object.keys(presets).join(", ")}` });
            return;
          }
          const a = (params?.a as number) || 0;
          const b = (params?.b as number) || 1;
          const tol = (params?.tolerance as number) || 1e-6;
          result = sacredGeometryOptimizer.goldenSectionSearch(f, a, b, tol);
          break;
        }
        case "platonicCluster": {
          const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
          const swarmAgents = swarmOrchestrator.getAgents();
          const topology = (params?.topology as "tetrahedron" | "octahedron" | "icosahedron" | "dodecahedron") || "tetrahedron";
          const agentData = swarmAgents.slice(0, 20).map(a => ({
            id: a.id,
            capabilities: a.capabilities,
            load: a.load,
            successRate: a.successRate,
          }));
          result = sacredGeometryOptimizer.formPlatonicCluster(agentData, topology);
          break;
        }
        case "vesicaPiscisOverlap": {
          const groupA = (params?.groupA as Array<{ id: string; result: number; confidence: number }>) || [];
          const groupB = (params?.groupB as Array<{ id: string; result: number; confidence: number }>) || [];
          result = sacredGeometryOptimizer.vesicaPiscisOverlap(groupA, groupB);
          break;
        }
        case "spiralOptimize": {
          const dims = (params?.dimensions as number) || 2;
          const bounds = (params?.bounds as Array<[number, number]>) || Array(dims).fill([0, 1]);
          const iters = (params?.iterations as number) || 100;
          const points = (params?.spiralPoints as number) || 20;
          const multiPresets: Record<string, (p: number[]) => number> = {
            sphere: (p) => p.reduce((s, v) => s + v * v, 0),
            rastrigin: (p) => 10 * p.length + p.reduce((s, v) => s + v * v - 10 * Math.cos(2 * Math.PI * v), 0),
            ackley: (p) => -20 * Math.exp(-0.2 * Math.sqrt(p.reduce((s, v) => s + v * v, 0) / p.length)) - Math.exp(p.reduce((s, v) => s + Math.cos(2 * Math.PI * v), 0) / p.length) + 20 + Math.E,
            rosenbrock: (p) => { let s = 0; for (let i = 0; i < p.length - 1; i++) s += 100 * Math.pow(p[i+1] - p[i]*p[i], 2) + Math.pow(1 - p[i], 2); return s; },
          };
          const mfname = (params?.function as string) || "sphere";
          const mf = multiPresets[mfname];
          if (!mf) {
            res.status(400).json({ error: `Unknown function preset: ${mfname}. Available: ${Object.keys(multiPresets).join(", ")}` });
            return;
          }
          result = sacredGeometryOptimizer.spiralOptimize(mf, dims, bounds, iters, points);
          break;
        }
      }

      res.json({ method, result });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/fourier-lens/route", ...auth, async (req: Request, res: Response) => {
    try {
      const RouteRequest = z.object({
        description: z.string().min(1).max(500),
        budgetTier: z.number().int().min(1).max(3).optional(),
      });

      const parsed = RouteRequest.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({ error: "Invalid request", details: parsed.error.issues });
        return;
      }

      const { fourierRouter } = await import("../../ai/engines/fourier-lens-router");
      const result = await fourierRouter.routeByResonance(parsed.data.description);

      res.json({
        method: "fourier-lens-dft",
        agent: result.agent,
        resonantFrequency: result.resonantFrequency,
        confidence: result.confidence,
        spectrumPeaks: result.spectrumPeaks,
        computeTimeMs: result.computeTimeMs,
        algorithm: "Discrete Fourier Transform on text-embedding-3-small (1536-dim → 768 Nyquist limit)",
        agentSignatureHz: Object.fromEntries(fourierRouter.getAgentSignatures()),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/fourier-lens/metrics", ...auth, async (_req: Request, res: Response) => {
    try {
      const { fourierRouter } = await import("../../ai/engines/fourier-lens-router");
      res.json(fourierRouter.getMetrics());
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/evaluation", ...auth, async (_req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const { agentEvaluator } = await import("../../ai/swarm/agent-evaluator");
      const { communicationBus } = await import("../../ai/swarm/communication-bus");

      const agents = swarmOrchestrator.getAgents();
      const busStats = communicationBus.getMessageStats();

      const evaluation = agentEvaluator.evaluateSystem(
        agents.map(a => ({
          id: a.id,
          type: a.type,
          capabilities: a.capabilities,
          load: a.load,
          successRate: a.successRate,
          tasksCompleted: a.tasksCompleted,
          costPerTask: a.costPerTask,
          averageResponseTime: a.averageResponseTime,
          tier: (a as any).tier as 'primary' | 'sub' | undefined,
          parentId: (a as any).parentId as string | undefined,
        })),
        undefined,
        busStats,
        7
      );

      res.json(evaluation);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/optimization", ...auth, async (_req, res) => {
    try {
      const { bayesianOptimizer } = await import("../../ai/swarm/bayesian-optimizer");
      const { agentEvaluator } = await import("../../ai/swarm/agent-evaluator");
      const { geneticOptimizer } = await import("../../ai/swarm/genetic-optimizer");

      const state = bayesianOptimizer.getState();
      const parameters = bayesianOptimizer.getParameters();
      const recommendations = bayesianOptimizer.generateRecommendations();
      const evaluationHistory = agentEvaluator.getEvaluationHistory();
      const gaEvolution = geneticOptimizer.getEvolutionSummary();

      res.json({
        state,
        parameters,
        recommendations,
        geneticAlgorithm: gaEvolution,
        evaluationHistory: evaluationHistory.slice(-10).map(e => ({
          timestamp: e.timestamp,
          systemCompositeScore: e.systemCompositeScore,
          systemHealth: e.systemHealth,
          verticalAverages: e.verticalAverages,
          recommendationCount: e.recommendations.length,
        })),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/genetic", ...auth, async (_req, res) => {
    try {
      const { geneticOptimizer } = await import("../../ai/swarm/genetic-optimizer");
      const gaState = geneticOptimizer.getState();

      res.json({
        generation: gaState.generation,
        populationSize: gaState.population.length,
        bestEver: {
          fitness: gaState.bestEver.fitness,
          genes: gaState.bestEver.genes,
          id: gaState.bestEver.id,
          generation: gaState.bestEver.generation,
        },
        config: gaState.config,
        isConverged: gaState.isConverged,
        stagnationCount: gaState.stagnationCount,
        topChromosomes: gaState.population
          .sort((a, b) => b.fitness - a.fitness)
          .slice(0, 10)
          .map(c => ({
            id: c.id,
            fitness: c.fitness,
            generation: c.generation,
            mutations: c.mutations,
            parentIds: c.parentIds,
          })),
        generationHistory: gaState.generationHistory.slice(-30),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/genetic/candidates", ...auth, async (req, res) => {
    try {
      const { geneticOptimizer } = await import("../../ai/swarm/genetic-optimizer");
      const count = Math.min(parseInt(req.query.count as string) || 5, 20);
      const candidates = geneticOptimizer.proposeHybridCandidates(count);

      const { bayesianOptimizer } = await import("../../ai/swarm/bayesian-optimizer");
      const paramDefs = bayesianOptimizer.getParameters();

      res.json({
        count: candidates.length,
        parameterNames: paramDefs.map(p => p.name),
        candidates: candidates.map(c => ({
          chromosomeId: c.chromosome.id,
          hybridScore: +c.hybridScore.toFixed(4),
          fitness: c.chromosome.fitness,
          generation: c.chromosome.generation,
          mutations: c.chromosome.mutations,
          parameters: Object.fromEntries(
            c.chromosome.genes.map((g, i) => [paramDefs[i]?.name || `param_${i}`, +g.toFixed(4)])
          ),
        })),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/genetic/evolve", ...swarmAdmin, async (_req, res) => {
    try {
      const { geneticOptimizer } = await import("../../ai/swarm/genetic-optimizer");
      const { bayesianOptimizer } = await import("../../ai/swarm/bayesian-optimizer");

      geneticOptimizer.seedFromBayesian();
      const stats = geneticOptimizer.evolve();

      const hybridBest = geneticOptimizer.proposeHybridCandidates(1);
      if (hybridBest.length > 0) {
        bayesianOptimizer.applyParameters(hybridBest[0].chromosome.genes);
      }

      res.json({
        ok: true,
        evolutionStats: stats,
        appliedBestParameters: hybridBest.length > 0,
        summary: geneticOptimizer.getEvolutionSummary(),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/subagents", ...auth, async (_req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const subAgents = swarmOrchestrator.getSubAgents();
      res.json({
        total: subAgents.length,
        subAgents: subAgents.map(a => ({
          id: a.id,
          type: a.type,
          parentId: a.parentId,
          tier: a.tier,
          status: a.status,
          load: a.load,
          capabilities: a.capabilities,
          specialization: a.specialization,
          costPerTask: a.costPerTask,
          successRate: a.successRate,
          tasksCompleted: a.tasksCompleted,
          averageResponseTime: a.averageResponseTime,
        })),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/agents/hierarchy", ...auth, async (_req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const hierarchy = swarmOrchestrator.getAgentHierarchy();
      res.json({
        totalPrimary: hierarchy.length,
        totalSubAgents: hierarchy.reduce((sum, h) => sum + h.subAgents.length, 0),
        hierarchy: hierarchy.map(h => ({
          primary: {
            id: h.primary.id,
            type: h.primary.type,
            status: h.primary.status,
            load: h.primary.load,
            capabilities: h.primary.capabilities,
            specialization: h.primary.specialization,
            successRate: h.primary.successRate,
            tasksCompleted: h.primary.tasksCompleted,
            costPerTask: h.primary.costPerTask,
          },
          subAgents: h.subAgents.map(s => ({
            id: s.id,
            parentId: s.parentId,
            status: s.status,
            load: s.load,
            capabilities: s.capabilities,
            specialization: s.specialization,
            successRate: s.successRate,
            tasksCompleted: s.tasksCompleted,
            costPerTask: s.costPerTask,
          })),
        })),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/subagents/:id/toggle", ...auth, async (req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const subAgentId = req.params.id;
      const { status } = req.body as { status: 'idle' | 'offline' };

      if (!status || !['idle', 'offline'].includes(status)) {
        return res.status(400).json({ error: "status must be 'idle' or 'offline'" });
      }

      const success = swarmOrchestrator.toggleSubAgent(subAgentId, status);
      if (!success) {
        return res.status(404).json({ error: `Sub-agent '${subAgentId}' not found or is not a sub-agent` });
      }

      res.json({ success: true, id: subAgentId, status });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/agents", ...auth, async (_req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const agents = swarmOrchestrator.getAgents();
      res.json({ agents, count: agents.length });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/agents/:agentId", ...auth, async (req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const agent = swarmOrchestrator.getAgent(req.params.agentId);
      if (!agent) {
        return res.status(404).json({ error: "Agent not found" });
      }
      res.json(agent);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/agents/:agentId/command", ...auth, async (req, res) => {
    try {
      const { swarmOrchestrator } = await import("../../ai/swarm/orchestrator");
      const { command, payload } = req.body;
      if (!command) {
        return res.status(400).json({ error: "command is required" });
      }
      const result = await swarmOrchestrator.commandAgent(req.params.agentId, command, payload || {});
      res.json({ agentId: req.params.agentId, command, result });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/skills", ...auth, async (req, res) => {
    try {
      const { skillsLibrary } = await import("../../ai/swarm/skills-library");
      const category = req.query.category as string | undefined;
      const query = req.query.query as string | undefined;

      let rawSkills;
      if (category) {
        rawSkills = skillsLibrary.findByCategory(category as any);
      } else if (query) {
        rawSkills = skillsLibrary.search(query);
      } else {
        rawSkills = skillsLibrary.getAllSkills();
      }

      const skills = rawSkills.map(s => ({
        id: s.id,
        name: s.name,
        category: s.category,
        description: s.description,
        requiredAgents: s.requiredAgents,
        cost: s.cost,
        agentCount: s.requiredAgents.length,
        status: "active",
      }));

      const categories = Array.from(new Set(rawSkills.map(s => s.category))).sort();
      res.json({ skills, count: skills.length, categories });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/skills/:skillId/execute", ...auth, async (req, res) => {
    try {
      const { skillsLibrary } = await import("../../ai/swarm/skills-library");
      const aiModels = await import("../../integrations/ai-models");
      const { agentAnalytics } = await import("../../ai/agent-analytics");

      const SkillExecuteBody = z.object({
        query: z.string().max(2000).optional(),
        data: z.record(z.unknown()).optional(),
        parameters: z.record(z.unknown()).optional(),
        priority: z.string().optional(),
      });
      const parsed = SkillExecuteBody.safeParse(req.body || {});
      if (!parsed.success) {
        return res.status(400).json({ error: "Invalid request body", details: parsed.error.issues });
      }
      const context = parsed.data;

      const skillId = req.params.skillId;
      const skill = skillsLibrary.get(skillId);
      if (!skill) {
        return res.status(404).json({ error: `Skill not found: ${skillId}` });
      }
      if (!Array.isArray(skill.requiredAgents) || skill.requiredAgents.length === 0) {
        return res.status(500).json({ error: `Skill ${skillId} has no agents configured` });
      }

      const startTime = Date.now();

      const dispatchFn = async (options: { task: string; priority?: string; timeout?: number }) => {
        const agentChain = skill.requiredAgents.join(" → ");
        const systemPrompt = `You are the Trinity Consortium AI executing a multi-agent skill pipeline.
Agent Chain: ${agentChain}
Skill: ${skill.name} (${skill.category})
Description: ${skill.description}

You represent the combined intelligence of these specialized agents: ${skill.requiredAgents.join(", ")}.
Provide thorough, actionable analysis. Structure your response with clear sections and recommendations.`;

        const messages = [
          { role: "system" as const, content: systemPrompt },
          { role: "user" as const, content: options.task },
        ];

        let responseText: string;
        try {
          const response = await aiModels.chat({ model: "gemini-2.5-flash" as any, messages, maxTokens: 4096, temperature: 0.7 });
          responseText = typeof response === "string" ? response : JSON.stringify(response);
        } catch (aiErr: any) {
          console.error(`[Skills] AI call failed for ${skillId}:`, aiErr.message);
          responseText = `[Skill execution encountered an AI error: ${aiErr.message}. The skill pipeline ${agentChain} was unable to complete. Please try again or check AI integration status.]`;
        }

        const duration = Date.now() - startTime;

        for (const agent of skill.requiredAgents) {
          agentAnalytics.recordToolExecution({
            executionId: `skill-${Date.now()}-${agent}`,
            agentName: agent,
            toolName: `skill:${skillId}`,
            success: true,
            durationMs: duration / skill.requiredAgents.length,
            estimatedCost: skill.cost / skill.requiredAgents.length,
          }).catch(() => {});
        }

        return {
          sessionId: `skill-${Date.now()}`,
          task: options.task,
          status: "completed",
          result: responseText,
          agents: skill.requiredAgents,
          duration,
          cost: skill.cost,
        };
      };

      const result = await skillsLibrary.execute(skillId, context, dispatchFn);
      res.json({
        skillId,
        skillName: skill.name,
        category: skill.category,
        agents: skill.requiredAgents,
        cost: skill.cost,
        result,
        executedAt: new Date().toISOString(),
      });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/cost/stats", ...auth, async (_req, res) => {
    try {
      const { costOptimizer } = await import("../../ai/swarm/cost-optimizer");
      const stats = costOptimizer.getCostStats();
      res.json(stats);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/cost/estimate", ...auth, async (req, res) => {
    try {
      const { costOptimizer } = await import("../../ai/swarm/cost-optimizer");
      const { estimatedTokens, priority } = req.body;
      const estimate = costOptimizer.estimateTaskCost(estimatedTokens || 1000, priority || "normal");
      res.json(estimate);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.get("/api/swarm/cost/limits", ...auth, async (_req, res) => {
    try {
      const { costOptimizer } = await import("../../ai/swarm/cost-optimizer");
      const limits = costOptimizer.getLimits();
      res.json(limits);
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.put("/api/swarm/cost/limits", ...auth, async (req, res) => {
    try {
      const { costOptimizer } = await import("../../ai/swarm/cost-optimizer");
      costOptimizer.updateLimits(req.body);
      res.json({ success: true, limits: costOptimizer.getLimits() });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/cost/emergency-reset", ...auth, async (_req, res) => {
    try {
      const { costOptimizer } = await import("../../ai/swarm/cost-optimizer");
      costOptimizer.resetEmergencyBrake();
      res.json({ success: true, message: "Emergency brake reset", stats: costOptimizer.getCostStats() });
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });

  app.post("/api/swarm/fourier-lens/route-all", ...auth, async (req: Request, res: Response) => {
    const { description } = req.body;
    if (!description) return res.status(400).json({ error: "description required" });
    try {
      const { swarmFourierRouter } = await import("../../ai/engines/fourier-lens-router");
      const result = await swarmFourierRouter.routeFullSpectrum(description);
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/swarm/fourier-lens/metrics-all", ...auth, async (_req: Request, res: Response) => {
    try {
      const { swarmFourierRouter } = await import("../../ai/engines/fourier-lens-router");
      res.json(swarmFourierRouter.getMetrics());
    } catch (error: unknown) {
      res.status(500).json({ error: errorMessage(error) });
    }
  });
}
