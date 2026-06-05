"""
Tax God v3.0 - FastAPI Application Entry Point
Multi-agent tax, legal & financial AI co-pilot.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, Histogram, generate_latest

import app.models  # noqa: F401 — register all models with Base.metadata
from app.core.config import Environment, get_settings
from app.core.database import Base, check_database_health
from app.core.database import engine as db_engine
from app.middleware.audit_middleware import AuditMiddleware
from app.middleware.security import RateLimitMiddleware, RequestIdMiddleware, SecurityHeadersMiddleware
from app.services.advanced_orchestrator import AdvancedTaxOrchestrator
from app.services.agent_gabriel import AgentGabriel
from app.services.ai_service import AIOrchestrator
from app.services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.services.citation_engine import CitationEngine
from app.services.cost_governor import CostGovernor
from app.services.integrations.google_service import GoogleService
from app.services.integrations.manager import IntegrationManager
from app.services.integrations.quickbooks_service import QuickBooksService
from app.services.parallel_processor import ParallelProcessor
from app.services.tax_writer import TaxWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


def _get_or_create_metric(cls, name, *args, **kwargs):
    """Get existing metric or create new one (prevents duplicate registration in tests)."""
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return cls(name, *args, **kwargs)


HTTP_REQUESTS_TOTAL = _get_or_create_metric(
    Counter,
    "taxgod_http_requests_total",
    "Total HTTP requests handled by Tax God API",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_LATENCY_SECONDS = _get_or_create_metric(
    Histogram,
    "taxgod_http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)
SERVICE_UP = _get_or_create_metric(Gauge, "taxgod_service_up", "Tax God service process status")


# ---------------------------------------------------------------------------
# Application Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and teardown shared services."""
    logger.info("Starting Tax God v%s [%s]", settings.APP_VERSION, settings.ENVIRONMENT.value)
    SERVICE_UP.set(1)

    # Auto-create tables (SQLite local dev)
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Connect Redis (graceful fallback if unavailable)
    redis_client = None
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connected: %s", settings.REDIS_URL)
    except Exception as exc:
        logger.warning("Redis unavailable (%s) - using in-memory fallback", exc)
        redis_client = None

    # Initialize service graph
    cost_governor = CostGovernor(redis_client)
    citation_engine = CitationEngine()
    ai_orchestrator = AIOrchestrator(cost_governor)
    advanced_orchestrator = AdvancedTaxOrchestrator(cost_governor)
    agent_gabriel = AgentGabriel(ai_orchestrator, citation_engine)
    tax_writer = TaxWriter(ai_orchestrator, citation_engine)
    parallel_processor = ParallelProcessor()

    # Initialize Integrations
    integration_manager = IntegrationManager(db_engine=db_engine)
    await integration_manager.initialize_storage()
    integration_manager.register(
        GoogleService(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )
    )
    integration_manager.register(
        QuickBooksService(
            client_id=settings.QUICKBOOKS_CLIENT_ID,
            client_secret=settings.QUICKBOOKS_CLIENT_SECRET,
            redirect_uri=settings.QUICKBOOKS_REDIRECT_URI,
        )
    )

    # Circuit breaker for external APIs (Trinity GEM)
    circuit_breaker = CircuitBreaker(
        CircuitBreakerConfig(
            error_threshold_percent=50.0,
            window_sec=300.0,
            pause_duration_sec=300.0,
            min_calls_before_trip=4,
            half_open_max_probes=2,
        )
    )

    # Attach services to app state for dependency injection
    app.state.redis = redis_client
    app.state.cost_governor = cost_governor
    app.state.circuit_breaker = circuit_breaker
    app.state.citation_engine = citation_engine
    app.state.ai_orchestrator = ai_orchestrator
    app.state.advanced_orchestrator = advanced_orchestrator
    app.state.agent_gabriel = agent_gabriel
    app.state.tax_writer = tax_writer
    app.state.parallel_processor = parallel_processor
    app.state.integration_manager = integration_manager

    # Background task: daily recurring invoice processing
    async def _recurring_invoice_loop():
        from app.core.database import async_session_factory
        from app.services.invoice_scheduler import process_recurring_invoices

        while True:
            try:
                async with async_session_factory() as session:
                    await process_recurring_invoices(session)
            except Exception as exc:
                logger.error("Recurring invoice task error: %s", exc)
            await asyncio.sleep(86400)  # 24 hours

    asyncio.create_task(_recurring_invoice_loop())

    logger.info("All services initialized. Tax God is ready.")
    yield

    # Shutdown
    if redis_client:
        await redis_client.aclose()
    await db_engine.dispose()
    SERVICE_UP.set(0)
    logger.info("Tax God shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Tax God API",
    description="Multi-agent AI tax, legal & financial co-pilot",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
)

app.add_middleware(RequestIdMiddleware)
if settings.is_production:
    app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=120 if not settings.is_production else 60,
    auth_requests_per_minute=10,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.ALLOWED_ORIGINS)
    if settings.is_production
    else list(
        {
            *settings.ALLOWED_ORIGINS,
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        }
    ),
    allow_origin_regex=r"chrome-extension://.*" if not settings.is_production else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(AuditMiddleware)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    path = request.url.path
    route = request.scope.get("route")
    if route:
        path = route.path
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - start
        HTTP_REQUESTS_TOTAL.labels(
            request.method,
            path,
            str(status_code),
        ).inc()
        HTTP_REQUEST_LATENCY_SECONDS.labels(request.method, path).observe(elapsed)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "services": {
            "cost_governor": "active",
            "ai_orchestrator": "active",
            "advanced_orchestrator": "active",
            "citation_engine": "active",
            "agent_gabriel": "active",
            "tax_writer": "active",
            "parallel_processor": "active",
        },
    }


