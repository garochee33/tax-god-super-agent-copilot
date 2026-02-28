import { db } from "../../db";
import { eq, and, sql, desc, asc, lt, isNull, inArray } from "drizzle-orm";
import { computeNodes, computeTasks, computeContributions, computeNetworkStats } from "@shared/schema";
import type { InsertComputeNode, InsertComputeTask, ComputeNode, ComputeTask } from "@shared/schema";
import crypto from "crypto";
import { pbftEngine } from "../../ai/consensus/pbft-engine";
import { gossipEngine } from "../../ai/consensus/gossip-engine";
import { contributionLedger } from "../../ai/consensus/crdt-engine";

interface NodeSpecs {
  cpuCores: number;
  cpuModel?: string;
  ramMb: number;
  gpuModel?: string;
  gpuVramMb?: number;
  osInfo?: string;
  maxCpuPercent?: number;
  maxRamPercent?: number;
  gpuEnabled?: boolean;
  activeHoursStart?: number;
  activeHoursEnd?: number;
}

export class ComputeBrokerService {
  private schedulerInterval: ReturnType<typeof setInterval> | null = null;

  private generateFingerprint(userId: string, specs: NodeSpecs): string {
    const data = `${userId}:${specs.cpuCores}:${specs.cpuModel || ""}:${specs.ramMb}:${specs.gpuModel || ""}:${specs.gpuVramMb || 0}:${specs.osInfo || ""}`;
    return crypto.createHash("sha256").update(data).digest("hex");
  }

  private hashPayload(payload: any): string {
    return crypto.createHash("sha256").update(JSON.stringify(payload)).digest("hex");
  }

  async registerNode(userId: string, specs: NodeSpecs): Promise<ComputeNode> {
    const fingerprint = this.generateFingerprint(userId, specs);

    const existing = await db
      .select()
      .from(computeNodes)
      .where(eq(computeNodes.nodeFingerprint, fingerprint))
      .limit(1);

    if (existing.length > 0) {
      const [updated] = await db
        .update(computeNodes)
        .set({
          cpuCores: specs.cpuCores,
          cpuModel: specs.cpuModel,
          ramMb: specs.ramMb,
          gpuModel: specs.gpuModel,
          gpuVramMb: specs.gpuVramMb,
          osInfo: specs.osInfo,
          maxCpuPercent: specs.maxCpuPercent ?? 50,
          maxRamPercent: specs.maxRamPercent ?? 50,
          gpuEnabled: specs.gpuEnabled ?? false,
          activeHoursStart: specs.activeHoursStart,
          activeHoursEnd: specs.activeHoursEnd,
          updatedAt: new Date(),
        })
        .where(eq(computeNodes.id, existing[0].id))
        .returning();
      console.log(`[ComputeBroker] Updated node ${updated.id} for user ${userId}`);
      return updated;
    }

    const [node] = await db
      .insert(computeNodes)
      .values({
        userId,
        nodeFingerprint: fingerprint,
        cpuCores: specs.cpuCores,
        cpuModel: specs.cpuModel,
        ramMb: specs.ramMb,
        gpuModel: specs.gpuModel,
        gpuVramMb: specs.gpuVramMb,
        osInfo: specs.osInfo,
        maxCpuPercent: specs.maxCpuPercent ?? 50,
        maxRamPercent: specs.maxRamPercent ?? 50,
        gpuEnabled: specs.gpuEnabled ?? false,
        activeHoursStart: specs.activeHoursStart,
        activeHoursEnd: specs.activeHoursEnd,
        status: "offline",
      })
      .returning();

    console.log(`[ComputeBroker] Registered new node ${node.id} for user ${userId}`);
    return node;
  }

  async updateNodeStatus(nodeId: string, status: "online" | "offline" | "paused"): Promise<void> {
    await db
      .update(computeNodes)
      .set({ status, updatedAt: new Date() })
      .where(eq(computeNodes.id, nodeId));
    console.log(`[ComputeBroker] Node ${nodeId} status -> ${status}`);
  }

