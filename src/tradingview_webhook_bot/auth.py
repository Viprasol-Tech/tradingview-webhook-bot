"""HMAC-SHA256 authentication for incoming webhook payloads.

TradingView itself cannot sign requests, but a common hardening pattern is to
embed a shared secret in the alert and/or front the bot with a proxy that adds
an ``X-Signature`` header computed as ``HMAC-SHA256(secret, raw_body)``. This
module implements the real signing and a constant-time verification so the bot
can reject forged or tampered payloads before parsing them.

Part of TradingView Webhook Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import hashlib
import hmac


def _to_bytes(value: str | bytes) -> bytes:
    """Coerce ``str`` to UTF-8 ``bytes``, passing ``bytes`` through unchanged."""
    return value.encode("utf-8") if isinstance(value, str) else value


def sign_payload(payload: str | bytes, secret: str | bytes) -> str:
    """Compute the hex HMAC-SHA256 signature of ``payload`` under ``secret``.

    Args:
        payload: The exact raw request body to authenticate.
        secret: The shared secret key.

    Returns:
        The lower-case hex digest of the HMAC-SHA256 signature.
    """
    mac = hmac.new(_to_bytes(secret), _to_bytes(payload), hashlib.sha256)
    return mac.hexdigest()


def verify_signature(
    payload: str | bytes,
    signature: str,
    secret: str | bytes,
) -> bool:
    """Verify a candidate signature against ``payload`` in constant time.

    The comparison uses :func:`hmac.compare_digest` to avoid leaking timing
    information about how many leading bytes matched. A ``sha256=`` prefix (as
    used by some webhook providers) is tolerated, and comparison is
    case-insensitive on the hex digits.

    Args:
        payload: The exact raw request body that was signed.
        signature: The provided signature to check (hex, optional ``sha256=``).
        secret: The shared secret key.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    provided = signature.strip()
    if provided.lower().startswith("sha256="):
        provided = provided[len("sha256=") :]
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, provided.lower())
