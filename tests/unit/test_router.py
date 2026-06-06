"""Tests for the webhook intent router and fake executor."""

from __future__ import annotations

import pytest

from tradingview_webhook_bot.auth import sign_payload
from tradingview_webhook_bot.intent import Side
from tradingview_webhook_bot.router import FakeExecutor, IntentRouter

_PAYLOAD = '{"ticker": "BTCUSDT", "action": "buy", "quantity": 0.5, "price": 64000}'
_SECRET = "super-secret"


def test_executor_receives_intent() -> None:
    executor = FakeExecutor()
    router = IntentRouter(executor)
    order_id = router.handle(_PAYLOAD)
    assert order_id == "SIM-1"
    assert len(executor.received) == 1
    intent = executor.received[0]
    assert intent.symbol == "BTCUSDT"
    assert intent.side is Side.BUY
    assert intent.limit_price == 64000.0


def test_router_accepts_valid_signature() -> None:
    executor = FakeExecutor()
    router = IntentRouter(executor, secret=_SECRET)
    signature = sign_payload(_PAYLOAD, _SECRET)
    router.handle(_PAYLOAD, signature)
    assert len(executor.received) == 1


def test_router_rejects_invalid_signature() -> None:
    executor = FakeExecutor()
    router = IntentRouter(executor, secret=_SECRET)
    with pytest.raises(PermissionError):
        router.handle(_PAYLOAD, "deadbeef")
    assert executor.received == []


def test_router_rejects_missing_signature() -> None:
    executor = FakeExecutor()
    router = IntentRouter(executor, secret=_SECRET)
    with pytest.raises(PermissionError):
        router.handle(_PAYLOAD)
    assert executor.received == []


def test_fake_executor_returns_incrementing_ids() -> None:
    executor = FakeExecutor()
    router = IntentRouter(executor)
    assert router.handle(_PAYLOAD) == "SIM-1"
    assert router.handle(_PAYLOAD) == "SIM-2"