  async heartbeat(nodeId: string): Promise<void> {
    const now = new Date();
    await db
      .update(computeNodes)
      .set({
        lastHeartbeat: now,
        status: sql`CASE WHEN ${computeNodes.status} = 'offline' THEN 'online' ELSE ${computeNodes.status} END`,
        updatedAt: now,
      })
      .where(eq(computeNodes.id, nodeId));

    const [node] = await db
      .select()
      .from(computeNodes)
      .where(eq(computeNodes.id, nodeId))
      .limit(1);

    if (node) {
      const activeTasks = await db
        .select({ count: sql<number>`COUNT(*)::int` })
        .from(computeTasks)
        .where(
          and(
            eq(computeTasks.assignedNodeId, nodeId),
            eq(computeTasks.status, "processing")
          )
        );

      gossipEngine.updateLocalState({
        nodeId: node.id,
        userId: node.userId,
        status: node.status as 'online' | 'offline' | 'paused',
        cpuCores: node.cpuCores,
        ramMb: node.ramMb,
        gpuModel: node.gpuModel,
        activeTasks: activeTasks[0]?.count ?? 0,
        trustScore: Number(node.trustScore) || 0,
        lastHeartbeat: now.getTime(),
        version: now.getTime(),
      });
    }
  }

  async getOnlineNodes(): Promise<ComputeNode[]> {
    const cutoff = new Date(Date.now() - 60_000);
    return db
      .select()
      .from(computeNodes)
      .where(
        and(
          eq(computeNodes.status, "online"),
          sql`${computeNodes.lastHeartbeat} >= ${cutoff}`
        )
      );
  }

  async getNodesByUser(userId: string): Promise<ComputeNode[]> {
    return db
      .select()
      .from(computeNodes)
      .where(eq(computeNodes.userId, userId));
  }

  async submitTask(
    taskType: string,
    payload: any,
    options?: {
      priority?: number;
      timeoutMs?: number;
      sourceAgentId?: string;
      parentTaskId?: string;
    }
  ): Promise<string> {
    const payloadHash = this.hashPayload(payload);

    const [task] = await db
      .insert(computeTasks)
      .values({
        taskType,
        payload,
        payloadHash,
        priority: options?.priority ?? 5,
        timeoutMs: options?.timeoutMs ?? 30000,
        sourceAgentId: options?.sourceAgentId,
        parentTaskId: options?.parentTaskId,
        status: "pending",
      })
      .returning();

    console.log(`[ComputeBroker] Task ${task.id} submitted (type: ${taskType}, priority: ${task.priority})`);
    return task.id;
  }

  async submitConsensusTask(
    taskType: string,
    payload: any,
    options?: {
      replicas?: number;
      timeoutMs?: number;
    }
  ): Promise<{ consensusId: string; replicas: number }> {
    const onlineNodes = await this.getOnlineNodes();

    if (onlineNodes.length < 4) {
      console.warn(`[ComputeBroker] Only ${onlineNodes.length} nodes online (need >= 4 for consensus), falling back to regular task submission`);
      const taskId = await this.submitTask(taskType, payload, { timeoutMs: options?.timeoutMs });
      return { consensusId: taskId, replicas: 1 };
    }

    const consensusId = crypto.randomUUID();
    const consensusRequest = pbftEngine.initiateConsensus(consensusId, taskType, payload, {
      replicas: options?.replicas,
      timeoutMs: options?.timeoutMs,
    });

    const replicas = consensusRequest.requiredReplicas;
    const taskIds: string[] = [];

    for (let i = 0; i < replicas; i++) {
      const [task] = await db
        .insert(computeTasks)
        .values({
          taskType,
          payload,
          payloadHash: this.hashPayload(payload),
          priority: 8,
          timeoutMs: options?.timeoutMs ?? 30000,
          parentTaskId: consensusId,
          status: "pending",
        })
        .returning();
      taskIds.push(task.id);
    }

    console.log(`[ComputeBroker] Consensus task ${consensusId} created with ${replicas} replicas: ${taskIds.join(', ')}`);
    return { consensusId, replicas };
  }

