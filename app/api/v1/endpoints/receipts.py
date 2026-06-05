"""Tax God API - Receipt Scanning (upload + AI extraction)"""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, DBSession
from app.models.expense import Expense, ExpenseCategory

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[4] / "uploads" / "receipts"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


class ReceiptExtraction(BaseModel):
    vendor: str | None = None
    amount: float | None = None
    date: str | None = None
    category: str | None = None
    description: str | None = None
    confidence: float = 0.0


class ReceiptUploadResponse(BaseModel):
    receipt_url: str
    extraction: ReceiptExtraction


@router.post("/upload", response_model=ReceiptUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(file: UploadFile, current_user: CurrentUser):
    """Upload a receipt image and extract data via AI."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Save file
    ext = Path(file.filename or "receipt.png").suffix or ".png"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(content)

    receipt_url = f"/uploads/receipts/{filename}"

    # AI extraction
    extraction = await _extract_receipt_data(content, file.content_type)

    return ReceiptUploadResponse(receipt_url=receipt_url, extraction=extraction)


@router.post("/extract")
async def extract_from_existing(expense_id: str, current_user: CurrentUser, db: DBSession):
    """Re-run AI extraction on an existing expense's receipt."""
    from sqlalchemy import select

    expense = (
        await db.execute(select(Expense).where(Expense.id == expense_id, Expense.owner_id == current_user.id))
    ).scalar_one_or_none()
    if not expense or not expense.receipt_url:
        raise HTTPException(status_code=404, detail="Expense or receipt not found")

    filepath = Path(__file__).resolve().parents[4] / expense.receipt_url.lstrip("/")
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Receipt file not found on disk")

    content = filepath.read_bytes()
    content_type = "image/png" if filepath.suffix == ".png" else "image/jpeg"
    extraction = await _extract_receipt_data(content, content_type)
    return {"extraction": extraction.model_dump()}


@router.post("/scan-and-create")
async def scan_and_create_expense(file: UploadFile, current_user: CurrentUser, db: DBSession):
    """Upload receipt, extract data, and auto-create an expense entry."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    ext = Path(file.filename or "receipt.png").suffix or ".png"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(content)
    receipt_url = f"/uploads/receipts/{filename}"

    extraction = await _extract_receipt_data(content, file.content_type)

    # Create expense from extraction
    category = _match_category(extraction.category)
    expense = Expense(
        owner_id=current_user.id,
        date=_parse_date(extraction.date),
        vendor=extraction.vendor or "Unknown Vendor",
        amount=extraction.amount or 0.0,
        category=category,
        description=extraction.description,
        receipt_url=receipt_url,
        tax_deductible=True,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)

    return {
        "expense_id": expense.id,
        "receipt_url": receipt_url,
        "extraction": extraction.model_dump(),
        "confidence": extraction.confidence,
    }


async def _extract_receipt_data(content: bytes, content_type: str) -> ReceiptExtraction:
    """Use AI (OpenAI vision or Anthropic) to extract receipt data."""
    import os

    import httpx

    b64 = base64.b64encode(content).decode()

    # Try OpenAI Vision first
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": _EXTRACTION_PROMPT},
                                    {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{b64}"}},
                                ],
                            }
                        ],
                        "max_tokens": 300,
                    },
                )
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"]
                    return _parse_extraction(text)
        except Exception:
            pass

    # Fallback: Anthropic Claude
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            media_type = content_type if content_type != "application/pdf" else "image/png"
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01"},
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 300,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                                    {"type": "text", "text": _EXTRACTION_PROMPT},
                                ],
                            }
                        ],
                    },
                )
                if resp.status_code == 200:
                    text = resp.json()["content"][0]["text"]
                    return _parse_extraction(text)
        except Exception:
            pass

    return ReceiptExtraction(confidence=0.0)


_EXTRACTION_PROMPT = """Extract the following from this receipt image. Return ONLY valid JSON:
{
  "vendor": "store/business name",
  "amount": 0.00,
  "date": "YYYY-MM-DD",
  "category": "one of: office_supplies, travel, meals, utilities, advertising, insurance, legal_professional, rent, equipment, vehicle, supplies, other",
  "description": "brief description of purchase",
  "confidence": 0.95
}
If you cannot read a field, use null. confidence = how sure you are (0-1)."""


def _parse_extraction(text: str) -> ReceiptExtraction:
    import json

    try:
        # Strip markdown code fences if present
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(clean)
        return ReceiptExtraction(**data)
    except Exception:
        return ReceiptExtraction(confidence=0.0)


def _match_category(cat: str | None) -> str:
    if not cat:
        return ExpenseCategory.OTHER.value
    cat_lower = cat.lower().replace(" ", "_")
    for ec in ExpenseCategory:
        if ec.value == cat_lower:
            return ec.value
    return ExpenseCategory.OTHER.value


def _parse_date(date_str: str | None) -> datetime:
    if not date_str:
        return datetime.now(UTC)
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return datetime.now(UTC)
