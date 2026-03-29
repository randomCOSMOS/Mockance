import os
import typer
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from typing import Optional

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import get_logger
from bot.orders import place_limit_order, place_market_order, place_stop_limit_order
from bot.services import fetch_order_history, fetch_balances, fetch_positions
from bot.validators import ValidationError, validate_all

load_dotenv()
app = typer.Typer(
    help="Binance Futures Testnet — Trading Terminal",
    add_completion=False,
    invoke_without_command=True,
)
console = Console()
logger = get_logger("bot.cli")

ACCENT   = "bold yellow"
DIM      = "dim white"
MUTED    = "grey62"
BUY_COL  = "bold green"
SELL_COL = "bold red"

_LOGO = """\
███╗   ███╗ ██████╗  ██████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
████╗ ████║██╔═══██╗██╔════╝██║ ██╔╝██╔══██╗████╗  ██║██╔════╝██╔════╝
██╔████╔██║██║   ██║██║     █████╔╝ ███████║██╔██╗ ██║██║     █████╗  
██║╚██╔╝██║██║   ██║██║     ██╔═██╗ ██╔══██║██║╚██╗██║██║     ██╔══╝  
██║ ╚═╝ ██║╚██████╔╝╚██████╗██║  ██╗██║  ██║██║ ╚████║╚██████╗███████╗
╚═╝     ╚═╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
 """

def _banner():
    console.print()
    logo     = Text(_LOGO, style="bold yellow", justify="center")
    subtitle = Text("FUTURES TESTNET  ·  TRADING TERMINAL", style="dim yellow", justify="center")
    console.print(Panel(
        Text.assemble(logo, "\n", subtitle),
        border_style="yellow", padding=(0, 6), box=box.HEAVY,
    ))
    console.print()

def get_client():
    key    = os.getenv("BINANCE_API_KEY", "").strip()
    secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not key or not secret:
        console.print(Panel(
            "[bold red]No API credentials found.[/]\nAdd BINANCE_API_KEY and BINANCE_API_SECRET to your .env file.",
            border_style="red", box=box.HEAVY,
        ))
        raise typer.Exit(1)
    return BinanceClient(key, secret)


def print_request(symbol, side, order_type, quantity, price=None, stop_price=None):
    t = Table(box=box.SIMPLE_HEAVY, border_style="yellow", show_lines=False,
              title=f"[{MUTED}]ORDER PREVIEW[/]", title_justify="left",
              title_style="dim", padding=(0, 2))
    headers = ["SYMBOL", "SIDE", "TYPE", "QTY"]
    side_fmt = f"[{BUY_COL}]{side}[/]" if side == "BUY" else f"[{SELL_COL}]{side}[/]"
    values   = [f"[bold]{symbol}[/]", side_fmt, f"[bold white]{order_type}[/]", str(quantity)]
    if stop_price is not None:
        headers.append("STOP"); values.append(f"[yellow]{stop_price}[/]")
    if price is not None:
        headers.append("LIMIT"); values.append(f"[yellow]{price}[/]")
    for h in headers:
        t.add_column(h, justify="center", header_style=MUTED, style="white")
    t.add_row(*values)
    console.print(t)


