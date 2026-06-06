"""
Integration manager.

Primary storage is PostgreSQL with encrypted credential payloads.
Falls back to in-memory storage when the DB is unavailable.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.crypto import get_fernet
from app.services.integrations.base import BaseIntegration, OAuthCredentials

logger = logging.getLogger(__name__)


class IntegrationManager:
    def __init__(self, db_engine: AsyncEngine | None = None):
        self._integrations: dict[str, BaseIntegration] = {}
        self._tokens: dict[str, dict[str, Any]] = {}
        self._db_engine = db_engine
        self._db_ready = False
        self._fernet = get_fernet()

    async def initialize_storage(self) -> None:
        """Ensure integration credential table exists."""
        if not self._db_engine:
            self._db_ready = False
            return

        try:
            async with self._db_engine.begin() as conn:
                await conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS integration_credentials (
                            user_id TEXT NOT NULL,
                            provider TEXT NOT NULL,
                            payload_encrypted TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (user_id, provider)
                        )
                        """
                    )
                )
            self._db_ready = True
        except Exception as exc:
            logger.warning("Integration credential DB init failed, using in-memory fallback: %s", exc)
            self._db_ready = False

    @property
    def storage_mode(self) -> str:
        return "postgres_encrypted" if self._db_ready else "memory_fallback"

    @property
    def storage_ready(self) -> bool:
        return self._db_ready

    def register(self, integration: BaseIntegration) -> None:
        self._integrations[integration.provider_name] = integration

    def get_provider(self, name: str) -> BaseIntegration | None:
        return self._integrations.get(name)

    def list_provider_names(self) -> list[str]:
        return sorted(self._integrations.keys())

    def list_providers(self) -> dict[str, str]:
        return {
            name: ("Active" if integration.is_configured else "NotConfigured")
            for name, integration in self._integrations.items()
        }

    @staticmethod
    def _token_key(user_id: str, provider: str) -> str:
        return f"{user_id}:{provider}"

    def _encrypt_payload(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, default=str).encode()
        return self._fernet.encrypt(raw).decode()

    def _decrypt_payload(self, payload_encrypted: str) -> dict[str, Any]:
        raw = self._fernet.decrypt(payload_encrypted.encode())
        return json.loads(raw.decode())

    async def save_credentials(self, user_id: str, provider: str, credentials: dict[str, Any]) -> None:
        creds = OAuthCredentials.from_token_response(credentials)
        payload = creds.to_dict()
        key = self._token_key(user_id, provider)
        self._tokens[key] = payload

        if not self._db_ready or not self._db_engine:
            return

        try:
            encrypted = self._encrypt_payload(payload)
            async with self._db_engine.begin() as conn:
                await conn.execute(
                    text(
                        """
                        INSERT INTO integration_credentials (user_id, provider, payload_encrypted, created_at, updated_at)
                        VALUES (:user_id, :provider, :payload_encrypted, NOW(), NOW())
                        ON CONFLICT (user_id, provider)
                        DO UPDATE SET payload_encrypted = EXCLUDED.payload_encrypted, updated_at = NOW()
                        """
                    ),
                    {
                        "user_id": user_id,
                        "provider": provider,
                        "payload_encrypted": encrypted,
                    },
                )
        except Exception as exc:
            logger.warning("Failed to persist integration credentials for %s/%s: %s", user_id, provider, exc)

    async def get_credentials(self, user_id: str, provider: str) -> OAuthCredentials | None:
        key = self._token_key(user_id, provider)

        if self._db_ready and self._db_engine:
            try:
                async with self._db_engine.begin() as conn:
                    result = await conn.execute(
                        text(
                            """
                            SELECT payload_encrypted
                            FROM integration_credentials
                            WHERE user_id = :user_id AND provider = :provider
                            """
                        ),
                        {"user_id": user_id, "provider": provider},
                    )
                    row = result.first()
                if row:
                    payload = self._decrypt_payload(row[0])
                    self._tokens[key] = payload
                    return OAuthCredentials.from_dict(payload)
            except Exception as exc:
                logger.warning("Failed to load integration credentials for %s/%s: %s", user_id, provider, exc)

        payload = self._tokens.get(key)
        if payload:
            return OAuthCredentials.from_dict(payload)
        return None

    async def remove_credentials(self, user_id: str, provider: str) -> bool:
        key = self._token_key(user_id, provider)
        removed = self._tokens.pop(key, None) is not None

        if self._db_ready and self._db_engine:
            try:
                async with self._db_engine.begin() as conn:
                    result = await conn.execute(
                        text(
                            """
                            DELETE FROM integration_credentials
                            WHERE user_id = :user_id AND provider = :provider
                            """
                        ),
                        {"user_id": user_id, "provider": provider},
                    )
                removed = removed or bool(result.rowcount)
            except Exception as exc:
                logger.warning("Failed to delete integration credentials for %s/%s: %s", user_id, provider, exc)

        return removed

    async def is_connected(self, user_id: str, provider: str) -> bool:
        token = await self.get_credentials(user_id, provider)
        return token is not None and bool(token.access_token)

    async def get_valid_access_token(self, user_id: str, provider: str) -> str | None:
        integration = self.get_provider(provider)
        if not integration:
            return None

        token = await self.get_credentials(user_id, provider)
        if not token:
            return None

        if not token.is_expired():
            return token.access_token

        if not token.refresh_token:
            logger.info("Token for %s/%s expired with no refresh token", user_id, provider)
            return None

        try:
            refreshed = await integration.refresh_token(token.refresh_token, metadata=token.metadata)
            merged = {**refreshed}
            if "refresh_token" not in merged:
                merged["refresh_token"] = token.refresh_token
            if "scope" not in merged:
                merged["scope"] = token.scope
            if "token_type" not in merged:
                merged["token_type"] = token.token_type
            if "metadata" not in merged:
                merged["metadata"] = token.metadata

            await self.save_credentials(user_id, provider, merged)
            new_token = await self.get_credentials(user_id, provider)
            return new_token.access_token if new_token else None
        except Exception as exc:
            logger.warning("Token refresh failed for %s/%s: %s", user_id, provider, exc)
            return None

    async def get_connection_snapshot(self, user_id: str, provider: str) -> dict[str, Any]:
        token = await self.get_credentials(user_id, provider)
        if not token:
            return {
                "provider": provider,
                "connected": False,
                "expires_at": None,
                "is_expired": None,
            }
        return {
            "provider": provider,
            "connected": True,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "is_expired": token.is_expired(),
            "has_refresh_token": bool(token.refresh_token),
            "updated_at": datetime.now(UTC).isoformat(),
        }

    async def _load_all_credentials(self) -> list[tuple[str, str, OAuthCredentials]]:
        records: list[tuple[str, str, OAuthCredentials]] = []

        if self._db_ready and self._db_engine:
            try:
                async with self._db_engine.begin() as conn:
                    result = await conn.execute(
                        text(
                            """
                            SELECT user_id, provider, payload_encrypted
                            FROM integration_credentials
                            """
                        )
                    )
                    for user_id, provider, encrypted in result.fetchall():
                        payload = self._decrypt_payload(encrypted)
                        records.append((user_id, provider, OAuthCredentials.from_dict(payload)))
                return records
            except Exception as exc:
                logger.warning("Failed to scan integration credentials from DB: %s", exc)

        for key, payload in self._tokens.items():
            user_id, provider = key.split(":", 1)
            records.append((user_id, provider, OAuthCredentials.from_dict(payload)))
        return records

    async def refresh_expiring_tokens(self, refresh_within_minutes: int = 30) -> dict[str, int]:
        """
        Refresh tokens that are expired or within refresh window.
        """
        refreshed = 0
        scanned = 0
        failed = 0

        deadline = datetime.now(UTC) + timedelta(minutes=refresh_within_minutes)
        records = await self._load_all_credentials()

        for user_id, provider_name, creds in records:
            scanned += 1
            provider = self.get_provider(provider_name)
            if not provider or not creds.refresh_token:
                continue

            if creds.expires_at and creds.expires_at > deadline:
                continue

            try:
                refreshed_payload = await provider.refresh_token(creds.refresh_token, metadata=creds.metadata)
                merged = {**refreshed_payload}
                if "refresh_token" not in merged:
                    merged["refresh_token"] = creds.refresh_token
                if "metadata" not in merged:
                    merged["metadata"] = creds.metadata
                await self.save_credentials(user_id, provider_name, merged)
                refreshed += 1
            except Exception as exc:
                logger.warning(
                    "Background token refresh failed for %s/%s: %s",
                    user_id,
                    provider_name,
                    exc,
                )
                failed += 1

        return {"scanned": scanned, "refreshed": refreshed, "failed": failed}
