"""
Encryption helpers for sensitive integration credentials.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet

from app.core.config import get_settings


@lru_cache
def get_fernet() -> Fernet:
    settings = get_settings()
    raw_key = settings.INTEGRATION_ENCRYPTION_KEY.strip()

    if raw_key:
        key = raw_key.encode()
    else:
        # Deterministic fallback derived from SECRET_KEY for local/dev continuity.
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)

    return Fernet(key)
