"""Tax God — Receipts Endpoint Tests"""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_receipt_success(client: AsyncClient, auth_headers: dict):
    """Upload a valid PNG receipt — AI extraction will return empty (no API key)."""
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    res = await client.post(
        "/api/v1/receipts/upload",
        headers=auth_headers,
        files={"file": ("receipt.png", io.BytesIO(fake_png), "image/png")},
    )
    assert res.status_code == 201
    data = res.json()
    assert "receipt_url" in data
    assert "extraction" in data


@pytest.mark.asyncio
async def test_upload_receipt_unsupported_type(client: AsyncClient, auth_headers: dict):
    """Upload a file with unsupported MIME type should return 400."""
    res = await client.post(
        "/api/v1/receipts/upload",
        headers=auth_headers,
        files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_upload_receipt_unauthenticated(client: AsyncClient):
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    res = await client.post(
        "/api/v1/receipts/upload",
        files={"file": ("receipt.png", io.BytesIO(fake_png), "image/png")},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_extract_from_existing_not_found(client: AsyncClient, auth_headers: dict):
    """Extract from non-existent expense returns 404."""
    res = await client.post(
        "/api/v1/receipts/extract",
        headers=auth_headers,
        params={"expense_id": "nonexistent"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_scan_and_create_success(client: AsyncClient, auth_headers: dict):
    """Scan and create with valid image should create expense."""
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    res = await client.post(
        "/api/v1/receipts/scan-and-create",
        headers=auth_headers,
        files={"file": ("receipt.png", io.BytesIO(fake_png), "image/png")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "expense_id" in data
    assert "receipt_url" in data


@pytest.mark.asyncio
async def test_scan_and_create_unsupported_type(client: AsyncClient, auth_headers: dict):
    res = await client.post(
        "/api/v1/receipts/scan-and-create",
        headers=auth_headers,
        files={"file": ("bad.exe", io.BytesIO(b"\x00"), "application/octet-stream")},
    )
    assert res.status_code == 400
