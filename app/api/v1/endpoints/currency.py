"""Tax God API - Currency Endpoints"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.currency_service import SUPPORTED_CURRENCIES, CurrencyService

router = APIRouter()
currency_service = CurrencyService()


class ConvertRequest(BaseModel):
    amount: float = Field(..., gt=0)
    from_currency: str = Field(..., alias="from", min_length=3, max_length=3)
    to_currency: str = Field(..., alias="to", min_length=3, max_length=3)

    model_config = {"populate_by_name": True}


@router.get("/rates")
async def get_rates(base: str = Query(default="USD", max_length=3)):
    rates = currency_service._fetch_rates(base.upper())
    return {"base": base.upper(), "rates": rates}


@router.post("/convert")
async def convert_currency(body: ConvertRequest):
    result = currency_service.convert(body.amount, body.from_currency, body.to_currency)
    return {
        "amount": body.amount,
        "from": body.from_currency.upper(),
        "to": body.to_currency.upper(),
        "result": result,
        "rate": currency_service.get_exchange_rate(body.from_currency, body.to_currency),
    }


@router.get("/supported")
async def supported_currencies():
    return {"currencies": SUPPORTED_CURRENCIES}