@app.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics. Requires valid METRICS_TOKEN in production."""
    if settings.is_production and settings.METRICS_TOKEN:
        token = request.headers.get("Authorization", "")
        expected = f"Bearer {settings.METRICS_TOKEN}"
        if token != expected:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health/detailed")
async def health_detailed(request: Request):
    if settings.ENVIRONMENT != Environment.DEV:
        if not request.headers.get("Authorization"):
            return JSONResponse(status_code=401, content={"detail": "Authentication required"})

    redis_client = request.app.state.redis
    integration_manager = request.app.state.integration_manager

    redis_ok = False
    if redis_client:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    db_ok = await check_database_health(db_engine)
    configured_providers = [
        p
        for p in integration_manager.list_provider_names()
        if integration_manager.get_provider(p) and integration_manager.get_provider(p).is_configured
    ]
    status = "healthy" if (db_ok and redis_ok) else "degraded"
    checkpoints: dict[str, Any] = {}
    if redis_ok and redis_client:
        for key, label in (
            ("tg:ops:token_refresh:last", "token_refresh"),
            ("tg:ops:budget_guard:last", "budget_guard"),
            ("tg:ops:regulatory_scan:last", "regulatory_scan"),
        ):
            try:
                raw = await redis_client.get(key)
                checkpoints[label] = json.loads(raw) if raw else None
            except Exception:
                checkpoints[label] = None

    return {
        "status": status,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "checks": {
            "database": {"ok": db_ok},
            "redis": {"ok": redis_ok},
            "integration_storage": {
                "ok": integration_manager.storage_ready,
                "mode": integration_manager.storage_mode,
            },
            "integrations": {
                "registered_providers": integration_manager.list_provider_names(),
                "configured_providers": configured_providers,
            },
            "ops_checkpoints": checkpoints,
        },
    }


@app.get("/readiness")
async def readiness_check(request: Request):
    redis_client = request.app.state.redis
    integration_manager = request.app.state.integration_manager

    redis_ok = False
    if redis_client:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    db_ok = await check_database_health(db_engine)
    ready = db_ok and bool(redis_client) and redis_ok and integration_manager is not None

    payload = {
        "ready": ready,
        "database_ok": db_ok,
        "redis_ok": redis_ok,
        "integration_manager_ok": integration_manager is not None,
    }
    if not ready:
        return JSONResponse(status_code=503, content=payload)
    return payload


# ---------------------------------------------------------------------------
# Register API Routers
# ---------------------------------------------------------------------------

from app.api.v1.endpoints import (  # noqa: E402
    accounts,
    advanced,
    analytics,
    audit,
    audit_trail,
    auth,
    bank_feeds,
    billing,
    businesses,
    chart_of_accounts,
    chat,
    client_portal,
    clients,
    dev_tracking,
    doc_generation,
    documents,
    expenses,
    integrations,
    invoices,
    notes,
    payments,
    profile,
    projects,
    receipts,
    recurring,
    spreadsheets,
    tax_estimates,
    tax_planning,
    teams,
    time_entries,
    transactions,
    vendors,
)
from app.api.v1.endpoints import logs as logs_ep  # noqa: E402
from app.api.v1.endpoints import settings as settings_ep  # noqa: E402
from app.api.v1.endpoints import settings_advanced as settings_adv  # noqa: E402

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(bank_feeds.router, prefix="/api/v1/bank-feeds", tags=["Bank Feeds"])
app.include_router(dev_tracking.router, prefix="/api/v1/dev", tags=["Dev Tracking"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(logs_ep.router, prefix="/api/v1/logs", tags=["Logs & Knowledge Base"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Agent Gabriel"])
app.include_router(audit_trail.router, prefix="/api/v1/audit-trail", tags=["Audit Trail"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["Integrations"])
app.include_router(advanced.router, prefix="/api/v1/advanced", tags=["Advanced Tax Processing"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["Clients (Agora)"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["Profile"])
app.include_router(settings_ep.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(settings_adv.router, prefix="/api/v1/settings", tags=["Settings Advanced"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(recurring.router, prefix="/api/v1/recurring", tags=["Recurring Invoices"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Stripe Payments"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(spreadsheets.router, prefix="/api/v1/spreadsheets", tags=["Spreadsheets"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["Notes"])
app.include_router(businesses.router, prefix="/api/v1/businesses", tags=["Businesses"])
app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(receipts.router, prefix="/api/v1/receipts", tags=["Receipt Scanning"])
app.include_router(time_entries.router, prefix="/api/v1/time-entries", tags=["Time Entries"])
app.include_router(vendors.router, prefix="/api/v1/vendors", tags=["Vendors"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(chart_of_accounts.router, prefix="/api/v1/ledger", tags=["Chart of Accounts"])
app.include_router(tax_estimates.router, prefix="/api/v1/estimates", tags=["Tax Estimates"])
app.include_router(tax_planning.router, prefix="/api/v1/tax-planning", tags=["Tax Planning"])
app.include_router(client_portal.router, prefix="/api/v1/portal", tags=["Client Portal"])
app.include_router(doc_generation.router, prefix="/api/v1/documents", tags=["Document Generation"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["Teams"])


# ---------------------------------------------------------------------------
# Static Files & Frontend
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
async def serve_spa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
