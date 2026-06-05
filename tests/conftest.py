"""
Tax God — Test Configuration & Fixtures
Uses async SQLite in-memory DB for fast isolated tests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Must set env BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "false"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient

from app.core.database import Base, engine, async_session_factory
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
from app.models.client import Client
from app.api.deps import get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db():
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def db_session():
    """Provide a test DB session."""
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """Async HTTP test client with DB override."""
    from app.main import app
    app.dependency_overrides[get_db] = _override_get_db

    # Disable rate limiting for tests
    from app.middleware.security import RateLimitMiddleware
    _orig_is_rate_limited = RateLimitMiddleware._is_rate_limited
    RateLimitMiddleware._is_rate_limited = lambda self, key, limit: False

    # Mock external services on app.state
    app.state.ai_orchestrator = MagicMock()
    app.state.citation_engine = MagicMock()
    app.state.citation_engine.enrich_response = MagicMock(return_value={"verified_citations": [], "supplemental_citations": []})
    app.state.citation_engine.search = MagicMock(return_value=[])
    app.state.parallel_processor = MagicMock()
    _mock_job = MagicMock(job_id="test-job-1")
    app.state.parallel_processor.batch_process_documents = AsyncMock(return_value=_mock_job)
    app.state.parallel_processor.multi_state_research = AsyncMock(return_value=_mock_job)
    app.state.parallel_processor.run_scenario_analysis = AsyncMock(return_value=_mock_job)
    app.state.parallel_processor.get_job_results = MagicMock(return_value={"job_id": "test-job-1", "status": "completed", "results": []})
    app.state.cost_governor = MagicMock()
    app.state.cost_governor.check_budget = AsyncMock(return_value={"allowed": True})
    app.state.cost_governor.get_dashboard = MagicMock(return_value={})
    app.state.cost_governor.get_analytics = AsyncMock(return_value={"total_queries": 0, "total_cost_usd": 0})
    app.state.cost_governor.estimate = AsyncMock(return_value=MagicMock(
        model_name="gpt-4o-mini", model_tier=MagicMock(value="budget"),
        routing_path="direct", estimated_swarm_agents=1,
        estimated_cost_usd=0.003, estimated_latency_sec=1.2,
        cache_hit=False, cache_tier=None, budget_mode="normal",
        budget_remaining_usd=99.0, approved=True,
        rejection_reason=None, downgrade_reason=None, gate_code="ALLOW",
        swarm_plan=None,
    ))
    app.state.cost_governor.engage_kill_switch = MagicMock()
    app.state.cost_governor.disengage_kill_switch = MagicMock()
    app.state.cost_governor.budget = MagicMock()
    app.state.cost_governor.budget.get_client_month_spend = AsyncMock(return_value=12.50)
    app.state.cost_governor.budget.get_daily_spend = AsyncMock(return_value=3.20)
    app.state.cost_governor.budget.get_budget_mode = AsyncMock(return_value="normal")
    app.state.circuit_breaker = MagicMock()
    app.state.circuit_breaker.get_status = MagicMock(return_value={"config": {}, "agents": {}, "tripped_agents": [], "healthy_agents": []})
    app.state.circuit_breaker.reset_agent = MagicMock(return_value=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    RateLimitMiddleware._is_rate_limited = _orig_is_rate_limited


@pytest_asyncio.fixture
async def test_user(db_session) -> User:
    """Create a test user and return it."""
    user = User(
        email="testuser@taxgod.dev",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test User",
        role=UserRole.CLIENT.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session) -> User:
    """Create an admin user."""
    user = User(
        email="admin@taxgod.dev",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin Zeus",
        role=UserRole.ADMIN.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Get auth headers for the test user."""
    token = create_access_token(test_user.id, extra={"role": test_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(admin_user: User) -> dict[str, str]:
    """Get auth headers for the admin user."""
    token = create_access_token(admin_user.id, extra={"role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}
