"""Tests for alert payload parsing."""

from __future__ import annotations

import pytest

from tradingview_webhook_bot.alert import Action, AlertSignal, parse_alert


def test_parse_json_payload() -> None:
    payload = '{"ticker": "btcusdt", "action": "buy", "quantity": 0.5, "price": 64000}'
    signal = parse_alert(payload)
    assert signal == AlertSignal(ticker="BTCUSDT", action=Action.BUY, quantity=0.5, price=64000.0)


def test_parse_dict_payload() -> None:
    signal = parse_alert({"symbol": "AAPL", "side": "sell", "qty": 10})
    assert signal.ticker == "AAPL"
    assert signal.action is Action.SELL
    assert signal.quantity == 10.0
    assert signal.price is None


def test_parse_templated_payload() -> None:
    payload = "ticker=ETHUSDT;action=sell;qty=2;price=3200;strategy=ema"
    signal = parse_alert(payload)
    assert signal.ticker == "ETHUSDT"
    assert signal.action is Action.SELL
    assert signal.quantity == 2.0
    assert signal.price == 3200.0
    assert signal.strategy == "ema"


def test_templated_with_placeholder_field_names() -> None:
    # Mirrors a real TradingView template after substitution.
    payload = "strategy.order.action=long,strategy.order.contracts=3,ticker=SOLUSDT"
    signal = parse_alert(payload)
    assert signal.ticker == "SOLUSDT"
    assert signal.action is Action.BUY  # "long" normalises to buy
    assert signal.quantity == 3.0


def test_action_synonyms() -> None:
    assert parse_alert({"ticker": "X", "action": "LONG", "qty": 1}).action is Action.BUY
    assert parse_alert({"ticker": "X", "action": "short", "qty": 1}).action is Action.SELL


@pytest.mark.parametrize("bad", ["", "   ", "{}", "foo=bar"])
def test_missing_fields_raise(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_alert(bad)


def test_unknown_action_raises() -> None:
    with pytest.raises(ValueError):
        parse_alert({"ticker": "X", "action": "hodl", "qty": 1})


def test_non_positive_quantity_raises() -> None:
    with pytest.raises(ValueError):
        parse_alert({"ticker": "X", "action": "buy", "qty": 0})
    with pytest.raises(ValueError):
        parse_alert({"ticker": "X", "action": "buy", "qty": -5})


def test_json_non_object_raises() -> None:
    with pytest.raises(ValueError):
        parse_alert("[1, 2, 3]")
