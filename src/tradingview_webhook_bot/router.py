"""Dispatch :class:`~tradingview_webhook_bot.intent.OrderIntent` objects to a
pluggable executor.

The :class:`Executor` protocol is the seam between this offline, broker-agnostic
core and any real venue: implement :meth:`Executor.execute` against your broker's
SDK and the rest of the pipeline (parse -> authenticate -> intent -> route) is
unchanged. :class:`FakeExecutor` is an in-memory implementation used by the demo
and the tests so everything runs without network access.

Part of TradingView Webhook Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from tradingview_webhook_bot.alert import parse_alert
from tradingview_webhook_bot.auth import verify_signature
from tradingview_webhook_bot.intent import OrderIntent, to_intent


@runtime_checkable
class Executor(Protocol):
    """Anything that can act on an :class:`OrderIntent`.

    Implementations return a broker order id (or any opaque receipt string).
    """

    def execute(self, intent: OrderIntent) -> str:
        """Act on ``intent`` and return a receipt/order id."""
        ...


class FakeExecutor:
    """In-memory executor that records every intent it receives.

    Useful for tests, dry-runs and the offline demo. Each call returns a
    deterministic ``"SIM-<n>"`` order id and appends the intent to
    :attr:`received`.
    """

    def __init__(self) -> None:
        self.received: list[OrderIntent] = []

    def execute(self, intent: OrderIntent) -> str:
        """Record ``intent`` and return a simulated order id."""
        self.received.append(intent)
        return f"SIM-{len(self.received)}"


class IntentRouter:
    """End-to-end webhook pipeline: authenticate, parse, map, and dispatch.

    Args:
        executor: The executor that intents are dispatched to.
        secret: Optional shared secret. When set, every payload handled by
            :meth:`handle` must carry a valid HMAC-SHA256 signature.
    """

    def __init__(self, executor: Executor, secret: str | None = None) -> None:
        self._executor = executor
        self._secret = secret

    def dispatch(self, intent: OrderIntent) -> str:
        """Send a ready-made ``intent`` straight to the executor."""
        return self._executor.execute(intent)

    def handle(self, payload: str, signature: str | None = None) -> str:
        """Process a raw webhook ``payload`` from authentication to dispatch.

        Args:
            payload: The raw alert body (JSON or templated text).
            signature: The provided HMAC signature. Required when this router
                was constructed with a ``secret``.

        Returns:
            The executor's receipt/order id.

        Raises:
            PermissionError: If a secret is configured and the signature is
                missing or invalid.
            ValueError: If the payload cannot be parsed into a valid intent.
        """
        if self._secret is not None:
            if signature is None:
                raise PermissionError("missing signature")
            if not verify_signature(payload, signature, self._secret):
                raise PermissionError("invalid signature")

        signal = parse_alert(payload)
        intent = to_intent(signal)
        return self.dispatch(intent)
