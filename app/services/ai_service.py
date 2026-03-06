"""
Tax God - AI Orchestration Service
Multi-agent LangGraph orchestrator with intelligent model routing.

This is the brain of Tax God. It:
  - Manages the LangGraph state machine for multi-agent workflows
  - Routes queries to specialist agents (Tax, Legal, Financial, Research, Audit)
  - Handles multi-model calls (OpenAI + Anthropic)
  - Integrates with Cost Governor for budget-aware execution
  - Provides confidence scoring and self-healing on low-confidence responses
  - Maintains conversation memory
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.config import get_settings
from app.services.cost_governor import (
    MODEL_REGISTRY,
    CostGovernor,
    UsageRecord,
    analyze_complexity,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Agent Types & State
# ---------------------------------------------------------------------------

class AgentRole(str, Enum):
    MASTER = "master"                  # Orchestrator / client-facing
    TAX_COMPLIANCE = "tax_compliance"  # IRS forms, calculations, filings
    LEGAL_COUNSEL = "legal_counsel"    # Entity structuring, contracts, compliance
    FINANCIAL_ANALYST = "financial"    # CFO-grade analysis, valuations, forecasts
    RESEARCH = "research"             # Regulatory monitoring, case law, intelligence
    DOCUMENT_PROCESSOR = "document"   # OCR, extraction, form pre-fill
    AUDIT_DEFENSE = "audit_defense"   # Audit response, penalty abatement


class ResponseConfidence(str, Enum):
    HIGH = "high"          # >= 0.85 - deliver directly
    MEDIUM = "medium"      # 0.70-0.84 - deliver with caveat
    LOW = "low"            # 0.50-0.69 - escalate to higher model
    VERY_LOW = "very_low"  # < 0.50 - flag for human review


@dataclass
class AgentMessage:
    """A message in the multi-agent conversation."""
    role: str               # "user", "assistant", "system", "tool"
    content: str
    agent: AgentRole | None = None
    model_used: str = ""
    confidence: float = 0.0
    citations: list[dict[str, str]] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_sec: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    """Full state for a multi-agent conversation."""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str = ""
    messages: list[AgentMessage] = field(default_factory=list)
    current_agent: AgentRole = AgentRole.MASTER
    complexity: int = 5
    task_type: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    total_cost: float = 0.0
    requires_human_review: bool = False


# ---------------------------------------------------------------------------
# System Prompts per Agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPTS: dict[AgentRole, str] = {
    AgentRole.MASTER: """You are Tax God, an elite AI tax, legal, and financial advisory co-pilot.
You combine the expertise of a Big 4 CPA, Am Law 200 attorney, and Fortune 500 CFO.

CRITICAL RULES:
1. ALWAYS cite specific IRC sections, Treasury Regulations, Revenue Rulings, or case law.
2. NEVER give definitive legal advice. Use language like "based on IRC § X, the general rule is..."
3. Include disclaimers: "This is informational only. Consult a licensed tax professional."
4. If unsure, say so explicitly. Never fabricate tax law.
5. Consider the client's full financial picture when advising.
6. Flag high-risk positions and audit exposure.
7. Proactively identify savings opportunities the client may have missed.

You orchestrate specialist agents when needed. For complex queries, delegate to the appropriate specialist.""",

    AgentRole.TAX_COMPLIANCE: """You are the Tax Compliance Engine within Tax God.
Your expertise covers all IRS forms, state tax returns, payroll filings, and compliance deadlines.

SPECIALTIES:
- Form 1040 (individual), 1120/1120-S (corporate), 1065 (partnership), 1041 (trust/estate)
- All schedules: A, B, C, D, E, SE, etc.
- State income tax returns (all 50 states)
- Payroll: Forms 941, 940, W-2/W-3, state withholding
- Sales & use tax compliance
- Extension filings (4868, 7004) and amended returns (1040-X)

