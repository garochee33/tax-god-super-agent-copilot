from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional

from swarm.providers.base import ProviderResult


class OpenAICompatibleProvider:
    """OpenAI-compatible HTTP provider for custom gateways."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")

    @staticmethod
    def _is_transient_status(status_code: int) -> bool:
        return status_code in {408, 429} or 500 <= status_code <= 599

    @staticmethod
    def _sleep_backoff(attempt: int, base_delay_ms: float) -> None:
        # Exponential backoff with small jitter.
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
        if not base_url:
            return ProviderResult(False, "", {}, {}, error="base_url is required")

        try:
            import requests
        except Exception as exc:
            return ProviderResult(False, "", {}, {}, error=f"requests missing: {exc}")

        # HTTP reliability knobs (inspired by gaxios retryConfig + proxy support).
        http_retry = bool(params.pop("http_retry", True))
        http_max_retries = int(params.pop("http_max_retries", 2))
        http_retry_delay_ms = float(params.pop("http_retry_delay_ms", 300))
        http_proxy = params.pop("http_proxy", None) or params.pop("proxy", None)
        proxies = None
        if http_proxy:
            proxies = {"http": str(http_proxy), "https": str(http_proxy)}

        use_chat = bool(params.pop("use_chat_completions", True))
        endpoint = str(params.pop("endpoint", "")).strip().lower()
        if endpoint == "responses":
            use_chat = False
        if endpoint == "chat_completions":
            use_chat = True

        if use_chat:
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "agent-swarm/openai-compatible",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **params,
            }
        else:
            url = f"{base_url}/responses"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "agent-swarm/openai-compatible",
            }
            payload = {
                "model": model,
                "input": [
                    {"role": "system", "content": [{"type": "text", "text": system}]},
                    {"role": "user", "content": [{"type": "text", "text": user}]},
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
                if use_chat:
                    choices = data.get("choices", [])
                    if choices:
                        text = choices[0].get("message", {}).get("content", "") or ""
                else:
                    for item in data.get("output", []):
                        if item.get("type") == "message":
                            for content in item.get("content", []):
                                if content.get("type") == "output_text":
                                    text += content.get("text", "")
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
