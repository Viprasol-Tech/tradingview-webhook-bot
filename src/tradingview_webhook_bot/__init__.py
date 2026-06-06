"""TradingView Webhook Bot — by Viprasol Tech Private Limited.

Parse TradingView alert payloads into validated, broker-agnostic order intents,
optionally authenticated with HMAC-SHA256, and dispatch them to a pluggable
executor — all fully offline and dependency-light.
"""

from __future__ import annotations

from tradingview_webhook_bot.alert import Action, AlertSignal, parse_alert
from tradingview_webhook_bot.auth import sign_payload, verify_signature
from tradingview_webhook_bot.intent import OrderIntent, to_intent
from tradingview_webhook_bot.router import FakeExecutor, IntentRouter

__all__ = [
    "Action",
    "AlertSignal",
    "FakeExecutor",
    "IntentRouter",
    "OrderIntent",
    "parse_alert",
    "sign_payload",
    "to_intent",
    "verify_signature",
]

__version__ = "0.1.0"
