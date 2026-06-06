"""Tax God - PDF/HTML Generation Service (pure Python, no external deps)."""

from __future__ import annotations

from datetime import datetime


async def generate_invoice_pdf(invoice, client, business) -> bytes:
    """Generate a printable HTML invoice."""
    client_name = getattr(client, "name", "N/A") if client else "N/A"
    client_email = getattr(client, "email", "") if client else ""
    biz_name = getattr(business, "name", "Tax God") if business else "Tax God"
    biz_address = getattr(business, "address", "") if business else ""

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Invoice {invoice.invoice_number}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:800px;margin:0 auto;padding:40px}}
table{{width:100%;border-collapse:collapse;margin:20px 0}}th,td{{padding:8px 12px;border-bottom:1px solid #ddd;text-align:left}}
th{{background:#f5f5f5}}.header{{display:flex;justify-content:space-between;margin-bottom:30px}}
.total{{font-size:1.4em;font-weight:bold;text-align:right;margin-top:20px}}</style></head><body>
<div class="header"><div><h1>{biz_name}</h1><p>{biz_address}</p></div>
<div><h2>INVOICE</h2><p>#{invoice.invoice_number}</p><p>Status: {invoice.status}</p></div></div>
<table><tr><th>Bill To</th><th>Date</th><th>Due Date</th></tr>
<tr><td>{client_name}<br>{client_email}</td><td>{invoice.created_at.strftime("%Y-%m-%d") if invoice.created_at else ""}</td>
<td>{invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "N/A"}</td></tr></table>
<table><tr><th>Description</th><th>Amount</th></tr>
<tr><td>{invoice.items or "Services rendered"}</td><td>${invoice.amount:,.2f}</td></tr>
<tr><td>Tax</td><td>${invoice.tax_amount:,.2f}</td></tr></table>
<div class="total">Total: ${invoice.amount + invoice.tax_amount:,.2f} {invoice.currency}</div>
{f"<p><em>Notes: {invoice.notes}</em></p>" if invoice.notes else ""}
</body></html>"""
    return html.encode("utf-8")


async def generate_report_pdf(report_type: str, data: dict) -> bytes:
    """Generate a printable HTML report."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    title = {
        "pnl": "Profit & Loss Statement",
        "expenses": "Expense Report",
        "tax-summary": "Tax Deduction Summary",
    }.get(report_type, report_type.replace("-", " ").title())

    rows_html = ""
    if report_type == "pnl":
        rows_html = f"""<table><tr><th>Metric</th><th>Amount</th></tr>
<tr><td>Total Income</td><td>${data.get("income", 0):,.2f}</td></tr>
<tr><td>Total Expenses</td><td>${data.get("expenses", 0):,.2f}</td></tr>
<tr><td><strong>Net Profit</strong></td><td><strong>${data.get("net", 0):,.2f}</strong></td></tr></table>"""
    elif report_type == "expenses":
        items = data.get("items", [])
        rows_html = "<table><tr><th>Category</th><th>Total</th></tr>"
        for item in items:
            rows_html += f"<tr><td>{item.get('category', '')}</td><td>${item.get('total', 0):,.2f}</td></tr>"
        rows_html += "</table>"
    elif report_type == "tax-summary":
        items = data.get("deductions", [])
        rows_html = "<table><tr><th>Category</th><th>Deductible Amount</th></tr>"
        for item in items:
            rows_html += f"<tr><td>{item.get('category', '')}</td><td>${item.get('total', 0):,.2f}</td></tr>"
        rows_html += f"</table><p class='total'>Total Deductions: ${data.get('total_deductions', 0):,.2f}</p>"

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{title}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:800px;margin:0 auto;padding:40px}}
table{{width:100%;border-collapse:collapse;margin:20px 0}}th,td{{padding:8px 12px;border-bottom:1px solid #ddd;text-align:left}}
th{{background:#f5f5f5}}.total{{font-size:1.2em;font-weight:bold;margin-top:20px}}</style></head><body>
<h1>{title}</h1><p>Generated: {now}</p>{rows_html}</body></html>"""
    return html.encode("utf-8")
