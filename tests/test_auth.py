"""
Tax God — Auth Endpoint Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "StrongP@ss1",
        "full_name": "New User",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "client"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "StrongP@ss1"}
    await client.post("/api/v1/auth/register", json=payload)
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "short",
    })
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "StrongP@ss1",
    })
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com", "password": "StrongP@ss1",
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "password": "StrongP@ss1",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com", "password": "StrongP@ss1",
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com", "password": "WrongPassword1",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={
        "email": "ghost@example.com", "password": "Whatever123",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com", "password": "StrongP@ss1",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "refresh@example.com", "password": "StrongP@ss1",
    })
    refresh_token = login.json()["refresh_token"]

    res = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    res = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid.token.here",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "testuser@taxgod.dev"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient):
    res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_dev_token(client: AsyncClient):
    res = await client.post("/api/v1/auth/dev-token")
    assert res.status_code == 200
    assert "access_token" in res.json()
