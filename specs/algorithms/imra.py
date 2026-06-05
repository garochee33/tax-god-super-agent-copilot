"""
Intelligent Memory Retrieval Algorithm (IMRA)
==============================================
Multi-tier memory retrieval with semantic search, temporal weighting,
and knowledge graph traversal.

Author: Tax God v3.0 System
License: Proprietary
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class MemoryTier(Enum):
    """Memory storage tiers"""
    IMMEDIATE = "immediate"          # Tier 1: Current conversation
    SHORT_TERM = "short_term"        # Tier 2: Active session (24-72h)
    LONG_TERM = "long_term"          # Tier 3: Client history (years)
    KNOWLEDGE_BASE = "knowledge_base"  # Tier 4: Universal tax knowledge
    COLLECTIVE = "collective"        # Tier 5: Anonymized patterns


@dataclass
class MemoryResult:
    """A single memory retrieval result"""
    content: str
    score: float
    timestamp: Optional[datetime] = None
    source: str = "unknown"
    tier: Optional[MemoryTier] = None
    temporal_weight: float = 1.0
    final_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalContext:
    """Context for memory retrieval"""
    query: str
    client_id: str
    max_results: int = 10
    include_collective: bool = True
    time_range_days: Optional[int] = None  # Limit to recent memories


class IntelligentMemoryRetrievalAlgorithm:
    """
    IMRA - Multi-tier memory retrieval with intelligent ranking

    Features:
    - 5-tier memory architecture
    - Semantic vector search
    - Temporal decay weighting
    - Knowledge graph traversal
    - Collective intelligence queries
    - Multi-factor ranking
    """

    # Tier priorities for ranking
    TIER_PRIORITIES = {
        MemoryTier.IMMEDIATE: 1.0,
        MemoryTier.SHORT_TERM: 0.9,
        MemoryTier.LONG_TERM: 0.8,
        MemoryTier.KNOWLEDGE_BASE: 0.85,
        MemoryTier.COLLECTIVE: 0.7
    }

    def __init__(
        self,
        vector_db=None,
        neo4j_db=None,
        collective_db=None,
        embedding_model=None
    ):
        """
        Initialize IMRA with database connections

        Args:
            vector_db: Vector database client (Pinecone/Weaviate)
            neo4j_db: Neo4j graph database client
            collective_db: Collective intelligence database
            embedding_model: Text embedding model
        """
        self.vector_db = vector_db
        self.neo4j_db = neo4j_db
        self.collective_db = collective_db
        self.embedding_model = embedding_model

        # In-memory caches for immediate and short-term memory
        self.immediate_context: List[MemoryResult] = []
        self.short_term_cache: Dict[str, List[MemoryResult]] = {}

    def retrieve_context(
        self,
        context: RetrievalContext
    ) -> List[MemoryResult]:
        """
        Main retrieval pipeline

        Args:
            context: RetrievalContext with query and parameters

        Returns:
            Ranked list of MemoryResult objects
        """
        all_candidates = []

        # Stage 1: Immediate context (Tier 1)
        immediate = self._get_immediate_context()
        all_candidates.extend(immediate)

        # Stage 2: Semantic vector search (Tier 2-3)
        vector_matches = self._semantic_search(
            query=context.query,
            namespace=context.client_id,
            top_k=50
        )
        all_candidates.extend(vector_matches)

        # Stage 3: Temporal weighting
        time_weighted = self._apply_temporal_decay(
            all_candidates,
            half_life_days=90
        )

        # Stage 4: Knowledge graph traversal (Tier 4)
        if self.neo4j_db:
            related_concepts = self._traverse_knowledge_graph(
                query=context.query,
                depth=2,
                max_nodes=30
            )
            time_weighted.extend(related_concepts)

        # Stage 5: Collective intelligence (Tier 5)
        if context.include_collective and self.collective_db:
            query_embedding = self._embed(context.query)
            similar_patterns = self._query_collective_intelligence(
                query_embedding=query_embedding,
                exclude_client_id=context.client_id
            )
            time_weighted.extend(similar_patterns)

        # Stage 6: Synthesize and rank
        ranked = self._rank_results(time_weighted, context.query)

        # Apply time range filter if specified
        if context.time_range_days:
            cutoff_date = datetime.utcnow() - timedelta(days=context.time_range_days)
            ranked = [r for r in ranked if r.timestamp and r.timestamp >= cutoff_date]

        return ranked[:context.max_results]

    def add_to_immediate_context(self, content: str, metadata: Optional[Dict] = None):
        """
        Add content to immediate context (Tier 1)

        Args:
            content: Content to add
            metadata: Optional metadata
        """
        result = MemoryResult(
            content=content,
            score=1.0,
            timestamp=datetime.utcnow(),
            source="immediate_context",
            tier=MemoryTier.IMMEDIATE,
            metadata=metadata or {}
        )
        self.immediate_context.append(result)

        # Keep only last 20 items in immediate context
        if len(self.immediate_context) > 20:
            self.immediate_context = self.immediate_context[-20:]

    def clear_immediate_context(self):
        """Clear immediate context (e.g., at end of conversation)"""
        self.immediate_context = []

    def _get_immediate_context(self) -> List[MemoryResult]:
        """
        Retrieve immediate context (Tier 1)

        Returns:
            List of recent conversation items
        """
        return self.immediate_context.copy()

    def _semantic_search(
        self,
        query: str,
        namespace: str,
        top_k: int = 50
    ) -> List[MemoryResult]:
        """
        Vector similarity search in vector database

        Args:
            query: Search query
            namespace: Client namespace for isolation
            top_k: Number of results

        Returns:
            List of matching MemoryResult objects
        """
        if not self.vector_db:
            return []

        query_embedding = self._embed(query)

        try:
            # Mock vector DB query (replace with actual implementation)
            results = self._mock_vector_search(query_embedding, namespace, top_k)

            return [
                MemoryResult(
                    content=r['text'],
                    score=r['score'],
                    timestamp=r.get('timestamp'),
                    source='vector_db',
                    tier=MemoryTier.LONG_TERM if r.get('age_days', 0) > 3 else MemoryTier.SHORT_TERM,
                    metadata=r.get('metadata', {})
                )
                for r in results
            ]
        except Exception as e:
            print(f"Vector search error: {e}")
            return []

    def _apply_temporal_decay(
        self,
        results: List[MemoryResult],
        half_life_days: int = 90
    ) -> List[MemoryResult]:
        """
        Apply exponential decay to older memories

        Args:
            results: List of memory results
            half_life_days: Half-life for decay (default 90 days)

        Returns:
            Results with temporal weighting applied
        """
        now = datetime.utcnow()

        for result in results:
            if result.timestamp:
                age_days = (now - result.timestamp).days
                decay_factor = math.exp(-math.log(2) * age_days / half_life_days)
                result.temporal_weight = decay_factor
                result.score *= decay_factor
            else:
                # No timestamp = assume recent
                result.temporal_weight = 1.0

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _traverse_knowledge_graph(
        self,
        query: str,
        depth: int = 2,
        max_nodes: int = 30
    ) -> List[MemoryResult]:
        """
        Neo4j graph traversal to find conceptually related nodes

        Args:
            query: Search query
            depth: Traversal depth
            max_nodes: Maximum nodes to return

        Returns:
            List of related knowledge items
        """
        if not self.neo4j_db:
            return []

        # Extract entities/concepts from query
        entities = self._extract_entities(query)

        if not entities:
            return []

        try:
            # Mock Neo4j query (replace with actual implementation)
            results = self._mock_graph_traversal(entities, depth, max_nodes)

            return [
                MemoryResult(
                    content=r['text'],
                    score=0.8 / (r['path_length'] + 1),  # Closer nodes = higher score
                    source='knowledge_graph',
                    tier=MemoryTier.KNOWLEDGE_BASE,
                    metadata={'path_length': r['path_length']}
                )
                for r in results
            ]
        except Exception as e:
            print(f"Graph traversal error: {e}")
            return []

    def _query_collective_intelligence(
        self,
        query_embedding: List[float],
        exclude_client_id: str
    ) -> List[MemoryResult]:
        """
        Anonymized pattern matching across all clients

        Args:
            query_embedding: Query vector embedding
            exclude_client_id: Client to exclude (privacy)

        Returns:
            List of collective patterns
        """
        if not self.collective_db:
            return []

        try:
            # Mock collective DB query (replace with actual implementation)
            patterns = self._mock_collective_search(query_embedding, exclude_client_id)

            return [
                MemoryResult(
                    content=p['pattern_description'],
                    score=p['frequency'] / 100,  # Normalize frequency
                    source='collective_intelligence',
                    tier=MemoryTier.COLLECTIVE,
                    metadata={'frequency': p['frequency']}
                )
                for p in patterns
            ]
        except Exception as e:
            print(f"Collective intelligence error: {e}")
            return []

    def _rank_results(
        self,
        candidates: List[MemoryResult],
        query: str
    ) -> List[MemoryResult]:
        """
        Final ranking with multiple factors

        Args:
            candidates: List of candidate results
            query: Original query

        Returns:
            Ranked results
        """
        query_embedding = self._embed(query)

        for candidate in candidates:
            # Calculate semantic similarity
            semantic_sim = self._calculate_semantic_similarity(
                query_embedding,
                candidate.content
            )

            # Get source priority
            source_priority = self._calculate_source_priority(candidate.source)

            # Tier priority
            tier_priority = self.TIER_PRIORITIES.get(candidate.tier, 0.5)

            # Multi-factor scoring
            candidate.final_score = (
                candidate.score * 0.3 +              # Base relevance
                semantic_sim * 0.3 +                 # Semantic similarity
                candidate.temporal_weight * 0.2 +    # Recency
                source_priority * 0.1 +              # Source reliability
                tier_priority * 0.1                  # Tier importance
            )

        return sorted(candidates, key=lambda x: x.final_score, reverse=True)

    def _embed(self, text: str) -> List[float]:
        """
        Generate text embedding vector

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.embedding_model:
            return self.embedding_model.encode(text)

        # Mock embedding: simple hash-based vector
        return self._mock_embedding(text)

    def _calculate_semantic_similarity(
        self,
        query_embedding: List[float],
        content: str
    ) -> float:
        """
        Calculate semantic similarity between query and content

        Args:
            query_embedding: Query vector
            content: Content text

        Returns:
            Similarity score (0-1)
        """
        content_embedding = self._embed(content)

        # Cosine similarity
        return self._cosine_similarity(query_embedding, content_embedding)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _calculate_source_priority(self, source: str) -> float:
        """Calculate priority score based on source"""
        source_priorities = {
            'immediate_context': 1.0,
            'vector_db': 0.9,
            'knowledge_graph': 0.85,
            'collective_intelligence': 0.7,
            'unknown': 0.5
        }
        return source_priorities.get(source, 0.5)

    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract key entities and concepts from text

        Args:
            text: Input text

        Returns:
            List of entities
        """
        # Simple keyword extraction (replace with NLP entity extraction)
        tax_keywords = [
            'deduction', 'credit', 'income', 'AGI', 'depreciation',
            'capital gains', 'ordinary income', 'passive activity',
            'S-Corp', 'LLC', 'partnership', 'C-Corp', 'IRA', '401k'
        ]

        text_lower = text.lower()
        entities = [kw for kw in tax_keywords if kw in text_lower]

        return entities[:10]  # Limit to 10 entities

    # Mock implementations (replace with actual DB queries)

    def _mock_embedding(self, text: str) -> List[float]:
        """Mock embedding generation"""
        # Simple hash-based vector (128 dimensions)
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to float vector
        vector = [float(b) / 255.0 for b in hash_bytes[:128]]

        # Pad if needed
        while len(vector) < 128:
            vector.append(0.0)

        return vector[:128]

    def _mock_vector_search(
        self,
        embedding: List[float],
        namespace: str,
        top_k: int
    ) -> List[Dict]:
        """Mock vector database search"""
        # Return mock results
        now = datetime.utcnow()

        return [
            {
                'text': "Client filed 1040 for tax year 2023 with AGI of $95,000",
                'score': 0.92,
                'timestamp': now - timedelta(days=30),
                'age_days': 30,
                'metadata': {'form': '1040', 'year': 2023}
            },
            {
                'text': "Previous consultation about home office deduction eligibility",
                'score': 0.88,
                'timestamp': now - timedelta(days=60),
                'age_days': 60,
                'metadata': {'topic': 'deductions'}
            },
            {
                'text': "Client has rental property in California generating $2,400/month",
                'score': 0.85,
                'timestamp': now - timedelta(days=90),
                'age_days': 90,
                'metadata': {'asset_type': 'rental'}
            }
        ]

    def _mock_graph_traversal(
        self,
        entities: List[str],
        depth: int,
        max_nodes: int
    ) -> List[Dict]:
        """Mock knowledge graph traversal"""
        return [
            {
                'text': "IRC Section 179 allows immediate expensing of qualifying property",
                'path_length': 1
            },
            {
                'text': "Home office deduction requires exclusive and regular business use",
                'path_length': 2
            }
        ]

    def _mock_collective_search(
        self,
        embedding: List[float],
        exclude_client: str
    ) -> List[Dict]:
        """Mock collective intelligence search"""
        return [
            {
                'pattern_description': "85% of S-Corp owners benefit from salary optimization",
                'frequency': 85
            },
            {
                'pattern_description': "Cost segregation studies average $18K tax savings",
                'frequency': 72
            }
        ]


# Example usage
if __name__ == "__main__":
    imra = IntelligentMemoryRetrievalAlgorithm()

    # Add some immediate context
    imra.add_to_immediate_context(
        "User asked about S-Corp tax benefits",
        metadata={'topic': 'entity_structure'}
    )
    imra.add_to_immediate_context(
        "User mentioned owning a consulting business",
        metadata={'business_type': 'consulting'}
    )

    # Test retrieval
    context = RetrievalContext(
        query="How can I optimize my S-Corp tax strategy?",
        client_id="client_123",
        max_results=5
    )

    results = imra.retrieve_context(context)

    print(f"Retrieved {len(results)} relevant memories:")
    print()

    for i, result in enumerate(results, 1):
        print(f"{i}. [{result.tier.value if result.tier else 'unknown'}] "
              f"Score: {result.final_score:.3f}")
        print(f"   {result.content[:100]}...")
        print(f"   Source: {result.source}, Temporal Weight: {result.temporal_weight:.3f}")
        print()
