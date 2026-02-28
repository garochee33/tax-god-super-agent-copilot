from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional

from swarm.providers.base import ProviderResult


class AnthropicProvider:
    """Native Anthropic provider using the official anthropic SDK."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    @staticmethod
    def _is_transient_status(status_code: Optional[int]) -> bool:
        if status_code is None:
            return False
        return status_code in {408, 429} or 500 <= status_code <= 599

    @staticmethod
    def _is_transient_exception(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        if AnthropicProvider._is_transient_status(status_code):
            return True
        msg = str(exc).lower()
        return any(
            s in msg
            for s in (
                "rate limit",
                "timeout",
                "timed out",
                "temporarily unavailable",
                "connection error",
                "server error",
                "bad gateway",
                "gateway timeout",
            )
        )

    @staticmethod
    def _sleep_backoff(attempt: int, base_delay_ms: float) -> None:
        delay_s = (base_delay_ms / 1000.0) * (2**attempt)
        jitter = random.random() * min(0.1, delay_s)
        time.sleep(delay_s + jitter)

    def generate(
        self,
        system: str,
        user: str,
        model: str,
        params: Dict[str, Any],
        timeout: int,
        base_url: Optional[str] = None,
    ) -> ProviderResult:
        if not self._api_key:
            return ProviderResult(False, "", {}, {}, error="ANTHROPIC_API_KEY missing")

        try:
            import anthropic
        except Exception as exc:  # pragma: no cover - optional dependency
            return ProviderResult(False, "", {}, {}, error=f"anthropic SDK missing: {exc}")

        http_retry = bool(params.pop("http_retry", True))
        http_max_retries = int(params.pop("http_max_retries", 2))
        http_retry_delay_ms = float(params.pop("http_retry_delay_ms", 300))

        client = anthropic.Anthropic(api_key=self._api_key, base_url=base_url)
        payload = {
            "model": model,
            "max_tokens": params.pop("max_tokens", 1024),
            "system": system,
            "messages": [{"role": "user", "content": user}],
            **params,
        }

        start = time.time()
        last_error: Optional[str] = None
        for attempt in range(http_max_retries + 1):
            try:
                resp = client.messages.create(timeout=timeout, **payload)
                latency_ms = (time.time() - start) * 1000
                text = ""
                try:
                    text = "".join(
                        [block.text for block in resp.content if hasattr(block, "text")]
                    )
                except Exception:
                    pass
                usage = getattr(resp, "usage", None)
                tokens = getattr(usage, "input_tokens", None)
                if tokens is not None:
                    output_tokens = getattr(usage, "output_tokens", None)
                    if output_tokens is not None:
                        tokens = tokens + output_tokens
                return ProviderResult(
                    True,
                    text.strip(),
                    resp.model_dump() if hasattr(resp, "model_dump") else {},
                    {},
                    latency_ms=latency_ms,
                    model_used=getattr(resp, "model", None),
                    tokens_used=tokens,
                )
            except Exception as exc:
                last_error = str(exc)
                if (
                    http_retry
                    and attempt < http_max_retries
                    and self._is_transient_exception(exc)
                ):
                    self._sleep_backoff(attempt, http_retry_delay_ms)
                    continue
                break

        latency_ms = (time.time() - start) * 1000
        return ProviderResult(
            False,
            "",
            {},
            {},
            error=last_error or "unknown error",
            latency_ms=latency_ms,
        )
