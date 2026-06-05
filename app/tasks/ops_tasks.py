"""
Operational background tasks for Tax God.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.database import engine as db_engine
from app.services.cost_governor import CostGovernor
from app.services.integrations.google_service import GoogleService
from app.services.integrations.manager import IntegrationManager
from app.services.integrations.quickbooks_service import QuickBooksService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def _run_async(coro):
    return asyncio.run(coro)


async def _build_integration_manager() -> IntegrationManager:
    manager = IntegrationManager(db_engine=db_engine)
    await manager.initialize_storage()
    manager.register(
        GoogleService(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )
    )
    manager.register(
        QuickBooksService(
            client_id=settings.QUICKBOOKS_CLIENT_ID,
            client_secret=settings.QUICKBOOKS_CLIENT_SECRET,
            redirect_uri=settings.QUICKBOOKS_REDIRECT_URI,
        )
    )
    return manager


async def _write_ops_checkpoint(redis_client: aioredis.Redis | None, key: str, payload: dict[str, Any]) -> None:
    if not redis_client:
        return
    try:
        await redis_client.setex(key, 86400, json.dumps(payload, default=str))
    except Exception as exc:
        logger.warning("Failed writing ops checkpoint %s: %s", key, exc)


@celery_app.task(name="app.tasks.ops_tasks.refresh_integration_tokens")
def refresh_integration_tokens() -> dict[str, Any]:
    """
    Refresh OAuth tokens near expiry to avoid interactive reconnect flows.
    """

    async def _run() -> dict[str, Any]:
        manager = await _build_integration_manager()
        result = await manager.refresh_expiring_tokens(refresh_within_minutes=30)
        payload = {
            "task": "refresh_integration_tokens",
            "timestamp": datetime.now(UTC).isoformat(),
            **result,
            "storage_mode": manager.storage_mode,
        }
        redis_client = None
        try:
            redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await _write_ops_checkpoint(redis_client, "tg:ops:token_refresh:last", payload)
        finally:
            if redis_client:
                await redis_client.aclose()
        return payload

    return _run_async(_run())


@celery_app.task(name="app.tasks.ops_tasks.budget_guard_watchdog")
def budget_guard_watchdog() -> dict[str, Any]:
    """
    Monitor cost usage and expose current budget mode for alerting.
    """

    async def _run() -> dict[str, Any]:
        redis_client = None
        try:
            redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            governor = CostGovernor(redis_client)
            daily_spend = await governor.budget.get_daily_spend()
            budget_mode = await governor.budget.get_budget_mode()
            reserve_trigger = settings.COST_HARD_LIMIT_DAILY - settings.COST_EMERGENCY_RESERVE
            payload = {
                "task": "budget_guard_watchdog",
                "timestamp": datetime.now(UTC).isoformat(),
                "daily_spend": round(daily_spend, 6),
                "hard_limit": settings.COST_HARD_LIMIT_DAILY,
                "reserve_trigger": reserve_trigger,
                "budget_mode": budget_mode,
                "alert": budget_mode in {"reserve", "hard_limit"},
            }
            await _write_ops_checkpoint(redis_client, "tg:ops:budget_guard:last", payload)
            return payload
        finally:
            if redis_client:
                await redis_client.aclose()

    return _run_async(_run())


@celery_app.task(name="app.tasks.ops_tasks.regulatory_scan_heartbeat")
def regulatory_scan_heartbeat() -> dict[str, Any]:
    """
    Scheduler heartbeat for regulatory monitoring lane.
    """

    async def _run() -> dict[str, Any]:
        payload = {
            "task": "regulatory_scan_heartbeat",
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "ok",
            "note": "Heartbeat active. Plug IRS/state scan workers into this lane.",
        }
        redis_client = None
        try:
            redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await _write_ops_checkpoint(redis_client, "tg:ops:regulatory_scan:last", payload)
        finally:
            if redis_client:
                await redis_client.aclose()
        return payload

    return _run_async(_run())