  async assignTasks(): Promise<void> {
    const pendingTasks = await db
      .select()
      .from(computeTasks)
      .where(
        and(
          eq(computeTasks.status, "pending"),
          isNull(computeTasks.assignedNodeId)
        )
      )
      .orderBy(desc(computeTasks.priority), asc(computeTasks.createdAt));

    if (pendingTasks.length === 0) return;

    const cutoff = new Date(Date.now() - 60_000);
    const availableNodes = await db
      .select()
      .from(computeNodes)
      .where(
        and(
          eq(computeNodes.status, "online"),
          sql`${computeNodes.lastHeartbeat} >= ${cutoff}`
        )
      )
      .orderBy(desc(computeNodes.trustScore));

    if (availableNodes.length === 0) return;

    const currentHour = new Date().getUTCHours();

    const eligibleNodes = availableNodes.filter((node) => {
      if (node.activeHoursStart !== null && node.activeHoursEnd !== null) {
        if (node.activeHoursStart <= node.activeHoursEnd) {
          return currentHour >= node.activeHoursStart && currentHour < node.activeHoursEnd;
        } else {
          return currentHour >= node.activeHoursStart || currentHour < node.activeHoursEnd;
        }
      }
      return true;
    });

    if (eligibleNodes.length === 0) return;

    let nodeIndex = 0;
    for (const task of pendingTasks) {
      if (nodeIndex >= eligibleNodes.length) break;

      const node = eligibleNodes[nodeIndex];
      const now = new Date();

      await db
        .update(computeTasks)
        .set({
          assignedNodeId: node.id,
          assignedAt: now,
          status: "processing",
        })
        .where(eq(computeTasks.id, task.id));

      console.log(`[ComputeBroker] Assigned task ${task.id} to node ${node.id}`);
      nodeIndex++;
    }
  }

  async completeTask(taskId: string, nodeId: string, result: any): Promise<void> {
    const resultHash = this.hashPayload(result);
    const now = new Date();

    const [task] = await db
      .select()
      .from(computeTasks)
      .where(eq(computeTasks.id, taskId))
      .limit(1);

    if (!task) {
      console.log(`[ComputeBroker] Task ${taskId} not found`);
      return;
    }

    await db
      .update(computeTasks)
      .set({
        status: "completed",
        result,
        resultHash,
        completedAt: now,
      })
      .where(eq(computeTasks.id, taskId));

    const [node] = await db
      .select()
      .from(computeNodes)
      .where(eq(computeNodes.id, nodeId))
      .limit(1);

    if (!node) {
      console.log(`[ComputeBroker] Node ${nodeId} not found`);
      return;
    }

    const computeMs = task.assignedAt
      ? now.getTime() - new Date(task.assignedAt).getTime()
      : 0;

    const rewardPoints = Math.max(1, Math.floor(computeMs / 1000));

    await db.insert(computeContributions).values({
      nodeId,
      userId: node.userId,
      taskId,
      computeMs,
      taskType: task.taskType,
      rewardPoints,
      verifiedAt: now,
    });

    contributionLedger.recordContribution(node.userId, nodeId, computeMs, rewardPoints);

    await db
      .update(computeNodes)
      .set({
        totalTasksCompleted: sql`${computeNodes.totalTasksCompleted} + 1`,
        totalComputeMs: sql`(CAST(${computeNodes.totalComputeMs} AS BIGINT) + ${computeMs})::text`,
        updatedAt: now,
      })
      .where(eq(computeNodes.id, nodeId));

    const newTrustScore = Number(node.trustScore) || 0;
    contributionLedger.updateTrustScore(nodeId, newTrustScore, Date.now());

    console.log(`[ComputeBroker] Task ${taskId} completed by node ${nodeId} (${computeMs}ms)`);

    if (task.parentTaskId) {
      const consensusRound = pbftEngine.getConsensusStatus(task.parentTaskId);
      if (consensusRound) {
        await this.handleConsensusVote(task.parentTaskId, nodeId, resultHash, result);
      }
    }
  }

