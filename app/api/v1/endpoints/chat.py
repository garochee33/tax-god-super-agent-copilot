"""
Tax God API - AI Chat Endpoints
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser

router = APIRouter()


# -- Request / Response Models -----------------------------------------------

class ChatQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000, description="The tax/legal/financial question")
    client_id: str = Field(default="", description="Client identifier")
    conversation_id: Optional[str] = Field(default=None, description="Continue existing conversation")
    task_type: str = Field(default="", description="Task type hint (tax_compliance, legal, financial, etc.)")
    require_citations: bool = Field(default=True, description="Include tax law citations")
    context: Optional[dict[str, Any]] = Field(default=None, description="Additional context")


class ChatResponse(BaseModel):
    content: str
    agent: Optional[str] = None
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
async def ai_query(body: ChatQuery, request: Request, current_user: CurrentUser):
    """
    Submit a tax/legal/financial question to Tax God.
    Routes to the appropriate specialist agent automatically.
    Requires authentication.
    """
    orchestrator = request.app.state.ai_orchestrator
    citation_engine = request.app.state.citation_engine

    client_id = body.client_id or current_user.id
    msg = await orchestrator.query(
        query=body.query,
        client_id=client_id,
        conversation_id=body.conversation_id,
        task_type=body.task_type,
        context=body.context,
        require_citations=body.require_citations,
    )

    # Enrich with verified citations
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
