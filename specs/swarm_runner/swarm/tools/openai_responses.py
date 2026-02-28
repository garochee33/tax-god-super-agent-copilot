"""
OpenAI API adapters for the Agent Swarm.

Supports two backends:
- Responses API (/v1/responses) — OpenAI's newer unified endpoint
- Chat Completions API (/v1/chat/completions) — Standard, widely supported

The run_openai() function auto-detects which endpoint to use based on base_url
or can be forced via the `use_chat_completions` parameter.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class OpenAIResult:
    ok: bool
    output_text: str
    raw: Dict[str, Any]
    headers: Dict[str, str]
    client_request_id: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None


def _run_chat_completions(
    api_key: str,
    model: str,
    system: str,
    user: str,
    base_url: str,
    client_request_id: str,
    timeout: int = 120,
    max_retries: int = 3,
) -> OpenAIResult:
    """
    Call standard Chat Completions API (/v1/chat/completions).
    Includes exponential backoff retry for transient failures.
    """
    import requests

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Request-Id": client_request_id,
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
    }

    last_error = None
    for attempt in range(max_retries):
        start = time.time()
        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=timeout
            )
            latency_ms = (time.time() - start) * 1000

            if resp.status_code == 429 or resp.status_code >= 500:
                # Retryable error - exponential backoff
                wait = (2 ** attempt) + 0.5
                time.sleep(wait)
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                continue

            if resp.status_code >= 400:
                return OpenAIResult(
                    False, "", {}, dict(resp.headers),
                    client_request_id=client_request_id,
                    error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                    latency_ms=latency_ms,
                )

            data = resp.json()
            output_text = ""
            model_used = data.get("model")
            tokens_used = data.get("usage", {}).get("total_tokens")

            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                output_text = message.get("content", "")

            return OpenAIResult(
                True,
                output_text.strip(),
                data,
                dict(resp.headers),
                client_request_id=client_request_id,
                latency_ms=latency_ms,
                model_used=model_used,
                tokens_used=tokens_used,
            )

        except requests.exceptions.Timeout:
            last_error = f"Request timeout after {timeout}s"
            wait = (2 ** attempt) + 0.5
            time.sleep(wait)
        except requests.exceptions.RequestException as e:
            last_error = f"Request failed: {e}"
            wait = (2 ** attempt) + 0.5
            time.sleep(wait)

    return OpenAIResult(
        False, "", {}, {},
        client_request_id=client_request_id,
        error=f"All {max_retries} retries failed. Last error: {last_error}",
    )


def _run_responses_api(
    api_key: str,
    model: str,
    system: str,
    user: str,
    base_url: str,
    client_request_id: str,
    timeout: int = 120,
) -> OpenAIResult:
    """
    Call OpenAI Responses API (/v1/responses).
    """
    import requests

    url = f"{base_url}/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Client-Request-Id": client_request_id,
    }
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "text", "text": system}]},
            {"role": "user", "content": [{"type": "text", "text": user}]},
        ],
    }

    start = time.time()
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    latency_ms = (time.time() - start) * 1000

    if resp.status_code >= 400:
        return OpenAIResult(
            False, "", {}, dict(resp.headers),
            client_request_id=client_request_id,
            error=f"HTTP {resp.status_code}: {resp.text}",
            latency_ms=latency_ms,
        )

    data = resp.json()
    output_text = ""
    try:
        for item in data.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        output_text += content.get("text", "")
    except Exception as exc:
        return OpenAIResult(
            False, "", data, dict(resp.headers),
            client_request_id=client_request_id,
            error=f"Parse error: {exc}",
            latency_ms=latency_ms,
        )

    return OpenAIResult(
        True,
        output_text.strip(),
        data,
        dict(resp.headers),
        client_request_id=client_request_id,
        latency_ms=latency_ms,
        model_used=data.get("model"),
    )


def run_openai(
    api_key: Optional[str],
    model: str,
    system: str,
    user: str,
    base_url: str = "https://api.openai.com/v1",
    use_chat_completions: Optional[bool] = None,
    timeout: int = 120,
    max_retries: int = 3,
) -> OpenAIResult:
    """
    Call OpenAI-compatible API with automatic endpoint detection.

    Args:
        api_key: OpenAI API key (or compatible provider key)
        model: Model name (e.g., "gpt-4o", "gpt-4o-mini")
        system: System prompt
        user: User message
        base_url: API base URL (default: OpenAI)
        use_chat_completions: Force Chat Completions API if True, Responses if False.
            If None, auto-detect: use Chat Completions for non-OpenAI endpoints.
        timeout: Request timeout in seconds
        max_retries: Max retries for transient failures (Chat Completions only)

    Returns:
        OpenAIResult with response data
    """
    if not api_key:
        return OpenAIResult(False, "", {}, {}, error="OPENAI_API_KEY missing")

    client_request_id = str(uuid.uuid4())

    # Auto-detect: use Chat Completions for non-OpenAI endpoints
    if use_chat_completions is None:
        use_chat_completions = "api.openai.com" not in base_url

    if use_chat_completions:
        return _run_chat_completions(
            api_key, model, system, user, base_url,
            client_request_id, timeout, max_retries
        )
    else:
        return _run_responses_api(
            api_key, model, system, user, base_url,
            client_request_id, timeout
        )


def run_openai_with_structured_output(
    api_key: Optional[str],
    model: str,
    system: str,
    user: str,
    response_schema: Dict[str, Any],
    base_url: str = "https://api.openai.com/v1",
    timeout: int = 120,
) -> OpenAIResult:
    """
    Call Chat Completions API with structured output (JSON schema enforcement).

    Args:
        response_schema: JSON schema for the expected response format
    """
    if not api_key:
        return OpenAIResult(False, "", {}, {}, error="OPENAI_API_KEY missing")

    import requests

    client_request_id = str(uuid.uuid4())
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Request-Id": client_request_id,
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_response",
                "strict": True,
                "schema": response_schema,
            },
        },
    }

    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        latency_ms = (time.time() - start) * 1000

        if resp.status_code >= 400:
            return OpenAIResult(
                False, "", {}, dict(resp.headers),
                client_request_id=client_request_id,
                error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                latency_ms=latency_ms,
            )

        data = resp.json()
        output_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        return OpenAIResult(
            True,
            output_text.strip(),
            data,
            dict(resp.headers),
            client_request_id=client_request_id,
            latency_ms=latency_ms,
            model_used=data.get("model"),
            tokens_used=data.get("usage", {}).get("total_tokens"),
        )
    except Exception as exc:
        return OpenAIResult(
            False, "", {}, {},
            client_request_id=client_request_id,
            error=f"Request failed: {exc}",
        )
