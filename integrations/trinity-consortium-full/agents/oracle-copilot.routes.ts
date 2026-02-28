import type { Express, Request, Response } from "express";
import type OpenAI from "openai";
import { z } from "zod";
import { requireAuth, requireMemberTier } from "../../auth/middleware";
import { canAccessConfidentiality } from "@shared/tier-constants";
import { costTracker } from "../../ai/cost-tracker";
import { storage } from "../../storage";
import { db } from "../../db";
import { vaultDocuments, knowledgeFiles, documentAcl } from "@shared/schema";
import { eq, desc, ilike, or, sql } from "drizzle-orm";

let _openai: OpenAI | null = null;
async function getOpenAI(): Promise<OpenAI> {
  if (!_openai) {
    const { default: OpenAIClass } = await import("openai");
    _openai = new OpenAIClass({
      apiKey: process.env.AI_INTEGRATIONS_OPENAI_API_KEY,
      baseURL: process.env.AI_INTEGRATIONS_OPENAI_BASE_URL,
    });
  }
  return _openai;
}

const chatRequestSchema = z.object({
  message: z.string().min(1).max(10000),
  conversationId: z.number().int().positive().optional(),
  documentId: z.string().optional(),
  projectId: z.string().optional(),
  action: z.enum(["chat", "summarize", "key_findings", "related", "recommend"]).default("chat"),
});

function buildDocumentContext(docs: any[]): string {
  if (docs.length === 0) {
    return "No documents found matching the query.";
  }

  return docs.map((doc, i) => {
    const parts = [
      `--- Document ${i + 1} ---`,
      `Name: ${doc.name}`,
      `ID: ${doc.id}`,
      `Category: ${doc.category || "N/A"}`,
      `File Type: ${doc.fileType || "N/A"}`,
      `Access Level: ${doc.accessLevel || "N/A"}`,
      `Confidentiality: ${doc.confidentialityLevel || "N/A"}`,
    ];
    if (doc.description) parts.push(`Description: ${doc.description}`);
    if (doc.summary) parts.push(`Summary: ${doc.summary}`);
    if (doc.tags?.length) parts.push(`Tags: ${doc.tags.join(", ")}`);
    if (doc.effectiveDate) parts.push(`Effective Date: ${doc.effectiveDate}`);
    if (doc.reportingPeriod) parts.push(`Reporting Period: ${doc.reportingPeriod}`);
    if (doc.version) parts.push(`Version: ${doc.version}`);
    return parts.join("\n");
  }).join("\n\n");
}

function buildActionInstruction(action: string): string {
  switch (action) {
    case "summarize":
      return "\n\nACTION: SUMMARIZE — Provide a comprehensive summary of the specified document. Include all key data points, dates, and figures exactly as stated. Structure with: Overview, Key Points, Important Details, and Caveats.";
    case "key_findings":
      return "\n\nACTION: KEY FINDINGS — Extract and list the most important findings from the specified document. Use bullet points. Include exact figures, dates, and data. Rank by significance.";
    case "related":
      return "\n\nACTION: RELATED DOCUMENTS — Based on the documents in context, identify and recommend related documents. Explain why each document is related (shared category, tags, subject matter). Only recommend documents that exist in the provided context.";
    case "recommend":
      return "\n\nACTION: RECOMMENDED READING — Based on the current document context, suggest which documents the user should review next. Explain the logical reading order and why each recommendation matters. Only recommend documents that exist in the provided context.";
    default:
      return "";
  }
}

const ORACLE_SYSTEM_PROMPT = `You are the ORACLE DATA-ROOM CO-PILOT for the Trinity Consortium Sovereign Portal.

ABSOLUTE RULES:
1. ONLY reference information from the VERIFIED DOCUMENTS provided below. Never fabricate data.
2. ALWAYS cite the specific document name when making any factual statement.
3. NEVER provide financial advice, investment projections, price forecasts, or return estimates.
4. NEVER mix information from different documents without clearly attributing each fact.
5. If information is not in the provided documents, say "This information is not available in the current data room documents."
6. NEVER speculate or extrapolate beyond what documents explicitly state.
7. Use exact figures, dates, and data from documents - never round or estimate.

YOUR CAPABILITIES:
- Answer questions using ONLY verified document content
- Summarize documents accurately with key findings
- Identify relevant documents for a given topic
- Cross-reference information across documents (with clear attribution)
- Help users navigate the data room efficiently
- Recommend related documents based on current viewing context

RESPONSE FORMAT:
- Be concise and professional
- Use bullet points for key findings
- Always end with "Sources: [document names]"
- Flag any uncertainties clearly

VERIFIED DOCUMENTS IN CONTEXT:
`;

