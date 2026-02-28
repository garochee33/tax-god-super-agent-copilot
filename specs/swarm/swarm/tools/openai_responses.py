from __future__ import annotations

import json
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


def run_openai(
    api_key: Optional[str],
    model: str,
    system: str,
    user: str,
    base_url: str = "https://api.openai.com/v1",
    enable_network: bool = False,
) -> OpenAIResult:
    if not enable_network:
        return OpenAIResult(False, "", {}, {}, error="Network disabled (use --enable-network)")
    if not api_key:
        return OpenAIResult(False, "", {}, {}, error="OPENAI_API_KEY missing")

    import requests

    url = f"{base_url}/responses"
    client_request_id = str(uuid.uuid4())
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
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    if resp.status_code >= 400:
        return OpenAIResult(
            False,
            "",
            {},
            dict(resp.headers),
            client_request_id=client_request_id,
            error=f"HTTP {resp.status_code}: {resp.text}",
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
            False,
            "",
            data,
            dict(resp.headers),
            client_request_id=client_request_id,
            error=f"Parse error: {exc}",
        )

    return OpenAIResult(
        True,
        output_text.strip(),
        data,
        dict(resp.headers),
        client_request_id=client_request_id,
    )
