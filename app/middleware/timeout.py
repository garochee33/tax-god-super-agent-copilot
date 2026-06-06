"""Tax God — Request Timeout Middleware."""

from __future__ import annotations

import asyncio

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


_AI_PREFIXES = ("/api/v1/chat", "/api/v1/audit", "/api/v1/advanced")
_DEFAULT_TIMEOUT = 30
_AI_TIMEOUT = 60


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        timeout = _AI_TIMEOUT if any(path.startswith(p) for p in _AI_PREFIXES) else _DEFAULT_TIMEOUT
        try:
            return await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            request_id = getattr(request.state, "request_id", "unknown")
            return JSONResponse(
                status_code=504,
                content={"error": "Gateway Timeout", "request_id": request_id},
            )
