"""
Tax God - AI Document Generation Service
Generates professional tax/accounting documents from templates, optionally polished by AI.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

TEMPLATES: dict[str, dict[str, str]] = {
    "engagement_letter": {
        "description": "Professional engagement letter for new tax clients",
        "template": (
            "Dear {client_name},\n\n"
            "This letter confirms our engagement to provide {service_type} services for the tax year {tax_year}.\n\n"
            "Scope: {scope}\n"
            "Fee: {fee}\n\n"
            "Please sign and return this letter to confirm your agreement.\n\n"
            "Sincerely,\n{firm_name}"
        ),
    },
    "w9_request": {
        "description": "Request for W-9 form from client or vendor",
        "template": (
            "Dear {client_name},\n\n"
            "We require a completed W-9 form for our records. "
            "Please provide your taxpayer identification number and certification at your earliest convenience.\n\n"
            "Company: {company}\n"
            "Filing Type: {filing_type}\n\n"
            "Thank you,\n{firm_name}"
        ),
    },
    "collection_notice": {
        "description": "Past-due invoice collection notice",
        "template": (
            "Dear {client_name},\n\n"
            "This is a reminder that invoice #{invoice_number} for ${amount_due} is past due as of {due_date}.\n\n"
            "Please remit payment immediately to avoid further action.\n\n"
            "Regards,\n{firm_name}"
        ),
    },
    "1099_summary": {
        "description": "Annual 1099 income summary for client",
        "template": (
            "1099 Income Summary - Tax Year {tax_year}\n"
            "Client: {client_name}\n"
            "Tax ID: {tax_id}\n\n"
            "Total 1099 Income: ${total_income}\n"
            "Number of 1099s: {num_forms}\n\n"
            "Details:\n{details}"
        ),
    },
    "tax_organizer": {
        "description": "Annual tax organizer checklist for clients",
        "template": (
            "Tax Organizer - {tax_year}\n"
            "Client: {client_name}\n\n"
            "Please gather the following documents:\n"
            "- W-2 forms from all employers\n"
            "- 1099 forms (interest, dividends, freelance income)\n"
            "- Mortgage interest statement (1098)\n"
            "- Property tax records\n"
            "- Charitable donation receipts\n"
            "- Business expense records\n"
            "- Health insurance forms (1095-A/B/C)\n\n"
            "Filing Type: {filing_type}\n"
            "Additional notes: {notes}"
        ),
    },
    "client_welcome": {
        "description": "Welcome letter for new clients",
        "template": (
            "Welcome to {firm_name}, {client_name}!\n\n"
            "We are thrilled to have you as a client. Here's what to expect:\n\n"
            "1. Initial consultation to review your tax situation\n"
            "2. Document collection via our secure portal\n"
            "3. Preparation and review of your returns\n"
            "4. Filing and year-round support\n\n"
            "Your dedicated contact: {contact_name}\nEmail: {contact_email}\n\n"
            "We look forward to working with you!"
        ),
    },
    "invoice_reminder": {
        "description": "Friendly payment reminder for upcoming/recent invoices",
        "template": (
            "Dear {client_name},\n\n"
            "This is a friendly reminder that invoice #{invoice_number} for ${amount_due} "
            "is due on {due_date}.\n\n"
            "Please let us know if you have any questions.\n\n"
            "Thank you,\n{firm_name}"
        ),
    },
}


def _fill_template(template: str, context_data: dict[str, Any]) -> str:
    """Fill template placeholders, using empty string for missing keys."""
    import re

    def _replacer(m):
        return str(context_data.get(m.group(1), ""))

    return re.sub(r"\{(\w+)\}", _replacer, template)


async def generate_document(
    doc_type: str,
    context_data: dict[str, Any],
    user_instructions: str | None = None,
) -> dict[str, Any]:
    """Generate a document from template, optionally enhanced by AI."""
    if doc_type not in TEMPLATES:
        raise ValueError(f"Unknown doc_type: {doc_type}. Available: {list(TEMPLATES.keys())}")

    template_info = TEMPLATES[doc_type]
    content = _fill_template(template_info["template"], context_data)

    # If OpenAI key is set, enhance with AI
    if os.environ.get("OPENAI_API_KEY"):
        try:
            import openai

            client = openai.AsyncOpenAI()
            prompt = (
                f"Polish this professional document. Keep all facts intact, improve tone and formatting.\n\n"
                f"Document:\n{content}"
            )
            if user_instructions:
                prompt += f"\n\nAdditional instructions: {user_instructions}"

            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
            )
            content = resp.choices[0].message.content or content
        except Exception:
            pass  # Fall back to template version

    return {
        "content": content,
        "metadata": {
            "doc_type": doc_type,
            "generated_at": datetime.now(UTC).isoformat(),
            "ai_enhanced": bool(os.environ.get("OPENAI_API_KEY")),
            "template_used": doc_type,
        },
    }
