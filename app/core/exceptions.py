"""Tax God — Custom Exception Classes."""

from __future__ import annotations


class TaxGodError(Exception):
    """Base exception for Tax God application."""

    status_code: int = 500
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(TaxGodError):
    status_code = 404
    detail = "Resource not found"


class ForbiddenError(TaxGodError):
    status_code = 403
    detail = "Access forbidden"


class RateLimitError(TaxGodError):
    status_code = 429
    detail = "Rate limit exceeded"


class ExternalServiceError(TaxGodError):
    """For when Stripe/Plaid/OpenAI fails."""

    status_code = 502
    detail = "External service unavailable"


class ValidationError(TaxGodError):
    status_code = 422
    detail = "Validation error"

    def __init__(self, detail: str | None = None, errors: list[dict] | None = None):
        self.errors = errors or []
        super().__init__(detail)
