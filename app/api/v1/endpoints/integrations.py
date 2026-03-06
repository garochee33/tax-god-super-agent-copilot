"""
Tax God API - Integrations Endpoints
OAuth and data sync entrypoints for Google and QuickBooks.
Production: validated params, rate-limit handling (429), structured logging.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.services.circuit_breaker import QB_AGENT_ID
from app.services.integrations.roadmap_catalog import get_roadmap_catalog

logger = logging.getLogger(__name__)
DATE_YYYY_MM_DD = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ConnectRequest(BaseModel):
    provider: str
    user_id: str = Field(default="current_user")


class CallbackRequest(BaseModel):
    provider: str
    code: str
    user_id: str = Field(default="current_user")
    realm_id: str | None = None


class DisconnectRequest(BaseModel):
    provider: str
    user_id: str = Field(default="current_user")


def _integration_catalog(
    status_map: dict[str, bool], configured_map: dict[str, bool]
) -> list[dict[str, Any]]:
    return [
        {
            "id": "google",
            "name": "Google Workspace",
            "description": "Gmail, Drive, Docs, Sheets",
            "status": "connected" if status_map.get("google") else "disconnected",
            "icon": "google",
            "configured": configured_map.get("google", False),
        },
        {
            "id": "quickbooks",
            "name": "QuickBooks Online",
            "description": "Accounting Data Sync",
            "status": "connected" if status_map.get("quickbooks") else "disconnected",
            "icon": "quickbooks",
            "configured": configured_map.get("quickbooks", False),
        },
    ]


@router.get("/list")
async def list_integrations(
    request: Request,
    user_id: str = Query(default="current_user", description="Client/user identifier"),
):
    """List integrations and connection status for a user."""
    manager = request.app.state.integration_manager
    configured_map = {
        provider: bool(manager.get_provider(provider).is_configured)
        for provider in manager.list_provider_names()
    }
    status_map = {
        provider: await manager.is_connected(user_id, provider)
        for provider in manager.list_provider_names()
    }
    return {
        "user_id": user_id,
        "integrations": _integration_catalog(status_map, configured_map),
    }


@router.get("/roadmap")
async def get_integrations_roadmap():
    """Return 2026 integration roadmap categories and tools (research, compliance, documents, planning, connectivity)."""
    return {"categories": get_roadmap_catalog()}


@router.post("/connect")
async def connect_integration(body: ConnectRequest, request: Request):
    """Get OAuth URL for provider connection."""
    manager = request.app.state.integration_manager
    provider = manager.get_provider(body.provider)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if not provider.is_configured:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{body.provider} is not configured. Add OAuth credentials in .env first."
            ),
        )

    url = provider.get_auth_url(state=body.user_id)
    return {"provider": body.provider, "user_id": body.user_id, "auth_url": url}


@router.post("/callback")
async def oauth_callback(body: CallbackRequest, request: Request):
    """
    Exchange OAuth code for tokens and persist connection credentials.
    Supports programmatic callbacks.
    """
    manager = request.app.state.integration_manager
    provider = manager.get_provider(body.provider)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        tokens = await provider.exchange_code(body.code, realm_id=body.realm_id)
        await manager.save_credentials(body.user_id, body.provider, tokens)
        return {"status": "connected", "provider": body.provider, "user_id": body.user_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {exc}") from exc


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback_get(
    request: Request,
    provider: str = Query(...),
    code: str = Query(...),
    state: str = Query(default="current_user"),
    realmId: str | None = Query(default=None),  # QuickBooks convention
):
    """
    Browser callback variant for OAuth providers.
    Stores credentials and returns a close-window page.
    """
    manager = request.app.state.integration_manager
    integration = manager.get_provider(provider)
    if not integration:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        tokens = await integration.exchange_code(code, realm_id=realmId)
        await manager.save_credentials(state, provider, tokens)
        return HTMLResponse(
            """
            <html><body style="font-family: sans-serif; padding: 24px;">
              <h3>Tax God Integration Connected</h3>
              <p>You can close this window and return to Tax God.</p>
              <script>setTimeout(() => window.close(), 1200);</script>
            </body></html>
            """
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {exc}") from exc


@router.post("/disconnect")
async def disconnect_integration(body: DisconnectRequest, request: Request):
    manager = request.app.state.integration_manager
    removed = await manager.remove_credentials(body.user_id, body.provider)
    return {"provider": body.provider, "user_id": body.user_id, "disconnected": removed}


@router.get("/status/{provider}")
async def integration_status(provider: str, request: Request, user_id: str = Query(default="current_user")):
    manager = request.app.state.integration_manager
    if not manager.get_provider(provider):
        raise HTTPException(status_code=404, detail="Provider not found")
    return await manager.get_connection_snapshot(user_id, provider)


@router.get("/google/emails")
async def list_google_emails(
    request: Request,
    user_id: str = Query(default="current_user"),
    query: str = Query(default=""),
    max_results: int = Query(default=10, ge=1, le=50),
):
    manager = request.app.state.integration_manager
    provider = manager.get_provider("google")
    if not provider:
        raise HTTPException(status_code=404, detail="Google provider not configured")

    access_token = await manager.get_valid_access_token(user_id, "google")
    if not access_token:
        raise HTTPException(status_code=401, detail="Google is not connected")

    try:
        emails = await provider.list_emails(access_token=access_token, query=query, max_results=max_results)
        return {"user_id": user_id, "provider": "google", "count": len(emails), "emails": emails}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Google request failed: {exc}") from exc


def _quickbooks_creds_and_token(request: Request, user_id: str):
    """Resolve QuickBooks provider, credentials, access token, and realm_id. Raises HTTPException on failure."""
    manager = request.app.state.integration_manager
    provider = manager.get_provider("quickbooks")
    if not provider:
        raise HTTPException(status_code=404, detail="QuickBooks provider not configured")
    creds = await manager.get_credentials(user_id, "quickbooks")
    access_token = await manager.get_valid_access_token(user_id, "quickbooks")
    if not creds or not access_token:
        raise HTTPException(status_code=401, detail="QuickBooks is not connected")
    realm_id = creds.metadata.get("realm_id") if creds.metadata else None
    if not realm_id:
        raise HTTPException(status_code=400, detail="QuickBooks realm_id is missing")
    return manager, provider, access_token, realm_id


def _quickbooks_http_error(
    exc: Exception,
    endpoint: str,
    user_id: str,
    circuit_breaker: Any = None,
) -> None:
    """Map QuickBooks/httpx errors to HTTP responses; log without secrets. Records failure on circuit breaker (Trinity GEM)."""
    status: int | None = getattr(exc.response, "status_code", None) if isinstance(exc, httpx.HTTPStatusError) else None
    if circuit_breaker:
        err_msg = str(exc)
        is_429 = (
            status == 429
            or "429" in err_msg
            or "rate limit" in err_msg.lower()
            or "insufficient_quota" in err_msg.lower()
        )
        circuit_breaker.record_failure(QB_AGENT_ID, error=err_msg, is_rate_limit=is_429)
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 429:
            logger.warning("QuickBooks rate limit (429) for user_id=%s endpoint=%s", user_id, endpoint)
            raise HTTPException(
                status_code=503,
                detail="QuickBooks rate limit exceeded. Try again in a minute.",
            ) from exc
        if status in (401, 403):
            logger.info("QuickBooks auth failure (%s) for user_id=%s endpoint=%s", status, user_id, endpoint)
        else:
            logger.warning("QuickBooks API error status=%s user_id=%s endpoint=%s", status, user_id, endpoint)
        detail = getattr(exc, "message", str(exc)) or f"QuickBooks request failed (HTTP {status})"
        raise HTTPException(status_code=400 if status >= 500 else status, detail=detail) from exc
    logger.exception("QuickBooks unexpected error user_id=%s endpoint=%s", user_id, endpoint)
    raise HTTPException(status_code=400, detail=f"QuickBooks request failed: {exc}") from exc


def _quickbooks_circuit_check(request: Request) -> None:
    """Trinity GEM: block if QuickBooks circuit is open."""
    cb = getattr(request.app.state, "circuit_breaker", None)
    if not cb:
        return
    check = cb.can_execute(QB_AGENT_ID)
    if not check.allowed:
        raise HTTPException(status_code=503, detail=check.reason or "QuickBooks temporarily unavailable")


@router.get("/quickbooks/company")
async def quickbooks_company(
    request: Request,
    user_id: str = Query(default="current_user"),
):
    """Get connected QuickBooks company info (name, legal name, etc.)."""
    _manager, provider, access_token, realm_id = _quickbooks_creds_and_token(request, user_id)
    _quickbooks_circuit_check(request)
    cb = getattr(request.app.state, "circuit_breaker", None)
    try:
        company = await provider.get_company_info(access_token=access_token, realm_id=realm_id)
        if cb:
            cb.record_success(QB_AGENT_ID)
        return {"user_id": user_id, "provider": "quickbooks", "company": company}
    except HTTPException:
        raise
    except Exception as exc:
        _quickbooks_http_error(exc, "company", user_id, cb)


@router.get("/quickbooks/profit-loss")
async def quickbooks_profit_loss(
    request: Request,
    user_id: str = Query(default="current_user"),
    year: int = Query(default=2024, ge=2000, le=2100),
):
    """Profit & Loss report for the given calendar year."""
    _manager, provider, access_token, realm_id = _quickbooks_creds_and_token(request, user_id)
    _quickbooks_circuit_check(request)
    cb = getattr(request.app.state, "circuit_breaker", None)
    try:
        report = await provider.get_profit_loss(access_token=access_token, realm_id=realm_id, year=year)
        if cb:
            cb.record_success(QB_AGENT_ID)
        return {"user_id": user_id, "provider": "quickbooks", "year": year, "report": report}
    except HTTPException:
        raise
    except Exception as exc:
        _quickbooks_http_error(exc, "profit-loss", user_id, cb)


@router.get("/quickbooks/balance-sheet")
async def quickbooks_balance_sheet(
    request: Request,
    user_id: str = Query(default="current_user"),
    as_of: str = Query(default=None, description="Date YYYY-MM-DD; default is end of prior month"),
):
    """Balance Sheet report as of a given date."""
    _manager, provider, access_token, realm_id = _quickbooks_creds_and_token(request, user_id)
    _quickbooks_circuit_check(request)
    cb = getattr(request.app.state, "circuit_breaker", None)
    if not as_of:
        today = datetime.now(timezone.utc).date()
        first = today.replace(day=1)
        end_prior = first - timedelta(days=1)
        as_of = end_prior.isoformat()
    else:
        if not DATE_YYYY_MM_DD.match(as_of.strip()):
            raise HTTPException(status_code=400, detail="as_of must be YYYY-MM-DD")
    try:
        report = await provider.get_balance_sheet(
            access_token=access_token, realm_id=realm_id, as_of_date=as_of.strip()
        )
        if cb:
            cb.record_success(QB_AGENT_ID)
        return {"user_id": user_id, "provider": "quickbooks", "as_of": as_of, "report": report}
    except HTTPException:
        raise
    except Exception as exc:
        _quickbooks_http_error(exc, "balance-sheet", user_id, cb)


@router.get("/quickbooks/vendors")
async def quickbooks_vendors(
    request: Request,
    user_id: str = Query(default="current_user"),
    max_results: int = Query(default=100, ge=1, le=1000),
):
    """List vendors (for 1099 prep); includes DisplayName and TaxIdentifier when present."""
    _manager, provider, access_token, realm_id = _quickbooks_creds_and_token(request, user_id)
    _quickbooks_circuit_check(request)
    cb = getattr(request.app.state, "circuit_breaker", None)
    try:
        vendors = await provider.get_vendors(
            access_token=access_token, realm_id=realm_id, max_results=max_results
        )
        if cb:
            cb.record_success(QB_AGENT_ID)
        return {"user_id": user_id, "provider": "quickbooks", "count": len(vendors), "vendors": vendors}
    except HTTPException:
        raise
    except Exception as exc:
        _quickbooks_http_error(exc, "vendors", user_id, cb)
