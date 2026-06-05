"""
Encryption helpers for sensitive integration credentials.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from functools import lru_cache

from cryptography.fernet import Fernet

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _derived_key(secret: str) -> bytes:
    """Deterministic Fernet key derived from SECRET_KEY for local/dev continuity."""
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache
def get_fernet() -> Fernet:
    settings = get_settings()
    raw_key = (settings.INTEGRATION_ENCRYPTION_KEY or settings.VAULT_MASTER_KEY or "").strip()
    derived = _derived_key(settings.SECRET_KEY)

    if raw_key:
        try:
            return Fernet(raw_key.encode())
        except (ValueError, Exception) as exc:
            logger.warning("Invalid Fernet key from config (%s); falling back to derived key", exc)
            return Fernet(derived)

    return Fernet(derived)
