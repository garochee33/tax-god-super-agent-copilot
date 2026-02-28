from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional

from swarm.providers.base import ProviderResult


class OpenAIProvider:
    """Native OpenAI provider using the official openai SDK."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")

    @staticmethod
    def _is_transient_status(status_code: Optional[int]) -> bool:
        if status_code is None:
            return False
        return status_code in {408, 429} or 500 <= status_code <= 599

    @staticmethod
    def _is_transient_exception(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        if OpenAIProvider._is_transient_status(status_code):
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
            return ProviderResult(False, "", {}, {}, error="OPENAI_API_KEY missing")

        try:
            import openai
        except Exception as exc:  # pragma: no cover - optional dependency
            return ProviderResult(False, "", {}, {}, error=f"openai SDK missing: {exc}")

        # Reliability knobs (inspired by gaxios retryConfig).
        http_retry = bool(params.pop("http_retry", True))
        http_max_retries = int(params.pop("http_max_retries", 2))
        http_retry_delay_ms = float(params.pop("http_retry_delay_ms", 300))

        client = openai.OpenAI(api_key=self._api_key, base_url=base_url)
        use_chat = bool(params.pop("use_chat_completions", False))
        endpoint = str(params.pop("endpoint", "")).strip().lower()
        if endpoint == "chat_completions":
            use_chat = True
        if endpoint == "responses":
            use_chat = False

        if use_chat:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **params,
            }
            start = time.time()
            last_error: Optional[str] = None
            for attempt in range(http_max_retries + 1):
                try:
                    resp = client.chat.completions.create(timeout=timeout, **payload)
                    latency_ms = (time.time() - start) * 1000
                    text = ""
                    try:
                        text = resp.choices[0].message.content or ""
                    except Exception:
                        pass
                    usage = getattr(resp, "usage", None)
                    tokens = getattr(usage, "total_tokens", None) if usage else None
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

        payload = {
            "model": model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **params,
        }
        start = time.time()
        last_error = None
        for attempt in range(http_max_retries + 1):
            try:
                resp = client.responses.create(timeout=timeout, **payload)
                latency_ms = (time.time() - start) * 1000
                text = ""
                if hasattr(resp, "output_text"):
                    text = resp.output_text or ""
                else:
                    # Best-effort parse
                    raw = resp.model_dump() if hasattr(resp, "model_dump") else {}
                    for item in raw.get("output", []):
                        if item.get("type") == "message":
                            for content in item.get("content", []):
                                if content.get("type") == "output_text":
                                    text += content.get("text", "")
                usage = getattr(resp, "usage", None)
                tokens = getattr(usage, "total_tokens", None) if usage else None
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
