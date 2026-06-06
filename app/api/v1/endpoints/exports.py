"""Tax God API - Export Endpoints (PDF/HTML & CSV)."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.business import Business
from app.models.client import Client
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.services.pdf_service import generate_invoice_pdf, generate_report_pdf

router = APIRouter()


@router.get("/invoice/{invoice_id}/pdf")
async def export_invoice_pdf(invoice_id: str, current_user: CurrentUser, db: DBSession):
    """Download invoice as HTML file."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    client = None
    if invoice.client_id:
        client = (await db.execute(select(Client).where(Client.id == invoice.client_id))).scalar_one_or_none()

    biz = (
        await db.execute(select(Business).where(Business.owner_id == current_user.id, Business.is_default.is_(True)))
    ).scalar_one_or_none()

    content = await generate_invoice_pdf(invoice, client, biz)
    return Response(
        content=content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="invoice-{invoice.invoice_number}.html"'},
    )


@router.get("/report/pnl")
async def export_pnl(current_user: CurrentUser, db: DBSession):
    """P&L report as downloadable HTML."""
    income = (
        await db.execute(
            select(func.sum(Invoice.amount)).where(Invoice.owner_id == current_user.id, Invoice.status == "paid")
        )
    ).scalar_one() or 0
    expenses = (
        await db.execute(select(func.sum(Expense.amount)).where(Expense.owner_id == current_user.id))
    ).scalar_one() or 0

    content = await generate_report_pdf("pnl", {"income": income, "expenses": expenses, "net": income - expenses})
    return Response(
        content=content,
        media_type="text/html",
        headers={"Content-Disposition": 'attachment; filename="pnl-report.html"'},
    )


@router.get("/report/expenses")
async def export_expenses_report(current_user: CurrentUser, db: DBSession):
    """Expense report by category."""
    result = await db.execute(
        select(Expense.category, func.sum(Expense.amount).label("total"))
        .where(Expense.owner_id == current_user.id)
        .group_by(Expense.category)
    )
    items = [{"category": r.category, "total": r.total or 0} for r in result.all()]
    content = await generate_report_pdf("expenses", {"items": items})
    return Response(
        content=content,
        media_type="text/html",
        headers={"Content-Disposition": 'attachment; filename="expense-report.html"'},
    )


@router.get("/report/tax-summary")
async def export_tax_summary(current_user: CurrentUser, db: DBSession):
    """Tax deduction summary."""
    result = await db.execute(
        select(Expense.category, func.sum(Expense.amount).label("total"))
        .where(Expense.owner_id == current_user.id, Expense.tax_deductible.is_(True))
        .group_by(Expense.category)
    )
    items = [{"category": r.category, "total": r.total or 0} for r in result.all()]
    total = sum(i["total"] for i in items)
    content = await generate_report_pdf("tax-summary", {"deductions": items, "total_deductions": total})
    return Response(
        content=content,
        media_type="text/html",
        headers={"Content-Disposition": 'attachment; filename="tax-summary.html"'},
    )


@router.post("/csv/{entity}")
async def export_csv(entity: str, current_user: CurrentUser, db: DBSession):
    """Export entity data as CSV."""
    models = {
        "clients": (Client, ["id", "name", "email", "phone", "company", "status", "created_at"]),
        "expenses": (Expense, ["id", "date", "vendor", "amount", "category", "description", "tax_deductible"]),
        "transactions": (Transaction, ["id", "date", "description", "amount", "category", "source", "reconciled"]),
        "invoices": (
            Invoice,
            ["id", "invoice_number", "status", "amount", "tax_amount", "currency", "due_date", "created_at"],
        ),
    }
    if entity not in models:
        raise HTTPException(status_code=400, detail=f"Invalid entity. Choose from: {list(models.keys())}")

    model, fields = models[entity]
    result = await db.execute(select(model).where(model.owner_id == current_user.id))
    rows = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(fields)
    for row in rows:
        writer.writerow([getattr(row, f, "") for f in fields])

    return Response(
        content=output.getvalue().encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{entity}.csv"'},
    )