def print_response(resp: dict):
    avg    = resp.get("avgPrice", "0") or "0"
    avg_d  = f"[yellow]{avg}[/]" if float(avg) > 0 else f"[{MUTED}]—[/]"
    status = resp.get("status", "N/A")
    st_fmt = f"[bold green]{status}[/]" if status == "FILLED" else f"[yellow]{status}[/]"
    side   = resp.get("side", "")
    sd_fmt = f"[{BUY_COL}]{side}[/]" if side == "BUY" else f"[{SELL_COL}]{side}[/]"

    t = Table(box=box.SIMPLE_HEAVY, border_style="green", show_lines=False,
              title=f"[{MUTED}]ORDER CONFIRMATION[/]", title_justify="left",
              title_style="dim", padding=(0, 2))
    for c in ["ORDER ID", "STATUS", "EXEC QTY", "AVG PRICE", "TYPE", "SIDE"]:
        t.add_column(c, justify="center", header_style=MUTED, style="white")
    t.add_row(
        f"[bold]{resp.get('orderId', 'N/A')}[/]", st_fmt,
        str(resp.get("executedQty", "0")), avg_d,
        resp.get("type", ""), sd_fmt,
    )
    console.print(t)
    console.print(Panel(
        f"[bold green]ORDER SUBMITTED[/]  [dim]#{resp.get('orderId')}[/]",
        border_style="green", box=box.HEAVY, padding=(0, 2),
    ))

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is not None:
        return

    _banner()
    console.print(f"  [{MUTED}]How would you like to proceed?[/]\n")
    console.print(f"    [{MUTED}]1[/]  Interactive TUI  [{MUTED}]·  guided menus, no flags[/]")
    console.print(f"    [{MUTED}]2[/]  CLI reference    [{MUTED}]·  show flag examples[/]")
    console.print()

    choice = Prompt.ask(f"  [{ACCENT}]›[/] [white]Select[/]", choices=["1", "2"], default="1")
    console.print()

    if choice == "1":
        from tui import tui_main
        tui_main()
    else:
        console.print(Rule(f"[{MUTED}]CLI USAGE[/]", style="yellow", align="left"))
        console.print()
        examples = [
            ("Market order",     "python cli.py place-order --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01"),
            ("Limit order",      "python cli.py place-order --symbol BTCUSDT --side SELL --order-type LIMIT --quantity 0.01 --price 95000"),
            ("Stop-Limit order", "python cli.py place-order --symbol BTCUSDT --side SELL --order-type STOP-LIMIT --quantity 0.01 --stop-price 90000 --price 89500"),
            ("Account balance",  "python cli.py balance"),
            ("Full help",        "python cli.py place-order --help"),
        ]
        for label, cmd in examples:
            console.print(f"  [{MUTED}]{label}[/]")
            console.print(f"  [bold white]{cmd}[/]\n")

