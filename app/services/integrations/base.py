"""
Base integration contracts and token model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass
class OAuthCredentials:
    access_token: str
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_expired(self, skew_seconds: int = 30) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(UTC) >= (self.expires_at - timedelta(seconds=skew_seconds))

    @classmethod
    def from_token_response(cls, payload: dict[str, Any]) -> OAuthCredentials:
        expires_in = int(payload.get("expires_in", 0) or 0)
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in) if expires_in > 0 else None
        return cls(
            access_token=str(payload.get("access_token", "")),
            refresh_token=str(payload.get("refresh_token", "")),
            token_type=str(payload.get("token_type", "Bearer")),
            expires_at=expires_at,
            scope=str(payload.get("scope", "")),
            metadata={
                k: v
                for k, v in payload.items()
                if k not in {"access_token", "refresh_token", "token_type", "expires_in", "scope"}
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    def to_safe_dict(self) -> dict[str, Any]:
        """Return dict with tokens masked for logging / API responses."""

        def _mask(token: str) -> str:
            if not token or len(token) < 4:
                return "***"
            return f"***{token[-4:]}"

        return {
            "access_token": _mask(self.access_token),
            "refresh_token": _mask(self.refresh_token),
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> OAuthCredentials:
        expires_at_raw = payload.get("expires_at")
        created_at_raw = payload.get("created_at")
        return cls(
            access_token=str(payload.get("access_token", "")),
            refresh_token=str(payload.get("refresh_token", "")),
            token_type=str(payload.get("token_type", "Bearer")),
            expires_at=datetime.fromisoformat(expires_at_raw) if expires_at_raw else None,
            scope=str(payload.get("scope", "")),
            metadata=dict(payload.get("metadata", {})),
            created_at=(datetime.fromisoformat(created_at_raw) if created_at_raw else datetime.now(UTC)),
        )


class BaseIntegration(ABC):
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier (e.g. google, quickbooks)."""

    @abstractmethod
    def get_auth_url(self, state: str = "") -> str:
        """Generate OAuth authorization URL."""

    @abstractmethod
    async def exchange_code(self, code: str, **kwargs: Any) -> dict[str, Any]:
        """Exchange OAuth code for token payload."""

    @abstractmethod
    async def refresh_token(self, refresh_token: str, **kwargs: Any) -> dict[str, Any]:
        """Refresh token payload."""

    @abstractmethod
    async def get_user_info(self, access_token: str, **kwargs: Any) -> dict[str, Any]:
        """Retrieve provider profile info."""

    @abstractmethod
    async def test_connection(self, access_token: str, **kwargs: Any) -> bool:
        """Verify integration connectivity."""
