"""Parse TradingView alert payloads into a typed :class:`AlertSignal`.

TradingView lets you write an alert ``message`` in two common shapes:

1. **JSON** — recommended. The payload is a JSON object whose keys map onto the
   signal fields, e.g.::

       {"ticker": "BTCUSDT", "action": "buy", "quantity": 0.5, "price": 64000}

2. **Templated text** — the classic ``key=value`` style built from TradingView
   placeholders such as ``{{ticker}}`` and ``{{strategy.order.action}}``::

       ticker={{ticker}};action={{strategy.order.action}};qty={{strategy.order.contracts}};price={{close}}

   After TradingView substitutes the placeholders, the bot receives a concrete
   string like ``ticker=BTCUSDT;action=buy;qty=0.5;price=64000`` which this
   module parses. Pairs may be separated by ``;``, newlines, or commas.

Both shapes resolve to the same :class:`AlertSignal`. Field names are matched
leniently (``ticker``/``symbol``, ``action``/``side``, ``quantity``/``qty``/
``contracts``, ``price``/``close``, ``strategy``/``strategy.name``) so the same
parser handles a range of real-world alert templates.

Part of TradingView Webhook Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import json
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Action(str, Enum):
    """Direction of a trade requested by an alert."""

    BUY = "buy"
    SELL = "sell"


# Lenient aliases: real TradingView templates use many spellings for the same
# concept. Each canonical field maps to the alternative keys we accept.
_TICKER_KEYS = ("ticker", "symbol", "pair")
_ACTION_KEYS = ("action", "side", "order_action", "strategy.order.action")
_QTY_KEYS = ("quantity", "qty", "contracts", "size", "strategy.order.contracts")
_PRICE_KEYS = ("price", "close", "limit_price", "strategy.order.price")
_STRATEGY_KEYS = ("strategy", "strategy_name", "strategy.name")

# Common buy/sell synonyms emitted by strategy scripts.
_BUY_WORDS = frozenset({"buy", "long", "bull", "enterlong", "enter_long"})
_SELL_WORDS = frozenset({"sell", "short", "bear", "entershort", "enter_short", "exit"})


class AlertSignal(BaseModel):
    """A validated, normalised view of a single TradingView alert.

    Attributes:
        ticker: Instrument symbol, upper-cased (e.g. ``"BTCUSDT"``).
        action: Trade direction, either :attr:`Action.BUY` or :attr:`Action.SELL`.
        quantity: Requested order size; must be strictly positive.
        price: Optional reference/limit price; ``None`` for market orders.
        strategy: Optional name of the originating strategy.
    """

    ticker: str = Field(min_length=1)
    action: Action
    quantity: float = Field(gt=0)
    price: float | None = None
    strategy: str | None = None

    @field_validator("ticker")
    @classmethod
    def _normalise_ticker(cls, value: str) -> str:
        return value.strip().upper()


def _normalise_action(raw: str) -> str:
    """Map a free-form action word onto ``"buy"``/``"sell"``."""
    token = raw.strip().lower().replace(" ", "")
    if token in _BUY_WORDS:
        return Action.BUY.value
    if token in _SELL_WORDS:
        return Action.SELL.value
    # Fall through unchanged so pydantic raises a clear, validated error.
    return token


def _to_float(value: object) -> float:
    """Coerce an alert field to ``float``, raising ``ValueError`` if it can't."""
    if isinstance(value, bool):  # avoid bool-as-number surprises
        raise ValueError(f"expected a number, got bool {value!r}")
    if isinstance(value, (int, float, str)):
        return float(value)
    raise ValueError(f"expected a number, got {type(value).__name__}")


def _first(data: dict[str, object], keys: tuple[str, ...]) -> object | None:
    """Return the first present, non-empty value among ``keys``."""
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return None


def _parse_templated(payload: str) -> dict[str, object]:
    """Parse ``key=value`` pairs separated by ``;``, newlines, or commas."""
    data: dict[str, object] = {}
    # Treat semicolons, newlines and commas as equivalent pair separators.
    normalised = payload.replace("\n", ";").replace(",", ";")
    for chunk in normalised.split(";"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        key, _, value = chunk.partition("=")
        data[key.strip().lower()] = value.strip()
    return data


def parse_alert(payload: str | dict[str, object]) -> AlertSignal:
    """Parse a TradingView alert payload into an :class:`AlertSignal`.

    Args:
        payload: Either a ``dict`` (already-decoded JSON), a JSON string, or a
            templated ``key=value`` string as emitted by a TradingView alert.

    Returns:
        The validated :class:`AlertSignal`.

    Raises:
        ValueError: If the payload is empty, has no recognisable fields, or
            fails validation (e.g. unknown action or non-positive quantity).
    """
    if isinstance(payload, dict):
        data: dict[str, object] = {str(k).lower(): v for k, v in payload.items()}
    else:
        text = payload.strip()
        if not text:
            raise ValueError("empty alert payload")
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            data = _parse_templated(text)
        else:
            if not isinstance(decoded, dict):
                raise ValueError("JSON alert payload must be an object")
            data = {str(k).lower(): v for k, v in decoded.items()}

    ticker = _first(data, _TICKER_KEYS)
    action = _first(data, _ACTION_KEYS)
    quantity = _first(data, _QTY_KEYS)
    if ticker is None or action is None or quantity is None:
        raise ValueError("alert payload missing required fields (need ticker, action, quantity)")

    price = _first(data, _PRICE_KEYS)
    strategy = _first(data, _STRATEGY_KEYS)

    return AlertSignal(
        ticker=str(ticker),
        action=Action(_normalise_action(str(action))),
        quantity=_to_float(quantity),
        price=None if price is None else _to_float(price),
        strategy=None if strategy is None else str(strategy),
    )
