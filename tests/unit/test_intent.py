"""Tests for mapping alert signals onto order intents."""

from __future__ import annotations

import pytest

from tradingview_webhook_bot.alert import Action, AlertSignal
from tradingview_webhook_bot.intent import OrderType, Side, to_intent


def test_market_intent_when_no_price() -> None:
    signal = AlertSignal(ticker="BTCUSDT", action=Action.BUY, quantity=1.0)
    intent = to_intent(signal)
    assert intent.symbol == "BTCUSDT"
    assert intent.side is Side.BUY
    assert intent.quantity == 1.0
    assert intent.order_type is OrderType.MARKET
    assert intent.limit_price is None


def test_limit_intent_when_price_present() -> None:
    signal = AlertSignal(
        ticker="ETHUSDT", action=Action.SELL, quantity=2.0, price=3200.0, strategy="ema"
    )
    intent = to_intent(signal)
    assert intent.side is Side.SELL
    assert intent.order_type is OrderType.LIMIT
    assert intent.limit_price == 3200.0
    assert intent.strategy == "ema"


def test_to_intent_rejects_non_positive_quantity() -> None:
    # Bypass AlertSignal validation via construct() to exercise to_intent's guard.
    signal = AlertSignal.model_construct(
        ticker="X", action=Action.BUY, quantity=0.0, price=None, strategy=None
    )
    with pytest.raises(ValueError):
        to_intent(signal)
