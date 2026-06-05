"""
Dynamic Task Decomposition Algorithm (DTDA)
============================================
Intelligently breaks complex requests into optimal sub-tasks with dependency
mapping for parallel or sequential execution.

Author: Tax God v3.0 System
License: Proprietary
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ExecutionPlan(Enum):
    """Execution plan types"""
    DIRECT = "direct"
    PARALLEL_SWARM = "parallel_swarm"
    SEQUENTIAL_SPECIALIZED = "sequential_specialized"


class TaskType(Enum):
    """Primary task categories"""
    TAX_PREPARATION = "tax_preparation"
    TAX_PLANNING = "tax_planning"
    LEGAL_ENTITY = "legal_entity"
    FINANCIAL_ANALYSIS = "financial_analysis"
    AUDIT_DEFENSE = "audit_defense"
    COMPLIANCE = "compliance"
    RESEARCH = "research"


@dataclass
class SubTask:
    """Represents a decomposed sub-task"""
    task: str
    priority: int
    agent_type: Optional[str] = None
    estimated_cost: float = 0.0
    estimated_time: int = 0  # seconds


@dataclass
class DecompositionResult:
    """Result of task decomposition"""
    execution_plan: ExecutionPlan
    task_type: TaskType
    complexity: float
    subtasks: List[SubTask]
    dependency_graph: Dict[int, List[int]]
    swarm_size: Optional[int] = None
    agents_needed: Optional[List[str]] = None
    estimated_cost: float = 0.0
    estimated_time: int = 0  # seconds
    parallelization_score: float = 0.0


class DynamicTaskDecompositionAlgorithm:
    """
    DTDA - Core algorithm for intelligent task breakdown

    Features:
    - Automatic complexity analysis
    - Intelligent task classification
    - Dependency graph generation
    - Parallel vs sequential optimization
    - Cost and time estimation
    """

    # Task classification keywords
    TASK_CATEGORIES = {
        TaskType.TAX_PREPARATION: ['1040', '1120', '1065', 'return', 'filing', 'form'],
        TaskType.TAX_PLANNING: ['minimize', 'optimize', 'strategy', 'deduction', 'planning'],
        TaskType.LEGAL_ENTITY: ['LLC', 'S-Corp', 'C-Corp', 'formation', 'structure', 'entity'],
        TaskType.FINANCIAL_ANALYSIS: ['cash flow', 'forecast', 'budget', 'valuation', 'analysis'],
        TaskType.AUDIT_DEFENSE: ['audit', 'notice', 'IRS', 'examination', 'defense'],
        TaskType.COMPLIANCE: ['file', 'deadline', 'extension', 'amendment', 'compliance'],
        TaskType.RESEARCH: ['what is', 'how do', 'explain', 'requirements', 'research']
    }

    # Calculated fields for validation
    CALCULATED_FIELDS = [
        'adjusted_gross_income', 'taxable_income', 'total_tax',
        'self_employment_tax', 'estimated_tax_payments'
    ]

    # Technical terms for complexity scoring
    TECHNICAL_TERMS = [
        'depreciation', 'amortization', 'capital gains', 'ordinary income',
        'passive activity', 'at-risk rules', 'basis', 'carryforward',
        'alternative minimum tax', 'net operating loss', 'section 179'
    ]

    # US states for multi-state detection
    US_STATES = [
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
        'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
        'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
        'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
        'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
        'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
        'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
        'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
        'West Virginia', 'Wisconsin', 'Wyoming', 'DC'
    ]

    def decompose_task(
        self,
        user_request: str,
        client_context: Optional[Dict[str, Any]] = None
    ) -> DecompositionResult:
        """
        Main decomposition pipeline

        Args:
            user_request: The user's natural language request
            client_context: Optional client profile and history data

        Returns:
            DecompositionResult with execution plan and metadata
        """
        # Stage 1: Parse and classify request
        task_type = self.classify_request(user_request)
        complexity = self.analyze_complexity(user_request, task_type)

        # Stage 2: Determine if decomposition needed
        if complexity < 3:
            # Simple task - direct execution
            return DecompositionResult(
                execution_plan=ExecutionPlan.DIRECT,
                task_type=task_type,
                complexity=complexity,
                subtasks=[SubTask(task='execute', priority=1)],
                dependency_graph={0: []},
                agents_needed=[self._select_single_agent(task_type)],
                estimated_cost=0.03,  # $0.01-0.05 range
                estimated_time=5  # 3-8 seconds
            )

        # Stage 3: Break into components
        subtasks = self._break_into_components(user_request, task_type)

        # Stage 4: Build dependency graph
        dependency_graph = self._build_dependencies(subtasks)

        # Stage 5: Calculate parallelization score
        parallelization_score = self._calculate_parallelization_score(dependency_graph)

        # Stage 6: Optimize execution path
        if parallelization_score >= 60:
            # Parallel execution via OpenClaw swarm
            return DecompositionResult(
                execution_plan=ExecutionPlan.PARALLEL_SWARM,
                task_type=task_type,
                complexity=complexity,
                subtasks=subtasks,
                dependency_graph=dependency_graph,
                swarm_size=len(subtasks),
                parallelization_score=parallelization_score,
                estimated_cost=0.05 + (len(subtasks) * 0.004),
                estimated_time=120  # 60-180 seconds
            )
        else:
            # Sequential execution with specialist agents
            execution_order = self._topological_sort(dependency_graph, subtasks)
            agents_needed = [self._assign_agent(st) for st in execution_order]

            return DecompositionResult(
                execution_plan=ExecutionPlan.SEQUENTIAL_SPECIALIZED,
                task_type=task_type,
                complexity=complexity,
                subtasks=execution_order,
                dependency_graph=dependency_graph,
                agents_needed=agents_needed,
                parallelization_score=parallelization_score,
                estimated_cost=sum([self._estimate_subtask_cost(st) for st in subtasks]),
                estimated_time=sum([self._estimate_subtask_time(st) for st in subtasks])
            )

    def classify_request(self, request: str) -> TaskType:
        """
        Classify request into primary categories using keyword matching

        Args:
            request: User's natural language request

        Returns:
            TaskType enum value
        """
        request_lower = request.lower()
        scores = {}

        for task_type, keywords in self.TASK_CATEGORIES.items():
            score = sum(1 for keyword in keywords if keyword.lower() in request_lower)
            scores[task_type] = score

        # Return category with highest score, default to RESEARCH
        if max(scores.values()) == 0:
            return TaskType.RESEARCH

        return max(scores, key=scores.get)

    def analyze_complexity(self, request: str, task_type: TaskType) -> float:
        """
        Rate complexity on 1-10 scale

        Args:
            request: User's request text
            task_type: Classified task type

        Returns:
            Complexity score (1.0 - 10.0)
        """
        complexity_factors = {
            'word_count': len(request.split()),
            'technical_terms': self._count_technical_terms(request),
            'multi_year': 'previous year' in request.lower() or 'last 3 years' in request.lower(),
            'multi_state': self._count_states_mentioned(request),
            'entity_count': self._count_entities_mentioned(request)
        }

        # Weighted complexity calculation
        score = 1.0
        score += min(complexity_factors['word_count'] / 20, 2.0)
        score += min(complexity_factors['technical_terms'] / 5, 2.0)
        score += 2.0 if complexity_factors['multi_year'] else 0
        score += min(complexity_factors['multi_state'] * 0.5, 2.0)
        score += min(complexity_factors['entity_count'] * 0.8, 2.0)

        return min(score, 10.0)

    def _count_technical_terms(self, text: str) -> int:
        """Count technical tax terms in text"""
        text_lower = text.lower()
        return sum(1 for term in self.TECHNICAL_TERMS if term in text_lower)

    def _count_states_mentioned(self, text: str) -> int:
        """Count US states mentioned in text"""
        count = 0
        for state in self.US_STATES:
            if re.search(r'\b' + re.escape(state) + r'\b', text, re.IGNORECASE):
                count += 1
        return count

    def _count_entities_mentioned(self, text: str) -> int:
        """Count business entities mentioned"""
        entity_patterns = [
            r'\bLLC\b', r'\bS-Corp\b', r'\bC-Corp\b',
            r'\bpartnership\b', r'\bcorporation\b'
        ]
        count = 0
        for pattern in entity_patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count

    def _break_into_components(
        self,
        request: str,
        task_type: TaskType
    ) -> List[SubTask]:
        """
        Decompose into logical subtasks based on task type

        Args:
            request: User's request
            task_type: Classified task type

        Returns:
            List of SubTask objects
        """
        if task_type == TaskType.TAX_PREPARATION:
            return [
                SubTask(task='gather_documents', priority=1),
                SubTask(task='extract_data', priority=2),
                SubTask(task='calculate_tax', priority=3),
                SubTask(task='fill_forms', priority=4),
                SubTask(task='validate', priority=5),
                SubTask(task='e_file', priority=6)
            ]

        elif task_type == TaskType.TAX_PLANNING:
            return [
                SubTask(task='analyze_current_situation', priority=1),
                SubTask(task='identify_opportunities', priority=2),
                SubTask(task='model_scenarios', priority=3),
                SubTask(task='recommend_strategy', priority=4)
            ]

        elif task_type == TaskType.LEGAL_ENTITY:
            return [
                SubTask(task='analyze_business_structure', priority=1),
                SubTask(task='compare_entity_types', priority=2),
                SubTask(task='calculate_tax_implications', priority=3),
                SubTask(task='recommend_structure', priority=4)
            ]

        elif task_type == TaskType.FINANCIAL_ANALYSIS:
            return [
                SubTask(task='gather_financial_data', priority=1),
                SubTask(task='calculate_ratios', priority=2),
                SubTask(task='benchmark_analysis', priority=3),
                SubTask(task='generate_report', priority=4)
            ]

        elif task_type == TaskType.AUDIT_DEFENSE:
            return [
                SubTask(task='analyze_notice', priority=1),
                SubTask(task='gather_supporting_docs', priority=2),
                SubTask(task='prepare_response', priority=3),
                SubTask(task='review_strategy', priority=4)
            ]

        elif task_type == TaskType.COMPLIANCE:
            return [
                SubTask(task='identify_requirements', priority=1),
                SubTask(task='check_deadlines', priority=2),
                SubTask(task='prepare_filings', priority=3),
                SubTask(task='submit', priority=4)
            ]

        else:  # RESEARCH
            return [
                SubTask(task='search_knowledge_base', priority=1),
                SubTask(task='analyze_regulations', priority=2),
                SubTask(task='synthesize_answer', priority=3)
            ]

    def _build_dependencies(self, subtasks: List[SubTask]) -> Dict[int, List[int]]:
        """
        Create directed acyclic graph (DAG) of dependencies

        Args:
            subtasks: List of subtasks

        Returns:
            Dictionary mapping task index to list of dependency indices
        """
        dag = {}

        for i, task in enumerate(subtasks):
            dependencies = []

            # Simple heuristic: tasks depend on all previous tasks with lower priority
            for j, potential_dep in enumerate(subtasks):
                if j < i and potential_dep.priority < task.priority:
                    dependencies.append(j)

            dag[i] = dependencies

        return dag

    def _calculate_parallelization_score(self, dependency_graph: Dict[int, List[int]]) -> float:
        """
        Calculate what percentage of tasks can run in parallel

        Args:
            dependency_graph: DAG of task dependencies

        Returns:
            Parallelization score (0-100)
        """
        total_tasks = len(dependency_graph)
        if total_tasks == 0:
            return 0.0

        independent_tasks = sum(1 for deps in dependency_graph.values() if len(deps) == 0)

        parallelization_score = (independent_tasks / total_tasks) * 100

        return parallelization_score

    def _topological_sort(
        self,
        dependency_graph: Dict[int, List[int]],
        subtasks: List[SubTask]
    ) -> List[SubTask]:
        """
        Sort tasks in execution order respecting dependencies

        Args:
            dependency_graph: DAG of dependencies
            subtasks: List of subtasks

        Returns:
            Ordered list of subtasks
        """
        # Simple topological sort using priority (already sequential in our case)
        return sorted(subtasks, key=lambda x: x.priority)

    def _select_single_agent(self, task_type: TaskType) -> str:
        """Select appropriate agent for simple direct execution"""
        agent_map = {
            TaskType.TAX_PREPARATION: "TaxPreparationAgent",
            TaskType.TAX_PLANNING: "TaxPlanningAgent",
            TaskType.LEGAL_ENTITY: "LegalEntityAgent",
            TaskType.FINANCIAL_ANALYSIS: "FinancialAnalysisAgent",
            TaskType.AUDIT_DEFENSE: "AuditDefenseAgent",
            TaskType.COMPLIANCE: "ComplianceAgent",
            TaskType.RESEARCH: "ResearchAgent"
        }
        return agent_map.get(task_type, "GeneralAgent")

    def _assign_agent(self, subtask: SubTask) -> str:
        """Assign specialist agent based on subtask type"""
        # Map subtask names to specialized agents
        agent_assignments = {
            'gather_documents': "DocumentProcessingAgent",
            'extract_data': "DataExtractionAgent",
            'calculate_tax': "TaxCalculationAgent",
            'fill_forms': "FormFillingAgent",
            'validate': "ValidationAgent",
            'e_file': "EFileAgent",
            'analyze_current_situation': "FinancialAnalysisAgent",
            'identify_opportunities': "TaxPlanningAgent",
            'model_scenarios': "ScenarioModelingAgent",
            'recommend_strategy': "StrategyAgent",
        }

        return agent_assignments.get(subtask.task, "GeneralAgent")

    def _estimate_subtask_cost(self, subtask: SubTask) -> float:
        """Estimate cost for a subtask in dollars"""
        # Base costs per task type
        cost_map = {
            'gather_documents': 0.02,
            'extract_data': 0.05,
            'calculate_tax': 0.10,
            'fill_forms': 0.08,
            'validate': 0.03,
            'e_file': 0.02,
            'analyze_current_situation': 0.15,
            'identify_opportunities': 0.12,
            'model_scenarios': 0.20,
            'recommend_strategy': 0.10,
        }

        return cost_map.get(subtask.task, 0.05)

    def _estimate_subtask_time(self, subtask: SubTask) -> int:
        """Estimate time for a subtask in seconds"""
        # Base times per task type
        time_map = {
            'gather_documents': 10,
            'extract_data': 15,
            'calculate_tax': 20,
            'fill_forms': 18,
            'validate': 8,
            'e_file': 5,
            'analyze_current_situation': 25,
            'identify_opportunities': 30,
            'model_scenarios': 45,
            'recommend_strategy': 20,
        }

        return time_map.get(subtask.task, 10)


# Example usage
if __name__ == "__main__":
    dtda = DynamicTaskDecompositionAlgorithm()

    # Test 1: Simple request
    result1 = dtda.decompose_task("What is the standard deduction for 2024?")
    print("Test 1 - Simple Query:")
    print(f"  Execution Plan: {result1.execution_plan.value}")
    print(f"  Complexity: {result1.complexity:.2f}")
    print(f"  Estimated Cost: ${result1.estimated_cost:.3f}")
    print(f"  Estimated Time: {result1.estimated_time}s")
    print()

    # Test 2: Complex multi-state business planning
    result2 = dtda.decompose_task(
        "I need help optimizing my S-Corp tax strategy across California and New York, "
        "including depreciation schedules and estimated tax payments for last 3 years"
    )
    print("Test 2 - Complex Query:")
    print(f"  Execution Plan: {result2.execution_plan.value}")
    print(f"  Task Type: {result2.task_type.value}")
    print(f"  Complexity: {result2.complexity:.2f}")
    print(f"  Subtasks: {len(result2.subtasks)}")
    print(f"  Parallelization Score: {result2.parallelization_score:.1f}%")
    print(f"  Estimated Cost: ${result2.estimated_cost:.3f}")
    print(f"  Estimated Time: {result2.estimated_time}s")
    print("  Subtask List:")
    for i, st in enumerate(result2.subtasks):
        print(f"    {i+1}. {st.task} (priority: {st.priority})")
