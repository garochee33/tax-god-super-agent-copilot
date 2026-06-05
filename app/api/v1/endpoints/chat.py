"""
Tax God API - AI Chat Endpoints
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, SubscribedUser, resolve_client_id

router = APIRouter()


# -- Request / Response Models -----------------------------------------------


class ChatQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000, description="The tax/legal/financial question")
    client_id: str = Field(default="", description="Client identifier")
    conversation_id: str | None = Field(default=None, description="Continue existing conversation")
    task_type: str = Field(default="", description="Task type hint (tax_compliance, legal, financial, etc.)")
    require_citations: bool = Field(default=True, description="Include tax law citations")
    context: dict[str, Any] | None = Field(default=None, description="Additional context")
    use_god_mode: bool = Field(default=False, description="Use God Mode v3.0 (DTDA→IMRA→SHVA pipeline)")


class ChatResponse(BaseModel):
    content: str
    agent: str | None = None
    model_used: str = ""
    confidence: float = 0.0
    confidence_level: str = ""
    citations: list[dict[str, Any]] = Field(default_factory=list)
    cost_usd: float = 0.0
    conversation_id: str = ""
    requires_human_review: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class CitationSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query for tax citations")
    max_results: int = Field(default=5, ge=1, le=20)


# -- Endpoints ---------------------------------------------------------------


@router.post("/query", response_model=ChatResponse)
async def ai_query(body: ChatQuery, request: Request, current_user: SubscribedUser):
    """
    Submit a tax/legal/financial question to Tax God.
    Routes to the appropriate specialist agent automatically.
    When use_god_mode=True, runs the full DTDA→IMRA→SHVA pipeline (God Mode v3.0).
    Requires authentication.
    """
    citation_engine = request.app.state.citation_engine
    client_id = resolve_client_id(body.client_id, current_user)

    if body.use_god_mode:
        advanced = getattr(request.app.state, "advanced_orchestrator", None)
        if not advanced:
            raise HTTPException(
                status_code=503,
                detail="God Mode v3.0 (advanced orchestrator) is not available",
            )
        result = await advanced.process_advanced_query(
            query=body.query,
            client_id=client_id,
            conversation_id=body.conversation_id,
            context=body.context or {},
            require_citations=body.require_citations,
        )
        msg = result.response
        enriched = citation_engine.enrich_response(msg.content, body.query)
        response_conversation_id = msg.metadata.get("conversation_id") or body.conversation_id or ""
        citations = enriched.get("verified_citations", []) + enriched.get("supplemental_citations", [])
        if not citations and getattr(msg, "citations", None):
            citations = msg.citations or []
        return ChatResponse(
            content=msg.content,
            agent=msg.agent.value if msg.agent else None,
            model_used=msg.model_used,
            confidence=result.final_confidence,
            confidence_level="god_mode" if result.decomposition else "",
            citations=citations,
            cost_usd=msg.cost_usd,
            conversation_id=response_conversation_id,
            requires_human_review=result.requires_human_review,
            metadata={
                **(msg.metadata or {}),
                "god_mode": True,
                "request_id": result.request_id,
                "processing_time": result.processing_time,
                "decomposition_task_type": result.decomposition.task_type.value
                if result.decomposition and hasattr(result.decomposition.task_type, "value")
                else str(result.decomposition.task_type)
                if result.decomposition
                else None,
                "fallback_used": result.fallback_used,
            },
        )

    orchestrator = request.app.state.ai_orchestrator
    msg = await orchestrator.query(
        query=body.query,
        client_id=client_id,
        conversation_id=body.conversation_id,
        task_type=body.task_type,
        context=body.context,
        require_citations=body.require_citations,
    )

    enriched = citation_engine.enrich_response(msg.content, body.query)
    response_conversation_id = msg.metadata.get("conversation_id") or body.conversation_id or ""

    return ChatResponse(
        content=msg.content,
        agent=msg.agent.value if msg.agent else None,
        model_used=msg.model_used,
        confidence=msg.confidence,
        confidence_level=msg.metadata.get("confidence_level", ""),
        citations=enriched.get("verified_citations", []) + enriched.get("supplemental_citations", []),
        cost_usd=msg.cost_usd,
        conversation_id=response_conversation_id,
        requires_human_review=msg.metadata.get("requires_human_review", False),
        metadata=msg.metadata,
    )


@router.post("/citations/search")
async def search_citations(body: CitationSearchRequest, request: Request, current_user: CurrentUser):
    """Search the tax law knowledge base for relevant citations."""
    engine = request.app.state.citation_engine
    result = engine.search(body.query, max_results=body.max_results)

    return {
        "query": result.query,
        "total_found": result.total_found,
        "search_time_ms": result.search_time_ms,
        "citations": [
            {
                "reference": c.reference,
                "title": c.title,
                "summary": c.summary,
                "type": c.citation_type.value,
                "year": c.year,
            }
            for c in result.citations
        ],
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, request: Request, current_user: CurrentUser):
    """Retrieve conversation history."""
    orchestrator = request.app.state.ai_orchestrator
    history = await orchestrator.get_conversation_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": history}
