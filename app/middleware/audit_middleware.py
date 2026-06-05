"""Tax God - Audit Middleware: auto-logs write operations."""

from __future__ import annotations

import logging

from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.background import BackgroundTask

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.services.audit_service import log_event

logger = logging.getLogger(__name__)

SKIP_PREFIXES = ("/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/chat/", "/api/v1/dev/", "/health")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
METHOD_ACTION = {"POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}


def _extract_entity_type(path: str) -> str:
    """'/api/v1/expenses/123' -> 'expense'"""
    parts = [p for p in path.split("/") if p]
    # parts: ['api', 'v1', 'expenses', ...]
    if len(parts) >= 3:
        raw = parts[2]  # e.g. 'expenses', 'audit-trail'
        raw = raw.replace("-", "_")
        return raw.rstrip("s") if raw.endswith("s") and raw != "s" else raw
    return "unknown"


def _extract_user_id(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


async def _log_audit_event(user_id: str, action: str, entity_type: str, ip: str | None, ua: str | None):
    try:
        async with async_session_factory() as db:
            from app.models.audit_event import AuditEvent
            import json
            event = AuditEvent(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                ip_address=ip,
                user_agent=ua[:500] if ua else None,
            )
            db.add(event)
            await db.commit()
    except Exception as exc:
        logger.debug("Audit middleware log failed: %s", exc)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        path = request.url.path
        method = request.method

        if method not in WRITE_METHODS or not path.startswith("/api/v1/"):
            return response

        if any(path.startswith(skip) for skip in SKIP_PREFIXES):
            return response

        try:
            user_id = _extract_user_id(request)
            if not user_id:
                return response

            action = METHOD_ACTION.get(method, "unknown")
            entity_type = _extract_entity_type(path)
            ip = request.client.host if request.client else None
            ua = request.headers.get("user-agent", "")

            task = BackgroundTask(_log_audit_event, user_id, action, entity_type, ip, ua)
            response.background = task
        except Exception:
            pass

        return response
