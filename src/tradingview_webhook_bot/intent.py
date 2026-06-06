"""Map an :class:`~tradingview_webhook_bot.alert.AlertSignal` onto a typed,
broker-agnostic :class:`OrderIntent`.

An :class:`OrderIntent` is what the bot would actually hand to a broker adapter.
Keeping it separate from the parsed alert means the same intent shape works for
any venue (equities, futures, crypto) and centralises the safety validation:
unknown actions and non-positive quantities are rejected here, before anything
touches a live account.

Part of TradingView Webhook Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from tradingview_webhook_bot.alert import Action, AlertSignal


class Side(str, Enum):
    """Broker-side order direction."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order execution type, inferred from whether a price is present."""

    MARKET = "market"
    LIMIT = "limit"


class OrderIntent(BaseModel):
    """A validated, broker-agnostic instruction to place a single order.

    Attributes:
        symbol: Instrument symbol, upper-cased.
        side: :attr:`Side.BUY` or :attr:`Side.SELL`.
        quantity: Order size; strictly positive.
        order_type: :attr:`OrderType.LIMIT` when a price is given, else market.
        limit_price: Limit price for limit orders; ``None`` for market orders.
        strategy: Optional originating strategy name, carried for audit.
    """

    symbol: str = Field(min_length=1)
    side: Side
    quantity: float = Field(gt=0)
    order_type: OrderType
    limit_price: float | None = None
    strategy: str | None = None


_ACTION_TO_SIDE: dict[Action, Side] = {
    Action.BUY: Side.BUY,
    Action.SELL: Side.SELL,
}


def to_intent(signal: AlertSignal) -> OrderIntent:
    """Build a validated :class:`OrderIntent` from an :class:`AlertSignal`.

    A market order is produced when the signal carries no price; otherwise a
    limit order at the signal's price is produced.

    Args:
        signal: The parsed alert signal.

    Returns:
        The validated :class:`OrderIntent`.

    Raises:
        ValueError: If the action is unknown or the quantity is not positive.
            (Both conditions are normally caught earlier by ``AlertSignal``,
            but are re-checked here so ``to_intent`` is safe to call on any
            externally-constructed signal.)
    """
    side = _ACTION_TO_SIDE.get(signal.action)
    if side is None:  # pragma: no cover - defensive; Action enum is exhaustive
        raise ValueError(f"unknown action: {signal.action!r}")
    if signal.quantity <= 0:
        raise ValueError(f"quantity must be positive, got {signal.quantity}")

    order_type = OrderType.MARKET if signal.price is None else OrderType.LIMIT
    return OrderIntent(
        symbol=signal.ticker,
        side=side,
        quantity=signal.quantity,
        order_type=order_type,
        limit_price=signal.price,
        strategy=signal.strategy,
    )
