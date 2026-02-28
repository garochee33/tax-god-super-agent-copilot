from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional, cast

from swarm.providers.base import ProviderResult


class GeminiProvider:
    """Native Google Gemini provider using the google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")

    @staticmethod
    def _is_transient_exception(exc: Exception) -> bool:
        # google-genai may raise transport-level exceptions without status codes.
        msg = str(exc).lower()
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int) and (
            status_code in {408, 429} or 500 <= status_code <= 599
        ):
            return True
        return any(
            s in msg
            for s in (
                "rate limit",
                "timeout",
                "timed out",
                "temporarily unavailable",
                "connection",
                "server error",
                "unavailable",
                "too many requests",
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
            return ProviderResult(False, "", {}, {}, error="GOOGLE_API_KEY missing")

        try:
            from google import genai
        except Exception as exc:  # pragma: no cover - optional dependency
            return ProviderResult(False, "", {}, {}, error=f"google-genai SDK missing: {exc}")

        http_retry = bool(params.pop("http_retry", True))
        http_max_retries = int(params.pop("http_max_retries", 2))
        http_retry_delay_ms = float(params.pop("http_retry_delay_ms", 300))

        client = genai.Client(api_key=self._api_key)
        config = dict(params) if isinstance(params, dict) else {}

        start = time.time()
        last_error: Optional[str] = None
        for attempt in range(http_max_retries + 1):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=[system, user],
                    config=cast(Any, config),
                )
                latency_ms = (time.time() - start) * 1000
                text = ""
                try:
                    text = resp.text or ""
                except Exception:
                    pass
                raw = resp.model_dump() if hasattr(resp, "model_dump") else {}
                tokens = None
                try:
                    usage = raw.get("usage", {})
                    tokens = usage.get("total_tokens")
                except Exception:
                    pass
                return ProviderResult(
                    True,
                    text.strip(),
                    raw if raw else {},
                    {},
                    latency_ms=latency_ms,
                    model_used=model,
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