  private async handleConsensusVote(taskId: string, nodeId: string, resultHash: string, result: any): Promise<void> {
    const signature = pbftEngine.generateSignature(nodeId, taskId, resultHash);
    const voteResult = pbftEngine.submitVote(taskId, nodeId, resultHash, result, signature, 'pre-prepare');

    if (voteResult.result && (voteResult.result.status === 'agreed' || voteResult.result.status === 'disputed')) {
      await this.processConsensusOutcome(taskId, voteResult.result);
    }
  }

  private async processConsensusOutcome(consensusId: string, consensusResult: import("../../ai/consensus/pbft-engine").ConsensusResult): Promise<void> {
    const now = new Date();

    if (consensusResult.status === 'agreed') {
      const existingParent = await db
        .select()
        .from(computeTasks)
        .where(eq(computeTasks.id, consensusId))
        .limit(1);

      if (existingParent.length > 0) {
        await db
          .update(computeTasks)
          .set({
            status: "completed",
            result: consensusResult.agreedResult,
            resultHash: consensusResult.agreedResultHash,
            completedAt: now,
          })
          .where(eq(computeTasks.id, consensusId));
      }

      console.log(`[ComputeBroker] Consensus ${consensusId} agreed — parent task marked completed`);
    } else if (consensusResult.status === 'disputed') {
      const existingParent = await db
        .select()
        .from(computeTasks)
        .where(eq(computeTasks.id, consensusId))
        .limit(1);

      if (existingParent.length > 0) {
        await db
          .update(computeTasks)
          .set({
            status: "failed",
            errorMessage: "Consensus disputed — nodes disagreed on result",
            completedAt: now,
          })
          .where(eq(computeTasks.id, consensusId));
      }

      console.log(`[ComputeBroker] Consensus ${consensusId} disputed — parent task marked failed`);
    }

    const childTasks = await db
      .select()
      .from(computeTasks)
      .where(eq(computeTasks.parentTaskId, consensusId));

    for (const childTask of childTasks) {
      if (!childTask.assignedNodeId) continue;

      const isDisputing = consensusResult.disputingNodes.includes(childTask.assignedNodeId);

      if (isDisputing) {
        await db
          .update(computeNodes)
          .set({
            trustScore: sql`${computeNodes.trustScore} * 0.95`,
            updatedAt: now,
          })
          .where(eq(computeNodes.id, childTask.assignedNodeId));
        console.log(`[ComputeBroker] Trust penalty (0.95x) for disputing node ${childTask.assignedNodeId}`);
      } else {
        await db
          .update(computeNodes)
          .set({
            trustScore: sql`${computeNodes.trustScore} * 1.02`,
            updatedAt: now,
          })
          .where(eq(computeNodes.id, childTask.assignedNodeId));
        console.log(`[ComputeBroker] Trust boost (1.02x) for agreeing node ${childTask.assignedNodeId}`);
      }
    }
  }

