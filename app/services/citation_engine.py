"""
Tax God - Citation Engine
Searches, verifies, and formats tax law citations.

Every Tax God response must be grounded in verifiable sources:
  - Internal Revenue Code (IRC) sections
  - Treasury Regulations (Treas. Reg.)
  - Revenue Rulings and Revenue Procedures
  - IRS Publications and Notices
  - Tax Court, Circuit Court, Supreme Court cases
  - State statutes and regulations

This engine:
  1. Maintains a local knowledge base of common tax provisions
  2. Searches for relevant citations given a topic/query
  3. Verifies that cited provisions actually exist
  4. Formats citations in standard legal/tax citation format
  5. Provides a confidence score for each citation
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Citation Types & Data Structures
# ---------------------------------------------------------------------------

class CitationType(str, Enum):
    IRC = "irc"                      # Internal Revenue Code
    TREASURY_REG = "treasury_reg"    # Treasury Regulations
    REV_RUL = "rev_rul"             # Revenue Rulings
    REV_PROC = "rev_proc"           # Revenue Procedures
    IRS_PUB = "irs_pub"             # IRS Publications
    IRS_NOTICE = "irs_notice"       # IRS Notices
    COURT_CASE = "court_case"       # Tax Court / Circuit / Supreme
    STATE_STATUTE = "state_statute"  # State-specific laws
    FORM_INSTRUCTION = "form_inst"   # IRS form instructions


@dataclass
class Citation:
    """A single verifiable citation."""
    citation_type: CitationType
    reference: str             # e.g., "IRC § 162(a)"
    title: str                 # short description
    summary: str               # what it says
    url: str = ""              # link to official source
    confidence: float = 1.0    # 0-1 how certain this citation is correct
    year: int = 2024           # tax year / effective year
    keywords: list[str] = field(default_factory=list)


@dataclass
class CitationResult:
    """Result of a citation search."""
    query: str
    citations: list[Citation]
    total_found: int
    search_time_ms: float = 0.0


# ---------------------------------------------------------------------------
# Tax Law Knowledge Base
# ---------------------------------------------------------------------------

# Core IRC sections organized by topic. This is the embedded knowledge base
# that enables instant citation without external API calls.

TAX_KNOWLEDGE_BASE: list[Citation] = [
    # === INDIVIDUAL INCOME TAX ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 1",
        title="Tax Imposed", summary="Imposes individual income tax on taxable income using graduated rate brackets.",
        keywords=["tax rate", "bracket", "income tax", "individual"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 61",
        title="Gross Income Defined", summary="Gross income means all income from whatever source derived, including compensation, business income, gains, rents, royalties, dividends, interest, and other items.",
        keywords=["gross income", "income", "definition", "all income"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 62",
        title="Adjusted Gross Income", summary="Defines adjusted gross income (AGI) as gross income minus above-the-line deductions including trade/business expenses, IRA contributions, student loan interest, and HSA contributions.",
        keywords=["agi", "adjusted gross income", "above the line"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 63",
        title="Taxable Income Defined", summary="Taxable income equals AGI minus the greater of itemized deductions or the standard deduction, minus the qualified business income deduction.",
        keywords=["taxable income", "standard deduction", "itemized"], year=2024,
    ),

    # === DEDUCTIONS ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 162(a)",
        title="Trade or Business Expenses", summary="Allows deduction of all ordinary and necessary expenses paid or incurred during the taxable year in carrying on any trade or business.",
        keywords=["business expense", "deduction", "ordinary", "necessary", "trade"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 163(h)",
        title="Qualified Residence Interest", summary="Allows deduction of interest on acquisition indebtedness up to $750,000 ($375,000 MFS) for qualified residences.",
        keywords=["mortgage interest", "home", "residence", "interest deduction"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 164",
        title="State and Local Taxes (SALT)", summary="Allows deduction of state/local income taxes, property taxes, subject to $10,000 annual cap ($5,000 MFS) under TCJA.",
        keywords=["salt", "state tax", "local tax", "property tax", "salt cap"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 170",
        title="Charitable Contributions", summary="Allows deduction for contributions to qualified charitable organizations, subject to AGI percentage limitations (60% cash, 30% capital gain property, 20% private foundations).",
        keywords=["charitable", "donation", "contribution", "charity", "501c3"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 199A",
        title="Qualified Business Income Deduction", summary="Allows up to 20% deduction on qualified business income from pass-through entities (sole proprietorships, partnerships, S-corps), subject to taxable income thresholds and specified service trade/business limitations.",
        keywords=["qbi", "199a", "pass-through", "qualified business income", "20%"], year=2024,
    ),

    # === HOME OFFICE ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 280A",
        title="Home Office Deduction", summary="Allows deduction for business use of home if used regularly and exclusively as principal place of business. Simplified method: $5/sq ft, max 300 sq ft ($1,500). Regular method: actual expenses pro-rated by business use percentage.",
        keywords=["home office", "work from home", "business use", "280a"], year=2024,
    ),

    # === CAPITAL GAINS ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 1(h)",
        title="Capital Gains Tax Rates", summary="Long-term capital gains (held >1 year) taxed at preferential rates: 0% (up to $47,025 single), 15% (up to $518,900 single), 20% (above). Short-term gains taxed as ordinary income.",
        keywords=["capital gains", "long-term", "short-term", "tax rate", "investment"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 1031",
        title="Like-Kind Exchange", summary="Allows deferral of gain on exchange of real property held for productive use or investment. Boot (non-like-kind property received) is taxable. Strict 45-day identification and 180-day closing deadlines.",
        keywords=["1031 exchange", "like-kind", "defer", "real estate", "swap"], year=2024,
    ),

    # === RETIREMENT ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 401(k)",
        title="401(k) Plans", summary="Employer-sponsored retirement plan. 2024 contribution limits: $23,000 (under 50), $30,500 (50+). Employer match not counted toward employee limit.",
        keywords=["401k", "retirement", "employer plan", "contribution limit"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 408",
        title="Individual Retirement Accounts (IRAs)", summary="Traditional IRA: $7,000 limit ($8,000 age 50+) for 2024. Deductibility depends on AGI and employer plan coverage. Roth IRA: same limits, income phase-out $146,000-$161,000 single.",
        keywords=["ira", "traditional ira", "roth ira", "retirement", "contribution"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 408A",
        title="Roth IRA", summary="After-tax contributions with tax-free qualified distributions. Income phase-outs: $146,000-$161,000 (single), $230,000-$240,000 (MFJ) for 2024. Backdoor Roth conversion allowed.",
        keywords=["roth", "roth ira", "backdoor roth", "conversion", "tax-free"], year=2024,
    ),

    # === SELF-EMPLOYMENT ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 1401",
        title="Self-Employment Tax", summary="Self-employment tax is 15.3% (12.4% Social Security on first $168,600 + 2.9% Medicare on all SE income). Deduct 50% of SE tax above the line.",
        keywords=["self-employment", "se tax", "social security", "medicare", "schedule se"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 162(l)",
        title="Self-Employed Health Insurance", summary="Self-employed individuals may deduct 100% of health insurance premiums as an above-the-line deduction, including coverage for spouse, dependents, and children under 27.",
        keywords=["health insurance", "self-employed", "premium", "deduction"], year=2024,
    ),

    # === DEPRECIATION ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 167/168",
        title="Depreciation (MACRS)", summary="Modified Accelerated Cost Recovery System. Business assets depreciated over: 3/5/7/10/15/20/27.5/39 years depending on class. 200% or 150% declining balance method.",
        keywords=["depreciation", "macrs", "useful life", "business asset"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 179",
        title="Section 179 Expensing", summary="Allows immediate expensing of qualifying business property up to $1,220,000 for 2024. Phase-out begins at $3,050,000 of total property placed in service.",
        keywords=["section 179", "expensing", "immediate", "deduction", "equipment"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 168(k)",
        title="Bonus Depreciation", summary="60% bonus depreciation for qualified property placed in service in 2024 (phasing down: 40% in 2025, 20% in 2026, 0% in 2027). Applies to new and used property.",
        keywords=["bonus depreciation", "168k", "first year", "accelerated"], year=2024,
    ),

    # === CREDITS ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 24",
        title="Child Tax Credit", summary="$2,000 per qualifying child under 17. Phase-out: $200,000 AGI ($400,000 MFJ). Refundable up to $1,700 (ACTC).",
        keywords=["child tax credit", "ctc", "dependent", "child"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 25A(b)",
        title="American Opportunity Tax Credit", summary="Up to $2,500/year for first 4 years of higher education. 100% of first $2,000 + 25% of next $2,000. 40% refundable ($1,000 max).",
        keywords=["aotc", "education credit", "college", "tuition"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 32",
        title="Earned Income Tax Credit", summary="Refundable credit for low-to-moderate income workers. Max credit for 2024: $7,830 (3+ children). Income limits and phase-outs apply.",
        keywords=["eitc", "earned income credit", "low income", "refundable"], year=2024,
    ),

    # === CRYPTO / DIGITAL ASSETS ===
    Citation(
        citation_type=CitationType.IRS_NOTICE, reference="IRS Notice 2014-21",
        title="Virtual Currency Guidance", summary="Virtual currency is treated as property for federal tax purposes. General property transaction principles apply. Mining income is ordinary income at FMV when received.",
        keywords=["crypto", "bitcoin", "virtual currency", "digital asset", "mining"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 1091",
        title="Wash Sale Rule", summary="Disallows loss deduction on sale of stock/securities if substantially identical stock/securities purchased within 30 days before or after. NOTE: IRS position unclear on crypto wash sales pre-2025.",
        keywords=["wash sale", "loss disallowed", "30 day", "crypto wash"], year=2024,
    ),

    # === ENTITY STRUCTURING ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 1361-1379",
        title="S Corporation Rules", summary="S-Corps pass income through to shareholders. Requirements: domestic corporation, ≤100 shareholders, one class of stock, eligible shareholders only. File Form 2553 for election.",
        keywords=["s-corp", "s corporation", "pass-through", "form 2553", "election"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 7701(a)(2)",
        title="Partnership Classification", summary="An unincorporated organization with two or more members is classified as a partnership unless it elects otherwise. Check-the-box regulations under Treas. Reg. § 301.7701-3.",
        keywords=["partnership", "llc", "check the box", "classification", "entity"], year=2024,
    ),

    # === INTERNATIONAL ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 911",
        title="Foreign Earned Income Exclusion", summary="U.S. citizens/residents living abroad may exclude up to $126,500 (2024) of foreign earned income. Must meet bona fide residence or physical presence test (330 days).",
        keywords=["foreign income", "exclusion", "expat", "abroad", "form 2555"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="31 USC § 5314 (FBAR)",
        title="FBAR - Foreign Bank Account Report", summary="U.S. persons with foreign financial accounts exceeding $10,000 aggregate at any time during the year must file FinCEN Form 114. Deadline: April 15 (auto-extension to October 15). Willful penalty: greater of $100K or 50% of account balance.",
        keywords=["fbar", "foreign account", "fincen", "overseas bank", "reporting"], year=2024,
    ),

    # === ESTATE & GIFT ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 2010",
        title="Estate Tax Exemption", summary="Federal estate tax exemption: $13,610,000 per individual for 2024 ($27,220,000 for married couples with portability). Set to revert to ~$7M in 2026 under TCJA sunset.",
        keywords=["estate tax", "exemption", "death tax", "unified credit", "portability"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 2503",
        title="Annual Gift Tax Exclusion", summary="$18,000 per recipient per year for 2024 ($36,000 for married couples gift-splitting). Gifts exceeding exclusion reduce lifetime exemption.",
        keywords=["gift tax", "annual exclusion", "gift", "form 709"], year=2024,
    ),

    # === AUDIT & PENALTIES ===
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 6662",
        title="Accuracy-Related Penalties", summary="20% penalty on underpayment due to: negligence, substantial understatement (>$5,000 or 10% of tax), or substantial valuation misstatement. Reasonable cause defense available.",
        keywords=["penalty", "accuracy", "understatement", "negligence", "6662"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRC, reference="IRC § 6651",
        title="Failure to File / Pay Penalties", summary="Failure to file: 5%/month up to 25%. Failure to pay: 0.5%/month up to 25%. Combined max: 47.5%. First-time abatement available for clean compliance history.",
        keywords=["failure to file", "failure to pay", "penalty", "late filing", "abatement"], year=2024,
    ),

    # === IRS PUBLICATIONS ===
    Citation(
        citation_type=CitationType.IRS_PUB, reference="IRS Publication 17",
        title="Your Federal Income Tax", summary="Comprehensive guide for individual taxpayers covering filing requirements, income, deductions, credits, and special situations.",
        keywords=["publication 17", "individual", "guide", "general"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRS_PUB, reference="IRS Publication 535",
        title="Business Expenses", summary="Comprehensive guide to deducting business expenses including what qualifies as ordinary and necessary, specific expense categories, and record-keeping requirements.",
        keywords=["publication 535", "business expense", "deduction", "ordinary necessary"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRS_PUB, reference="IRS Publication 544",
        title="Sales and Other Dispositions of Assets", summary="Covers gain/loss recognition on property sales, like-kind exchanges, involuntary conversions, installment sales.",
        keywords=["publication 544", "sale", "disposition", "gain", "loss", "asset"], year=2024,
    ),
    Citation(
        citation_type=CitationType.IRS_PUB, reference="IRS Publication 946",
        title="How to Depreciate Property", summary="Comprehensive guide to MACRS depreciation, Section 179, bonus depreciation, and listed property rules.",
        keywords=["publication 946", "depreciation", "macrs", "section 179", "bonus"], year=2024,
    ),
]


# ---------------------------------------------------------------------------
# Citation Search Engine
# ---------------------------------------------------------------------------

class CitationEngine:
    """
    Searches the tax knowledge base for relevant citations.
    Uses keyword matching + relevance scoring.
    """

    def __init__(self, knowledge_base: list[Citation] | None = None):
        self._kb = knowledge_base or TAX_KNOWLEDGE_BASE

    def search(
        self,
        query: str,
        max_results: int = 5,
        citation_types: list[CitationType] | None = None,
        min_confidence: float = 0.3,
    ) -> CitationResult:
        """
        Search the knowledge base for citations relevant to the query.
        """
        import time as _time
        start = _time.time()

        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored: list[tuple[float, Citation]] = []

        for cite in self._kb:
            if citation_types and cite.citation_type not in citation_types:
                continue

            score = self._relevance_score(query_lower, query_words, cite)
            if score >= min_confidence:
                scored.append((score, cite))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [c for _, c in scored[:max_results]]

        return CitationResult(
            query=query,
            citations=results,
            total_found=len(scored),
            search_time_ms=round((_time.time() - start) * 1000, 2),
        )

    def _relevance_score(
        self, query_lower: str, query_words: set[str], cite: Citation
    ) -> float:
        """Calculate relevance score (0-1) for a citation against a query."""
        score = 0.0

        # Keyword overlap
        keyword_hits = sum(1 for kw in cite.keywords if kw in query_lower)
        if cite.keywords:
            score += (keyword_hits / len(cite.keywords)) * 0.5

        # Title word overlap
        title_words = set(cite.title.lower().split())
        title_overlap = len(query_words & title_words) / max(len(title_words), 1)
        score += title_overlap * 0.25

        # Summary word overlap
        summary_words = set(cite.summary.lower().split())
        summary_overlap = len(query_words & summary_words) / max(len(summary_words), 1)
        score += summary_overlap * 0.15

        # Direct reference mention (e.g., user mentions "IRC § 162")
        if cite.reference.lower() in query_lower:
            score += 0.3

        # Exact keyword phrase match (bonus)
        for kw in cite.keywords:
            if len(kw.split()) > 1 and kw in query_lower:
                score += 0.15

        return min(1.0, score)

    def verify_citation(self, reference: str) -> Citation | None:
        """Check if a citation reference exists in the knowledge base."""
        ref_lower = reference.lower().strip()
        for cite in self._kb:
            if ref_lower in cite.reference.lower():
                return cite
        return None

    def format_citation(self, cite: Citation, style: str = "standard") -> str:
        """Format a citation for display."""
        if style == "standard":
            return f"{cite.reference} - {cite.title}"
        elif style == "full":
            return f"{cite.reference} ({cite.title}): {cite.summary}"
        elif style == "inline":
            return f"See {cite.reference}"
        return cite.reference

    def extract_citations_from_text(self, text: str) -> list[str]:
        """Extract citation references from AI-generated text."""
        patterns = [
            r"IRC\s*§\s*\d+[a-zA-Z]*(?:\([a-zA-Z0-9]+\))*",
            r"Section\s+\d+[a-zA-Z]*(?:\([a-zA-Z0-9]+\))*",
            r"Treas\.\s*Reg\.\s*§?\s*[\d.]+",
            r"Rev\.\s*Rul\.\s*\d{2,4}-\d+",
            r"Rev\.\s*Proc\.\s*\d{2,4}-\d+",
            r"IRS\s+(?:Publication|Pub\.?|Notice)\s+\d+",
            r"Form\s+\d{3,4}[A-Z]*(?:-[A-Z]+)?",
        ]

        found: list[str] = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.extend(matches)

        return list(dict.fromkeys(found))  # deduplicate, preserve order

    def enrich_response(self, response_text: str, query: str) -> dict[str, Any]:
        """
        Analyze an AI response and enrich it with verified citations.
        Returns the response text + citation metadata.
        """
        # Extract citations mentioned in the response
        mentioned = self.extract_citations_from_text(response_text)

        # Verify each extracted citation
        verified: list[dict[str, Any]] = []
        unverified: list[str] = []

        for ref in mentioned:
            cite = self.verify_citation(ref)
            if cite:
                verified.append({
                    "reference": cite.reference,
                    "title": cite.title,
                    "summary": cite.summary,
                    "type": cite.citation_type.value,
                    "verified": True,
                })
            else:
                unverified.append(ref)

        # Search for additional relevant citations the AI might have missed
        search_result = self.search(query, max_results=3)
        supplemental = []
        verified_refs = {v["reference"] for v in verified}

        for cite in search_result.citations:
            if cite.reference not in verified_refs:
                supplemental.append({
                    "reference": cite.reference,
                    "title": cite.title,
                    "summary": cite.summary,
                    "type": cite.citation_type.value,
                    "verified": True,
                    "supplemental": True,
                })

        return {
            "text": response_text,
            "verified_citations": verified,
            "unverified_citations": unverified,
            "supplemental_citations": supplemental,
            "citation_count": len(verified),
            "verification_rate": (
                len(verified) / len(mentioned) if mentioned else 1.0
            ),
        }
