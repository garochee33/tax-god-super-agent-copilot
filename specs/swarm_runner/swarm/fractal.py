"""
Fractal AGI Web of Life — Knowledge Core, Planner, Routing.

Aligns with: Input & Encoding, Planner/Conductor, Fractal Knowledge Core,
Routing/Physics/Belief Engine. See docs/FRACTAL_AGI_OMNISYNTH_INGEST.md.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class NodeArchetype(str, Enum):
    """Sacred geometry node archetypes (Fractal Knowledge Core)."""
    SEED = "seed"      # Minimal, generative anchor
    PATTERN = "pattern"  # Recurring structure
    ARTIFACT = "artifact"  # Concrete output (code, patch, doc)


@dataclass
class FractalNode:
    """Single node in the geometry-tag hierarchy."""
    id: str
    archetype: NodeArchetype
    geometry_tag: str  # Symbolic tag for routing/clustering
    payload: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    energy_cost: float = 0.0  # For least-action routing


@dataclass
class TaskDescriptor:
    """Input-layer task specification (Planner input)."""
    goal: str
    repo_root: Path
    geometry_tags: List[str] = field(default_factory=list)
    max_energy: Optional[float] = None


@dataclass
class SubTask:
    """Planner output: one decomposed subtask with energy assignment."""
    id: str
    goal: str
    role_hint: str  # e.g. architect, reasoner, developer
    energy_budget: float
    geometry_tags: List[str] = field(default_factory=list)


def decompose_goal(goal: str, repo_map_len: int) -> List[SubTask]:
    """
    Planner: task decomposition and energy assignment.
    Returns subtasks with role hints and energy budgets (Fibonacci-like scaling).
    """
    # Fibonacci-like weights for role ordering (least-action preference)
    weights = {
        "reasoner": 1,
        "architect": 2,
        "feature": 2,
        "implementer": 3,
        "refactor": 3,
        "bugfix": 3,
        "debugger": 3,
        "tests": 3,
        "optimizer": 3,
        "security": 3,
        "docs": 2,
        "teacher": 2,
        "critic": 5,
    }
    base = 1.0 / max(sum(weights.values()), 1)
    subtasks: List[SubTask] = []
    for i, (role, w) in enumerate(weights.items()):
        subtasks.append(SubTask(
            id=f"st_{i}",
            goal=goal,
            role_hint=role,
            energy_budget=w * base,
            geometry_tags=[],
        ))
    return subtasks


def energy_cost_for_agent(agent_name: str, constraints: Dict[str, str]) -> float:
    """
    Routing: energy cost scoring (lower = prefer first in least-action).
    """
    cost = 1.0
    name_lower = agent_name.lower()
    if "reasoner" in name_lower or "critic" in name_lower:
        cost = 0.5  # High value, run early for cognition
    elif "architect" in name_lower or "feature" in name_lower:
        cost = 1.0
    elif "implementer" in name_lower or "bugfix" in name_lower:
        cost = 2.0
    elif "review" in name_lower:
        cost = 3.0  # Gate at end
    return cost


def order_agents_least_action(agent_names: List[str], constraints: Dict[str, str]) -> List[str]:
    """Route agents by energy cost (ascending) for least-action ordering."""
    with_cost = [(name, energy_cost_for_agent(name, constraints)) for name in agent_names]
    with_cost.sort(key=lambda x: x[1])
    return [name for name, _ in with_cost]


def get_subtask_goal_for_role(
    role_hint: str,
    subtasks: List[SubTask],
    fallback_goal: str,
) -> str:
    """Return subtask goal for role_hint; fallback if none match."""
    for st in subtasks:
        if st.role_hint == role_hint:
            return st.goal
    return fallback_goal


# --- Fractal memory: persist nodes and retrieve by relevance ---

# Optional: ChromaDB for vector similarity search
_CHROMADB = None
try:
    import chromadb
    _CHROMADB = chromadb
except Exception:
    pass

# Optional: Mem0 for persistent AI memory
_MEM0 = None
try:
    from mem0 import Memory
    _MEM0 = Memory
except Exception:
    pass


class FractalMemoryStore:
    """
    Persist FractalNodes to workspace and retrieve by relevance.

    Supports three backends (auto-selected based on availability):
    1. Mem0 (if installed): Production-grade persistent memory with consolidation
    2. ChromaDB (if installed): Vector similarity search
    3. JSON (default): Simple keyword matching, always available
    """

    def __init__(
        self,
        workspace: Path,
        user_id: str = "agent_swarm",
        use_vector_store: bool = True,
        database_url: Optional[str] = None,
        memory_backend: Optional[str] = None,
    ) -> None:
        self.workspace = workspace
        self._path = workspace / "fractal_memory.json"
        self._nodes: List[Dict[str, Any]] = []
        self._user_id = user_id
        self._use_vector = use_vector_store
        self._database_url = database_url
        self._memory_backend = memory_backend

        # Initialize backends
        self._mem0: Optional[Any] = None
        self._chroma_client: Optional[Any] = None
        self._chroma_collection: Optional[Any] = None
        self._pgvector: Optional[Any] = None

        # Try pgvector hybrid if explicitly requested
        if memory_backend == "pgvector_hybrid" and database_url:
            try:
                from swarm.memory.pgvector_hybrid import PgvectorHybridStore
                self._pgvector = PgvectorHybridStore(database_url)
            except Exception:
                pass

        if _MEM0 and use_vector_store and not self._pgvector:
            try:
                self._mem0 = _MEM0()
            except Exception:
                pass

        if _CHROMADB and use_vector_store and not self._mem0 and not self._pgvector:
            try:
                chroma_path = workspace / "chroma_db"
                chroma_path.mkdir(parents=True, exist_ok=True)
                self._chroma_client = _CHROMADB.PersistentClient(path=str(chroma_path))
                self._chroma_collection = self._chroma_client.get_or_create_collection(
                    name="fractal_memory",
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception:
                self._chroma_client = None
                self._chroma_collection = None

    @property
    def backend(self) -> str:
        """Return the active backend name."""
        if self._pgvector:
            return "pgvector_hybrid"
        if self._mem0:
            return "mem0"
        if self._chroma_collection:
            return "chromadb"
        return "json"

    def load(self) -> None:
        """Load nodes from JSON file."""
        if self._path.exists():
            try:
                raw = self._path.read_text(encoding="utf-8")
                self._nodes = json.loads(raw)
            except Exception:
                self._nodes = []

    def save(self) -> None:
        """Save nodes to JSON file."""
        self.workspace.mkdir(parents=True, exist_ok=True)
        try:
            data = json.dumps(self._nodes, indent=2)
        except TypeError:
            # Defensive: payloads may sometimes contain Paths/objects in evidence.
            # Preserve data rather than crashing the run.
            data = json.dumps(self._nodes, indent=2, default=str)
        self._path.write_text(data, encoding="utf-8")

    def add_node(
        self,
        archetype: str,
        geometry_tag: str,
        payload: Dict[str, Any],
        energy_cost: float = 0.0,
    ) -> str:
        """Add a node to memory. Returns the node ID."""
        node_id = str(uuid.uuid4())
        node = {
            "id": node_id,
            "archetype": archetype,
            "geometry_tag": geometry_tag,
            "payload": payload,
            "energy_cost": energy_cost,
        }
        self._nodes.append(node)
        self.save()

        # Add to vector store if available
        content = self._payload_to_text(payload)
        if self._mem0 and content:
            try:
                self._mem0.add(
                    content,
                    user_id=self._user_id,
                    metadata={"node_id": node_id, "archetype": archetype},
                )
            except Exception:
                pass
        elif self._chroma_collection and content:
            try:
                self._chroma_collection.add(
                    documents=[content],
                    ids=[node_id],
                    metadatas=[{"archetype": archetype, "geometry_tag": geometry_tag}],
                )
            except Exception:
                pass

        return node_id

    def _payload_to_text(self, payload: Dict[str, Any]) -> str:
        """Convert payload to searchable text."""
        parts = []
        for k, v in payload.items():
            if isinstance(v, str):
                parts.append(v)
            elif v is not None:
                parts.append(str(v))
        return " ".join(parts)

    def get_relevant(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return payloads whose text overlaps with query."""
        if not query:
            return []

        # Try Mem0 first
        if self._mem0:
            try:
                results = self._mem0.search(query, user_id=self._user_id, limit=limit)
                if results:
                    payloads = []
                    for r in results:
                        # Mem0 returns memory objects; extract relevant info
                        memory_text = r.get("memory", "") if isinstance(r, dict) else str(r)
                        payloads.append({"summary": memory_text})
                    return payloads
            except Exception:
                pass

        # Try ChromaDB
        if self._chroma_collection:
            try:
                results = self._chroma_collection.query(
                    query_texts=[query],
                    n_results=min(limit, 10),
                )
                if results and results.get("documents"):
                    return [{"summary": doc} for doc in results["documents"][0]]
            except Exception:
                pass

        # Fallback to keyword matching
        if not self._nodes:
            return []
        q_words = set(query.lower().split())
        scored: List[tuple[float, Dict[str, Any]]] = []
        for n in self._nodes:
            text = " ".join(str(v) for v in n.get("payload", {}).values()).lower()
            overlap = len(q_words & set(text.split()))
            if overlap > 0:
                scored.append((overlap, n.get("payload", {})))
        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored[:limit]]

    def format_relevant_for_context(self, query: str, limit: int = 5) -> str:
        """Return a string of relevant payloads for injection into agent context."""
        payloads = self.get_relevant(query, limit=limit)
        if not payloads:
            return ""
        backend_note = f" (via {self.backend})" if self._use_vector else ""
        lines = [f"[Fractal memory — relevant prior context{backend_note}]", ""]
        for i, p in enumerate(payloads, 1):
            raw = p.get("summary", p.get("snippet", str(p)))
            text = str(raw)[:400]
            if len(str(raw)) > 400:
                text += "..."
            lines.append(f"{i}. {text}")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Return memory store statistics."""
        return {
            "backend": self.backend,
            "node_count": len(self._nodes),
            "workspace": str(self.workspace),
        }
