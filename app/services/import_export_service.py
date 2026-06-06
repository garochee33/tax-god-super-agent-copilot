"""Tax God - Data Import/Export Service"""

from __future__ import annotations

import csv
import io
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chart_of_accounts import ChartOfAccount
from app.models.client import Client
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.models.time_entry import TimeEntry
from app.models.transaction import Transaction
from app.models.vendor import Vendor

ENTITY_MAP = {
    "clients": Client,
    "expenses": Expense,
    "invoices": Invoice,
    "transactions": Transaction,
    "vendors": Vendor,
    "time_entries": TimeEntry,
}

EXPORT_FIELDS = {
    "clients": ["id", "name", "email", "phone", "company", "status", "tax_id", "filing_type"],
    "expenses": ["id", "date", "vendor", "amount", "category", "description", "tax_deductible"],
    "invoices": ["id", "invoice_number", "status", "amount", "tax_amount", "currency", "due_date"],
    "transactions": ["id", "date", "description", "amount", "category", "reconciled", "source"],
    "vendors": ["id", "name", "email", "phone", "company", "category", "tax_id", "is_1099", "total_paid"],
    "time_entries": ["id", "description", "hours", "date", "billable", "rate", "invoiced"],
}


async def export_to_csv(db: AsyncSession, user_id: str, entity_type: str) -> str:
    """Export entity records to CSV string."""
    model = ENTITY_MAP[entity_type]
    result = await db.execute(select(model).where(model.owner_id == user_id))
    rows = result.scalars().all()

    fields = EXPORT_FIELDS[entity_type]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({f: getattr(row, f, "") for f in fields})
    return output.getvalue()


async def import_from_csv(db: AsyncSession, user_id: str, entity_type: str, csv_content: str) -> dict:
    """Parse CSV and create records. Returns {imported: N, errors: [...]}."""
    model = ENTITY_MAP[entity_type]
    reader = csv.DictReader(io.StringIO(csv_content))
    imported = 0
    errors = []

    for i, row in enumerate(reader, 1):
        try:
            row.pop("id", None)
            # Convert types for known fields
            for key in list(row.keys()):
                if row[key] == "":
                    row[key] = None
            if "amount" in row and row["amount"] is not None:
                row["amount"] = float(row["amount"])
            if "hours" in row and row["hours"] is not None:
                row["hours"] = float(row["hours"])
            if "rate" in row and row["rate"] is not None:
                row["rate"] = float(row["rate"])
            if "tax_amount" in row and row["tax_amount"] is not None:
                row["tax_amount"] = float(row["tax_amount"])
            if "total_paid" in row and row["total_paid"] is not None:
                row["total_paid"] = float(row["total_paid"])
            if "tax_deductible" in row and row["tax_deductible"] is not None:
                row["tax_deductible"] = row["tax_deductible"].lower() in ("true", "1", "yes")
            if "billable" in row and row["billable"] is not None:
                row["billable"] = row["billable"].lower() in ("true", "1", "yes")
            if "invoiced" in row and row["invoiced"] is not None:
                row["invoiced"] = row["invoiced"].lower() in ("true", "1", "yes")
            if "reconciled" in row and row["reconciled"] is not None:
                row["reconciled"] = row["reconciled"].lower() in ("true", "1", "yes")
            if "is_1099" in row and row["is_1099"] is not None:
                row["is_1099"] = row["is_1099"].lower() in ("true", "1", "yes")
            if "date" in row and row["date"] is not None:
                row["date"] = datetime.fromisoformat(row["date"].replace("Z", "+00:00"))

            # Remove None values for fields not in model
            valid_cols = {c.name for c in model.__table__.columns}
            filtered = {k: v for k, v in row.items() if k in valid_cols and k != "owner_id"}
            obj = model(owner_id=user_id, **filtered)
            db.add(obj)
            imported += 1
        except Exception as exc:
            errors.append(f"Row {i}: {str(exc)}")

    if imported:
        await db.commit()
    return {"imported": imported, "errors": errors}


async def export_iif(db: AsyncSession, user_id: str) -> str:
    """Generate QuickBooks IIF export for chart of accounts + transactions."""
    lines = []

    # Chart of Accounts
    result = await db.execute(select(ChartOfAccount).where(ChartOfAccount.owner_id == user_id))
    accounts = result.scalars().all()
    if accounts:
        lines.append("!ACCNT\tNAME\tACCNTTYPE\tDESC")
        type_map = {"asset": "BANK", "liability": "CCARD", "equity": "EQUITY", "revenue": "INC", "expense": "EXP"}
        for acct in accounts:
            iif_type = type_map.get(acct.account_type, "EXP")
            lines.append(f"ACCNT\t{acct.name}\t{iif_type}\t{acct.description or ''}")

    # Transactions
    result = await db.execute(select(Transaction).where(Transaction.owner_id == user_id))
    txns = result.scalars().all()
    if txns:
        lines.append("!TRNS\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tMEMO")
        lines.append("!SPL\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tMEMO")
        lines.append("!ENDTRNS")
        for txn in txns:
            date_str = txn.date.strftime("%m/%d/%Y") if txn.date else ""
            lines.append(
                f"TRNS\tGENERAL JOURNAL\t{date_str}\t{txn.category or 'Uncategorized'}\t{txn.amount:.2f}\t{txn.description}"
            )
            lines.append(f"SPL\tGENERAL JOURNAL\t{date_str}\tSplit\t{-txn.amount:.2f}\t{txn.description}")
            lines.append("ENDTRNS")

    return "\n".join(lines)
