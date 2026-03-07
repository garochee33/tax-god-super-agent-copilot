"""
Tax God - Advanced Tax Processing API Endpoints
Provides access to the complete DTDA → IMRA → SHVA pipeline
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, AdminUser
from app.services.advanced_orchestrator import AdvancedTaxOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class AdvancedTaxRequest(BaseModel):
    """Request model for advanced tax processing."""
    query: str = Field(..., description="The tax query to process")
    client_id: str = Field("", description="Client identifier for personalization")
    conversation_id: str | None = Field(None, description="Conversation thread ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    require_citations: bool = Field(True, description="Whether to require citations in responses")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Help me optimize my S-Corp taxes across California and New York",
                "client_id": "client_123",
                "context": {
                    "multi_state": True,
                    "entity_type": "s-corp",
                    "deadline_pressure": False,
                    "audit_concerns": False
                },
                "require_citations": True
            }
        }


class DecompositionResponse(BaseModel):
    """Response model for task decomposition results."""
    execution_plan: str
    task_type: str
    complexity: float
    subtasks: list[Dict[str, Any]]
    dependency_graph: Dict[int, list[int]]
    swarm_size: int | None = None
    agents_needed: list[str] | None = None
    estimated_cost: float
    estimated_time: int
    parallelization_score: float


class MemoryResultResponse(BaseModel):
    """Response model for memory retrieval results."""
    tier: str
    content: str
    final_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResponse(BaseModel):
    """Response model for validation results."""
    is_valid: bool | None = None
    confidence_score: float | None = None
    errors: list[Dict[str, Any]] = []
    healing_log: list[str] = []
    requires_human_review: bool | None = None


class AgentMessageResponse(BaseModel):
    """Response model for AI agent messages."""
    role: str
    content: str
    agent: str | None = None
    model_used: str
    confidence: float
    citations: list[Dict[str, str]]
    cost_usd: float
    latency_sec: float
    metadata: Dict[str, Any]


class AdvancedTaxResponseModel(BaseModel):
    """Complete response model for advanced tax processing."""
    request_id: str
    query: str
    response: AgentMessageResponse
    decomposition: DecompositionResponse | None = None
    memory_context: list[MemoryResultResponse] = []
    validation: ValidationResponse | None = None
    final_confidence: float
    processing_time: float
    requires_human_review: bool
    fallback_used: bool = False
    error_message: str | None = None


# Dependency injection functions
async def get_advanced_orchestrator(request: Request) -> AdvancedTaxOrchestrator:
    """Get the advanced tax orchestrator from app state."""
    orchestrator = getattr(request.app.state, 'advanced_orchestrator', None)
    if not orchestrator:
        raise HTTPException(
            status_code=503,
            detail="Advanced tax orchestrator service is not available"
        )
    return orchestrator


# API Endpoints
@router.post(
    "/query",
    response_model=AdvancedTaxResponseModel,
    summary="Process Advanced Tax Query",
    description="""
    Process a tax query using the complete DTDA → IMRA → SHVA pipeline.

    This endpoint provides:
    - **DTDA**: Intelligent task decomposition and complexity analysis
    - **IMRA**: 5-tier memory retrieval for relevant context
    - **SHVA**: Self-healing validation and quality assurance
    - **Advanced routing**: Intelligent agent selection based on task analysis

    **Use cases:**
    - Complex multi-state tax optimization
    - Entity restructuring analysis
    - Audit defense strategies
    - Advanced tax planning scenarios
    """,
    tags=["Advanced Tax Processing"]
)
async def process_advanced_tax_query(
    request: AdvancedTaxRequest,
    current_user: CurrentUser,
    orchestrator: AdvancedTaxOrchestrator = Depends(get_advanced_orchestrator),
) -> AdvancedTaxResponseModel:
    """
    Process a tax query using the complete advanced AI pipeline.

    Returns comprehensive results including task decomposition, memory context,
    validation results, and final AI response with confidence scoring.
    """
    try:
        logger.info(f"Processing advanced tax query: {request.query[:100]}...")

        result = await orchestrator.process_advanced_query(
            query=request.query,
            client_id=request.client_id,
            conversation_id=request.conversation_id,
            context=request.context,
            require_citations=request.require_citations,
        )

        # Convert to response model
        response_data = result.to_dict()

        return AdvancedTaxResponseModel(**response_data)

    except Exception as exc:
        logger.error("Advanced tax query processing failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to process advanced tax query",
        )


@router.post(
    "/decompose",
    response_model=DecompositionResponse,
    summary="Task Decomposition Analysis",
    description="""
    Analyze and decompose a tax query using DTDA (Dynamic Task Decomposition Algorithm).

    Returns detailed breakdown including:
    - Execution plan (direct, sequential, or parallel swarm)
    - Task type classification
    - Complexity scoring
    - Subtask breakdown with dependencies
    - Cost and time estimates
    """,
    tags=["Task Analysis"]
)
async def decompose_tax_task(
    request: AdvancedTaxRequest,
    current_user: CurrentUser,
    orchestrator: AdvancedTaxOrchestrator = Depends(get_advanced_orchestrator),
) -> DecompositionResponse:
    """
    Decompose a tax task using DTDA without full processing.

    Useful for understanding query complexity and planning before execution.
    """
    try:
        decomposition = await orchestrator._decompose_task(
            request.query,
            request.context
        )

        return DecompositionResponse(
            execution_plan=decomposition.execution_plan.value,
            task_type=decomposition.task_type,
            complexity=decomposition.complexity,
            subtasks=[
                {
                    "task": subtask.task,
                    "priority": subtask.priority,
                    "description": subtask.description,
                    "agent_type": subtask.agent_type,
                    "estimated_cost": subtask.estimated_cost,
                    "estimated_time": subtask.estimated_time,
                }
                for subtask in decomposition.subtasks
            ] if decomposition.subtasks else [],
            dependency_graph=decomposition.dependency_graph,
            swarm_size=decomposition.swarm_size,
            agents_needed=decomposition.agents_needed,
            estimated_cost=decomposition.estimated_cost,
            estimated_time=decomposition.estimated_time,
            parallelization_score=getattr(decomposition, 'parallelization_score', 0.0)
        )

    except Exception as exc:
        logger.error("Task decomposition failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to decompose task",
        )


@router.post(
    "/memory",
    response_model=list[MemoryResultResponse],
    summary="Memory Context Retrieval",
    description="""
    Retrieve relevant context from the 5-tier IMRA memory system.

    Returns memories from different tiers:
    - **Immediate**: Current conversation context
    - **Short-term**: Recent session data
    - **Long-term**: Historical client data
    - **Knowledge**: Tax law and regulations
    - **Collective**: Anonymized patterns across all clients
    """,
    tags=["Memory & Context"]
)
async def retrieve_tax_memory(
    request: AdvancedTaxRequest,
    current_user: CurrentUser,
    orchestrator: AdvancedTaxOrchestrator = Depends(get_advanced_orchestrator),
) -> list[MemoryResultResponse]:
    """
    Retrieve relevant memory context for a tax query using IMRA.
    """
    try:
        memory_results = await orchestrator._retrieve_context(
            request.query,
            request.client_id
        )

        return [
            MemoryResultResponse(
                tier=result.tier,
                content=result.content,
                final_score=result.final_score,
                metadata=result.metadata
            )
            for result in memory_results
        ]

    except Exception as exc:
        logger.error("Memory retrieval failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve memory context",
        )


@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Response Validation",
    description="""
    Validate tax analysis or response using SHVA (Self-Healing Validation Algorithm).

    Performs multi-stage validation:
    - **Structure**: Data types and required fields
    - **Calculation**: Mathematical accuracy
    - **Compliance**: Regulatory rule adherence
    - **Consistency**: Logical relationships
    - **Completeness**: All necessary data present

    Auto-heals detected issues where possible.
    """,
    tags=["Validation & Quality"]
)
async def validate_tax_response(
    body: AdvancedTaxRequest,
    current_user: CurrentUser,
    orchestrator: AdvancedTaxOrchestrator = Depends(get_advanced_orchestrator),
) -> ValidationResponse:
    """
    Validate tax content using SHVA.
    """
    try:
        content = body.query
        task_type = body.context.get("task_type", "general") if body.context else "general"
        context = body.context or {}

        validation_result = await orchestrator._validate_response(
            content, task_type, context
        )

        if validation_result:
            return ValidationResponse(
                is_valid=validation_result.is_valid,
                confidence_score=validation_result.confidence_score,
                errors=[
                    {
                        "stage": err.stage.value if hasattr(err, 'stage') else str(err),
                        "severity": err.severity.value if hasattr(err, 'severity') else "unknown",
                        "field": getattr(err, 'field', 'unknown'),
                        "error_type": getattr(err, 'error_type', 'unknown'),
                        "message": getattr(err, 'message', str(err)),
                    }
                    for err in (validation_result.errors or [])
                ],
                healing_log=validation_result.healing_log,
                requires_human_review=validation_result.requires_human_review
            )
        else:
            return ValidationResponse(
                is_valid=None,
                confidence_score=None,
                errors=[],
                healing_log=[],
                requires_human_review=None
            )

    except Exception as exc:
        logger.error("Validation failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to validate response",
        )


@router.get(
    "/health",
    summary="Advanced Services Health Check",
    description="Check the health and availability of advanced AI services (DTDA, IMRA, SHVA).",
    tags=["Health & Monitoring"]
)
async def advanced_services_health(
    current_user: AdminUser,
    orchestrator: AdvancedTaxOrchestrator = Depends(get_advanced_orchestrator),
) -> Dict[str, Any]:
    """Check health of advanced AI services."""
    try:
        # Test basic functionality
        test_decomposition = await orchestrator._decompose_task(
            "Test tax query", {}
        )

        return {
            "status": "healthy",
            "services": {
                "dtda": "operational",
                "imra": "operational",
                "shva": "operational",
                "advanced_orchestrator": "operational"
            },
            "test_results": {
                "decomposition_complexity": test_decomposition.complexity,
                "decomposition_plan": test_decomposition.execution_plan.value,
            }
        }
    except Exception as exc:
        logger.error(f"Advanced services health check failed: {exc}")
        return {
            "status": "degraded",
            "services": {
                "dtda": "error",
                "imra": "error",
                "shva": "error",
                "advanced_orchestrator": "error"
            },
            "error": str(exc)
        }