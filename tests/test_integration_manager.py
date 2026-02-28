from __future__ import annotations

import asyncio
from typing import Any

from app.services.integrations.base import BaseIntegration
from app.services.integrations.manager import IntegrationManager


class DummyIntegration(BaseIntegration):
    @property
    def provider_name(self) -> str:
        return "dummy"

    def get_auth_url(self, state: str = "") -> str:
        return f"https://example.test/oauth?state={state}"

    async def exchange_code(self, code: str, **kwargs: Any) -> dict[str, Any]:
        return {"access_token": f"token_{code}", "refresh_token": "refresh_x", "expires_in": 1}

    async def refresh_token(self, refresh_token: str, **kwargs: Any) -> dict[str, Any]:
        return {"access_token": "token_refreshed", "refresh_token": refresh_token, "expires_in": 3600}

    async def get_user_info(self, access_token: str, **kwargs: Any) -> dict[str, Any]:
        return {"sub": "test-user", "access_token": access_token}

    async def test_connection(self, access_token: str, **kwargs: Any) -> bool:
        return bool(access_token)


def test_integration_manager_memory_roundtrip():
    manager = IntegrationManager(db_engine=None)
    asyncio.run(manager.initialize_storage())
    manager.register(DummyIntegration("id", "secret", "http://localhost/callback"))

    asyncio.run(
        manager.save_credentials(
            user_id="user_1",
            provider="dummy",
            credentials={
                "access_token": "token_1",
                "refresh_token": "refresh_1",
                "expires_in": 1200,
            },
        )
    )

    creds = asyncio.run(manager.get_credentials("user_1", "dummy"))
    assert creds is not None
    assert creds.access_token == "token_1"
    assert manager.storage_mode == "memory_fallback"

    removed = asyncio.run(manager.remove_credentials("user_1", "dummy"))
    assert removed is True
    assert asyncio.run(manager.get_credentials("user_1", "dummy")) is None


def test_refresh_expiring_tokens():
    manager = IntegrationManager(db_engine=None)
    asyncio.run(manager.initialize_storage())
    manager.register(DummyIntegration("id", "secret", "http://localhost/callback"))

    asyncio.run(
        manager.save_credentials(
            user_id="user_2",
            provider="dummy",
            credentials={
                "access_token": "token_old",
                "refresh_token": "refresh_2",
                "expires_in": 1,
            },
        )
    )

    result = asyncio.run(manager.refresh_expiring_tokens(refresh_within_minutes=30))
    assert result["scanned"] == 1
    assert result["refreshed"] == 1
    assert result["failed"] == 0

    refreshed = asyncio.run(manager.get_credentials("user_2", "dummy"))
    assert refreshed is not None
    assert refreshed.access_token == "token_refreshed"