export function registerOracleCopilotRoutes(app: Express): void {
  /**
   * DOMAIN: Oracle Copilot
   * Purpose: Oracle AI copilot chat with deep document grounding
   *
   * Auth:
   * - requireAuth() + requireMemberTier(1)
   * - Inline admin check for advanced features
   *
   * Middleware chain: requireAuth() → requireMemberTier(1)
   *
   * Key tables: documents, vaultDocuments, knowledgeFiles, embeddings
   *
   * Grep hooks: requireMemberTier(, /api/oracle-copilot/
   */

  app.post("/api/oracle-copilot/chat", requireAuth(), requireMemberTier(1), async (req: Request, res: Response) => {
    try {
      const parsed = chatRequestSchema.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: "Invalid request", details: parsed.error.flatten() });
      }

      const { message, documentId, projectId, action } = parsed.data;

      const userId = req.user!.sub;
      const isAdmin = (req.user!.adminTier ?? 0) >= 1;

      let allowedProjectIds: string[] = [];
      let allowedDocIds: string[] = [];
      if (!isAdmin) {
        const memberships = await storage.getProjectMembershipsForUser(userId);
        allowedProjectIds = memberships.map(m => m.projectId);
        const aclEntries = await storage.getWorkspaceDocumentAcl(userId);
        allowedDocIds = aclEntries.filter(a => a.canView).map(a => a.documentId);
      }

      const canAccessDoc = (doc: { id: string; projectId?: string | null }) =>
        isAdmin ||
        allowedDocIds.includes(doc.id) ||
        (doc.projectId && allowedProjectIds.includes(doc.projectId));

      let contextDocs: any[] = [];

      if (documentId) {
        const docs = await db
          .select({
            id: vaultDocuments.id,
            name: vaultDocuments.name,
            description: vaultDocuments.description,
            summary: vaultDocuments.summary,
            tags: vaultDocuments.tags,
            category: vaultDocuments.category,
            accessLevel: vaultDocuments.accessLevel,
            fileType: vaultDocuments.fileType,
            confidentialityLevel: vaultDocuments.confidentialityLevel,
            effectiveDate: vaultDocuments.effectiveDate,
            reportingPeriod: vaultDocuments.reportingPeriod,
            version: vaultDocuments.version,
            projectId: vaultDocuments.projectId,
          })
          .from(vaultDocuments)
          .where(eq(vaultDocuments.id, documentId))
          .limit(1);
        if (docs.length > 0 && !canAccessDoc(docs[0])) {
          return res.status(403).json({ error: "Access denied to this document" });
        }
        contextDocs = docs;
      } else if (projectId) {
        if (!isAdmin && !allowedProjectIds.includes(projectId)) {
          return res.status(403).json({ error: "Access denied to this project" });
        }
        const docs = await db
          .select({
            id: vaultDocuments.id,
            name: vaultDocuments.name,
            description: vaultDocuments.description,
            summary: vaultDocuments.summary,
            tags: vaultDocuments.tags,
            category: vaultDocuments.category,
            accessLevel: vaultDocuments.accessLevel,
            fileType: vaultDocuments.fileType,
            confidentialityLevel: vaultDocuments.confidentialityLevel,
            effectiveDate: vaultDocuments.effectiveDate,
            reportingPeriod: vaultDocuments.reportingPeriod,
            version: vaultDocuments.version,
            projectId: vaultDocuments.projectId,
          })
          .from(vaultDocuments)
          .where(eq(vaultDocuments.projectId, projectId))
          .orderBy(desc(vaultDocuments.updatedAt))
          .limit(10);
        contextDocs = docs;
      } else {
        const queryWords = message.toLowerCase().split(/\s+/).filter(w => w.length > 2);
        if (queryWords.length > 0) {
          const searchConditions = queryWords.map(word => {
            const pattern = `%${word}%`;
            return or(
              ilike(vaultDocuments.name, pattern),
              ilike(vaultDocuments.description, pattern),
              ilike(vaultDocuments.summary, pattern),
              sql`array_to_string(${vaultDocuments.tags}, ' ') ILIKE ${pattern}`
            );
          });

          const docs = await db
            .select({
              id: vaultDocuments.id,
              name: vaultDocuments.name,
              description: vaultDocuments.description,
              summary: vaultDocuments.summary,
              tags: vaultDocuments.tags,
              category: vaultDocuments.category,
              accessLevel: vaultDocuments.accessLevel,
              fileType: vaultDocuments.fileType,
              confidentialityLevel: vaultDocuments.confidentialityLevel,
              effectiveDate: vaultDocuments.effectiveDate,
              reportingPeriod: vaultDocuments.reportingPeriod,
              version: vaultDocuments.version,
              projectId: vaultDocuments.projectId,
            })
            .from(vaultDocuments)
            .where(or(...searchConditions))
            .orderBy(desc(vaultDocuments.updatedAt))
            .limit(10);
          contextDocs = docs.filter(canAccessDoc);
        } else {
          const docs = await db
            .select({
              id: vaultDocuments.id,
              name: vaultDocuments.name,
              description: vaultDocuments.description,
              summary: vaultDocuments.summary,
              tags: vaultDocuments.tags,
              category: vaultDocuments.category,
              accessLevel: vaultDocuments.accessLevel,
              fileType: vaultDocuments.fileType,
              confidentialityLevel: vaultDocuments.confidentialityLevel,
              effectiveDate: vaultDocuments.effectiveDate,
              reportingPeriod: vaultDocuments.reportingPeriod,
              version: vaultDocuments.version,
              projectId: vaultDocuments.projectId,
            })
            .from(vaultDocuments)
            .orderBy(desc(vaultDocuments.updatedAt))
            .limit(10);
          contextDocs = docs.filter(canAccessDoc);
        }
      }

      const userMemberTier = req.user!.memberTier ?? 0;
      const userAdminTier = req.user!.adminTier ?? 0;
      contextDocs = contextDocs.filter(doc =>
        canAccessConfidentiality(userMemberTier, userAdminTier, doc.confidentialityLevel || "PUBLIC")
      );

      const documentContext = buildDocumentContext(contextDocs);
      const actionInstruction = buildActionInstruction(action);
      const systemPrompt = ORACLE_SYSTEM_PROMPT + documentContext + actionInstruction;

      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");

      const budgetCheck = costTracker.isWithinBudget(0.005);
      if (!budgetCheck.allowed) {
        res.write(`data: ${JSON.stringify({ error: "Budget limit reached", reason: budgetCheck.reason })}\n\n`);
        res.end();
        return;
      }

      const openai = await getOpenAI();
      const stream = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: message },
        ],
        stream: true,
        max_completion_tokens: 2048,
      });

      let fullResponse = "";

      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content || "";
        if (content) {
          fullResponse += content;
          res.write(`data: ${JSON.stringify({ content })}\n\n`);
        }
      }

      costTracker.recordSpend({
        source: "oracle_copilot" as any,
        model: "gpt-4o-mini",
        estimatedCostUSD: 0.003,
        iterations: 1,
      });

      const sourceNames = contextDocs.map(d => d.name);
      const sourceIds = contextDocs.map(d => d.id);

      res.write(`data: ${JSON.stringify({ done: true, sources: sourceNames, documentIds: sourceIds })}\n\n`);
      res.end();
    } catch (error) {
      console.error("[Oracle Copilot] Chat error:", error);
      if (res.headersSent) {
        res.write(`data: ${JSON.stringify({ error: "Failed to process message" })}\n\n`);
        res.end();
      } else {
        res.status(500).json({ error: "Failed to process message" });
      }
    }
  });

  app.get("/api/oracle-copilot/quick-actions", requireAuth(), requireMemberTier(1), (_req: Request, res: Response) => {
    res.json({
      actions: [
        { id: "summarize", label: "Summarize Document", icon: "file-text" },
        { id: "key_findings", label: "Key Findings", icon: "search" },
        { id: "related", label: "Related Documents", icon: "link" },
        { id: "recommend", label: "Recommended Reading", icon: "sparkles" },
      ],
    });
  });
}
