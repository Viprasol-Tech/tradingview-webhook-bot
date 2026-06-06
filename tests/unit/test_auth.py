"""Tests for HMAC-SHA256 authentication."""

from __future__ import annotations

import hashlib
import hmac

from tradingview_webhook_bot.auth import sign_payload, verify_signature


def test_sign_matches_stdlib_reference() -> None:
    payload = '{"ticker": "BTCUSDT", "action": "buy"}'
    secret = "super-secret"
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    assert sign_payload(payload, secret) == expected


def test_verify_accepts_valid_signature() -> None:
    payload = "ticker=ETHUSDT;action=sell;qty=2"
    secret = "k"
    assert verify_signature(payload, sign_payload(payload, secret), secret) is True


def test_verify_accepts_sha256_prefix_and_uppercase() -> None:
    payload = "data"
    secret = "k"
    sig = sign_payload(payload, secret)
    assert verify_signature(payload, f"sha256={sig.upper()}", secret) is True


def test_verify_rejects_tampered_payload() -> None:
    secret = "k"
    sig = sign_payload("original", secret)
    assert verify_signature("tampered", sig, secret) is False


def test_verify_rejects_wrong_secret() -> None:
    payload = "data"
    sig = sign_payload(payload, "right")
    assert verify_signature(payload, sig, "wrong") is False


def test_bytes_and_str_secret_equivalent() -> None:
    payload = "data"
    assert sign_payload(payload, "k") == sign_payload(payload.encode(), b"k")