@app.command("place-order")
def place_order(
    symbol:     str             = typer.Option(...,  help="Trading pair, e.g. BTCUSDT"),
    side:       str             = typer.Option(...,  help="BUY or SELL"),
    order_type: str             = typer.Option(...,  "--order-type", help="MARKET, LIMIT, or STOP-LIMIT"),
    quantity:   float           = typer.Option(...,  help="Quantity in base asset"),
    price:      Optional[float] = typer.Option(None, help="Limit price — required for LIMIT and STOP-LIMIT"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price", help="Trigger price — required for STOP-LIMIT"),
    dry_run:    bool            = typer.Option(False, "--dry-run", help="Simulate order without sending to exchange"),
):
    """Place a MARKET, LIMIT, or STOP-LIMIT order.
    Includes risk guard and dry-run support."""
    
    logger.info("CLI: place-order symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
                symbol, side, order_type, quantity, price, stop_price)

    client = get_client()

    try:
        symbol, side, order_type, quantity, price, stop_price = validate_all(
            symbol, side, order_type, quantity, price, stop_price
        )
    except ValidationError as e:
        console.print(Panel(f"[red]{e}[/]", border_style="red", box=box.HEAVY,
                            title="[bold red]VALIDATION ERROR[/]", title_align="left"))
        logger.error("Validation failed: %s", e)
        raise typer.Exit(1)
    print_request(symbol, side, order_type, quantity, price, stop_price)
    try:
        account = client.get_account()
        available_balance = float(account.get("availableBalance", 0))

        est_price = price if price else 60000
        notional = quantity * est_price

        usage_pct = (notional / available_balance) * 100 if available_balance > 0 else 0

        if usage_pct > 50:
            console.print(Panel(
                f"[yellow]⚠ High Risk Trade[/]\n"
                f"Estimated notional: {notional:.2f} USDT\n"
                f"Using ~{usage_pct:.1f}% of available balance",
                border_style="yellow",
                box=box.HEAVY,
            ))

        if usage_pct > 80:
            confirm = Prompt.ask("Proceed anyway?", choices=["y", "n"], default="n")
            if confirm.lower() != "y":
                console.print("[red]Order cancelled due to risk.[/]")
                logger.warning("Order cancelled by risk guard | usage=%.2f%%", usage_pct)
                raise typer.Exit()

    except Exception as e:
        logger.warning("Risk check skipped: %s", e)

    if dry_run:
        console.print(Panel(
            "[bold yellow]DRY RUN[/]\nOrder validated successfully.\nNo request was sent to Binance.",
            border_style="yellow",
            box=box.HEAVY,
        ))
        logger.info("Dry run executed — no API call made")
        raise typer.Exit(0)
    
    try:
        if order_type == "MARKET":
            resp = place_market_order(client, symbol, side, quantity)
        elif order_type == "LIMIT":
            resp = place_limit_order(client, symbol, side, quantity, price)
        else:
            resp = place_stop_limit_order(client, symbol, side, quantity, price, stop_price)

        print_response(resp)

    except BinanceAPIError as e:
        console.print(Panel(f"[red]Error {e.code}:[/] {e.msg}", border_style="red",
                            box=box.HEAVY, title="[bold red]ORDER FAILED[/]", title_align="left"))
        logger.error("Order failed: code=%s msg=%s", e.code, e.msg)
        raise typer.Exit(1)

    except Exception as e:
        console.print(Panel(f"[red]{e}[/]", border_style="red", box=box.HEAVY,
                            title="[bold red]UNEXPECTED ERROR[/]", title_align="left"))
        logger.exception("Unexpected error")
        raise typer.Exit(1)

@app.command("balance")
def show_balance():
    """Show Demo Futures account balances."""
    client = get_client()
    try:
        data = client.get_account()
    except BinanceAPIError as e:
        console.print(Panel(f"[red]Error {e.code}:[/] {e.msg}", border_style="red",
                            box=box.HEAVY, title="[bold red]ERROR[/]", title_align="left"))
        raise typer.Exit(1)

    assets = fetch_balances(client)
    if not assets:
        console.print(Panel(f"[{MUTED}]No assets with non-zero balance.[/]",
                            border_style="yellow", box=box.HEAVY))
        return

    t = Table(box=box.SIMPLE_HEAVY, border_style="yellow", show_lines=False,
              title=f"[{MUTED}]TESTNET ACCOUNT[/]", title_justify="left",
              title_style="dim", padding=(0, 2))
    t.add_column("ASSET",      header_style=MUTED, style="bold white")
    t.add_column("WALLET",     justify="right", header_style=MUTED, style="white")
    t.add_column("AVAIL",      justify="right", header_style=MUTED, style="white")
    t.add_column("UNREAL PNL", justify="right", header_style=MUTED)

    for a in assets:
        pnl = float(a.get("unrealizedProfit", 0))
        pnl_fmt = f"[green]+{pnl:.4f}[/]" if pnl >= 0 else f"[red]{pnl:.4f}[/]"
        t.add_row(a["asset"],
                  a.get("walletBalance",    "0"),
                  a.get("availableBalance", "0"),
                  pnl_fmt)
    console.print(t)

@app.command("history")
def order_history(
    symbol: str = typer.Option(..., help="Trading pair, e.g. BTCUSDT"),
    limit: int = typer.Option(10, help="Number of recent orders"),
):
    """View recent order history for a symbol."""
    client = get_client()

    try:
        orders = fetch_order_history(client, symbol, limit)
    except BinanceAPIError as e:
        console.print(Panel(f"[red]Error {e.code}:[/] {e.msg}", border_style="red"))
        raise typer.Exit(1)

    if not orders:
        console.print("[yellow]No orders found.[/]")
        return

    t = Table(title="Recent Orders", border_style="yellow")
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

@app.command("positions")
def show_positions():
    """Show open futures positions."""
    client = get_client()

    try:
        data = client.get_account()
    except BinanceAPIError as e:
        console.print(f"[red]Error {e.code}: {e.msg}[/]")
        raise typer.Exit(1)

    positions = fetch_positions(client)

    if not positions:
        console.print("[yellow]No open positions.[/]")
        return

    t = Table(title="Open Positions", border_style="yellow")
    t.add_column("SYMBOL")
    t.add_column("SIZE")
    t.add_column("ENTRY")
    t.add_column("PNL")

    for p in positions:
        pnl = float(p["unrealizedProfit"])
        pnl_fmt = f"[green]{pnl:.4f}[/]" if pnl >= 0 else f"[red]{pnl:.4f}[/]"

        t.add_row(
            p["symbol"],
            p["positionAmt"],
            p["entryPrice"],
            pnl_fmt,
        )

    console.print(t)

if __name__ == "__main__":
    app()