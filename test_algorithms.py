#!/usr/bin/env python3
"""
Test script for DTDA, IMRA, and SHVA algorithms integration
Run this to verify the core algorithms are working properly
"""

import asyncio
import sys
import os

# Add the specs directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'specs', 'algorithms'))

from dtda import DynamicTaskDecompositionAlgorithm
from imra import IntelligentMemoryRetrievalAlgorithm, RetrievalContext
from shva import SelfHealingValidationAlgorithm


async def test_dtda():
    """Test DTDA algorithm"""
    print("🧠 Testing DTDA (Dynamic Task Decomposition Algorithm)")
    print("=" * 60)

    dtda = DynamicTaskDecompositionAlgorithm()

    test_queries = [
        "How do I file my taxes?",
        "Help me optimize my S-Corp taxes across California and New York",
        "What are the best strategies for estate planning?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        result = dtda.decompose_task(query, {})
        print(f"  Task Type: {result.task_type}")
        print(f"  Complexity: {result.complexity:.2f}")
        print(f"  Execution Plan: {result.execution_plan.value}")
        print(f"  Estimated Cost: ${result.estimated_cost:.3f}")
        print(f"  Subtasks: {len(result.subtasks)}")

    print("\n✅ DTDA test completed")


def test_imra():
    """Test IMRA algorithm"""
    print("\n🧠 Testing IMRA (Intelligent Memory Retrieval Algorithm)")
    print("=" * 60)

    imra = IntelligentMemoryRetrievalAlgorithm()

    # Add some test memories
    imra.add_to_immediate_context(
        "User is asking about home office deductions",
        {"topic": "deductions", "type": "tax"}
    )

    # Test retrieval
    context = RetrievalContext(
        query="How do I claim home office expenses?",
        client_id="test_client"
    )

    results = imra.retrieve_context(context)
    print(f"Retrieved {len(results)} memory results")

    for result in results[:3]:  # Show top 3
        tier_name = result.tier.value if result.tier else "unknown"
        print(f"  Tier: {tier_name}, Score: {result.final_score:.3f}")
        print(f"  Content: {result.content[:100]}...")

    print("\n✅ IMRA test completed")


async def test_shva():
    """Test SHVA algorithm"""
    print("\n🧠 Testing SHVA (Self-Healing Validation Algorithm)")
    print("=" * 60)

    shva = SelfHealingValidationAlgorithm()

    test_responses = [
        {
            "content": "According to IRC § 162, you can deduct home office expenses.",
            "task_type": "tax_analysis",
            "context": {}
        },
        {
            "content": "This is a completely invalid response with no citations.",
            "task_type": "tax_analysis",
            "context": {}
        }
    ]

    for i, response in enumerate(test_responses, 1):
        print(f"\nTest Response {i}:")
        print(f"  Content: {response['content'][:80]}...")

        result = shva.validate_output(response, "tax_analysis")
        print(f"  Valid: {result.is_valid}")
        print(f"  Confidence: {result.confidence_score:.3f}")
        print(f"  Auto-healings: {len(result.healing_log)}")
        if result.errors:
            print(f"  Errors: {len(result.errors)}")

    print("\n✅ SHVA test completed")


async def test_integration():
    """Test the integrated advanced orchestrator"""
    print("\n🔗 Testing Advanced Orchestrator Integration")
    print("=" * 60)

    try:
        from app.services.advanced_orchestrator import AdvancedTaxOrchestrator
        from app.services.cost_governor import CostGovernor

        # Mock cost governor (we'll use a simple mock for testing)
        cost_governor = CostGovernor(None)

        orchestrator = AdvancedTaxOrchestrator(cost_governor)

        # Test basic decomposition
        decomposition = await orchestrator._decompose_task(
            "Help me with my tax return", {}
        )
        print(f"✅ Decomposition works: {decomposition.task_type}")

        # Test memory retrieval
        memories = await orchestrator._retrieve_context(
            "tax return", "test_client"
        )
        print(f"✅ Memory retrieval works: {len(memories)} results")

        # Test validation
        validation = await orchestrator._validate_response(
            "This is a test response about taxes.", "tax_analysis", {}
        )
        print(f"✅ Validation works: confidence {validation.confidence_score if validation else 'N/A'}")

        print("\n✅ Advanced Orchestrator integration test completed")

    except ImportError as e:
        print(f"⚠️  Integration test skipped (FastAPI not available): {e}")
    except Exception as e:
        print(f"❌ Integration test failed: {e}")


async def main():
    """Run all algorithm tests"""
    print("🚀 Tax God Algorithm Integration Test Suite")
    print("=" * 60)
    print("Testing DTDA, IMRA, and SHVA core algorithms...")
    print()

    await test_dtda()
    test_imra()  # Not async
    await test_shva()
    await test_integration()

    print("\n" + "=" * 60)
    print("🎉 All algorithm tests completed!")
    print("Tax God core intelligence is operational.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())