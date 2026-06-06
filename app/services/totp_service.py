"""Tax God - TOTP Two-Factor Authentication Service (stdlib only)"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import time
import urllib.parse


def generate_secret() -> str:
    """Generate a base32-encoded TOTP secret."""
    return base64.b32encode(os.urandom(20)).decode("ascii")


def generate_provisioning_uri(secret: str, email: str) -> str:
    """Generate otpauth:// URI for authenticator apps."""
    params = urllib.parse.urlencode({
        "secret": secret,
        "issuer": "TaxGod",
        "algorithm": "SHA1",
        "digits": "6",
        "period": "30",
    })
    label = urllib.parse.quote(f"TaxGod:{email}")
    return f"otpauth://totp/{label}?{params}"


def _compute_totp(secret: str, time_step: int) -> str:
    """Compute TOTP code for a given time step."""
    key = base64.b32decode(secret, casefold=True)
    msg = struct.pack(">Q", time_step)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % 10**6).zfill(6)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code with ±1 window."""
    current_step = int(time.time()) // 30
    for offset in (-1, 0, 1):
        if hmac.compare_digest(_compute_totp(secret, current_step + offset), code):
            return True
    return False
