from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

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
    "rg",
    "fd",
    "tree",
]


@dataclass
class OpenAIConfig:
    api_key: Optional[str] = None
    model: str = "gpt-5"
    base_url: str = "https://api.openai.com/v1"
    enable_network: bool = False


@dataclass
class SwarmConfig:
    repo_root: Path = Path(".")
    workspace_dir: Path = Path(".swarm_work")
    concurrency: int = 4
    allowlist: List[str] = field(default_factory=lambda: list(DEFAULT_ALLOWLIST))


@dataclass
class AppConfig:
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    swarm: SwarmConfig = field(default_factory=SwarmConfig)


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def load_config(path: Optional[str] = None) -> AppConfig:
    cfg = AppConfig()
    if path is None:
        config_path = Path.home() / ".config" / "agent_swarm" / "config.toml"
    else:
        config_path = Path(path)
    data = _load_toml(config_path)
    openai = data.get("openai", {})
    swarm = data.get("swarm", {})

    cfg.openai.api_key = os.environ.get("OPENAI_API_KEY") or cfg.openai.api_key
    env_enable = os.environ.get("AGENT_SWARM_ENABLE_NETWORK", "").lower()
    if env_enable in {"1", "true", "yes"}:
        cfg.openai.enable_network = True
    if openai.get("api_key"):
        cfg.openai.api_key = openai["api_key"]
    if openai.get("model"):
        cfg.openai.model = openai["model"]
    if openai.get("base_url"):
        cfg.openai.base_url = openai["base_url"]
    if openai.get("enable_network") is not None:
        cfg.openai.enable_network = bool(openai["enable_network"])

    if swarm.get("repo_root"):
        cfg.swarm.repo_root = Path(swarm["repo_root"])
    if swarm.get("workspace_dir"):
        cfg.swarm.workspace_dir = Path(swarm["workspace_dir"])
    if swarm.get("concurrency"):
        cfg.swarm.concurrency = int(swarm["concurrency"])
    if swarm.get("allowlist"):
        cfg.swarm.allowlist = list(swarm["allowlist"])
    return cfg
