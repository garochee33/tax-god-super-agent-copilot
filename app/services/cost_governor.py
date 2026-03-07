"""
Tax God - Cost Governor Service
The financial brain of the system. Every LLM call passes through here.

Responsibilities:
  - Pre-flight cost estimation before any LLM call
  - Intelligent model selection based on complexity + budget
  - 4-tier cache management (hot / session / knowledge / cold)
  - Per-client and system-wide budget enforcement
  - Real-time usage tracking and analytics
  - Progressive complexity execution (cheapest model first, escalate if needed)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import ModelTier, get_settings
from app.services.swarm_cost_planner import create_swarm_cost_plan

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

class ComplexityLevel(int, Enum):
    TRIVIAL = 1       # tax rate lookup, form instructions
    SIMPLE = 3        # standard deduction questions, filing status
    MODERATE = 5      # Schedule C, rental property calculations
    COMPLEX = 7       # multi-state, entity structuring
    EXPERT = 9        # M&A due diligence, transfer pricing, audit defense
    STRATEGIC = 10    # multi-year planning, complex estate strategies


class RoutingPath(str, Enum):
    CACHE = "cache"
    SINGLE_AGENT = "single_agent"
    OPENCLAW_SWARM = "openclaw_swarm"


class CostGateCode(str, Enum):
    """Trinity-style gate codes (TRINITY_GEMS)."""
    ALLOW = "ALLOW"
    BUDGET_EXCEEDED_PER_TASK = "BUDGET_EXCEEDED_PER_TASK"
    BUDGET_EXCEEDED_SESSION = "BUDGET_EXCEEDED_SESSION"
    BUDGET_EXCEEDED_DAILY = "BUDGET_EXCEEDED_DAILY"
    KILL_SWITCH_TRIGGERED = "KILL_SWITCH_TRIGGERED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    CAPTURE_OVER_BUDGET = "CAPTURE_OVER_BUDGET"


@dataclass
class CostGateResult:
    """Cost gate evaluation result (Trinity GEM)."""
    allowed: bool
    code: CostGateCode
    reason: str
    details: dict[str, Any]


@dataclass
class ModelSpec:
    """Specification for an LLM model."""
    name: str
    provider: str                    # "openai" | "anthropic"
    tier: ModelTier
    input_cost_per_1m: float         # $ per 1M input tokens
    output_cost_per_1m: float        # $ per 1M output tokens
    max_context: int                 # max tokens
    avg_latency_sec: float           # typical response time
    strengths: list[str] = field(default_factory=list)


@dataclass
class CostEstimate:
    """Pre-flight cost estimate for a query."""
    model_name: str
    model_tier: ModelTier
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    estimated_latency_sec: float
    cache_hit: bool = False
    cache_tier: Optional[str] = None
    budget_remaining_usd: float = 0.0
    approved: bool = True
    rejection_reason: Optional[str] = None
    routing_path: str = RoutingPath.SINGLE_AGENT.value
    estimated_swarm_agents: int = 0
    budget_mode: str = "normal"
    downgrade_reason: Optional[str] = None
    gate_code: str = "ALLOW"
    swarm_plan: Optional[dict[str, Any]] = None


@dataclass
class UsageRecord:
    """Tracks actual usage for a single LLM call."""
    request_id: str
    client_id: str
    model_name: str
    model_tier: ModelTier
    input_tokens: int
    output_tokens: int
    actual_cost_usd: float
    latency_sec: float
    cache_hit: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    task_type: str = ""
    complexity: int = 0
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# Model Registry
# ---------------------------------------------------------------------------

MODEL_REGISTRY: dict[str, ModelSpec] = {
    settings.MODEL_GPT4O: ModelSpec(
        name=settings.MODEL_GPT4O,
        provider="openai",
        tier=ModelTier.PREMIUM,
        input_cost_per_1m=settings.PRICING_GPT4O_INPUT,
        output_cost_per_1m=settings.PRICING_GPT4O_OUTPUT,
        max_context=128_000,
        avg_latency_sec=8.0,
        strengths=["strategic_reasoning", "complex_tax", "multi_step", "high_stakes"],
    ),
    settings.MODEL_GPT4O_MINI: ModelSpec(
        name=settings.MODEL_GPT4O_MINI,
        provider="openai",
        tier=ModelTier.BUDGET,
        input_cost_per_1m=settings.PRICING_GPT4O_MINI_INPUT,
        output_cost_per_1m=settings.PRICING_GPT4O_MINI_OUTPUT,
        max_context=128_000,
        avg_latency_sec=3.0,
        strengths=["simple_lookup", "form_instructions", "classification", "extraction"],
    ),
    settings.MODEL_CLAUDE_SONNET: ModelSpec(
        name=settings.MODEL_CLAUDE_SONNET,
        provider="anthropic",
        tier=ModelTier.STANDARD,
        input_cost_per_1m=settings.PRICING_CLAUDE_SONNET_INPUT,
        output_cost_per_1m=settings.PRICING_CLAUDE_SONNET_OUTPUT,
        max_context=200_000,
        avg_latency_sec=5.0,
        strengths=["legal_analysis", "long_document", "nuanced_writing", "research"],
    ),
    settings.MODEL_CLAUDE_HAIKU: ModelSpec(
        name=settings.MODEL_CLAUDE_HAIKU,
        provider="anthropic",
        tier=ModelTier.BUDGET,
        input_cost_per_1m=settings.PRICING_CLAUDE_HAIKU_INPUT,
        output_cost_per_1m=settings.PRICING_CLAUDE_HAIKU_OUTPUT,
        max_context=200_000,
        avg_latency_sec=2.0,
        strengths=["classification", "simple_qa", "extraction", "summarization"],
    ),
}


# ---------------------------------------------------------------------------
# Complexity Analyzer
# ---------------------------------------------------------------------------

# Keywords that signal higher complexity
_COMPLEXITY_SIGNALS: dict[str, int] = {
    # Expert / Strategic (9-10)
    "transfer pricing": 9, "m&a": 9, "merger": 9, "acquisition": 9,
    "estate planning": 9, "generation-skipping": 10, "subpart f": 9,
    "gilti": 9, "controlled foreign": 9, "offer in compromise": 8,
    "innocent spouse": 8, "audit defense": 8, "tax court": 9,
    # Complex (7-8)
    "multi-state": 7, "nexus": 7, "apportionment": 7,
    "entity structuring": 8, "s-corp election": 7, "1031 exchange": 7,
    "cost segregation": 8, "r&d credit": 7, "opportunity zone": 7,
    "qualified business income": 7, "section 199a": 7,
    # Moderate (5-6)
    "schedule c": 5, "self-employment": 5, "rental property": 5,
    "schedule e": 5, "capital gains": 5, "depreciation": 5,
    "section 179": 5, "home office": 5, "estimated tax": 5,
    "crypto": 6, "nft": 6, "defi": 6, "staking": 6,
    # Simple (2-4)
    "standard deduction": 2, "filing status": 2, "w-2": 3,
    "1099": 3, "child tax credit": 3, "education credit": 3,
    "hsa": 3, "ira": 4, "roth": 4, "form 1040": 3,
    "extension": 2, "refund": 2, "withholding": 3,
}


def analyze_complexity(query: str, context: dict[str, Any] | None = None) -> int:
    """
    Score query complexity on a 1-10 scale using keyword signals,
    query length, and optional context hints.
    """
    query_lower = query.lower()
    scores: list[int] = []

    for keyword, score in _COMPLEXITY_SIGNALS.items():
        if keyword in query_lower:
            scores.append(score)

    if not scores:
        word_count = len(query.split())
        if word_count < 15:
            scores.append(3)
        elif word_count < 50:
            scores.append(5)
        else:
            scores.append(6)

    if context:
        if context.get("multi_entity"):
            scores.append(7)
        if context.get("international"):
            scores.append(8)
        if context.get("high_income", False):
            scores.append(6)

    base = max(scores) if scores else 5
    return min(10, max(1, base))


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return max(50, len(text) // 4)


# ---------------------------------------------------------------------------
# Cache Manager
# ---------------------------------------------------------------------------

class CacheManager:
    """
    4-tier cache system:
      Tier 1 - Hot Cache (Redis):     common queries, tax tables     ~0.5s  $0.001
      Tier 2 - Session Cache (Redis): current conversation context   ~1s    $0.001
      Tier 3 - Knowledge Cache (PG):  client history, past returns   ~2-3s  $0.005
      Tier 4 - Cold Storage (S3):     archived docs, multi-year      ~5-10s $0.01
    """

    TIER_HOT = "hot"
    TIER_SESSION = "session"
    TIER_KNOWLEDGE = "knowledge"
    TIER_COLD = "cold"

    def __init__(self, redis_client: aioredis.Redis | None = None):
        self._redis = redis_client
        self._local_cache: dict[str, tuple[Any, float]] = {}  # fallback in-memory

    @staticmethod
    def _cache_key(query: str, client_id: str = "") -> str:
        raw = f"{client_id}:{query.strip().lower()}"
        return f"tg:cache:{hashlib.sha256(raw.encode()).hexdigest()[:24]}"

    async def get(self, query: str, client_id: str = "") -> tuple[Any | None, str | None]:
        """Check all cache tiers. Returns (result, tier_name) or (None, None)."""
        key = self._cache_key(query, client_id)

        # Tier 1: Hot cache (Redis)
        if self._redis:
            try:
                cached = await self._redis.get(f"hot:{key}")
                if cached:
                    logger.debug("Cache HIT tier=hot key=%s", key)
                    return json.loads(cached), self.TIER_HOT
            except Exception:
                pass

        # Tier 2: Session cache (Redis with client prefix)
        if self._redis and client_id:
            try:
                cached = await self._redis.get(f"session:{client_id}:{key}")
                if cached:
                    logger.debug("Cache HIT tier=session key=%s", key)
                    return json.loads(cached), self.TIER_SESSION
            except Exception:
                pass

        # Fallback: in-memory local cache
        if key in self._local_cache:
            value, expires = self._local_cache[key]
            if time.time() < expires:
                logger.debug("Cache HIT tier=local key=%s", key)
                return value, self.TIER_HOT
            else:
                del self._local_cache[key]

        return None, None

    async def set(
        self,
        query: str,
        result: Any,
        client_id: str = "",
        tier: str = TIER_HOT,
        ttl: int | None = None,
    ) -> None:
        """Store result in the specified cache tier."""
        key = self._cache_key(query, client_id)
        ttl = ttl or settings.REDIS_CACHE_TTL
        serialized = json.dumps(result, default=str)

        if self._redis:
            try:
                prefix = f"session:{client_id}:" if tier == self.TIER_SESSION else f"{tier}:"
                await self._redis.setex(f"{prefix}{key}", ttl, serialized)
            except Exception as exc:
                logger.warning("Redis set failed: %s", exc)

        # Always write to local cache as fallback
        self._local_cache[key] = (result, time.time() + ttl)

    async def invalidate(self, query: str, client_id: str = "") -> None:
        key = self._cache_key(query, client_id)
        if self._redis:
            try:
                await self._redis.delete(f"hot:{key}")
                if client_id:
                    await self._redis.delete(f"session:{client_id}:{key}")
            except Exception:
                pass
        self._local_cache.pop(key, None)


# ---------------------------------------------------------------------------
# Budget Tracker
# ---------------------------------------------------------------------------

class BudgetTracker:
    """Per-client and system-wide budget enforcement."""

    def __init__(self, redis_client: aioredis.Redis | None = None):
        self._redis = redis_client
        self._fallback: dict[str, float] = {}

    def _daily_key(self) -> str:
        return f"tg:budget:daily:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    def _client_month_key(self, client_id: str) -> str:
        return f"tg:budget:client:{client_id}:{datetime.now(timezone.utc).strftime('%Y-%m')}"

    async def get_daily_spend(self) -> float:
        if self._redis:
            try:
                val = await self._redis.get(self._daily_key())
                return float(val) if val else 0.0
            except Exception:
                pass
        return self._fallback.get(self._daily_key(), 0.0)

    async def get_client_month_spend(self, client_id: str) -> float:
        key = self._client_month_key(client_id)
        if self._redis:
            try:
                val = await self._redis.get(key)
                return float(val) if val else 0.0
            except Exception:
                pass
        return self._fallback.get(key, 0.0)

    async def record_spend(self, client_id: str, amount: float) -> None:
        daily_key = self._daily_key()
        client_key = self._client_month_key(client_id)

        if self._redis:
            try:
                pipe = self._redis.pipeline()
                pipe.incrbyfloat(daily_key, amount)
                pipe.expire(daily_key, 86400 * 2)
                pipe.incrbyfloat(client_key, amount)
                pipe.expire(client_key, 86400 * 35)
                await pipe.execute()
                return
            except Exception as exc:
                logger.warning("Redis budget tracking failed: %s", exc)

        self._fallback[daily_key] = self._fallback.get(daily_key, 0.0) + amount
        self._fallback[client_key] = self._fallback.get(client_key, 0.0) + amount

    async def check_budget(
        self, client_id: str, estimated_cost: float, high_priority: bool = False
    ) -> tuple[bool, str | None]:
        """Returns (approved, rejection_reason)."""
        daily = await self.get_daily_spend()
        reserve_trigger = settings.COST_HARD_LIMIT_DAILY - settings.COST_EMERGENCY_RESERVE
        projected_daily = daily + estimated_cost

        if daily >= reserve_trigger and not high_priority:
            return (
                False,
                "Emergency reserve mode active. Only high-priority queries are allowed",
            )

        if projected_daily > settings.COST_HARD_LIMIT_DAILY and not high_priority:
            return False, f"Daily system limit ${settings.COST_HARD_LIMIT_DAILY:.2f} exceeded"

        if projected_daily > settings.COST_HARD_LIMIT_DAILY and high_priority:
            return False, "Emergency reserve depleted. High-priority processing paused"

        client_month = await self.get_client_month_spend(client_id)
        if client_month + estimated_cost > settings.COST_SOFT_LIMIT_PER_CLIENT_MONTH:
            return False, f"Client monthly limit ${settings.COST_SOFT_LIMIT_PER_CLIENT_MONTH:.2f} exceeded"

        return True, None

    async def get_budget_mode(self) -> str:
        """
        normal  -> under reserve trigger
        reserve -> only high-priority queries should pass
        hard_limit -> all processing should be blocked
        """
        daily = await self.get_daily_spend()
        reserve_trigger = settings.COST_HARD_LIMIT_DAILY - settings.COST_EMERGENCY_RESERVE
        if daily >= settings.COST_HARD_LIMIT_DAILY:
            return "hard_limit"
        if daily >= reserve_trigger:
            return "reserve"
        return "normal"


# ---------------------------------------------------------------------------
# Cost Governor (Main Class)
# ---------------------------------------------------------------------------

def _rejection_to_gate_code(reason: str | None) -> str:
    """Map rejection_reason to Trinity-style gate code."""
    if not reason:
        return CostGateCode.ALLOW.value
    r = reason.lower()
    if "daily" in r or "system limit" in r:
        return CostGateCode.BUDGET_EXCEEDED_DAILY.value
    if "client monthly" in r or "client limit" in r:
        return CostGateCode.BUDGET_EXCEEDED_SESSION.value
    if "soft limit" in r or "per-query" in r:
        return CostGateCode.BUDGET_EXCEEDED_PER_TASK.value
    if "emergency" in r or "reserve" in r:
        return CostGateCode.BUDGET_EXCEEDED_DAILY.value
    return CostGateCode.ALLOW.value


class CostGovernor:
    """
    Central cost governance service. Every LLM call must pass through:
      1. estimate()   - pre-flight cost + model selection
      2. approve()    - budget check
      3. record()     - post-flight actual cost tracking
    Trinity GEM: gate codes, kill switch, swarm cost plan.
    """

    def __init__(self, redis_client: aioredis.Redis | None = None):
        self.cache = CacheManager(redis_client)
        self.budget = BudgetTracker(redis_client)
        self._usage_log: list[UsageRecord] = []
        self._kill_switch_engaged: bool = False

    def engage_kill_switch(self) -> None:
        """Emergency stop: blocks all dispatches (Trinity GEM)."""
        self._kill_switch_engaged = True
        logger.warning("Cost governor kill switch engaged")

    def disengage_kill_switch(self) -> None:
        """Resume normal operation."""
        self._kill_switch_engaged = False
        logger.info("Cost governor kill switch disengaged")

    @staticmethod
    def _is_high_priority_task(task_type: str, query: str = "") -> bool:
        high_priority_signals = (
            "audit", "audit_defense", "irs notice", "deadline", "penalty", "collections"
        )
        payload = f"{task_type.lower()} {query.lower()}".strip()
        return any(signal in payload for signal in high_priority_signals)

    @staticmethod
    def _estimate_swarm_cost(batch_size: int) -> float:
        batch_size = max(1, batch_size)
        return round(settings.COST_SWARM_BASE + (batch_size * settings.COST_SWARM_PER_ITEM), 6)

    @staticmethod
    def _estimate_swarm_latency(batch_size: int) -> float:
        # Approximation for parallel batch execution: 60-180s typical.
        return float(min(180, max(60, 50 + batch_size * 2)))

    # -- Model Selection -------------------------------------------------------

    def select_model(
        self,
        complexity: int,
        task_type: str = "",
        budget_remaining: float = 100.0,
        prefer_provider: str | None = None,
        requires_vision: bool = False,
    ) -> ModelSpec:
        """
        Intelligent model selection based on:
          - Query complexity (1-10)
          - Budget pressure
          - Task type affinities
          - Provider preference
        """
        # Budget emergency mode: only cheapest models
        if budget_remaining < 1.0:
            return MODEL_REGISTRY[settings.MODEL_GPT4O_MINI]

        # Vision tasks require GPT-4o
        if requires_vision:
            return MODEL_REGISTRY[settings.MODEL_GPT4O]

        # Complexity-based routing
        if complexity >= 8:
            return MODEL_REGISTRY[settings.MODEL_GPT4O]
        elif complexity >= 6:
            # Legal/research tasks prefer Claude for nuanced analysis
            if task_type in ("legal_analysis", "research", "document_review", "memo_writing"):
                return MODEL_REGISTRY[settings.MODEL_CLAUDE_SONNET]
            return MODEL_REGISTRY[settings.MODEL_GPT4O]
        elif complexity >= 4:
            if prefer_provider == "anthropic":
                return MODEL_REGISTRY[settings.MODEL_CLAUDE_SONNET]
            return MODEL_REGISTRY[settings.MODEL_GPT4O_MINI]
        else:
            # Simple queries: cheapest model
            return MODEL_REGISTRY[settings.MODEL_GPT4O_MINI]

    # -- Pre-flight Estimation ------------------------------------------------

    async def estimate(
        self,
        query: str,
        client_id: str = "",
        task_type: str = "",
        context: dict[str, Any] | None = None,
    ) -> CostEstimate:
        """
        Pre-flight cost estimation + cache check + model selection.
        Call this BEFORE making any LLM request.
        """
        context = context or {}
        high_priority = self._is_high_priority_task(task_type, query)

        # Kill switch (Trinity GEM): block all dispatches
        if self._kill_switch_engaged:
            return CostEstimate(
                model_name="",
                model_tier=ModelTier.BUDGET,
                estimated_input_tokens=0,
                estimated_output_tokens=0,
                estimated_cost_usd=0.0,
                estimated_latency_sec=0.0,
                approved=False,
                rejection_reason="Kill switch engaged — all dispatches halted",
                gate_code=CostGateCode.KILL_SWITCH_TRIGGERED.value,
                budget_mode=await self.budget.get_budget_mode(),
            )

        # Step 1: Check cache
        cached, cache_tier = await self.cache.get(query, client_id)
        if cached is not None:
            client_spend = await self.budget.get_client_month_spend(client_id)
            budget_remaining = settings.COST_SOFT_LIMIT_PER_CLIENT_MONTH - client_spend
            return CostEstimate(
                model_name="cache",
                model_tier=ModelTier.CACHE,
                estimated_input_tokens=0,
                estimated_output_tokens=0,
                estimated_cost_usd=0.001,
                estimated_latency_sec=0.5,
                cache_hit=True,
                cache_tier=cache_tier,
                budget_remaining_usd=round(budget_remaining, 2),
                approved=True,
                routing_path=RoutingPath.CACHE.value,
                budget_mode=await self.budget.get_budget_mode(),
                gate_code=CostGateCode.ALLOW.value,
            )

        # Step 2: Analyze complexity
        complexity = analyze_complexity(query, context)

        # Step 3: Check budget
        client_spend = await self.budget.get_client_month_spend(client_id)
        budget_remaining = settings.COST_SOFT_LIMIT_PER_CLIENT_MONTH - client_spend
        budget_mode = await self.budget.get_budget_mode()

        # Step 4: Swarm routing lane for highly parallelizable workloads.
        parallelizable_score = int(context.get("parallelizable_score", 0) or 0)
        batch_size = int(context.get("batch_size", 1) or 1)

        if (
            parallelizable_score >= settings.SWARM_PARALLEL_THRESHOLD
            and batch_size >= settings.SWARM_MIN_BATCH_SIZE
        ):
            # Trinity GEM: SwarmCostPlanner for non-linear swarm cost
            plan = create_swarm_cost_plan(
                worker_count=max(1, batch_size),
                delegation_depth=1,
                expected_tool_calls=2,
                historical_variance=0.2,
                model_tier="standard",
            )
            swarm_cost = plan.total_estimate
            approved, reason = await self.budget.check_budget(
                client_id=client_id, estimated_cost=swarm_cost, high_priority=high_priority
            )
            swarm_plan_dict = {
                "planner_cost": plan.planner_cost,
                "worker_count": plan.worker_count,
                "worker_cost_estimate": plan.worker_cost_estimate,
                "swarm_multiplier": plan.swarm_multiplier,
                "synthesis_cost": plan.synthesis_cost,
                "tool_execution_cost": plan.tool_execution_cost,
                "retry_reserve": plan.retry_reserve,
                "total_estimate": plan.total_estimate,
                "quality_tier": plan.quality_tier,
            }
            gate = _rejection_to_gate_code(reason) if not approved else CostGateCode.ALLOW.value
            return CostEstimate(
                model_name="openclaw_swarm",
                model_tier=ModelTier.BUDGET,
                estimated_input_tokens=estimate_tokens(query),
                estimated_output_tokens=min(estimate_tokens(query) * 2, 4096),
                estimated_cost_usd=swarm_cost,
                estimated_latency_sec=self._estimate_swarm_latency(batch_size),
                budget_remaining_usd=round(budget_remaining, 2),
                approved=approved,
                rejection_reason=reason,
                routing_path=RoutingPath.OPENCLAW_SWARM.value,
                estimated_swarm_agents=min(max(batch_size, 1), 500),
                budget_mode=budget_mode,
                gate_code=gate,
                swarm_plan=swarm_plan_dict,
            )

        # Step 5: Select model
        budget_remaining_for_selection = budget_remaining
        if budget_mode in ("reserve", "hard_limit") and not high_priority:
            budget_remaining_for_selection = 0.0

        model = self.select_model(
            complexity=complexity,
            task_type=task_type,
            budget_remaining=budget_remaining_for_selection,
        )

        # Step 6: Estimate cost
        est_input = estimate_tokens(query) + estimate_tokens(json.dumps(context))
        est_output = min(est_input * 2, 4096)  # rough: output ≈ 2x input, capped

        cost = (
            (est_input / 1_000_000) * model.input_cost_per_1m
            + (est_output / 1_000_000) * model.output_cost_per_1m
        )

        # Step 7: Budget approval
        approved, reason = await self.budget.check_budget(
            client_id=client_id, estimated_cost=cost, high_priority=high_priority
        )

        # If over soft limit for single query, try downgrading model
        downgrade_reason = None
        if cost > settings.COST_SOFT_LIMIT_PER_QUERY and model.tier != ModelTier.BUDGET:
            cheaper = MODEL_REGISTRY[settings.MODEL_GPT4O_MINI]
            cost = (
                (est_input / 1_000_000) * cheaper.input_cost_per_1m
                + (est_output / 1_000_000) * cheaper.output_cost_per_1m
            )
            model = cheaper
            downgrade_reason = "Per-query soft limit enforced"
            logger.info("Downgraded model to %s to stay within query soft limit", cheaper.name)

        if complexity >= 8 and cost > settings.COST_SOFT_LIMIT_PER_COMPLEX_TASK:
            downgrade_reason = (
                f"Complex-task soft limit (${settings.COST_SOFT_LIMIT_PER_COMPLEX_TASK:.2f}) exceeded"
            )

        gate_code = (
            _rejection_to_gate_code(reason) if not approved else CostGateCode.ALLOW.value
        )
        return CostEstimate(
            model_name=model.name,
            model_tier=model.tier,
            estimated_input_tokens=est_input,
            estimated_output_tokens=est_output,
            estimated_cost_usd=round(cost, 6),
            estimated_latency_sec=model.avg_latency_sec,
            budget_remaining_usd=round(budget_remaining, 2),
            approved=approved,
            rejection_reason=reason,
            routing_path=RoutingPath.SINGLE_AGENT.value,
            budget_mode=budget_mode,
            downgrade_reason=downgrade_reason,
            gate_code=gate_code,
        )

    # -- Post-flight Recording ------------------------------------------------

    async def record(self, usage: UsageRecord) -> None:
        """Record actual usage after an LLM call completes."""
        await self.budget.record_spend(usage.client_id, usage.actual_cost_usd)
        self._usage_log.append(usage)
        if len(self._usage_log) > 10_000:
            self._usage_log = self._usage_log[-5_000:]
        logger.info(
            "LLM call: model=%s cost=$%.4f tokens_in=%d tokens_out=%d latency=%.1fs",
            usage.model_name,
            usage.actual_cost_usd,
            usage.input_tokens,
            usage.output_tokens,
            usage.latency_sec,
        )

    # -- Analytics ------------------------------------------------------------

    async def get_analytics(self, client_id: str | None = None) -> dict[str, Any]:
        """Return usage analytics summary."""
        records = self._usage_log
        if client_id:
            records = [r for r in records if r.client_id == client_id]

        if not records:
            return {"total_queries": 0, "total_cost": 0.0}

        total_cost = sum(r.actual_cost_usd for r in records)
        cache_hits = sum(1 for r in records if r.cache_hit)

        return {
            "total_queries": len(records),
            "total_cost": round(total_cost, 4),
            "avg_cost_per_query": round(total_cost / len(records), 6),
            "cache_hit_rate": round(cache_hits / len(records), 3),
            "model_distribution": _model_distribution(records),
            "daily_spend": await self.budget.get_daily_spend(),
            "budget_mode": await self.budget.get_budget_mode(),
            "client_month_spend": (
                await self.budget.get_client_month_spend(client_id) if client_id else None
            ),
        }

    def calculate_actual_cost(
        self, model_name: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate actual cost from real token counts."""
        spec = MODEL_REGISTRY.get(model_name)
        if not spec:
            return 0.0
        return round(
            (input_tokens / 1_000_000) * spec.input_cost_per_1m
            + (output_tokens / 1_000_000) * spec.output_cost_per_1m,
            6,
        )


def _model_distribution(records: list[UsageRecord]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for r in records:
        dist[r.model_name] = dist.get(r.model_name, 0) + 1
    return dist
