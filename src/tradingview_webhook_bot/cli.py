"""Command-line interface for TradingView Webhook Bot.

``tradingview-webhook-bot demo`` parses a sample TradingView alert into a
validated order intent, signs and verifies it with HMAC, and dispatches it to an
in-memory executor — no network, no API keys, no risk.

Part of TradingView Webhook Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import typer
from rich.console import Console

from tradingview_webhook_bot import __version__
from tradingview_webhook_bot.alert import parse_alert
from tradingview_webhook_bot.auth import sign_payload
from tradingview_webhook_bot.intent import to_intent
from tradingview_webhook_bot.router import FakeExecutor, IntentRouter

app = typer.Typer(add_completion=False, help="TradingView Webhook Bot — by Viprasol Tech.")
console = Console()

_SAMPLE_JSON = (
    '{"ticker": "BTCUSDT", "action": "buy", "quantity": 0.5, '
    '"price": 64000, "strategy": "rsi-cross"}'
)
_SAMPLE_TEMPLATED = "ticker=ETHUSDT;action=sell;qty=2;price=3200;strategy=ema-trend"


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"tradingview-webhook-bot [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def demo(secret: str = typer.Option("super-secret", help="Shared HMAC secret.")) -> None:
    """Parse two sample alerts, authenticate, and route them offline."""
    executor = FakeExecutor()
    router = IntentRouter(executor, secret=secret)

    for label, payload in (("JSON", _SAMPLE_JSON), ("templated", _SAMPLE_TEMPLATED)):
        signal = parse_alert(payload)
        intent = to_intent(signal)
        signature = sign_payload(payload, secret)
        order_id = router.handle(payload, signature)
        console.print(f"[bold]{label}[/] alert -> {payload}")
        console.print(
            f"  intent: [cyan]{intent.side.value}[/] {intent.quantity} "
            f"{intent.symbol} ({intent.order_type.value}"
            + (f" @ {intent.limit_price}" if intent.limit_price is not None else "")
            + ")"
        )
        console.print(f"  signature ok -> executor order id [green]{order_id}[/]\n")

    console.print(f"Executor received [bold]{len(executor.received)}[/] order(s).")


if __name__ == "__main__":
    app()
