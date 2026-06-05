"""
Tax God - Advanced AI Orchestrator with DTDA Integration
Combines DTDA (Dynamic Task Decomposition), IMRA (Intelligent Memory), and SHVA (Self-Healing Validation)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, List

from app.core.config import get_settings
from app.services.ai_service import AIOrchestrator, AgentRole, AgentMessage
from app.services.cost_governor import CostGovernor

# Import the core algorithms
import asyncio

from specs.algorithms.dtda import DynamicTaskDecompositionAlgorithm, DecompositionResult, ExecutionPlan, TaskType
from specs.algorithms.imra import IntelligentMemoryRetrievalAlgorithm, RetrievalContext, MemoryResult
from specs.algorithms.shva import SelfHealingValidationAlgorithm, ValidationResult

logger = logging.getLogger(__name__)
settings = get_settings()


class AdvancedTaxOrchestrator:
    """
    Advanced AI Orchestrator that integrates DTDA, IMRA, and SHVA algorithms
    for enterprise-grade tax processing capabilities.

    This orchestrator:
    1. Uses DTDA to intelligently decompose complex tax queries
    2. Leverages IMRA's 5-tier memory system for context retrieval
    3. Applies SHVA for automatic validation and self-healing
    4. Routes to appropriate specialist agents based on decomposition
    5. Provides confidence scoring and quality assurance
    """

    def __init__(self, cost_governor: CostGovernor):
        self.cost_governor = cost_governor

        # Initialize core algorithms
        self.dtda = DynamicTaskDecompositionAlgorithm()
        self.imra = IntelligentMemoryRetrievalAlgorithm()
        self.shva = SelfHealingValidationAlgorithm()

        # Fallback to basic orchestrator if algorithms fail
        self.fallback_orchestrator = AIOrchestrator(cost_governor)

        self.task_type_agent_mapping = {
            TaskType.TAX_PREPARATION: AgentRole.TAX_COMPLIANCE,
            TaskType.TAX_PLANNING: AgentRole.FINANCIAL_ANALYST,
            TaskType.LEGAL_ENTITY: AgentRole.LEGAL_COUNSEL,
            TaskType.FINANCIAL_ANALYSIS: AgentRole.FINANCIAL_ANALYST,
            TaskType.AUDIT_DEFENSE: AgentRole.AUDIT_DEFENSE,
            TaskType.COMPLIANCE: AgentRole.TAX_COMPLIANCE,
            TaskType.RESEARCH: AgentRole.RESEARCH,
        }

    async def process_advanced_query(
        self,
        query: str,
        client_id: str = "",
        conversation_id: str | None = None,
        context: dict[str, Any] | None = None,
        require_citations: bool = True,
    ) -> AdvancedTaxResponse:
        """
        Process a tax query using the complete DTDA → IMRA → SHVA pipeline.

        Returns comprehensive results including decomposition, memory context,
        validation results, and final AI response.
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        try:
            # Step 1: DTDA - Decompose the task
            logger.info(f"[{request_id}] Starting DTDA decomposition for query: {query[:100]}...")
            decomposition = await self._decompose_task(query, context or {})

            # Step 2: IMRA - Retrieve relevant context
            logger.info(f"[{request_id}] Retrieving memory context...")
            memory_results = await self._retrieve_context(query, client_id)

            # Step 3: Execute AI processing with enhanced context
            logger.info(f"[{request_id}] Executing AI processing with {len(memory_results)} memory results...")
            ai_response = await self._execute_ai_processing(
                query=query,
                decomposition=decomposition,
                memory_context=memory_results,
                client_id=client_id,
                conversation_id=conversation_id,
                require_citations=require_citations
            )

            # Step 4: SHVA - Validate and potentially heal the response
            logger.info(f"[{request_id}] Validating response with SHVA...")
            validation_result = await self._validate_response(
                ai_response.content,
                decomposition.task_type,
                context
            )

            # Step 5: Final quality assessment
            final_confidence = self._calculate_final_confidence(
                ai_response.confidence,
                validation_result.confidence_score if validation_result else 0.5,
                decomposition.complexity
            )

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            return AdvancedTaxResponse(
                query=query,
                response=ai_response,
                decomposition=decomposition,
                memory_context=memory_results,
                validation=validation_result,
                final_confidence=final_confidence,
                processing_time=processing_time,
                request_id=request_id,
                requires_human_review=self._requires_human_review(
                    final_confidence,
                    validation_result,
                    decomposition.complexity
                )
            )

        except Exception as exc:
            logger.error(f"[{request_id}] Advanced processing failed: {exc}")
            # Fallback to basic orchestrator
            try:
                basic_response = await self.fallback_orchestrator.query(
                    query=query,
                    client_id=client_id,
                    conversation_id=conversation_id,
                    context=context,
                    require_citations=require_citations
                )
                return AdvancedTaxResponse(
                    query=query,
                    response=basic_response,
                    decomposition=None,
                    memory_context=[],
                    validation=None,
                    final_confidence=basic_response.confidence,
                    processing_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
                    request_id=request_id,
                    requires_human_review=basic_response.confidence < 0.7,
                    fallback_used=True,
                    error_message=str(exc)
                )
            except Exception as fallback_exc:
                logger.error(f"[{request_id}] Fallback also failed: {fallback_exc}")
                raise exc

    async def _decompose_task(self, query: str, context: dict[str, Any]) -> DecompositionResult:
        """Use DTDA to decompose the tax query intelligently."""
        try:
            # Prepare context for DTDA
            dtda_context = {
                "has_multi_state": context.get("multi_state", False),
                "entity_type": context.get("entity_type", "individual"),
                "complexity_indicators": context.get("complexity_indicators", []),
                "deadline_pressure": context.get("deadline_pressure", False),
                "audit_concerns": context.get("audit_concerns", False),
            }

            result = await asyncio.to_thread(self.dtda.decompose_task, query, dtda_context)

            # Log decomposition results
            logger.info(f"DTDA Result: Plan={result.execution_plan.value}, "
                       f"Complexity={result.complexity:.2f}, "
                       f"Tasks={len(result.subtasks) if result.subtasks else 0}")

            return result

        except Exception as exc:
            logger.warning(f"DTDA decomposition failed: {exc}, using fallback")
            # Return a basic decomposition
            return DecompositionResult(
                execution_plan=ExecutionPlan.SEQUENTIAL_SPECIALIZED,
                task_type=TaskType.RESEARCH,
                complexity=5.0,
                subtasks=[],
                dependency_graph={},
                estimated_cost=0.10,
                estimated_time=60
            )

    async def _retrieve_context(self, query: str, client_id: str) -> List[MemoryResult]:
        """Use IMRA to retrieve relevant context from the 5-tier memory system."""
        try:
            retrieval_context = RetrievalContext(
                query=query,
                client_id=client_id,
                max_results=10
            )

            results = await asyncio.to_thread(self.imra.retrieve_context, retrieval_context)

            # Log memory retrieval results
            tier_counts = {}
            for result in results:
                tier_counts[result.tier] = tier_counts.get(result.tier, 0) + 1

            logger.info(f"IMRA retrieved {len(results)} memories: {tier_counts}")

            return results

        except Exception as exc:
            logger.warning(f"IMRA context retrieval failed: {exc}, using empty context")
            return []

    async def _execute_ai_processing(
        self,
        query: str,
        decomposition: DecompositionResult,
        memory_context: List[MemoryResult],
        client_id: str,
        conversation_id: str | None,
        require_citations: bool
    ) -> AgentMessage:
        """Execute AI processing using the enhanced context and routing."""

        # Determine the best agent based on DTDA task type
        agent_role = self.task_type_agent_mapping.get(
            decomposition.task_type,
            AgentRole.MASTER  # Default fallback
        )

        # Enhance query with decomposition insights and memory context
        enhanced_query = self._enhance_query_with_context(
            query, decomposition, memory_context
        )

        # Build enhanced context for the AI orchestrator
        enhanced_context = {
            "decomposition": {
                "task_type": decomposition.task_type,
                "complexity": decomposition.complexity,
                "execution_plan": decomposition.execution_plan.value,
                "estimated_cost": decomposition.estimated_cost,
                "parallelizable": decomposition.execution_plan == ExecutionPlan.PARALLEL_SWARM,
            },
            "memory_context": [
                {
                    "tier": mem.tier,
                    "content": mem.content[:500],  # Truncate for context
                    "relevance_score": mem.final_score,
                }
                for mem in memory_context[:5]  # Top 5 memories
            ],
            "enhanced_query": enhanced_query,
        }

        # Execute with the AI orchestrator using the selected agent
        response = await self.fallback_orchestrator.query(
            query=enhanced_query,
            client_id=client_id,
            conversation_id=conversation_id,
            context=enhanced_context,
            require_citations=require_citations
        )

        # Override the agent role to reflect our intelligent routing
        response.agent = agent_role

        return response

    async def _validate_response(
        self,
        response_content: str,
        task_type: str,
        context: dict[str, Any] | None
    ) -> ValidationResult | None:
        """Use SHVA to validate the AI response."""
        try:
            # Prepare response for validation based on task type
            response_data = {
                "content": response_content,
                "task_type": task_type,
                "context": context or {},
            }

            # Validate based on task type
            task_type_str = task_type.value if hasattr(task_type, "value") else str(task_type)
            if task_type_str in ("tax_preparation", "tax_planning", "financial_analysis"):
                validation_result = await asyncio.to_thread(self.shva.validate_output, response_data, "tax_analysis")
            else:
                validation_result = await asyncio.to_thread(self.shva.validate_output, response_data, "general_response")

            logger.info(f"SHVA validation: valid={validation_result.is_valid}, "
                       f"confidence={validation_result.confidence_score:.3f}, "
                       f"auto_healings={len(validation_result.healing_log)}")

            return validation_result

        except Exception as exc:
            logger.warning(f"SHVA validation failed: {exc}, skipping validation")
            return None

    def _enhance_query_with_context(
        self,
        original_query: str,
        decomposition: DecompositionResult,
        memory_context: List[MemoryResult]
    ) -> str:
        """Enhance the original query with insights from decomposition and memory."""

        enhancements = []

        # Add decomposition insights
        if decomposition.complexity > 7:
            enhancements.append("This is a highly complex query requiring detailed analysis.")
        elif decomposition.complexity > 5:
            enhancements.append("This query has moderate complexity requiring careful consideration.")
        else:
            enhancements.append("This appears to be a straightforward query.")

        if decomposition.execution_plan == ExecutionPlan.PARALLEL_SWARM:
            enhancements.append("Consider parallel processing approaches for efficiency.")

        # Add relevant memory context
        relevant_memories = [mem for mem in memory_context if mem.final_score > 0.7][:3]
        if relevant_memories:
            enhancements.append("Relevant historical context available:")
            for mem in relevant_memories:
                enhancements.append(f"- {mem.content[:200]}...")

        if enhancements:
            enhanced_query = f"{original_query}\n\n[SYSTEM CONTEXT]\n" + "\n".join(enhancements)
        else:
            enhanced_query = original_query

        return enhanced_query

    def _calculate_final_confidence(
        self,
        ai_confidence: float,
        validation_confidence: float,
        complexity: float
    ) -> float:
        """Calculate final confidence score combining all factors."""

        # Weight the different confidence sources
        ai_weight = 0.5
        validation_weight = 0.3
        complexity_weight = 0.2

        # Complexity factor (higher complexity should have higher bar)
        complexity_factor = min(1.0, complexity / 10.0)

        final_score = (
            ai_confidence * ai_weight +
            validation_confidence * validation_weight +
            complexity_factor * complexity_weight
        )

        return round(final_score, 3)

    def _requires_human_review(
        self,
        final_confidence: float,
        validation_result: ValidationResult | None,
        complexity: float
    ) -> bool:
        """Determine if human review is required."""

        # Automatic review triggers
        if final_confidence < 0.6:
            return True

        if complexity > 8 and final_confidence < 0.8:
            return True

        if validation_result and not validation_result.is_valid:
            return True

        if validation_result and validation_result.requires_human_review:
            return True

        return False


