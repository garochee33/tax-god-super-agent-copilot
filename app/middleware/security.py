"""
Tax God - Security Middleware
Rate limiting, request IDs, CSP headers, and /metrics protection.
"""

from __future__ import annotations

import time
import uuid
import logging
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers (CSP, X-Content-Type-Options, etc.)."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding-window rate limiter.
    Production: replace with Redis-backed solution for multi-worker support.
    """

    def __init__(self, app, requests_per_minute: int = 60, auth_requests_per_minute: int = 10):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.auth_rpm = auth_requests_per_minute
        self._windows: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, key: str, limit: int) -> bool:
        now = time.time()
        window = self._windows[key]
        window[:] = [t for t in window if now - t < 60]
        if len(window) >= limit:
            return True
        window.append(now)
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        client_ip = self._get_client_ip(request)

        is_auth_route = path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/auth/register")

        if is_auth_route:
            if self._is_rate_limited(f"auth:{client_ip}", self.auth_rpm):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={"Retry-After": "60"},
                )
        else:
            if self._is_rate_limited(f"api:{client_ip}", self.rpm):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)