  async failTask(taskId: string, nodeId: string, errorMessage: string): Promise<void> {
    const [task] = await db
      .select()
      .from(computeTasks)
      .where(eq(computeTasks.id, taskId))
      .limit(1);

    if (!task) {
      console.log(`[ComputeBroker] Task ${taskId} not found for failure`);
      return;
    }

    const newRetryCount = task.retryCount + 1;

    if (newRetryCount >= task.maxRetries) {
      await db
        .update(computeTasks)
        .set({
          status: "failed",
          errorMessage,
          retryCount: newRetryCount,
          assignedNodeId: null,
          assignedAt: null,
        })
        .where(eq(computeTasks.id, taskId));
      console.log(`[ComputeBroker] Task ${taskId} permanently failed after ${newRetryCount} retries`);
    } else {
      await db
        .update(computeTasks)
        .set({
          status: "pending",
          errorMessage,
          retryCount: newRetryCount,
          assignedNodeId: null,
          assignedAt: null,
        })
        .where(eq(computeTasks.id, taskId));
      console.log(`[ComputeBroker] Task ${taskId} failed, retry ${newRetryCount}/${task.maxRetries}`);
    }

    await db
      .update(computeNodes)
      .set({
        trustScore: sql`${computeNodes.trustScore} * 0.98`,
        updatedAt: new Date(),
      })
      .where(eq(computeNodes.id, nodeId));
  }

  async getTasksForNode(nodeId: string): Promise<ComputeTask[]> {
    return db
      .select()
      .from(computeTasks)
      .where(eq(computeTasks.assignedNodeId, nodeId));
  }

  async getPendingTasks(): Promise<ComputeTask[]> {
    return db
      .select()
      .from(computeTasks)
      .where(
        and(
          eq(computeTasks.status, "pending"),
          isNull(computeTasks.assignedNodeId)
        )
      )
      .orderBy(desc(computeTasks.priority), asc(computeTasks.createdAt));
  }

  async captureNetworkSnapshot(): Promise<void> {
    const cutoff = new Date(Date.now() - 60_000);
    const cutoff24h = new Date(Date.now() - 86_400_000);

    const [nodeStats] = await db
      .select({
        totalNodes: sql<number>`COUNT(*)::int`,
        onlineNodes: sql<number>`COUNT(*) FILTER (WHERE ${computeNodes.status} = 'online' AND ${computeNodes.lastHeartbeat} >= ${cutoff})::int`,
        totalCpuCores: sql<number>`COALESCE(SUM(${computeNodes.cpuCores}), 0)::int`,
        totalRamMb: sql<number>`COALESCE(SUM(${computeNodes.ramMb}), 0)::int`,
        totalGpuNodes: sql<number>`COUNT(*) FILTER (WHERE ${computeNodes.gpuEnabled} = true)::int`,
      })
      .from(computeNodes);

    const [taskStats] = await db
      .select({
        activeTasks: sql<number>`COUNT(*) FILTER (WHERE ${computeTasks.status} = 'processing')::int`,
        completedTasks24h: sql<number>`COUNT(*) FILTER (WHERE ${computeTasks.status} = 'completed' AND ${computeTasks.completedAt} >= ${cutoff24h})::int`,
        failedTasks24h: sql<number>`COUNT(*) FILTER (WHERE ${computeTasks.status} = 'failed' AND ${computeTasks.createdAt} >= ${cutoff24h})::int`,
        avgTaskLatencyMs: sql<number>`AVG(EXTRACT(EPOCH FROM (${computeTasks.completedAt} - ${computeTasks.assignedAt})) * 1000) FILTER (WHERE ${computeTasks.status} = 'completed' AND ${computeTasks.completedAt} >= ${cutoff24h})::int`,
      })
      .from(computeTasks);

    const [computeSum] = await db
      .select({
        totalComputeMs24h: sql<string>`COALESCE(SUM(${computeContributions.computeMs}), 0)::text`,
      })
      .from(computeContributions)
      .where(sql`${computeContributions.createdAt} >= ${cutoff24h}`);

    const topContributors = await db
      .select({
        userId: computeContributions.userId,
        totalPoints: sql<number>`SUM(${computeContributions.rewardPoints})::int`,
      })
      .from(computeContributions)
      .groupBy(computeContributions.userId)
      .orderBy(desc(sql`SUM(${computeContributions.rewardPoints})`))
      .limit(10);

    await db.insert(computeNetworkStats).values({
      totalNodes: nodeStats.totalNodes,
      onlineNodes: nodeStats.onlineNodes,
      totalCpuCores: nodeStats.totalCpuCores,
      totalRamMb: nodeStats.totalRamMb,
      totalGpuNodes: nodeStats.totalGpuNodes,
      activeTasks: taskStats.activeTasks,
      completedTasks24h: taskStats.completedTasks24h,
      failedTasks24h: taskStats.failedTasks24h,
      avgTaskLatencyMs: taskStats.avgTaskLatencyMs,
      totalComputeMs24h: computeSum.totalComputeMs24h,
      topContributors,
    });

    console.log(`[ComputeBroker] Network snapshot captured: ${nodeStats.onlineNodes} online, ${taskStats.activeTasks} active tasks`);
  }

