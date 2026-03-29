import os
import sys

from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import get_logger
from bot.orders import place_limit_order, place_market_order, place_stop_limit_order
from bot.services import fetch_balances, fetch_positions, fetch_order_history
from bot.validators import ValidationError, validate_all

load_dotenv()
console = Console()
logger = get_logger("bot.tui")

ACCENT   = "bold yellow"
DIM      = "dim white"
BORDER   = "yellow"
BUY_COL  = "bold green"
SELL_COL = "bold red"
MUTED    = "grey62"

_ERROR_HINTS: dict[int, str] = {
    -1121: (
        "Symbol not found on testnet.\n"
        "  Valid pairs: BTCUSDT · ETHUSDT · BNBUSDT · SOLUSDT\n"
        "  Use the futures symbol format — no slashes."
    ),
    -2027: (
        "Position size exceeds your leverage limit.\n"
        "  Options:\n"
        "    · Reduce quantity\n"
        "    · Lower leverage on the testnet UI\n"
        "    · Close your existing position first"
    ),
    -1111: "Quantity precision error — check the minimum lot size for this symbol.",
    -1013: "Quantity or notional is below the exchange minimum.",
    -2019: "Insufficient margin — available balance too low.",
    -1116: "Invalid order type for this symbol.",
    -1117: "Side must be BUY or SELL.",
    -2021: "Order would immediately trigger — adjust your stop price.",
    -1102: "A required parameter is missing (symbol, side, or quantity).",
}

def _friendly(e: BinanceAPIError) -> str:
    try:
        hint = _ERROR_HINTS.get(int(e.code))
    except (ValueError, TypeError):
        hint = None
    return f"[bold]Error {e.code}[/]\n\n{hint}" if hint else f"[bold]Error {e.code}:[/] {e.msg}"

_LOGO = """\
███╗   ███╗ ██████╗  ██████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
████╗ ████║██╔═══██╗██╔════╝██║ ██╔╝██╔══██╗████╗  ██║██╔════╝██╔════╝
██╔████╔██║██║   ██║██║     █████╔╝ ███████║██╔██╗ ██║██║     █████╗  
██║╚██╔╝██║██║   ██║██║     ██╔═██╗ ██╔══██║██║╚██╗██║██║     ██╔══╝  
██║ ╚═╝ ██║╚██████╔╝╚██████╗██║  ██╗██║  ██║██║ ╚████║╚██████╗███████╗
╚═╝     ╚═╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
"""

def _header():
    console.print()
    logo = Text(_LOGO, style="bold yellow", justify="center")
    subtitle = Text("FUTURES TESTNET  ·  TRADING TERMINAL", style="dim yellow", justify="center")
    console.print(Panel(
        Text.assemble(logo, "\n", subtitle),
        border_style="yellow",
        padding=(0, 6),
        box=box.HEAVY,
    ))
    console.print()

def _divider(label: str = ""):
    console.print(Rule(f"[{MUTED}]{label}[/]", style="yellow", align="left"))

def _get_client() -> BinanceClient:
    key    = os.getenv("BINANCE_API_KEY", "").strip()
    secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not key or not secret:
        console.print(Panel("[bold red]No API credentials found.[/]\nCreate a .env file with BINANCE_API_KEY and BINANCE_API_SECRET.",
                            border_style="red", box=box.HEAVY))
        sys.exit(1)
    return BinanceClient(key, secret)

def _ask(prompt: str) -> str:
    return Prompt.ask(f"  [{ACCENT}]›[/] [white]{prompt}[/]").strip()

def _pick(label: str, choices: list[str]) -> str:
    console.print(f"\n  [{ACCENT}]›[/] [white]{label}[/]")
    for i, c in enumerate(choices, 1):
        console.print(f"    [{MUTED}]{i}[/]  {c}")
    while True:
        raw = Prompt.ask(f"  [{ACCENT}]›[/] [white]Select[/]").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        console.print(f"  [red]✗[/] Enter a number between 1 and {len(choices)}.")

def _field_loop(prompt: str, *, converter=str, validate=None):
    while True:
        raw = _ask(prompt)
        try:
            value = converter(raw)
            if validate:
                validate(value)
            return value
        except (ValueError, ValidationError) as e:
            console.print(f"  [red]✗[/] {e}")

