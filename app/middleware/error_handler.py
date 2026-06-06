"""Tax God — Global Exception Handler Middleware."""

from __future__ import annotations

import logging
import traceback
import uuid

from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Environment, get_settings
from app.core.exceptions import TaxGodError
from app.core.exceptions import ValidationError as TaxGodValidationError

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or str(uuid.uuid4())


def _is_production() -> bool:
    return get_settings().ENVIRONMENT == Environment.PRODUCTION


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


async def taxgod_exception_handler(request: Request, exc: TaxGodError) -> JSONResponse:
    request_id = _get_request_id(request)
    logger.error("TaxGodError [%s]: %s", request_id, exc.detail)
    body: dict = {"error": exc.detail, "request_id": request_id}
    if isinstance(exc, TaxGodValidationError) and exc.errors:
        body["fields"] = exc.errors
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    request_id = _get_request_id(request)
    logger.warning("ValidationError [%s]: %s", request_id, exc.error_count())
    fields = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"error": "Validation error", "request_id": request_id, "fields": fields})


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    request_id = _get_request_id(request)
    logger.error("Database error [%s]: %s\n%s", request_id, exc, traceback.format_exc())
    return JSONResponse(status_code=500, content={"error": "Database error", "request_id": request_id})


async def timeout_exception_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    request_id = _get_request_id(request)
    logger.error("Timeout [%s]: %s", request_id, exc)
    return JSONResponse(status_code=504, content={"error": "Gateway Timeout", "request_id": request_id})


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = _get_request_id(request)
    logger.error("Unhandled exception [%s]: %s\n%s", request_id, exc, traceback.format_exc())
    if _is_production():
        return JSONResponse(status_code=500, content={"error": "Internal server error", "request_id": request_id})
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "request_id": request_id, "traceback": traceback.format_exc()},
    )
