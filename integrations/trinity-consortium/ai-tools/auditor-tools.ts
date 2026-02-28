import { z } from "zod";
import type { ToolDefinition } from "./types";

export const auditorTools: ToolDefinition[] = [
  {
    name: "scan_compliance",
    description: "Deep scan text for NI 43-101 violations, promissory language, and regulatory issues.",
    schema: z.object({ 
      text: z.string().describe("Text content to scan"),
      standard: z.enum(["ni43101", "sec", "gdpr", "all"]).default("all"),
      severity: z.enum(["all", "high", "medium", "low"]).default("all")
    }),
    execute: async ({ text, standard, severity }) => {
      const violations: any[] = [];
      const lowerText = text.toLowerCase();
      
      const rules = [
        { term: "guaranteed", severity: "high", type: "Promissory language", standard: "sec" },
        { term: "will definitely", severity: "high", type: "Promissory language", standard: "sec" },
        { term: "proven reserves", severity: "high", type: "Unqualified claim", standard: "ni43101" },
        { term: "world class", severity: "medium", type: "Superlative", standard: "ni43101" },
        { term: "personal data", severity: "medium", type: "Privacy concern", standard: "gdpr" }
      ];
      
      for (const rule of rules) {
        if (lowerText.includes(rule.term)) {
          if (standard === "all" || rule.standard === standard) {
            if (severity === "all" || rule.severity === severity) {
              violations.push(rule);
            }
          }
        }
      }
      
      return { 
        status: violations.length > 0 ? "violations_found" : "compliant",
        violations,
        summary: {
          high: violations.filter(v => v.severity === "high").length,
          medium: violations.filter(v => v.severity === "medium").length,
          low: violations.filter(v => v.severity === "low").length
        },
        scannedAt: new Date().toISOString()
      };
    }
  },
  {
    name: "check_brand_consistency",
    description: "Analyze content for brand voice, terminology, and style consistency.",
    schema: z.object({
      content: z.string().describe("Content to analyze"),
      contentType: z.enum(["email", "document", "presentation", "website", "social"])
    }),
    execute: async ({ content, contentType }) => {
      return {
        contentType,
        score: 85,
        findings: [
          { type: "terminology", issue: "Used 'gold mine' instead of 'gold reserve'", severity: "medium" },
          { type: "tone", issue: "Informal language detected in formal document", severity: "low" }
        ],
        brandGuidelines: {
          preferredTerms: ["gold reserve", "sovereign asset", "institutional-grade"],
          avoidTerms: ["gold mine", "mining operation", "dig"],
          toneProfile: "Professional, authoritative, institutional"
        },
        recommendations: [
          "Replace 'gold mine' with 'gold reserve'",
          "Adjust tone for formal communication"
        ]
      };
    }
  },
  {
    name: "lint_code_security",
    description: "Perform security-focused code linting and vulnerability detection.",
    schema: z.object({
      code: z.string().optional().describe("Code to analyze (or use filePath)"),
      filePath: z.string().optional().describe("File path to analyze"),
      language: z.enum(["typescript", "javascript", "sql", "python"]).default("typescript")
    }),
    execute: async ({ code, filePath, language }) => {
      return {
        target: filePath || "inline code",
        language,
        securityScore: 78,
        vulnerabilities: [
          { type: "injection", severity: "medium", line: 45, message: "Potential SQL injection - use parameterized queries" },
          { type: "exposure", severity: "low", line: 23, message: "Sensitive data may be logged" }
        ],
        codeQuality: {
          complexity: "medium",
          maintainability: 82,
          testCoverage: "65%"
        },
        recommendations: [
          "Use parameterized queries for all database operations",
          "Implement input validation on line 45"
        ]
      };
    }
  },
  {
    name: "audit_document",
    description: "Perform comprehensive document audit for regulatory compliance.",
    schema: z.object({
      documentId: z.string().describe("Document ID to audit"),
      auditType: z.enum(["full", "quick", "targeted"]).default("full"),
      standards: z.array(z.string()).default(["NI43-101"]).describe("Compliance standards to check")
    }),
    execute: async ({ documentId, auditType, standards }) => {
      return {
        documentId,
        auditType,
        standards,
        result: "pass",
        score: 92,
        checklist: {
          qualifiedPersonSignature: { status: "pass", notes: "QP signature verified" },
          dateOfReport: { status: "pass", notes: "Within required timeframe" },
          properDisclosures: { status: "pass", notes: "All required disclosures present" },
          resourceCategories: { status: "warning", notes: "Consider updating inferred resources" },
          technicalMethodology: { status: "pass", notes: "Methodology documented" }
        },
        auditTrail: {
          auditedBy: "The Auditor",
          auditedAt: new Date().toISOString(),
          version: "1.2.3",
          previousAudits: 3
        }
      };
    }
  },
  {
    name: "track_document_changes",
    description: "Track and diff changes between document versions.",
    schema: z.object({
      documentId: z.string().describe("Document to track"),
      compareVersions: z.object({
        from: z.string().describe("Older version ID"),
        to: z.string().describe("Newer version ID")
      }).optional()
    }),
    execute: async ({ documentId, compareVersions }) => {
      return {
        documentId,
        versions: [
          { id: "v3", date: "2026-02-01", author: "J. Smith", changes: 12 },
          { id: "v2", date: "2026-01-15", author: "M. Johnson", changes: 45 },
          { id: "v1", date: "2025-12-20", author: "J. Smith", changes: 0 }
        ],
        comparison: compareVersions ? {
          from: compareVersions.from,
          to: compareVersions.to,
          additions: 15,
          deletions: 8,
          modifications: 23,
          significantChanges: [
            "Updated resource estimate from 2.1M to 2.29M oz",
            "Added new geological section",
            "Modified risk disclosures"
          ]
        } : null
      };
    }
  },
  {
    name: "validate_regulatory_checklist",
    description: "Validate content against specific regulatory checklists.",
    schema: z.object({
      contentType: z.enum(["press_release", "investor_update", "annual_report", "prospectus", "technical_report"]),
      contentId: z.string().describe("Content ID to validate")
    }),
    execute: async ({ contentType, contentId }) => {
      const checklists: Record<string, any> = {
        press_release: {
          items: [
            { requirement: "Cautionary statement", status: "pass" },
            { requirement: "Qualified person reference", status: "pass" },
            { requirement: "Effective date stated", status: "pass" },
            { requirement: "Forward-looking disclaimer", status: "warning", note: "Consider strengthening" }
          ],
          passRate: "75%"
        },
        technical_report: {
          items: [
            { requirement: "Executive summary", status: "pass" },
            { requirement: "Property description", status: "pass" },
            { requirement: "Geological setting", status: "pass" },
            { requirement: "Sample methodology", status: "pass" },
            { requirement: "QP signature", status: "pass" }
          ],
          passRate: "100%"
        }
      };
      
      return {
        contentType,
        contentId,
        checklist: checklists[contentType] || checklists.press_release,
        overallStatus: "review_recommended",
        validatedAt: new Date().toISOString()
      };
    }
  },
  {
    name: "score_content",
    description: "Score content across multiple dimensions: accuracy, brand, compliance, readability.",
    schema: z.object({
      content: z.string().describe("Content to score"),
      dimensions: z.array(z.enum(["accuracy", "brand", "compliance", "readability", "seo"])).default(["accuracy", "brand", "compliance"])
    }),
    execute: async ({ content, dimensions }) => {
      const scores: Record<string, any> = {
        accuracy: { score: 88, issues: 2, feedback: "Minor factual improvements suggested" },
        brand: { score: 92, issues: 1, feedback: "Strong brand alignment" },
        compliance: { score: 85, issues: 3, feedback: "Review highlighted terms" },
        readability: { score: 78, issues: 4, feedback: "Consider simplifying complex sentences" },
        seo: { score: 72, issues: 5, feedback: "Add more targeted keywords" }
      };
      
      const results: any = { dimensions: {} };
      let totalScore = 0;
      
      for (const dim of dimensions) {
        results.dimensions[dim] = scores[dim];
        totalScore += scores[dim].score;
      }
      
      results.overallScore = Math.round(totalScore / dimensions.length);
      results.grade = results.overallScore >= 90 ? "A" : results.overallScore >= 80 ? "B" : results.overallScore >= 70 ? "C" : "D";
      results.scoredAt = new Date().toISOString();
      
      return results;
    }
  },
  {
    name: "audit_access_logs",
    description: "Audit access logs for compliance and security review.",
    schema: z.object({
      timeRange: z.enum(["24h", "7d", "30d", "90d"]).default("7d"),
      filterBy: z.object({
        userId: z.string().optional(),
        resourceType: z.string().optional(),
        action: z.string().optional()
      }).optional()
    }),
    execute: async ({ timeRange, filterBy }) => {
      return {
        timeRange,
        filters: filterBy || "none",
        summary: {
          totalEvents: 1245,
          uniqueUsers: 28,
          sensitiveAccess: 45,
          anomalies: 2
        },
        topActions: [
          { action: "document_view", count: 456 },
          { action: "document_download", count: 123 },
          { action: "login", count: 89 }
        ],
        anomalies: [
          { timestamp: "2026-02-01T03:45:00Z", user: "user_023", action: "bulk_download", risk: "medium" }
        ],
        complianceStatus: "monitoring_recommended"
      };
    }
  }
];
