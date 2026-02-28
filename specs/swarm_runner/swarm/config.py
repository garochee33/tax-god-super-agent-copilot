from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


DEFAULT_ALLOWLIST = [
    "pytest",
    "ruff",
    "mypy",
    "npm test",
    "pnpm test",
    "go test",
    "cargo test",
    "git status",
    "git diff",
    "git log",
    "git apply",
    "patch",
    "rg",
    "fd",
    "tree",
]


@dataclass
class OpenAIConfig:
    api_key: Optional[str] = None
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"


@dataclass
class OracleConfig:
    """Oracle layer: web search, optional sandbox."""
    enabled: bool = False
    search_api_key: Optional[str] = None  # SERPER_API_KEY or TAVILY_API_KEY
    search_provider: str = "serper"  # serper | tavily
    max_search_results: int = 5


@dataclass
class ModelSpec:
    provider: str = "openai"  # openai | anthropic | gemini | xai | openai_compatible
    model: str = ""
    base_url: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    fallback_models: List[str] = field(default_factory=list)

    @staticmethod
    def from_raw(raw: Any) -> "ModelSpec":
        if isinstance(raw, str):
            return ModelSpec(provider="openai", model=raw)
        if isinstance(raw, dict):
            provider = str(raw.get("provider", "openai"))
            model = str(raw.get("model", "")).strip()
            if provider != "openai" and not model:
                raise ValueError(f"ModelSpec for provider '{provider}' requires a model")
            base_url = raw.get("base_url")
            raw_params = raw.get("params")
            params: Dict[str, Any] = dict(raw_params) if isinstance(raw_params, dict) else {}
            fallback_models = (
                list(raw.get("fallback_models", []))
                if isinstance(raw.get("fallback_models"), list)
                else []
            )
            return ModelSpec(
                provider=provider,
                model=model,
                base_url=base_url,
                params=params,
                fallback_models=[str(m) for m in fallback_models],
            )
        return ModelSpec()


@dataclass
class ClusterSpec:
    name: str
    bots: List[str]
    execution: str = "sequential"  # sequential | parallel
    concurrency: Optional[int] = None

    @staticmethod
    def from_raw(raw: Any) -> Optional["ClusterSpec"]:
        if not isinstance(raw, dict):
            return None
        name = raw.get("name")
        bots = raw.get("bots")
        if not name or not isinstance(bots, list):
            return None
        execution = str(raw.get("execution", "sequential"))
        concurrency = raw.get("concurrency")
        if concurrency is not None:
            try:
                concurrency = int(concurrency)
            except (TypeError, ValueError):
                concurrency = None
        return ClusterSpec(
            name=str(name),
            bots=[str(b) for b in bots],
            execution=execution,
            concurrency=concurrency,
        )


@dataclass
class SwarmConfig:
    repo_root: Path = Path(".")
    workspace_dir: Path = Path(".swarm_work")
    concurrency: int = 4
    allowlist: List[str] = field(default_factory=lambda: list(DEFAULT_ALLOWLIST))
    bots: List[dict] = field(default_factory=list)
    promotion_ladder: List[str] = field(default_factory=list)
    fractal_routing: bool = True
    fractal_planner: bool = False
    # Pass prior agents' summaries to later agents (forces sequential when True)
    inter_agent_context: bool = True
    # Per-agent run timeout; None = no limit (avoids one agent blocking the run)
    agent_timeout_seconds: Optional[int] = None
    # Apply generated patches to repo (allowlisted git apply / patch)
    apply_patches: bool = False
    # When True, only log planned apply commands; do not modify repo
    apply_patches_dry_run: bool = False
    # Persist FractalNodes and inject retrieval into context
    fractal_memory: bool = True
    # Multi-model: per-role model override. Keys = bot name, value = model key
    # from [models] or literal model name
    model_by_role: Dict[str, str] = field(default_factory=dict)
    # Named models: key = name, value = model string (and optional base_url in extended form)
    models: Dict[str, ModelSpec] = field(default_factory=dict)
    # Optional: enable/disable bots by name
    enabled_bots: List[str] = field(default_factory=list)
    disabled_bots: List[str] = field(default_factory=list)
    # Presets and clusters
    active_preset: Optional[str] = None
    presets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    active_cluster: Optional[str] = None
    clusters: List[ClusterSpec] = field(default_factory=list)
    # Reflection loop: enable self-correction when agent output indicates failure
    enable_reflection: bool = True
    # Max reflection iterations per agent (0 = disabled)
    max_reflection_iterations: int = 2
    # Use Chat Completions API instead of Responses API (for non-OpenAI providers)
    use_chat_completions: Optional[bool] = None
    # Use vector store for memory (Mem0/ChromaDB if installed, else JSON fallback)
    use_vector_memory: bool = True
    # Memory backend: auto | json | chromadb | mem0 | pgvector_hybrid
    memory_backend: Optional[str] = None
    # PostgreSQL URL for pgvector_hybrid (env DATABASE_URL overrides)
    database_url: Optional[str] = None


