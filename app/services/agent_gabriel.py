"""
Tax God - Agent Gabriel (Audit & Review System)
Named "Gabriel" -- the guardian angel that reviews every return.

Agent Gabriel performs automated audits on tax returns to:
  1. Detect errors (math, missing forms, inconsistencies)
  2. Flag audit risk positions (red/yellow/green)
  3. Identify missed savings opportunities
  4. Score overall return quality
  5. Generate actionable recommendations

This runs BEFORE any return is filed and after every significant change.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.services.ai_service import AIOrchestrator, AgentRole
from app.services.citation_engine import CitationEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Flag System
# ---------------------------------------------------------------------------

class FlagSeverity(str, Enum):
    RED = "red"            # Critical issue, DO NOT file until resolved
    YELLOW = "yellow"      # Warning, should review before filing
    GREEN = "green"        # Opportunity or positive finding
    INFO = "info"          # Informational note


class FlagCategory(str, Enum):
    MATH_ERROR = "math_error"
    MISSING_FORM = "missing_form"
    MISSING_INCOME = "missing_income"
    INCONSISTENCY = "inconsistency"
    AUDIT_RISK = "audit_risk"
    PENALTY_RISK = "penalty_risk"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    COMPLIANCE = "compliance"
    DOCUMENTATION = "documentation"
    DEADLINE = "deadline"


@dataclass
class AuditFlag:
    """A single finding from Agent Gabriel's review."""
    severity: FlagSeverity
    category: FlagCategory
    title: str
    description: str
    recommendation: str
    form_reference: str = ""       # e.g., "Form 1040, Line 7"
    irc_reference: str = ""        # e.g., "IRC § 162(a)"
    estimated_impact_usd: float = 0.0
    confidence: float = 0.9


@dataclass
class AuditReport:
    """Complete audit report from Agent Gabriel."""
    report_id: str
    client_id: str
    tax_year: int
    form_type: str                 # "1040", "1120", "1065", etc.
    flags: list[AuditFlag] = field(default_factory=list)
    overall_score: float = 0.0     # 0-100 quality score
    risk_level: str = "low"        # "low", "medium", "high", "critical"
    total_savings_found: float = 0.0
    total_errors_found: int = 0
    ai_summary: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_by_human: bool = False

    @property
    def red_flags(self) -> list[AuditFlag]:
        return [f for f in self.flags if f.severity == FlagSeverity.RED]

    @property
    def yellow_flags(self) -> list[AuditFlag]:
        return [f for f in self.flags if f.severity == FlagSeverity.YELLOW]

    @property
    def green_flags(self) -> list[AuditFlag]:
        return [f for f in self.flags if f.severity == FlagSeverity.GREEN]


# ---------------------------------------------------------------------------
# Built-in Audit Rules (Rule Engine)
# ---------------------------------------------------------------------------

@dataclass
class AuditRule:
    """A single deterministic audit check."""
    rule_id: str
    title: str
    category: FlagCategory
    check_fn_name: str  # name of the check method
    description: str


