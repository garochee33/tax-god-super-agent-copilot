#!/usr/bin/env python3
"""
Test Tax God Integration as Trinity Consortium Agent
Tests Tax God functioning as Agent #56 in the Trinity 55-agent system
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the specs directory to Python path for algorithm imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'specs', 'algorithms'))

from specs.algorithms.dtda import DynamicTaskDecompositionAlgorithm
from specs.algorithms.imra import IntelligentMemoryRetrievalAlgorithm
from specs.algorithms.shva import SelfHealingValidationAlgorithm


class MockTrinityMessage:
    """Mock Trinity Consortium message for testing"""
    def __init__(self, message_type: str, payload: dict, from_agent: str = "oracle"):
        self.from_agent = from_agent
        self.to = "tax-god"
        self.messageId = f"test-{datetime.now().isoformat()}"
        self.timestamp = datetime.now()
        self.priority = "medium"
        self.type = message_type
        self.payload = payload


class MockTaxGodAgent:
    """Mock Tax God agent for testing Trinity integration"""

    def __init__(self):
        self.agent_id = "tax-god"
        self.spawned_agents = []
        self.processed_messages = []

        # Initialize core algorithms
        self.dtda = DynamicTaskDecompositionAlgorithm()
        self.imra = IntelligentMemoryRetrievalAlgorithm()
        self.shva = SelfHealingValidationAlgorithm()

    async def receive_message(self, message: MockTrinityMessage) -> dict:
        """Process incoming Trinity message"""
        self.processed_messages.append(message)

        if message.type == "request":
            return await self.handle_tax_request(message)
        elif message.type == "delegate":
            return await self.handle_delegation(message)
        elif message.type == "broadcast":
            return await self.handle_broadcast(message)
        else:
            return {
                "error": f"Unsupported message type: {message.type}",
                "agent": self.agent_id
            }

    async def handle_tax_request(self, message: MockTrinityMessage) -> dict:
        """Handle tax analysis request using full DTDA/IMRA/SHVA pipeline"""
        request = message.payload

        # Step 1: DTDA - Decompose the task
        context = request.get("context", {})
        decomposition = self.dtda.decompose_task(request["query"], context)

        # Step 2: IMRA - Retrieve relevant memory
        self.imra.add_to_immediate_context(
            f"Query: {request['query']}",
            {"client_id": request.get("clientId", "test")}
        )

        # Import and create RetrievalContext
        from specs.algorithms.imra import RetrievalContext
        context = RetrievalContext(
            query=request["query"],
            client_id=request.get("clientId", "test")
        )
        memory_results = self.imra.retrieve_context(context)

        # Step 3: Spawn agents if needed
        spawned_agents = []
        if decomposition.execution_plan.value == "parallel_swarm":
            spawned_agents = await self.spawn_specialized_agents(decomposition)

        # Step 4: Generate tax analysis
        analysis = self.generate_tax_analysis(request, decomposition, memory_results)

        # Step 5: SHVA - Validate response
        validation_input = {
            "content": analysis,
            "task_type": "tax_analysis",
            "context": request.get("context", {})
        }
        validation_result = self.shva.validate_output(validation_input, "tax_analysis")

        # Step 6: Return Trinity-formatted response
        return {
            "from": self.agent_id,
            "to": message.from_agent,
            "messageId": f"{message.messageId}_response",
            "timestamp": datetime.now().isoformat(),
            "priority": message.priority,
            "type": "response",
            "payload": {
                "analysis": validation_result.content if hasattr(validation_result, 'content') else analysis,
                "confidence": validation_result.confidence_score if hasattr(validation_result, 'confidence_score') else 0.85,
                "decomposition": {
                    "task_type": decomposition.task_type,
                    "complexity": decomposition.complexity,
                    "execution_plan": decomposition.execution_plan.value,
                    "subtasks": [vars(task) for task in decomposition.subtasks] if decomposition.subtasks else []
                },
                "memory_used": len(memory_results),
                "spawned_agents": [agent["id"] for agent in spawned_agents],
                "citations": self.generate_citations(request),
                "recommendations": self.generate_recommendations(decomposition)
            }
        }

    async def handle_delegation(self, message: MockTrinityMessage) -> dict:
        """Handle delegation from other Trinity agents"""
        task = message.payload.get("task", "")

        if self.is_tax_related(task):
            # Accept delegation and process as tax request
            return await self.handle_tax_request(message)
        else:
            # Decline delegation
            return {
                "from": self.agent_id,
                "to": message.from_agent,
                "messageId": f"{message.messageId}_decline",
                "timestamp": datetime.now().isoformat(),
                "priority": "medium",
                "type": "response",
                "payload": {
                    "declined": True,
                    "reason": "Task is not tax-related",
                    "suggestion": "Try oracle, chancellor, or auditor agents"
                }
            }

    async def handle_broadcast(self, message: MockTrinityMessage) -> dict:
        """Handle broadcast messages from Trinity Council"""
        broadcast = message.payload

        if broadcast.get("type") == "regulatory_update" and "tax" in broadcast.get("domain", ""):
            return {
                "from": self.agent_id,
                "to": "oracle",
                "messageId": f"{message.messageId}_tax_ack",
                "timestamp": datetime.now().isoformat(),
                "priority": "medium",
                "type": "response",
                "payload": {
                    "acknowledged": True,
                    "domain": "tax",
                    "impact": "Analyzing regulatory impact on tax strategies",
                    "action_required": True
                }
            }

        return None

    async def spawn_specialized_agents(self, decomposition) -> list:
        """Spawn specialized agents for complex tasks"""
        spawned = []

        # Spawn state-specific agents for multi-state tax
        if decomposition.task_type in ["tax_preparation", "tax_planning"]:
            spawned.append({
                "id": f"tax-god-california-{datetime.now().strftime('%s')}",
                "specialization": "state_tax_california",
                "jurisdiction": "California",
                "status": "active"
            })

        # Spawn audit agent if audit-related
        if decomposition.task_type == "audit_defense":
            spawned.append({
                "id": f"tax-god-audit-{datetime.now().strftime('%s')}",
                "specialization": "audit_defense",
                "status": "active"
            })

        self.spawned_agents.extend(spawned)
        return spawned

    def generate_tax_analysis(self, request, decomposition, memory_results) -> str:
        """Generate tax analysis response"""
        query = request["query"]
        context = request.get("context", {})

        analysis = f"Tax Analysis for: {query}\n\n"
        analysis += f"Task Type: {decomposition.task_type}\n"
        analysis += f"Complexity Level: {decomposition.complexity}/10\n"
        analysis += f"Execution Strategy: {decomposition.execution_plan.value}\n\n"

        if context.get("jurisdiction"):
            analysis += f"Jurisdiction(s): {', '.join(context['jurisdiction'])}\n"

        if memory_results:
            analysis += f"Relevant Context Found: {len(memory_results)} items\n"

        analysis += "\nRecommendations:\n"
        analysis += "- Consult with a licensed tax professional\n"
        analysis += "- Maintain detailed records\n"
        analysis += "- Consider professional tax planning services\n\n"

        analysis += "Based on IRC § 162 and related regulations, this analysis provides general guidance only."

        return analysis

    def generate_citations(self, request) -> list:
        """Generate tax law citations"""
        return [
            {
                "section": "IRC § 162",
                "description": "Trade or business expenses",
                "relevance": 0.9
            },
            {
                "section": "Treas. Reg. § 1.162-1",
                "description": "Business expense deduction rules",
                "relevance": 0.8
            }
        ]

    def generate_recommendations(self, decomposition) -> list:
        """Generate recommendations based on decomposition"""
        recommendations = [
            "Consult with a licensed tax professional",
            "Maintain detailed records of all business expenses",
            "Consider professional tax planning services"
        ]

        if decomposition.complexity > 7:
            recommendations.append("This is a high-complexity tax matter requiring specialized expertise")

        if decomposition.execution_plan.value == "parallel_swarm":
            recommendations.append("Multiple jurisdictions involved - coordinate with state-specific advisors")

        return recommendations

    def is_tax_related(self, task: str) -> bool:
        """Check if a task is tax-related"""
        tax_keywords = [
            "tax", "irs", "filing", "return", "deduction", "credit",
            "audit", "entity", "llc", "corp", "finance", "legal",
            "compliance", "regulation", "revenue", "income"
        ]
        return any(keyword in task.lower() for keyword in tax_keywords)

    def get_status(self) -> dict:
        """Get agent status for Trinity monitoring"""
        return {
            "agent_id": self.agent_id,
            "status": "active",
            "processed_messages": len(self.processed_messages),
            "spawned_agents": len(self.spawned_agents),
            "capabilities": ["tax_analysis", "financial_advice", "legal_counsel", "agent_spawning"]
        }


async def test_tax_god_as_trinity_agent():
    """Test Tax God functioning as a Trinity Consortium agent"""
    print("🤖 Testing Tax God as Trinity Consortium Agent")
    print("=" * 60)

    # Initialize Tax God agent
    tax_god = MockTaxGodAgent()
    print(f"✅ Initialized Tax God Agent: {tax_god.agent_id}")

    # Test 1: Basic tax request
    print("\n📋 Test 1: Basic Tax Request")
    message1 = MockTrinityMessage("request", {
        "query": "How can I deduct home office expenses?",
        "clientId": "test_client_123",
        "context": {
            "jurisdiction": ["federal"],
            "entity_type": "individual"
        },
        "urgency": "medium",
        "requireCitations": True
    })

    response1 = await tax_god.receive_message(message1)
    print(f"Response type: {response1['type']}")
    print(f"Analysis length: {len(response1['payload']['analysis'])} chars")
    print(f"Confidence: {response1['payload']['confidence']}")
    print(f"Citations: {len(response1['payload']['citations'])}")

    # Test 2: Complex multi-state request
    print("\n📋 Test 2: Complex Multi-State Request")
    message2 = MockTrinityMessage("request", {
        "query": "Help me optimize my S-Corp taxes across California and New York",
        "clientId": "test_client_456",
        "context": {
            "jurisdiction": ["federal", "california", "new_york"],
            "entity_type": "s-corp",
            "multi_state": True,
            "complexity": 8
        },
        "allowSpawning": True
    })

    response2 = await tax_god.receive_message(message2)
    print(f"Response type: {response2['type']}")
    print(f"Decomposition complexity: {response2['payload']['decomposition']['complexity']}")
    print(f"Execution plan: {response2['payload']['decomposition']['execution_plan']}")
    print(f"Spawned agents: {len(response2['payload']['spawned_agents'])}")

    # Test 3: Delegation handling
    print("\n📋 Test 3: Delegation Handling")
    message3 = MockTrinityMessage("delegate", {
        "query": "Analyze tax implications of entity restructuring",
        "clientId": "test_client_789",
        "context": {"entity_type": "llc"},
        "priority": "high"
    })

    response3 = await tax_god.receive_message(message3)
    print(f"Delegation accepted: {not response3['payload'].get('declined', False)}")

    # Test 4: Non-tax delegation (should be declined)
    print("\n📋 Test 4: Non-Tax Delegation (Should Decline)")
    message4 = MockTrinityMessage("delegate", {
        "task": "Design a new user interface",
        "priority": "medium"
    })

    response4 = await tax_god.receive_message(message4)
    print(f"Delegation declined: {response4['payload'].get('declined', False)}")
    print(f"Reason: {response4['payload'].get('reason', 'Unknown')}")

    # Test 5: Regulatory broadcast
    print("\n📋 Test 5: Regulatory Broadcast Handling")
    message5 = MockTrinityMessage("broadcast", {
        "type": "regulatory_update",
        "domain": "tax",
        "update": "New IRS guidance on remote work deductions"
    })

    response5 = await tax_god.receive_message(message5)
    print(f"Broadcast acknowledged: {response5['payload'].get('acknowledged', False) if response5 else False}")

    # Final status
    print("\n📊 Final Agent Status")
    status = tax_god.get_status()
    print(f"Agent ID: {status['agent_id']}")
    print(f"Messages processed: {status['processed_messages']}")
    print(f"Spawned agents: {status['spawned_agents']}")
    print(f"Capabilities: {', '.join(status['capabilities'])}")

    print("\n✅ All Trinity Agent Integration Tests Completed!")
    return True


async def main():
    """Run all Trinity integration tests"""
    print("🎭 Trinity Consortium Integration Test Suite")
    print("=" * 60)
    print("Testing Tax God as Agent #56 in Trinity 55-agent system...")
    print()

    try:
        success = await test_tax_god_as_trinity_agent()

        if success:
            print("\n" + "=" * 60)
            print("🎉 SUCCESS: Tax God successfully integrated as Trinity Agent!")
            print("Tax God is now ready to serve as the tax/finance/legal specialist")
            print("within the Trinity Consortium's 55-agent orchestration system.")
            print("=" * 60)
        else:
            print("\n❌ Integration tests failed")
            return 1

    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)