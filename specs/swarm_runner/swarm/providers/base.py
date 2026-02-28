from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass
class ProviderResult:
    ok: bool
    output_text: str
    raw: Dict[str, Any]
    headers: Dict[str, str]
    error: Optional[str] = None
    latency_ms: Optional[float] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None


class ProviderClient(Protocol):
    def generate(
        self,
        system: str,
        user: str,
        model: str,
        params: Dict[str, Any],
        timeout: int,
        base_url: Optional[str] = None,
    ) -> ProviderResult: ...