@dataclass
class AppConfig:
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    swarm: SwarmConfig = field(default_factory=SwarmConfig)
    oracle: OracleConfig = field(default_factory=OracleConfig)


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return cast(dict[str, Any], tomllib.load(f))


def _parse_models(raw: Any) -> Dict[str, ModelSpec]:
    if not isinstance(raw, dict):
        return {}
    parsed: Dict[str, ModelSpec] = {}
    for key, val in raw.items():
        parsed[str(key)] = ModelSpec.from_raw(val)
    return parsed


def _parse_clusters(raw: Any) -> List[ClusterSpec]:
    if not isinstance(raw, list):
        return []
    clusters: List[ClusterSpec] = []
    for item in raw:
        spec = ClusterSpec.from_raw(item)
        if spec:
            clusters.append(spec)
    return clusters


def apply_swarm_overrides(cfg: AppConfig, overrides: Dict[str, Any]) -> None:
    if "concurrency" in overrides:
        cfg.swarm.concurrency = int(overrides["concurrency"])
    if "inter_agent_context" in overrides:
        cfg.swarm.inter_agent_context = bool(overrides["inter_agent_context"])
    if "agent_timeout_seconds" in overrides:
        cfg.swarm.agent_timeout_seconds = int(overrides["agent_timeout_seconds"])
    if "apply_patches" in overrides:
        cfg.swarm.apply_patches = bool(overrides["apply_patches"])
    if "apply_patches_dry_run" in overrides:
        cfg.swarm.apply_patches_dry_run = bool(overrides["apply_patches_dry_run"])
    if "fractal_routing" in overrides:
        cfg.swarm.fractal_routing = bool(overrides["fractal_routing"])
    if "fractal_planner" in overrides:
        cfg.swarm.fractal_planner = bool(overrides["fractal_planner"])
    if "fractal_memory" in overrides:
        cfg.swarm.fractal_memory = bool(overrides["fractal_memory"])
    if "use_vector_memory" in overrides:
        cfg.swarm.use_vector_memory = bool(overrides["use_vector_memory"])
    if "memory_backend" in overrides:
        cfg.swarm.memory_backend = (
            str(overrides["memory_backend"]).strip() or None
        )
    if "database_url" in overrides:
        cfg.swarm.database_url = (
            str(overrides["database_url"]).strip() if overrides["database_url"] else None
        )
    if "enable_reflection" in overrides:
        cfg.swarm.enable_reflection = bool(overrides["enable_reflection"])
    if "max_reflection_iterations" in overrides:
        cfg.swarm.max_reflection_iterations = int(overrides["max_reflection_iterations"])
    if "use_chat_completions" in overrides:
        cfg.swarm.use_chat_completions = bool(overrides["use_chat_completions"])
    if "model_by_role" in overrides and isinstance(overrides.get("model_by_role"), dict):
        cfg.swarm.model_by_role.update(dict(overrides["model_by_role"]))
    if "models" in overrides and isinstance(overrides.get("models"), dict):
        cfg.swarm.models.update(_parse_models(overrides.get("models")))
    if "enabled_bots" in overrides and isinstance(overrides.get("enabled_bots"), list):
        cfg.swarm.enabled_bots = [str(b) for b in overrides.get("enabled_bots", [])]
    if "disabled_bots" in overrides and isinstance(overrides.get("disabled_bots"), list):
        cfg.swarm.disabled_bots = [str(b) for b in overrides.get("disabled_bots", [])]
    if "active_cluster" in overrides:
        cfg.swarm.active_cluster = str(overrides.get("active_cluster")) or None
    if "active_preset" in overrides:
        preset_name = str(overrides.get("active_preset") or "").strip() or None
        cfg.swarm.active_preset = preset_name
        if preset_name:
            apply_preset(cfg, preset_name)


def apply_preset(cfg: AppConfig, preset_name: str) -> None:
    if not preset_name:
        return
    preset = cfg.swarm.presets.get(preset_name)
    if not isinstance(preset, dict):
        return
    apply_swarm_overrides(cfg, preset)


