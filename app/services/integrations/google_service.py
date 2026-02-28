"""
Google Workspace integration.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from app.services.integrations.base import BaseIntegration


class GoogleService(BaseIntegration):
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    GMAIL_LIST_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

    SCOPES = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    @property
    def provider_name(self) -> str:
        return "google"

    def get_auth_url(self, state: str = "") -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": " ".join(self.SCOPES),
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
        )
        return f"{self.AUTH_URL}?{query}"

    async def exchange_code(self, code: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                },
            )
        response.raise_for_status()
        return response.json()

    async def refresh_token(self, refresh_token: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
        response.raise_for_status()
        return response.json()

    async def get_user_info(self, access_token: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        response.raise_for_status()
        return response.json()

    async def test_connection(self, access_token: str, **kwargs: Any) -> bool:
        try:
            await self.get_user_info(access_token)
            return True
        except Exception:
            return False

    async def list_emails(self, access_token: str, query: str = "", max_results: int = 10) -> list[dict]:
        params = {"maxResults": max(1, min(max_results, 50))}
        if query:
            params["q"] = query

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                self.GMAIL_LIST_URL,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        response.raise_for_status()
        payload = response.json()
        messages = payload.get("messages", [])
        return [{"id": m.get("id", ""), "thread_id": m.get("threadId", "")} for m in messages]