# Response Models
class AdvancedTaxResponse:
    """Comprehensive response from the advanced tax orchestrator."""

    def __init__(
        self,
        query: str,
        response: AgentMessage,
        decomposition: DecompositionResult | None,
        memory_context: List[MemoryResult],
        validation: ValidationResult | None,
        final_confidence: float,
        processing_time: float,
        request_id: str,
        requires_human_review: bool,
        fallback_used: bool = False,
        error_message: str | None = None,
    ):
        self.query = query
        self.response = response
        self.decomposition = decomposition
        self.memory_context = memory_context
        self.validation = validation
        self.final_confidence = final_confidence
        self.processing_time = processing_time
        self.request_id = request_id
        self.requires_human_review = requires_human_review
        self.fallback_used = fallback_used
        self.error_message = error_message

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "request_id": self.request_id,
            "query": self.query,
            "response": {
                "role": getattr(self.response, "role", "assistant"),
                "content": self.response.content,
                "agent": self.response.agent.value if self.response.agent else None,
                "model_used": self.response.model_used,
                "confidence": self.response.confidence,
                "citations": self.response.citations,
                "cost_usd": self.response.cost_usd,
                "latency_sec": getattr(self.response, "latency_sec", 0.0),
                "metadata": getattr(self.response, "metadata", None) or {},
            },
            "decomposition": {
                "execution_plan": self.decomposition.execution_plan.value if self.decomposition else None,
                "task_type": self.decomposition.task_type.value if self.decomposition and hasattr(self.decomposition.task_type, "value") else (str(self.decomposition.task_type) if self.decomposition else None),
                "complexity": self.decomposition.complexity if self.decomposition else None,
                "subtasks": [vars(task) for task in (self.decomposition.subtasks or [])] if self.decomposition else [],
                "estimated_cost": self.decomposition.estimated_cost if self.decomposition else None,
                "estimated_time": self.decomposition.estimated_time if self.decomposition else None,
            } if self.decomposition else None,
            "memory_context": [
                {
                    "tier": mem.tier,
                    "content": mem.content,
                    "relevance_score": mem.final_score,
                    "source": mem.metadata.get("source", "unknown"),
                }
                for mem in self.memory_context
            ],
            "validation": {
                "is_valid": self.validation.is_valid if self.validation else None,
                "confidence_score": self.validation.confidence_score if self.validation else None,
                "errors": [vars(err) for err in (self.validation.errors or [])] if self.validation else [],
                "healing_log": self.validation.healing_log if self.validation else [],
                "requires_human_review": self.validation.requires_human_review if self.validation else None,
            } if self.validation else None,
            "final_confidence": self.final_confidence,
            "processing_time": self.processing_time,
            "requires_human_review": self.requires_human_review,
            "fallback_used": self.fallback_used,
            "error_message": self.error_message,
        }