def load_config(path: Optional[str] = None) -> AppConfig:
    cfg = AppConfig()
    if path is None:
        config_path = Path.home() / ".config" / "agent_swarm" / "config.toml"
    else:
        config_path = Path(path)
    data = _load_toml(config_path)
    openai = data.get("openai", {})
    swarm = data.get("swarm", {})

    # API keys: environment overrides config (so OPENAI_API_KEY etc. always apply)
    cfg.openai.api_key = os.environ.get("OPENAI_API_KEY") or openai.get("api_key") or None
    if openai.get("model"):
        cfg.openai.model = openai["model"]
    if openai.get("base_url"):
        cfg.openai.base_url = openai["base_url"]

    if swarm.get("repo_root"):
        cfg.swarm.repo_root = Path(swarm["repo_root"])
    if swarm.get("workspace_dir"):
        cfg.swarm.workspace_dir = Path(swarm["workspace_dir"])
    if swarm.get("concurrency"):
        cfg.swarm.concurrency = int(swarm["concurrency"])
    if swarm.get("allowlist"):
        cfg.swarm.allowlist = list(swarm["allowlist"])
    if swarm.get("bots"):
        cfg.swarm.bots = list(swarm["bots"])
    if swarm.get("promotion_ladder"):
        cfg.swarm.promotion_ladder = list(swarm["promotion_ladder"])
    if "fractal_routing" in swarm:
        cfg.swarm.fractal_routing = bool(swarm["fractal_routing"])
    if "fractal_planner" in swarm:
        cfg.swarm.fractal_planner = bool(swarm["fractal_planner"])
    if "inter_agent_context" in swarm:
        cfg.swarm.inter_agent_context = bool(swarm["inter_agent_context"])
    if "agent_timeout_seconds" in swarm and swarm["agent_timeout_seconds"] is not None:
        cfg.swarm.agent_timeout_seconds = int(swarm["agent_timeout_seconds"])
    if "apply_patches" in swarm:
        cfg.swarm.apply_patches = bool(swarm["apply_patches"])
    if "apply_patches_dry_run" in swarm:
        cfg.swarm.apply_patches_dry_run = bool(swarm["apply_patches_dry_run"])
    if "fractal_memory" in swarm:
        cfg.swarm.fractal_memory = bool(swarm["fractal_memory"])
    if "model_by_role" in swarm and isinstance(swarm.get("model_by_role"), dict):
        cfg.swarm.model_by_role = dict(swarm["model_by_role"])
    if "models" in swarm and isinstance(swarm.get("models"), dict):
        cfg.swarm.models = _parse_models(swarm.get("models"))
    if "enabled_bots" in swarm and isinstance(swarm.get("enabled_bots"), list):
        cfg.swarm.enabled_bots = [str(b) for b in swarm.get("enabled_bots", [])]
    if "disabled_bots" in swarm and isinstance(swarm.get("disabled_bots"), list):
        cfg.swarm.disabled_bots = [str(b) for b in swarm.get("disabled_bots", [])]
    if "active_preset" in swarm:
        cfg.swarm.active_preset = str(swarm.get("active_preset")) or None
    if "presets" in swarm and isinstance(swarm.get("presets"), dict):
        cfg.swarm.presets = dict(swarm.get("presets", {}))
    if "active_cluster" in swarm:
        cfg.swarm.active_cluster = str(swarm.get("active_cluster")) or None
    if "clusters" in swarm and isinstance(swarm.get("clusters"), list):
        cfg.swarm.clusters = _parse_clusters(swarm.get("clusters"))
    if "enable_reflection" in swarm:
        cfg.swarm.enable_reflection = bool(swarm["enable_reflection"])
    if "max_reflection_iterations" in swarm:
        cfg.swarm.max_reflection_iterations = int(swarm["max_reflection_iterations"])
    if "use_chat_completions" in swarm:
        cfg.swarm.use_chat_completions = bool(swarm["use_chat_completions"])
    if "use_vector_memory" in swarm:
        cfg.swarm.use_vector_memory = bool(swarm["use_vector_memory"])
    if "memory_backend" in swarm and swarm["memory_backend"]:
        cfg.swarm.memory_backend = str(swarm["memory_backend"]).strip() or None
    if "database_url" in swarm and swarm["database_url"]:
        cfg.swarm.database_url = str(swarm["database_url"]).strip() or None
    # Env override for database URL (e.g. Replit / production)
    if os.environ.get("DATABASE_URL"):
        cfg.swarm.database_url = os.environ.get("DATABASE_URL")

    # Oracle: env overrides config for search API key
    oracle_data = data.get("oracle", {})
    cfg.oracle.enabled = bool(oracle_data.get("enabled", False))
    cfg.oracle.search_api_key = (
        os.environ.get("SERPER_API_KEY")
        or os.environ.get("TAVILY_API_KEY")
        or oracle_data.get("search_api_key")
        or None
    )
    cfg.oracle.search_provider = str(oracle_data.get("search_provider", "serper"))
    cfg.oracle.max_search_results = int(oracle_data.get("max_search_results", 5))

    # Apply preset from config so file-based active_preset is effective
    if cfg.swarm.active_preset:
        apply_preset(cfg, cfg.swarm.active_preset)

    return cfg