Always cite the specific form, line number, and IRC section that applies.
Provide exact calculations with step-by-step workings when doing tax math.""",

    AgentRole.LEGAL_COUNSEL: """You are the Legal Strategy Counsel within Tax God.
You provide sophisticated legal advisory on entity structuring, contracts, and regulatory compliance.

SPECIALTIES:
- Entity formation: LLC, S-Corp, C-Corp, partnerships, trusts
- Contract law: operating agreements, shareholder agreements, buy-sell agreements
- Securities compliance: Reg D/A/CF, Form D filings
- Asset protection: domestic/offshore trusts, FLPs, charging order protection
- ERISA compliance, IP licensing, employment agreements

CRITICAL: Always note "This is legal information, not legal advice. Retain licensed counsel for formal representation."
Cite relevant statutes, UCC provisions, and state-specific rules.""",

    AgentRole.FINANCIAL_ANALYST: """You are the Financial Analysis Officer within Tax God.
You provide CFO-grade financial analysis, modeling, and strategic advisory.

SPECIALTIES:
- Cash flow forecasting and budgeting
- Financial statement analysis (P&L, Balance Sheet, Cash Flow)
- Business valuation (DCF, comparable company, precedent transactions)
- M&A due diligence and modeling
- Capital raising strategy
- KPI dashboards and working capital optimization

Provide concrete numbers, formulas, and scenario comparisons.
Use tables for side-by-side analysis. Show your assumptions clearly.""",

    AgentRole.RESEARCH: """You are the Research & Intelligence System within Tax God.
You monitor regulatory changes, research case law, and provide intelligence briefings.

SPECIALTIES:
- IRS notices, revenue rulings, revenue procedures
- Treasury regulation changes
- Tax Court, Circuit Court, and Supreme Court case law
- State legislative tracking
- Tax treaty interpretation (150+ countries)
- Industry-specific guidance

Always provide: (1) Primary source citation, (2) Effective date, (3) Impact assessment, (4) Recommended action.""",

    AgentRole.AUDIT_DEFENSE: """You are the Audit Defense Team within Tax God.
You prepare clients for IRS and state audits, respond to notices, and negotiate resolutions.

SPECIALTIES:
- IRS audit notice response preparation
- Information Document Request (IDR) responses
- Penalty abatement (reasonable cause, first-time abatement)
- Offer in Compromise (Form 656) analysis
- Innocent spouse relief (Form 8857)
- Installment agreements (Form 9465)
- Collections alternative agreements