def _print_request(symbol, side, order_type, quantity, price=None, stop_price=None):
    t = Table(box=box.SIMPLE_HEAVY, border_style="yellow", show_lines=False,
              title=f"[{MUTED}]ORDER PREVIEW[/]", title_justify="left",
              title_style="dim", padding=(0, 2))

    headers = ["SYMBOL", "SIDE", "TYPE", "QTY"]
    side_fmt = f"[{BUY_COL}]{side}[/]" if side == "BUY" else f"[{SELL_COL}]{side}[/]"
    values   = [f"[bold]{symbol}[/]", side_fmt, f"[bold white]{order_type}[/]", str(quantity)]

    if stop_price is not None:
        headers.append("STOP")
        values.append(f"[yellow]{stop_price}[/]")
    if price is not None:
        headers.append("LIMIT")
        values.append(f"[yellow]{price}[/]")

    for h in headers:
        t.add_column(h, justify="center", header_style=MUTED, style="white")
    t.add_row(*values)
    console.print()
    console.print(t)


def _print_response(resp: dict):
    avg = resp.get("avgPrice", "0") or "0"
    avg_display = f"[yellow]{avg}[/]" if float(avg) > 0 else f"[{MUTED}]—[/]"

    status = resp.get("status", "N/A")
    status_fmt = f"[bold green]{status}[/]" if status == "FILLED" else f"[yellow]{status}[/]"

    t = Table(box=box.SIMPLE_HEAVY, border_style="green", show_lines=False,
              title=f"[{MUTED}]ORDER CONFIRMATION[/]", title_justify="left",
              title_style="dim", padding=(0, 2))

    cols = ["ORDER ID", "STATUS", "EXEC QTY", "AVG PRICE", "TYPE", "SIDE"]
    side = resp.get("side", "")
    side_fmt = f"[{BUY_COL}]{side}[/]" if side == "BUY" else f"[{SELL_COL}]{side}[/]"
    vals = [
        f"[bold]{resp.get('orderId', 'N/A')}[/]",
        status_fmt,
        str(resp.get("executedQty", "0")),
        avg_display,
        resp.get("type", ""),
        side_fmt,
    ]
    for c in cols:
        t.add_column(c, justify="center", header_style=MUTED, style="white")
    t.add_row(*vals)
    console.print(t)
    console.print(Panel(
        f"[bold green]ORDER SUBMITTED[/]  [dim]#{resp.get('orderId')}[/]",
        border_style="green", box=box.HEAVY, padding=(0, 2)
    ))

def screen_place_order(client: BinanceClient):
    console.print()
    _divider("NEW ORDER")
    console.print()

    def _val_symbol(v: str):
        if not v.isalnum() or len(v) < 3:
            raise ValidationError(f"'{v}' is not a valid symbol. Try BTCUSDT.")

    symbol = _field_loop("Symbol", converter=lambda s: s.upper().strip(), validate=_val_symbol)
    side   = _pick("Side", ["BUY", "SELL"])
    order_type = _pick("Order Type", ["MARKET", "LIMIT", "STOP-LIMIT"])

    def _val_qty(v: float):
        if v <= 0:
            raise ValidationError(f"Quantity must be > 0")
    quantity = _field_loop("Quantity", converter=float, validate=_val_qty)

    price = stop_price = None

    if order_type == "LIMIT":
        def _val_price(v: float):
            if v <= 0: raise ValidationError("Price must be > 0")
        price = _field_loop("Limit Price", converter=float, validate=_val_price)

    elif order_type == "STOP-LIMIT":
        def _val_stop(v: float):
            if v <= 0: raise ValidationError("Stop price must be > 0")
        stop_price = _field_loop("Stop Price  [dim](trigger)[/]", converter=float, validate=_val_stop)
        def _val_limit(v: float):
            if v <= 0: raise ValidationError("Limit price must be > 0")
        price = _field_loop("Limit Price [dim](fill after trigger)[/]", converter=float, validate=_val_limit)

    _print_request(symbol, side, order_type, quantity, price, stop_price)
    console.print()

    confirm = _pick("Submit order?", ["Yes — send it", "No — cancel"])
    if confirm.startswith("No"):
        console.print(f"\n  [{MUTED}]Order cancelled.[/]")
        return

    logger.info("TUI: placing %s %s | symbol=%s qty=%s price=%s stopPrice=%s",
                side, order_type, symbol, quantity, price, stop_price)
    console.print()
    try:
        if order_type == "MARKET":
            resp = place_market_order(client, symbol, side, quantity)
        elif order_type == "LIMIT":
            resp = place_limit_order(client, symbol, side, quantity, price)
        else:
            resp = place_stop_limit_order(client, symbol, side, quantity, price, stop_price)
        _print_response(resp)
    except BinanceAPIError as e:
        logger.debug("TUI order failed: code=%s msg=%s", e.code, e.msg)
        console.print(Panel(_friendly(e), border_style="red", box=box.HEAVY, padding=(1, 2),
                            title="[bold red]ORDER FAILED[/]", title_align="left"))
    except Exception as e:
        console.print(Panel(f"[red]{e}[/]", border_style="red", box=box.HEAVY,
                            title="[bold red]UNEXPECTED ERROR[/]", title_align="left"))
        logger.exception("TUI unexpected error")


