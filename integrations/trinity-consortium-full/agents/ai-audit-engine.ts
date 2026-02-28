import { db } from "../../db";
import { members, aiAuditScores, memberActivity, tasks } from "@shared/schema";
import { eq, count, and, gte } from "drizzle-orm";

interface AuditFactors {
  verification: number;
  ndaCompliance: number;
  tenure: number;
  engagement: number;
  taskCompletion: number;
  kycStatus: number;
  tierProgression: number;
}

interface AuditResult {
  score: number;
  riskLevel: "LOW" | "MEDIUM" | "HIGH";
  factors: AuditFactors;
  explanation: string;
}

export async function computeAuditScore(memberId: string): Promise<AuditResult> {
  const [member] = await db.select().from(members).where(eq(members.id, memberId)).limit(1);
  if (!member) throw new Error("Member not found");

  const factors: AuditFactors = {
    verification: (member.status === "active") ? 15 : 0,
    ndaCompliance: member.ndaSigned ? 15 : 0,
    kycStatus: member.kycVerified ? 15 : 0,
    tenure: Math.min(15, member.createdAt ? Math.floor((Date.now() - new Date(member.createdAt).getTime()) / (30 * 24 * 60 * 60 * 1000)) * 3 : 0),
    tierProgression: Math.min(15, (member.memberTier || 0) * 5),
    engagement: 0,
    taskCompletion: 0,
  };

  try {
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const [activityCount] = await db
      .select({ count: count() })
      .from(memberActivity)
      .where(and(eq(memberActivity.memberId, memberId), gte(memberActivity.createdAt, thirtyDaysAgo)));
    factors.engagement = Math.min(15, (activityCount?.count || 0) * 2);
  } catch {
    factors.engagement = 0;
  }

  try {
    const [totalTasks] = await db
      .select({ count: count() })
      .from(tasks)
      .where(eq(tasks.assignedTo, memberId));
    const [completedTasks] = await db
      .select({ count: count() })
      .from(tasks)
      .where(and(eq(tasks.assignedTo, memberId), eq(tasks.status, "completed")));
    const total = totalTasks?.count || 0;
    const completed = completedTasks?.count || 0;
    factors.taskCompletion = total > 0 ? Math.round((completed / total) * 10) : 5;
  } catch {
    factors.taskCompletion = 5;
  }

  const score = Object.values(factors).reduce((a, b) => a + b, 0);

  const riskLevel: "LOW" | "MEDIUM" | "HIGH" =
    score >= 75 ? "LOW" :
    score >= 50 ? "MEDIUM" :
    "HIGH";

  const explanation = [
    `Member ${member.firstName} ${member.lastName} audit score: ${score}/100`,
    `Risk Level: ${riskLevel}`,
    `Verification: ${factors.verification}/15 (${member.status === "active" ? "Active" : "Inactive"})`,
    `NDA: ${factors.ndaCompliance}/15 (${member.ndaSigned ? "Signed" : "Not signed"})`,
    `KYC: ${factors.kycStatus}/15 (${member.kycVerified ? "Verified" : "Not verified"})`,
    `Tenure: ${factors.tenure}/15`,
    `Tier: ${factors.tierProgression}/15 (Current: L${member.memberTier || 0})`,
    `Engagement: ${factors.engagement}/15 (30-day activity)`,
    `Tasks: ${factors.taskCompletion}/10`,
  ].join("\n");

  return { score, riskLevel, factors, explanation };
}

export async function generateAndStoreAuditScore(memberId: string, triggeredBy: string = "manual"): Promise<AuditResult & { id: string }> {
  const result = await computeAuditScore(memberId);

  const [stored] = await db.insert(aiAuditScores).values({
    memberId,
    score: result.score,
    riskLevel: result.riskLevel,
    factors: result.factors,
    explanation: result.explanation,
    triggeredBy,
  }).returning();

  return { ...result, id: stored.id };
}