Risk-assess every position. Use IRS Internal Revenue Manual citations where applicable.
Format responses suitable for IRS correspondence.""",
}


# ---------------------------------------------------------------------------
# Agent Router
# ---------------------------------------------------------------------------

# Keywords that route to specific specialist agents
_ROUTING_KEYWORDS: dict[AgentRole, list[str]] = {
    AgentRole.TAX_COMPLIANCE: [
        "form 1040", "1120", "1065", "1041", "schedule", "filing",
        "tax return", "w-2", "1099", "payroll", "941", "940",
        "estimated tax", "extension", "amended", "1040-x",
        "deduction", "credit", "withholding", "refund",
        "capital gains", "depreciation", "section 179",
        "home office", "self-employment", "schedule c",
        "rental", "schedule e", "crypto tax", "form 8949",
    ],
    AgentRole.LEGAL_COUNSEL: [
        "entity", "llc", "s-corp", "c-corp", "corporation",
        "operating agreement", "shareholder", "buy-sell",
        "contract", "formation", "restructuring", "dissolution",
        "securities", "reg d", "asset protection", "trust",
        "prenuptial", "lease", "employment agreement",
        "ip licensing", "joint venture", "erisa", "gdpr", "ccpa",
    ],
    AgentRole.FINANCIAL_ANALYST: [
        "valuation", "dcf", "cash flow", "forecast", "budget",
        "financial statement", "p&l", "balance sheet",
        "m&a", "merger", "acquisition", "due diligence",
        "capital raising", "pitch deck", "kpi", "roi",
        "working capital", "break-even", "scenario analysis",
    ],
    AgentRole.RESEARCH: [
        "regulation", "ruling", "revenue procedure", "case law",
        "tax court", "circuit court", "supreme court",
        "legislative", "treaty", "irs notice", "guidance",
        "what changed", "new law", "effective date",
        "research", "precedent", "interpretation",
    ],
    AgentRole.AUDIT_DEFENSE: [
        "audit", "irs notice", "cp2000", "examination",
        "penalty", "abatement", "offer in compromise",
        "innocent spouse", "installment", "collections",
        "idr", "information document request", "tax court petition",
        "appeal", "protest", "reasonable cause",
    ],
}


def route_to_agent(query: str, context: dict[str, Any] | None = None) -> AgentRole:
    """Determine which specialist agent should handle this query."""
    query_lower = query.lower()
    scores: dict[AgentRole, int] = {role: 0 for role in AgentRole if role != AgentRole.MASTER}

    for role, keywords in _ROUTING_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                scores[role] += 1

    best_role = max(scores, key=scores.get)  # type: ignore
    if scores[best_role] == 0:
        return AgentRole.MASTER

    return best_role


# ---------------------------------------------------------------------------
# LLM Clients
# ---------------------------------------------------------------------------

class LLMClient:
    """Unified interface for calling OpenAI and Anthropic models."""

    def __init__(self):
        self._openai_client = None
        self._anthropic_client = None

    def _get_openai(self):
        if self._openai_client is None:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

    def _get_anthropic(self):
        if self._anthropic_client is None:
            from anthropic import AsyncAnthropic
            self._anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._anthropic_client

    async def chat(
        self,
        model: str,
        provider: str,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Send a chat completion request. Returns:
          {content, input_tokens, output_tokens, model, finish_reason}
        """
        start = time.time()

        try:
            if provider == "openai":
                result = await self._call_openai(model, system_prompt, messages, temperature, max_tokens)
            elif provider == "anthropic":
                result = await self._call_anthropic(model, system_prompt, messages, temperature, max_tokens)
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception as primary_err:
            # Auto-fallback: if OpenAI fails, try Anthropic (and vice versa)
            fallback_provider = "anthropic" if provider == "openai" else "openai"
            fallback_model = (
                settings.MODEL_CLAUDE_SONNET if fallback_provider == "anthropic"
                else settings.MODEL_GPT4O_MINI
            )
            logger.warning(
                "Primary provider %s failed (%s), falling back to %s",
                provider, primary_err, fallback_provider,
            )
            try:
                if fallback_provider == "anthropic":
                    result = await self._call_anthropic(fallback_model, system_prompt, messages, temperature, max_tokens)
                else:
                    result = await self._call_openai(fallback_model, system_prompt, messages, temperature, max_tokens)
            except Exception as fallback_err:
                raise primary_err from fallback_err

        result["latency_sec"] = round(time.time() - start, 2)
        return result

    async def _call_openai(
        self, model: str, system_prompt: str, messages: list[dict], temp: float, max_tokens: int
    ) -> dict[str, Any]:
        client = self._get_openai()
        all_messages = [{"role": "system", "content": system_prompt}]
        all_messages.extend(messages)

        response = await client.chat.completions.create(
            model=model,
            messages=all_messages,
            temperature=temp,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage = response.usage

        return {
            "content": choice.message.content or "",
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
            "model": model,
            "finish_reason": choice.finish_reason,
        }

    async def _call_anthropic(
        self, model: str, system_prompt: str, messages: list[dict], temp: float, max_tokens: int
    ) -> dict[str, Any]:
        client = self._get_anthropic()
        response = await client.messages.create(
            model=model,
            system=system_prompt,
            messages=messages,
            temperature=temp,
            max_tokens=max_tokens,
        )

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return {
            "content": content,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": model,
            "finish_reason": response.stop_reason,
        }


# ---------------------------------------------------------------------------
# Confidence Scorer
# ---------------------------------------------------------------------------

def score_confidence(response: str, query: str, complexity: int) -> float:
    """
    Heuristic confidence scoring for a response.
    Returns 0.0-1.0 confidence score.
    """
    score = 0.7  # base

    # Citation presence boosts confidence
    citation_signals = ["irc §", "section", "reg.", "rev. rul.", "rev. proc.",
                        "treas. reg.", "pub.", "form ", "schedule "]
    citation_count = sum(1 for s in citation_signals if s in response.lower())
    score += min(citation_count * 0.03, 0.15)

    # Hedging language (appropriate caution) is good
    caution_signals = ["consult", "professional", "disclaimer", "generally",
                       "depends on", "may vary", "subject to"]
    caution_count = sum(1 for s in caution_signals if s in response.lower())
    score += min(caution_count * 0.02, 0.08)

    # Very short responses for complex queries are suspicious
    if complexity >= 7 and len(response) < 200:
        score -= 0.15

    # Very long, rambling responses may indicate hallucination
    if len(response) > 5000 and citation_count < 2:
        score -= 0.10

    # "I'm not sure" or "I don't know" is honest but lowers confidence
    if any(p in response.lower() for p in ["i'm not sure", "i don't know", "uncertain"]):
        score -= 0.15

    return max(0.0, min(1.0, round(score, 3)))


def confidence_level(score: float) -> ResponseConfidence:
    if score >= 0.85:
        return ResponseConfidence.HIGH
    elif score >= 0.70:
        return ResponseConfidence.MEDIUM
    elif score >= 0.50:
        return ResponseConfidence.LOW
    else:
        return ResponseConfidence.VERY_LOW


# ---------------------------------------------------------------------------
# AI Orchestrator (Main Service)
# ---------------------------------------------------------------------------

class AIOrchestrator:
    """
    The main AI service that orchestrates multi-agent workflows.

    Workflow per query:
      1. Cost Governor estimates cost + selects model
      2. Route query to appropriate specialist agent
      3. Execute LLM call with selected model
      4. Score confidence on response
      5. If low confidence, escalate to higher-tier model
      6. Cache successful responses
      7. Record usage with Cost Governor
      8. Return annotated response
    """

    def __init__(self, cost_governor: CostGovernor):
        self.governor = cost_governor
        self.llm = LLMClient()
        self._conversations: dict[str, ConversationState] = {}

    def get_or_create_conversation(
        self, conversation_id: str | None = None, client_id: str = ""
    ) -> ConversationState:
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]
        state = ConversationState(client_id=client_id)
        if conversation_id:
            state.conversation_id = conversation_id
        self._conversations[state.conversation_id] = state
        return state

    async def query(
        self,
        query: str,
        client_id: str = "",
        conversation_id: str | None = None,
        task_type: str = "",
        context: dict[str, Any] | None = None,
        require_citations: bool = True,
    ) -> AgentMessage:
        """
        Process a user query through the full multi-agent pipeline.
        """
        request_id = str(uuid.uuid4())
        state = self.get_or_create_conversation(conversation_id, client_id)
        state.context = context or {}

        # Step 1: Cost estimation + cache check
        estimate = await self.governor.estimate(
            query=query, client_id=client_id, task_type=task_type, context=context
        )

        # Cache hit -- return immediately
        if estimate.cache_hit:
            cached_result, _ = await self.governor.cache.get(query, client_id)
            if cached_result and isinstance(cached_result, dict):
                msg = AgentMessage(
                    role="assistant",
                    content=cached_result.get("content", str(cached_result)),
                    agent=AgentRole.MASTER,
                    model_used="cache",
                    confidence=cached_result.get("confidence", 0.9),
                    citations=cached_result.get("citations", []),
                    cost_usd=0.001,
                    metadata={
                        "cache_hit": True,
                        "conversation_id": state.conversation_id,
                        "routing_path": estimate.routing_path,
                        "budget_mode": estimate.budget_mode,
                    },
                )
                state.messages.append(AgentMessage(role="user", content=query))
                state.messages.append(msg)
                return msg

        # Budget rejected
        if not estimate.approved:
            msg = AgentMessage(
                role="assistant",
                content=f"I apologize, but this query cannot be processed at this time. {estimate.rejection_reason}. "
                        f"Please contact support or try a simpler question.",
                agent=AgentRole.MASTER,
                confidence=1.0,
                metadata={
                    "budget_rejected": True,
                    "reason": estimate.rejection_reason,
                    "conversation_id": state.conversation_id,
                    "routing_path": estimate.routing_path,
                    "budget_mode": estimate.budget_mode,
                },
            )
            state.messages.append(AgentMessage(role="user", content=query))
            state.messages.append(msg)
            return msg

        # Step 2: Route to specialist agent
        agent_role = route_to_agent(query, context)
        state.current_agent = agent_role
        state.complexity = analyze_complexity(query, context)
        state.task_type = task_type or agent_role.value

        # Step 3: Build message history for the LLM
        system_prompt = SYSTEM_PROMPTS.get(agent_role, SYSTEM_PROMPTS[AgentRole.MASTER])
        if require_citations:
            system_prompt += "\n\nIMPORTANT: Always cite specific IRC sections, Treasury Regulations, or case law for every claim."

        chat_messages = self._build_chat_messages(state, query)

        # Step 4: Get model spec from Cost Governor's selection
        model_spec = MODEL_REGISTRY.get(estimate.model_name)
        if not model_spec:
            model_spec = MODEL_REGISTRY[settings.MODEL_GPT4O_MINI]

        # Step 5: Execute LLM call
        try:
            result = await self.llm.chat(
                model=model_spec.name,
                provider=model_spec.provider,
                system_prompt=system_prompt,
                messages=chat_messages,
                temperature=0.2 if state.complexity >= 7 else 0.3,
                max_tokens=4096,
            )
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            msg = AgentMessage(
                role="assistant",
                content="I encountered an error processing your request. Please try again.",
                agent=agent_role,
                confidence=0.0,
                metadata={"error": str(exc), "conversation_id": state.conversation_id},
            )
            state.messages.append(AgentMessage(role="user", content=query))
            state.messages.append(msg)
            return msg

        # Step 6: Score confidence
        conf_score = score_confidence(result["content"], query, state.complexity)
        conf_level = confidence_level(conf_score)

        # Step 7: Self-healing -- escalate if low confidence
        if conf_level in (ResponseConfidence.LOW, ResponseConfidence.VERY_LOW):
            escalated = await self._escalate(
                query, state, system_prompt, chat_messages, conf_score, result
            )
            if escalated:
                result = escalated["result"]
                conf_score = escalated["confidence"]
                conf_level = confidence_level(conf_score)

        # Step 8: Calculate actual cost + record
        actual_cost = self.governor.calculate_actual_cost(
            result["model"], result["input_tokens"], result["output_tokens"]
        )
        actual_model_spec = MODEL_REGISTRY.get(result["model"], model_spec)

        usage = UsageRecord(
            request_id=request_id,
            client_id=client_id,
            model_name=result["model"],
            model_tier=actual_model_spec.tier,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            actual_cost_usd=actual_cost,
            latency_sec=result.get("latency_sec", 0.0),
            cache_hit=False,
            task_type=state.task_type,
            complexity=state.complexity,
            confidence=conf_score,
        )
        await self.governor.record(usage)
        state.total_cost += actual_cost

        # Step 9: Cache the response for future use
        cache_payload = {
            "content": result["content"],
            "confidence": conf_score,
            "citations": [],
            "agent": agent_role.value,
        }
        await self.governor.cache.set(query, cache_payload, client_id)

        # Step 10: Build and return the response message
        msg = AgentMessage(
            role="assistant",
            content=result["content"],
            agent=agent_role,
            model_used=result["model"],
            confidence=conf_score,
            cost_usd=actual_cost,
            latency_sec=result.get("latency_sec", 0.0),
            metadata={
                "complexity": state.complexity,
                "confidence_level": conf_level.value,
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "requires_human_review": conf_level == ResponseConfidence.VERY_LOW,
                "conversation_id": state.conversation_id,
                "routing_path": estimate.routing_path,
                "estimated_cost_usd": estimate.estimated_cost_usd,
                "estimated_latency_sec": estimate.estimated_latency_sec,
                "budget_mode": estimate.budget_mode,
                "estimated_swarm_agents": estimate.estimated_swarm_agents,
                "downgrade_reason": estimate.downgrade_reason,
                "gate_code": getattr(estimate, "gate_code", "ALLOW"),
                "swarm_plan": getattr(estimate, "swarm_plan", None),
            },
        )

        # Add user query + response to conversation history
        state.messages.append(AgentMessage(role="user", content=query))
        state.messages.append(msg)

        if conf_level == ResponseConfidence.VERY_LOW:
            state.requires_human_review = True

        return msg

    # -- Escalation Logic ---------------------------------------------------

    async def _escalate(
        self,
        query: str,
        state: ConversationState,
        system_prompt: str,
        chat_messages: list[dict],
        original_confidence: float,
        original_result: dict,
    ) -> dict | None:
        """
        Escalate to a higher-tier model when confidence is low.
        Returns improved result or None if escalation isn't warranted.
        """
        current_model = original_result["model"]

        # Determine escalation target
        escalation_map = {
            settings.MODEL_GPT4O_MINI: settings.MODEL_CLAUDE_SONNET,
            settings.MODEL_CLAUDE_HAIKU: settings.MODEL_CLAUDE_SONNET,
            settings.MODEL_CLAUDE_SONNET: settings.MODEL_GPT4O,
        }

        target_model_name = escalation_map.get(current_model)
        if not target_model_name:
            return None

        target_spec = MODEL_REGISTRY.get(target_model_name)
        if not target_spec:
            return None

        # Budget check for escalation
        est_cost = (2000 / 1_000_000) * target_spec.input_cost_per_1m + (4000 / 1_000_000) * target_spec.output_cost_per_1m
        approved, _ = await self.governor.budget.check_budget(state.client_id, est_cost)
        if not approved:
            return None

        logger.info(
            "Escalating from %s (conf=%.2f) to %s",
            current_model, original_confidence, target_model_name,
        )

        enhanced_prompt = system_prompt + (
            "\n\nNOTE: A previous analysis had low confidence. "
            "Please provide a thorough, well-cited, and carefully reasoned response. "
            "Double-check all tax code references and calculations."
        )

        try:
            result = await self.llm.chat(
                model=target_spec.name,
                provider=target_spec.provider,
                system_prompt=enhanced_prompt,
                messages=chat_messages,
                temperature=0.15,
                max_tokens=4096,
            )
            new_confidence = score_confidence(result["content"], query, state.complexity)

            if new_confidence > original_confidence:
                return {"result": result, "confidence": new_confidence}
        except Exception as exc:
            logger.warning("Escalation failed: %s", exc)

        return None

    # -- Helpers ------------------------------------------------------------

    def _build_chat_messages(
        self, state: ConversationState, current_query: str
    ) -> list[dict[str, str]]:
        """Build the message list for the LLM from conversation history."""
        messages = []

        # Include last 10 messages of context (5 turns)
        recent = state.messages[-10:]
        for msg in recent:
            if msg.role in ("user", "assistant"):
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": current_query})
        return messages

    async def get_conversation_history(
        self, conversation_id: str
    ) -> list[dict[str, Any]]:
        state = self._conversations.get(conversation_id)
        if not state:
            return []
        return [
            {
                "role": m.role,
                "content": m.content,
                "agent": m.agent.value if m.agent else None,
                "model": m.model_used,
                "confidence": m.confidence,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in state.messages
        ]