def screen_wallet(client: BinanceClient):
    console.print()
    _divider("WALLET BALANCE")
    console.print()

    try:
        data = client.get_account()
    except BinanceAPIError as e:
        console.print(Panel(_friendly(e), border_style="red"))
        return

    assets = fetch_balances(client)

    if not assets:
        console.print("[yellow]No assets with non-zero balance.[/]")
        return

    t = Table(box=box.SIMPLE_HEAVY, border_style="yellow")
    t.add_column("ASSET")
    t.add_column("WALLET", justify="right")
    t.add_column("AVAILABLE", justify="right")

    for a in assets:
        t.add_row(
            a["asset"],
            a.get("walletBalance", "0"),
            a.get("availableBalance", "0"),
        )

    console.print(t)

def screen_positions(client: BinanceClient):
    console.print()
    _divider("OPEN POSITIONS")
    console.print()

    try:
        data = client.get_account()
    except BinanceAPIError as e:
        console.print(Panel(_friendly(e), border_style="red"))
        return

    positions = fetch_positions(client)

    if not positions:
        console.print("[yellow]No open positions.[/]")
        return

    t = Table(box=box.SIMPLE_HEAVY, border_style="green")
    t.add_column("SYMBOL")
    t.add_column("SIZE", justify="right")
    t.add_column("ENTRY", justify="right")
    t.add_column("PNL", justify="right")

    for p in positions:
        size = float(p["positionAmt"])
        pnl = float(p["unrealizedProfit"])

        pnl_fmt = f"[green]{pnl:.4f}[/]" if pnl >= 0 else f"[red]{pnl:.4f}[/]"

        t.add_row(
            p["symbol"],
            f"{size:.4f}",
            p["entryPrice"],
            pnl_fmt,
        )

    console.print(t)

def screen_history(client: BinanceClient):
    console.print()
    _divider("ORDER HISTORY")
    console.print()

    symbol = _ask("Symbol (e.g. BTCUSDT)").upper().strip()

    if not symbol:
        console.print("[red]Please enter a trading pair.[/]")
        return

    try:
        orders = fetch_order_history(client, symbol, 10)
    except BinanceAPIError as e:
        console.print(Panel(_friendly(e), border_style="red"))
        return

    if not orders:
        console.print("[yellow]No orders found.[/]")
        return

    t = Table(box=box.SIMPLE_HEAVY, border_style="yellow")
    t.add_column("ID")
    t.add_column("SIDE")
    t.add_column("TYPE")
    t.add_column("STATUS")
    t.add_column("QTY")
    t.add_column("PRICE")

    for o in orders[::-1]:
        t.add_row(
            str(o["orderId"]),
            o["side"],
            o["type"],
            o["status"],
            o["origQty"],
            o["price"],
        )

    console.print(t)

MENU = ["Place Order", "Wallet Balance", "Open Positions", "Order History", "Exit"]

def tui_main():
    _header()
    client = _get_client()
    console.print(f"  [{MUTED}]● connected  ·  demo-fapi.binance.com[/]\n")

    while True:
        choice = _pick("Command", MENU)
        console.print()

        if choice == "Place Order":
            screen_place_order(client)
        elif choice == "Wallet Balance":
            screen_wallet(client)
        elif choice == "Order History":
            screen_history(client)
        elif choice == "Open Positions":
            screen_positions(client)
        elif choice == "Exit":
            console.print(Panel(f"[{MUTED}]Session closed.[/]",
                                border_style="yellow", box=box.HEAVY, padding=(0, 2)))
            break
        console.print()

if __name__ == "__main__":
    tui_main()