# Individual 1040 audit rules
INDIVIDUAL_RULES: list[AuditRule] = [
    AuditRule("IND-001", "W-2/1099 Income Reconciliation", FlagCategory.MISSING_INCOME,
              "check_income_reconciliation", "Verify reported income matches W-2s and 1099s"),
    AuditRule("IND-002", "Standard vs Itemized Deduction", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_deduction_optimization", "Compare standard deduction to itemized to ensure optimal choice"),
    AuditRule("IND-003", "Estimated Tax Payments", FlagCategory.PENALTY_RISK,
              "check_estimated_payments", "Check if underpayment penalty applies (safe harbor rules)"),
    AuditRule("IND-004", "HSA Contribution Limits", FlagCategory.COMPLIANCE,
              "check_hsa_limits", "Verify HSA contributions don't exceed annual limits"),
    AuditRule("IND-005", "Retirement Contribution Limits", FlagCategory.COMPLIANCE,
              "check_retirement_limits", "Verify 401k/IRA contributions within limits"),
    AuditRule("IND-006", "Child Tax Credit Eligibility", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_child_credit", "Verify all qualifying children claimed"),
    AuditRule("IND-007", "EITC Eligibility", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_eitc", "Check if client qualifies for Earned Income Tax Credit"),
    AuditRule("IND-008", "QBI Deduction (199A)", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_qbi_deduction", "Verify Section 199A deduction claimed if eligible"),
    AuditRule("IND-009", "Home Office Deduction", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_home_office", "Check if home office deduction applies (regular & exclusive use)"),
    AuditRule("IND-010", "Capital Loss Carryforward", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_loss_carryforward", "Verify prior year capital loss carryforwards applied"),
    AuditRule("IND-011", "SALT Deduction Cap", FlagCategory.COMPLIANCE,
              "check_salt_cap", "Ensure SALT deduction doesn't exceed $10,000 cap"),
    AuditRule("IND-012", "Charitable Contribution Limits", FlagCategory.COMPLIANCE,
              "check_charitable_limits", "Verify charitable deductions within AGI percentage limits"),
    AuditRule("IND-013", "Self-Employment Tax", FlagCategory.MATH_ERROR,
              "check_se_tax", "Verify SE tax calculation (15.3% with proper deductions)"),
    AuditRule("IND-014", "AMT Exposure", FlagCategory.AUDIT_RISK,
              "check_amt", "Check for Alternative Minimum Tax exposure"),
    AuditRule("IND-015", "FBAR/FATCA Reporting", FlagCategory.COMPLIANCE,
              "check_foreign_reporting", "Check if foreign account reporting requirements triggered"),
    AuditRule("IND-016", "Crypto Transaction Reporting", FlagCategory.COMPLIANCE,
              "check_crypto_reporting", "Verify digital asset question answered and transactions reported"),
    AuditRule("IND-017", "Education Credits", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_education_credits", "Check eligibility for AOTC or LLC"),
    AuditRule("IND-018", "Energy Credits", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_energy_credits", "Check for residential clean energy credit eligibility"),
    AuditRule("IND-019", "Filing Status Optimization", FlagCategory.SAVINGS_OPPORTUNITY,
              "check_filing_status", "Verify optimal filing status selected"),
    AuditRule("IND-020", "Multi-State Filing Required", FlagCategory.MISSING_FORM,
              "check_multi_state", "Check if income earned in other states requires additional filings"),
]


# ---------------------------------------------------------------------------
# Agent Gabriel Service
# ---------------------------------------------------------------------------

class AgentGabriel:
    """
    The Tax God audit and review agent.

    Performs two types of analysis:
      1. Rule-Based: Deterministic checks against known audit rules
      2. AI-Powered: LLM-based analysis for nuanced issues
    """

    def __init__(
        self,
        ai_orchestrator: AIOrchestrator | None = None,
        citation_engine: CitationEngine | None = None,
    ):
        self.ai = ai_orchestrator
        self.citations = citation_engine or CitationEngine()

    async def audit_individual_return(
        self,
        client_id: str,
        tax_year: int,
        return_data: dict[str, Any],
    ) -> AuditReport:
        """
        Run a comprehensive audit on an individual tax return (Form 1040).
        """
        import uuid

        report = AuditReport(
            report_id=str(uuid.uuid4()),
            client_id=client_id,
            tax_year=tax_year,
            form_type="1040",
        )

        # Phase 1: Run deterministic rule checks
        rule_flags = self._run_rule_checks(return_data, INDIVIDUAL_RULES)
        report.flags.extend(rule_flags)

        # Phase 2: AI-powered deep analysis (if orchestrator available)
        if self.ai:
            ai_flags = await self._run_ai_analysis(client_id, tax_year, return_data)
            report.flags.extend(ai_flags)

        # Calculate summary metrics
        report.total_errors_found = len(report.red_flags) + len(report.yellow_flags)
        report.total_savings_found = sum(
            f.estimated_impact_usd for f in report.green_flags
        )
        report.overall_score = self._calculate_score(report)
        report.risk_level = self._assess_risk_level(report)
        report.ai_summary = self._generate_summary(report)

        return report

    # -- Rule Engine ----------------------------------------------------------

    def _run_rule_checks(
        self, return_data: dict[str, Any], rules: list[AuditRule]
    ) -> list[AuditFlag]:
        """Execute all deterministic audit rules against return data."""
        flags: list[AuditFlag] = []

        for rule in rules:
            check_method = getattr(self, f"_rule_{rule.check_fn_name}", None)
            if check_method:
                try:
                    result = check_method(return_data)
                    if result:
                        flags.append(result)
                except Exception as exc:
                    logger.warning("Rule %s failed: %s", rule.rule_id, exc)

        return flags

    # -- Individual Rule Implementations --------------------------------------

    def _rule_check_income_reconciliation(self, data: dict) -> AuditFlag | None:
        w2_total = sum(w.get("wages", 0) for w in data.get("w2s", []))
        reported_wages = data.get("wages_reported", 0)

        if w2_total and reported_wages and abs(w2_total - reported_wages) > 1:
            diff = w2_total - reported_wages
            return AuditFlag(
                severity=FlagSeverity.RED,
                category=FlagCategory.MISSING_INCOME,
                title="W-2 Income Mismatch",
                description=f"W-2 total (${w2_total:,.2f}) differs from reported wages (${reported_wages:,.2f}) by ${abs(diff):,.2f}.",
                recommendation="Reconcile all W-2s with Line 1 of Form 1040. IRS matching programs will flag this discrepancy.",
                form_reference="Form 1040, Line 1",
                irc_reference="IRC § 61",
                estimated_impact_usd=abs(diff) * 0.25,
            )
        return None

    def _rule_check_deduction_optimization(self, data: dict) -> AuditFlag | None:
        filing_status = data.get("filing_status", "single")
        standard_amounts = {
            "single": 14600, "mfj": 29200, "mfs": 14600,
            "hoh": 21900, "widow": 29200,
        }
        standard = standard_amounts.get(filing_status, 14600)
        itemized = data.get("total_itemized", 0)
        used = data.get("deduction_type", "standard")

        if itemized > standard and used == "standard":
            savings = (itemized - standard) * 0.22
            return AuditFlag(
                severity=FlagSeverity.GREEN,
                category=FlagCategory.SAVINGS_OPPORTUNITY,
                title="Itemize for Greater Deduction",
                description=f"Itemized deductions (${itemized:,.0f}) exceed standard deduction (${standard:,.0f}). Switch to itemized.",
                recommendation=f"Switch to itemized deductions on Schedule A. Estimated tax savings: ${savings:,.0f}.",
                form_reference="Form 1040, Line 12; Schedule A",
                irc_reference="IRC § 63",
                estimated_impact_usd=savings,
            )
        elif itemized and itemized < standard and used == "itemized":
            savings = (standard - itemized) * 0.22
            return AuditFlag(
                severity=FlagSeverity.GREEN,
                category=FlagCategory.SAVINGS_OPPORTUNITY,
                title="Standard Deduction is Higher",
                description=f"Standard deduction (${standard:,.0f}) exceeds itemized (${itemized:,.0f}). Switch to standard.",
                recommendation=f"Switch to standard deduction. Estimated tax savings: ${savings:,.0f}.",
                form_reference="Form 1040, Line 12",
                irc_reference="IRC § 63",
                estimated_impact_usd=savings,
            )
        return None

    def _rule_check_estimated_payments(self, data: dict) -> AuditFlag | None:
        withholding = data.get("total_withholding", 0)
        tax_liability = data.get("total_tax", 0)
        estimated_paid = data.get("estimated_payments", 0)
        prior_year_tax = data.get("prior_year_tax", 0)

        total_paid = withholding + estimated_paid
        if tax_liability <= 0 or total_paid <= 0:
            return None

        safe_harbor_100 = prior_year_tax if prior_year_tax else tax_liability
        safe_harbor_110 = safe_harbor_100 * 1.10
        agi = data.get("agi", 0)

        threshold = safe_harbor_110 if agi > 150_000 else safe_harbor_100
        if total_paid < min(tax_liability * 0.90, threshold):
            shortfall = tax_liability - total_paid
            return AuditFlag(
                severity=FlagSeverity.YELLOW,
                category=FlagCategory.PENALTY_RISK,
                title="Estimated Tax Underpayment Risk",
                description=f"Total payments (${total_paid:,.0f}) may fall short of safe harbor. Potential underpayment: ${shortfall:,.0f}.",
                recommendation="Review IRC § 6654 safe harbor rules. Consider increasing Q4 estimated payment or withholding.",
                form_reference="Form 2210",
                irc_reference="IRC § 6654",
                estimated_impact_usd=shortfall * 0.08,
            )
        return None

    def _rule_check_hsa_limits(self, data: dict) -> AuditFlag | None:
        hsa_contribution = data.get("hsa_contribution", 0)
        if not hsa_contribution:
            return None

        coverage = data.get("hsa_coverage", "self")
        limits = {"self": 4150, "family": 8300}
        catch_up = 1000 if data.get("age", 0) >= 55 else 0
        limit = limits.get(coverage, 4150) + catch_up

        if hsa_contribution > limit:
            excess = hsa_contribution - limit
            return AuditFlag(
                severity=FlagSeverity.RED,
                category=FlagCategory.COMPLIANCE,
                title="HSA Excess Contribution",
                description=f"HSA contribution (${hsa_contribution:,.0f}) exceeds {coverage}-only limit (${limit:,.0f}) by ${excess:,.0f}.",
                recommendation=f"Withdraw excess ${excess:,.0f} before tax filing deadline to avoid 6% excise tax (IRC § 4973).",
                form_reference="Form 8889",
                irc_reference="IRC § 223(b)",
                estimated_impact_usd=excess * 0.06,
            )
        return None

    def _rule_check_retirement_limits(self, data: dict) -> AuditFlag | None:
        k401_contribution = data.get("401k_contribution", 0)
        age = data.get("age", 30)
        limit = 30500 if age >= 50 else 23000

        if k401_contribution > limit:
            excess = k401_contribution - limit
            return AuditFlag(
                severity=FlagSeverity.RED,
                category=FlagCategory.COMPLIANCE,
                title="401(k) Excess Contribution",
                description=f"401(k) contribution (${k401_contribution:,.0f}) exceeds limit (${limit:,.0f}) by ${excess:,.0f}.",
                recommendation=f"Contact plan administrator to return excess ${excess:,.0f} before April 15.",
                form_reference="Form 1040, Line 1",
                irc_reference="IRC § 402(g)",
                estimated_impact_usd=excess * 0.30,
            )
        return None

    def _rule_check_salt_cap(self, data: dict) -> AuditFlag | None:
        salt_deducted = data.get("salt_deduction", 0)
        filing_status = data.get("filing_status", "single")
        cap = 5000 if filing_status == "mfs" else 10000

        if salt_deducted > cap:
            return AuditFlag(
                severity=FlagSeverity.RED,
                category=FlagCategory.COMPLIANCE,
                title="SALT Deduction Exceeds Cap",
                description=f"SALT deduction (${salt_deducted:,.0f}) exceeds ${cap:,.0f} cap under TCJA.",
                recommendation=f"Reduce Schedule A SALT to ${cap:,.0f}. Consider SALT cap workarounds (PTE election if applicable).",
                form_reference="Schedule A, Line 5d",
                irc_reference="IRC § 164(b)(6)",
            )
        return None

    def _rule_check_qbi_deduction(self, data: dict) -> AuditFlag | None:
        has_business_income = data.get("schedule_c_income", 0) > 0 or data.get("k1_income", 0) > 0
        qbi_claimed = data.get("qbi_deduction", 0)

        if has_business_income and qbi_claimed == 0:
            biz_income = data.get("schedule_c_income", 0) + data.get("k1_income", 0)
            potential = biz_income * 0.20
            return AuditFlag(
                severity=FlagSeverity.GREEN,
                category=FlagCategory.SAVINGS_OPPORTUNITY,
                title="QBI Deduction Not Claimed",
                description=f"Business income detected but no Section 199A deduction claimed. Potential deduction: ${potential:,.0f}.",
                recommendation="Calculate Section 199A QBI deduction. Potential tax savings significant for pass-through income.",
                form_reference="Form 8995 or 8995-A",
                irc_reference="IRC § 199A",
                estimated_impact_usd=potential * 0.24,
            )
        return None

    def _rule_check_home_office(self, data: dict) -> AuditFlag | None:
        has_schedule_c = data.get("schedule_c_income", 0) > 0
        home_office_claimed = data.get("home_office_deduction", 0) > 0
        works_from_home = data.get("works_from_home", False)

        if has_schedule_c and works_from_home and not home_office_claimed:
            return AuditFlag(
                severity=FlagSeverity.GREEN,
                category=FlagCategory.SAVINGS_OPPORTUNITY,
                title="Home Office Deduction Available",
                description="Self-employed and works from home but no home office deduction claimed.",
                recommendation="Claim home office deduction (simplified: $5/sq ft, max $1,500; or actual expenses method).",
                form_reference="Form 8829",
                irc_reference="IRC § 280A",
                estimated_impact_usd=1500 * 0.30,
            )
        return None

    def _rule_check_crypto_reporting(self, data: dict) -> AuditFlag | None:
        has_crypto = data.get("has_crypto_transactions", False)
        crypto_reported = data.get("crypto_gains_reported", False)
        digital_asset_question = data.get("digital_asset_question_answered", None)

        if has_crypto and not crypto_reported:
            return AuditFlag(
                severity=FlagSeverity.RED,
                category=FlagCategory.COMPLIANCE,
                title="Unreported Crypto Transactions",
                description="Digital asset transactions detected but not reported on Form 8949/Schedule D.",
                recommendation="Report all crypto dispositions on Form 8949. Answer 'Yes' to digital asset question on Form 1040.",
                form_reference="Form 1040 (digital asset question); Form 8949",
                irc_reference="IRS Notice 2014-21",
            )
        if digital_asset_question is None and has_crypto:
            return AuditFlag(
                severity=FlagSeverity.YELLOW,
                category=FlagCategory.COMPLIANCE,
                title="Digital Asset Question Unanswered",
                description="Form 1040 digital asset question must be answered by all filers.",
                recommendation="Answer 'Yes' if any digital assets were received, sold, or exchanged during the year.",
                form_reference="Form 1040, Page 1",
            )
        return None

    # Stub implementations for remaining rules
    def _rule_check_child_credit(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_eitc(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_loss_carryforward(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_charitable_limits(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_se_tax(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_amt(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_foreign_reporting(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_education_credits(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_energy_credits(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_filing_status(self, data: dict) -> AuditFlag | None: return None
    def _rule_check_multi_state(self, data: dict) -> AuditFlag | None: return None

    # -- AI-Powered Analysis --------------------------------------------------

    async def _run_ai_analysis(
        self, client_id: str, tax_year: int, return_data: dict
    ) -> list[AuditFlag]:
        """Use AI to find nuanced issues rule engine can't detect."""
        if not self.ai:
            return []

        prompt = (
            f"You are Agent Gabriel, an expert tax return auditor. "
            f"Review this tax year {tax_year} return data and identify:\n"
            f"1. Any errors or inconsistencies\n"
            f"2. Audit risk positions (IRS flags)\n"
            f"3. Missed savings opportunities\n"
            f"4. Missing forms or schedules\n\n"
            f"Return data summary:\n{_summarize_return(return_data)}\n\n"
            f"For each finding, provide: severity (red/yellow/green), category, description, "
            f"specific IRC citation, and recommended action."
        )

        try:
            response = await self.ai.query(
                query=prompt,
                client_id=client_id,
                task_type="audit_review",
            )
            # The AI response is natural language; in production this would be
            # parsed into structured AuditFlags. For now return as single info flag.
            if response.content:
                return [AuditFlag(
                    severity=FlagSeverity.INFO,
                    category=FlagCategory.COMPLIANCE,
                    title="AI Deep Analysis",
                    description=response.content[:2000],
                    recommendation="Review the AI analysis above for additional insights.",
                    confidence=response.confidence,
                )]
        except Exception as exc:
            logger.warning("AI audit analysis failed: %s", exc)

        return []

    # -- Scoring & Summary ----------------------------------------------------

    def _calculate_score(self, report: AuditReport) -> float:
        """Calculate 0-100 quality score for the return."""
        score = 100.0
        score -= len(report.red_flags) * 15
        score -= len(report.yellow_flags) * 5
        score += min(len(report.green_flags) * 2, 10)
        return max(0, min(100, round(score, 1)))

    def _assess_risk_level(self, report: AuditReport) -> str:
        if len(report.red_flags) >= 3:
            return "critical"
        elif len(report.red_flags) >= 1:
            return "high"
        elif len(report.yellow_flags) >= 3:
            return "medium"
        return "low"

    def _generate_summary(self, report: AuditReport) -> str:
        parts = [f"Agent Gabriel Review - Tax Year {report.tax_year} ({report.form_type})"]
        parts.append(f"Score: {report.overall_score}/100 | Risk: {report.risk_level.upper()}")
        parts.append(f"Red: {len(report.red_flags)} | Yellow: {len(report.yellow_flags)} | Green: {len(report.green_flags)}")

        if report.total_savings_found > 0:
            parts.append(f"Potential savings identified: ${report.total_savings_found:,.0f}")
        if report.red_flags:
            parts.append("CRITICAL ISSUES requiring resolution before filing:")
            for f in report.red_flags:
                parts.append(f"  - {f.title}: {f.description}")

        return "\n".join(parts)


def _summarize_return(data: dict) -> str:
    """Create a text summary of return data for AI analysis."""
    lines = []
    key_fields = [
        "filing_status", "agi", "total_income", "wages_reported",
        "schedule_c_income", "rental_income", "capital_gains",
        "total_itemized", "deduction_type", "total_tax",
        "total_withholding", "estimated_payments", "refund_or_due",
    ]
    for k in key_fields:
        if k in data:
            lines.append(f"  {k}: {data[k]}")
    return "\n".join(lines) if lines else "No return data provided"
