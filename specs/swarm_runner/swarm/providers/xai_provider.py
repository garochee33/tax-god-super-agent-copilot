from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional

from swarm.providers.base import ProviderResult


class XAIProvider:
    """xAI Grok provider. Uses xai-grok-sdk if available, otherwise HTTP fallback."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("XAI_API_KEY")

    @staticmethod
    def _is_transient_status(status_code: int) -> bool:
        return status_code in {408, 429} or 500 <= status_code <= 599

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
            return ProviderResult(False, "", {}, {}, error="XAI_API_KEY missing")

        # Try native SDK first
        try:
            import xai_grok_sdk as xai

            client = xai.Client(api_key=self._api_key)
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **params,
            }
            start = time.time()
            resp = client.chat.completions.create(timeout=timeout, **payload)
            latency_ms = (time.time() - start) * 1000
            text = ""
            try:
                text = resp.choices[0].message.content or ""
            except Exception:
                pass
            raw = resp.model_dump() if hasattr(resp, "model_dump") else {}
            tokens = None
            try:
                tokens = raw.get("usage", {}).get("total_tokens")
            except Exception:
                pass
            return ProviderResult(
                True,
                text.strip(),
                raw,
                {},
                latency_ms=latency_ms,
                model_used=model,
                tokens_used=tokens,
            )
        except Exception:
            pass

        # Fallback: HTTP OpenAI-compatible
        try:
            import requests
        except Exception as exc:
            return ProviderResult(False, "", {}, {}, error=f"requests missing: {exc}")

        http_retry = bool(params.pop("http_retry", True))
        http_max_retries = int(params.pop("http_max_retries", 2))
        http_retry_delay_ms = float(params.pop("http_retry_delay_ms", 300))
        http_proxy = params.pop("http_proxy", None) or params.pop("proxy", None)
        proxies = None
        if http_proxy:
            proxies = {"http": str(http_proxy), "https": str(http_proxy)}

        api_base = base_url or os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")
        url = f"{api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": "agent-swarm/xai-http",
        }
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
        last_headers: Dict[str, str] = {}
        for attempt in range(http_max_retries + 1):
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                    proxies=proxies,
                )
                last_headers = dict(getattr(resp, "headers", {}) or {})
                if resp.status_code >= 400:
                    last_error = f"HTTP {resp.status_code}: {getattr(resp, 'text', '')[:500]}"
                    if (
                        http_retry
                        and attempt < http_max_retries
                        and self._is_transient_status(int(resp.status_code))
                    ):
                        self._sleep_backoff(attempt, http_retry_delay_ms)
                        continue
                    latency_ms = (time.time() - start) * 1000
                    return ProviderResult(
                        False,
                        "",
                        {},
                        last_headers,
                        error=last_error,
                        latency_ms=latency_ms,
                    )

                data = resp.json()
                text = ""
                choices = data.get("choices", [])
                if choices:
                    text = choices[0].get("message", {}).get("content", "") or ""
                tokens = data.get("usage", {}).get("total_tokens")
                latency_ms = (time.time() - start) * 1000
                return ProviderResult(
                    True,
                    text.strip(),
                    data,
                    last_headers,
                    latency_ms=latency_ms,
                    model_used=data.get("model"),
                    tokens_used=tokens,
                )
            except Exception as exc:
                last_error = str(exc)
                if http_retry and attempt < http_max_retries:
                    self._sleep_backoff(attempt, http_retry_delay_ms)
                    continue
                latency_ms = (time.time() - start) * 1000
                return ProviderResult(
                    False,
                    "",
                    {},
                    last_headers,
                    error=last_error,
                    latency_ms=latency_ms,
                )

        latency_ms = (time.time() - start) * 1000
        return ProviderResult(
            False,
            "",
            {},
            last_headers,
            error=last_error or "unknown error",
            latency_ms=latency_ms,
        )