  async getLatestNetworkStats() {
    const [stats] = await db
      .select()
      .from(computeNetworkStats)
      .orderBy(desc(computeNetworkStats.snapshotAt))
      .limit(1);
    return stats || null;
  }

  async getContributionLeaderboard(limit: number = 10) {
    return db
      .select({
        userId: computeContributions.userId,
        totalPoints: sql<number>`SUM(${computeContributions.rewardPoints})::int`,
        totalTasks: sql<number>`COUNT(*)::int`,
        totalComputeMs: sql<number>`SUM(${computeContributions.computeMs})::int`,
      })
      .from(computeContributions)
      .groupBy(computeContributions.userId)
      .orderBy(desc(sql`SUM(${computeContributions.rewardPoints})`))
      .limit(limit);
  }

  async cleanupStaleTasks(): Promise<void> {
    const staleTasks = await db
      .select()
      .from(computeTasks)
      .where(
        and(
          eq(computeTasks.status, "processing"),
          sql`${computeTasks.assignedAt} IS NOT NULL AND ${computeTasks.assignedAt} + (${computeTasks.timeoutMs} || ' milliseconds')::interval < NOW()`
        )
      );

    for (const task of staleTasks) {
      if (task.assignedNodeId) {
        await this.failTask(task.id, task.assignedNodeId, "Task timed out");
      }
    }

    if (staleTasks.length > 0) {
      console.log(`[ComputeBroker] Cleaned up ${staleTasks.length} stale tasks`);
    }
  }

  async markStaleNodesOffline(): Promise<void> {
    const cutoff = new Date(Date.now() - 90_000);

    const result = await db
      .update(computeNodes)
      .set({ status: "offline", updatedAt: new Date() })
      .where(
        and(
          sql`${computeNodes.status} != 'offline'`,
          sql`${computeNodes.lastHeartbeat} < ${cutoff}`
        )
      )
      .returning({ id: computeNodes.id });

    if (result.length > 0) {
      console.log(`[ComputeBroker] Marked ${result.length} stale nodes offline`);
    }
  }

  getDistributedAlgorithmStats() {
    return {
      pbft: pbftEngine.getStats(),
      gossip: gossipEngine.getNetworkTopology(),
      crdt: {
        leaderboard: contributionLedger.getLeaderboard(10),
      },
    };
  }

  startSchedulerLoop(): void {
    if (this.schedulerInterval) {
      console.log("[ComputeBroker] Scheduler loop already running");
      return;
    }

    console.log("[ComputeBroker] Starting scheduler loop (5s interval)");
    this.schedulerInterval = setInterval(async () => {
      try {
        await this.assignTasks();
        await this.cleanupStaleTasks();
        await this.markStaleNodesOffline();
      } catch (err) {
        console.error("[ComputeBroker] Scheduler loop error:", err);
      }
    }, 5000);

    gossipEngine.startGossipLoop(10000);
  }

  stopSchedulerLoop(): void {
    if (this.schedulerInterval) {
      clearInterval(this.schedulerInterval);
      this.schedulerInterval = null;
      console.log("[ComputeBroker] Scheduler loop stopped");
    }
    gossipEngine.stopGossipLoop();
  }
}

export const computeBroker = new ComputeBrokerService();
