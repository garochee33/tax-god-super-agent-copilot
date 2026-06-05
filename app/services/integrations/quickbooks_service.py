"""
QuickBooks Online integration.
"""

from __future__ import annotations

import base64
from typing import Any
from urllib.parse import urlencode

import httpx

from app.services.integrations.base import BaseIntegration


class QuickBooksService(BaseIntegration):
    AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
    TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    USERINFO_URL = "https://accounts.platform.intuit.com/v1/openid_connect/userinfo"

    SCOPES = [
        "com.intuit.quickbooks.accounting",
        "openid",
        "profile",
        "email",
    ]

    @property
    def provider_name(self) -> str:
        return "quickbooks"

    def _basic_auth_header(self) -> str:
        raw = f"{self.client_id}:{self.client_secret}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    def get_auth_url(self, state: str = "") -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": " ".join(self.SCOPES),
                "state": state,
            }
        )
        return f"{self.AUTH_URL}?{query}"

    async def exchange_code(self, code: str, **kwargs: Any) -> dict[str, Any]:
        realm_id = kwargs.get("realm_id")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                headers={
                    "Authorization": self._basic_auth_header(),
                    "Accept": "application/json",
                },
            )
        response.raise_for_status()
        payload = response.json()
        if realm_id:
            payload["realm_id"] = realm_id
        return payload

    async def refresh_token(self, refresh_token: str, **kwargs: Any) -> dict[str, Any]:
        metadata = kwargs.get("metadata", {})
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={
                    "Authorization": self._basic_auth_header(),
                    "Accept": "application/json",
                },
            )
        response.raise_for_status()
        payload = response.json()
        if metadata.get("realm_id") and not payload.get("realm_id"):
            payload["realm_id"] = metadata["realm_id"]
        return payload

    async def get_user_info(self, access_token: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        response.raise_for_status()
        return response.json()

    async def test_connection(self, access_token: str, **kwargs: Any) -> bool:
        realm_id = kwargs.get("realm_id")
        if not realm_id:
            return bool(access_token)
        try:
            await self.get_company_info(access_token, realm_id)
            return True
        except Exception:
            return False

    async def get_company_info(self, access_token: str, realm_id: str) -> dict[str, Any]:
        url = f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/companyinfo/{realm_id}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                params={"minorversion": 75},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    async def get_profit_loss(self, access_token: str, realm_id: str, year: int) -> dict:
        url = f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/reports/ProfitAndLoss"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                params={
                    "start_date": f"{year}-01-01",
                    "end_date": f"{year}-12-31",
                    "minorversion": 75,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    async def get_balance_sheet(self, access_token: str, realm_id: str, as_of_date: str) -> dict[str, Any]:
        """Balance Sheet report as of a given date (YYYY-MM-DD)."""
        url = f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/reports/BalanceSheet"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                params={
                    "as_of_date": as_of_date,
                    "minorversion": 75,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    async def get_vendors(self, access_token: str, realm_id: str, max_results: int = 100) -> list[dict[str, Any]]:
        """List vendors for 1099 relevance (includes DisplayName, TaxIdentifier if present)."""
        url = f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/query"
        query = f"SELECT * FROM Vendor MAXRESULTS {min(max_results, 1000)}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                params={"query": query, "minorversion": 75},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
        response.raise_for_status()
        data = response.json()
        query_response = data.get("QueryResponse", {})
        raw = query_response.get("Vendor", [])
        vendors = raw if isinstance(raw, list) else ([raw] if raw else [])

        def _mask_tax_id(val: str | None) -> str | None:
            if not val:
                return None
            return f"***{val[-4:]}" if len(val) >= 4 else "****"

        return [
            {
                "Id": v.get("Id"),
                "DisplayName": v.get("DisplayName"),
                "CompanyName": v.get("CompanyName"),
                "TaxIdentifier": _mask_tax_id(v.get("TaxIdentifier")),
            }
            for v in vendors
        ]
