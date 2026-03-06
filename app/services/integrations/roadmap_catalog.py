"""
2026 Integration Roadmap catalog.

Defines categories and tools for research, compliance, documents, planning,
and connectivity. Used by GET /api/v1/integrations/roadmap and Hermes UI.
See specs/INTEGRATION_ROADMAP_2026.md for full details.
"""

from __future__ import annotations

from typing import Any

ROADMAP_CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "research",
        "name": "Advanced Tax Research & Case Law",
        "description": "Expert-level reasoning and citation (IRC, IRS regs, court cases).",
        "tools": [
            {"id": "taxgpt", "name": "TaxGPT", "description": "AI Tax OS — structured, source-backed responses."},
            {"id": "bluej", "name": "Blue J Tax", "description": "Predictive tax research and case law analysis."},
            {"id": "lamo", "name": "Lamo", "description": "Generative AI for tough tax research with cited answers."},
            {"id": "thomsonreuters", "name": "Thomson Reuters Tax", "description": "Enterprise tax research and compliance."},
        ],
        "status": "planned",
    },
    {
        "id": "compliance",
        "name": "Indirect Tax & Global Compliance",
        "description": "Multi-state and international nexus, rates, transaction compliance.",
        "tools": [
            {"id": "chatfin", "name": "ChatFin", "description": "Transaction intelligence vs global tax rules in real time."},
            {"id": "anrok", "name": "Anrok", "description": "SaaS global sales tax/VAT and economic nexus."},
            {"id": "vertex", "name": "Vertex", "description": "Enterprise transaction tax for retail and high-volume."},
        ],
        "status": "planned",
    },
    {
        "id": "documents",
        "name": "AI Document Extraction & Practice Management",
        "description": "Auto-tag, categorize, and extract from client source documents.",
        "tools": [
            {"id": "taxdome", "name": "TaxDome AI", "description": "Auto-tag, categorize, rename client documents."},
            {"id": "1040scan", "name": "1040SCAN (SurePrep)", "description": "Scan, organize, assemble tax workpapers."},
            {"id": "holistiplan", "name": "Holistiplan", "description": "OCR and analysis of returns; planning in ~45s."},
            {"id": "rightworks", "name": "Rightworks", "description": "Practice management and workflow."},
        ],
        "status": "planned",
    },
    {
        "id": "planning",
        "name": "Strategic Planning & Forecasting",
        "description": "What-if modeling and multi-year tax and estate planning.",
        "tools": [
            {"id": "corvee", "name": "Corvee Tax Planning", "description": "Tax savings and multi-year strategy modeling."},
            {"id": "abacum", "name": "Abacum", "description": "FP&A scenario modeling; syncs to QuickBooks."},
            {"id": "fpalpha", "name": "FP Alpha", "description": "Wills, trusts, insurance — estate and tax planning."},
        ],
        "status": "planned",
    },
    {
        "id": "connectivity",
        "name": "Connectivity & Automation Layers",
        "description": "Single API layer for multiple backends (QuickBooks, CRMs, etc.).",
        "tools": [
            {"id": "mulesoft", "name": "MuleSoft Anypoint", "description": "Single API layer and security for many systems."},
            {"id": "cdata", "name": "CData Connect AI", "description": "QuickBooks (and others) to AI platforms without duplicating data."},
        ],
        "status": "planned",
    },
]


def get_roadmap_catalog() -> list[dict[str, Any]]:
    """Return roadmap categories and tools for API and UI."""
    return [dict(c) for c in ROADMAP_CATEGORIES]
