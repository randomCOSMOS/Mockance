# Mockance — Binance Futures Demo Trading Bot

Mockance is a command-line and web trading bot for Binance USDT-M Futures (Demo Trading environment) built with Python.
It supports Market and Limitorders with an interactive TUI, a flag-based CLI, and a browser-based web terminal.

**Note on Testnet Migration**
Binance Futures Testnet has been migrated to a Demo Trading environment.
Older endpoints such as `testnet.binancefuture.com` are deprecated.

This project uses the current official API endpoint:

```
https://demo-fapi.binance.com
```

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, retries, error handling)
│   ├── orders.py          # Order placement logic + fill polling
│   ├── validators.py      # Input validation
│   ├── services.py        # Shared data layer (balances, positions, history)
│   └── logging_config.py  # Rotating file + console logger
├── web/
│   ├── app.py             # Flask server + JSON API routes
│   ├── templates/
│   │   └── index.html     # Single-page web terminal
│   └── static/
│       ├── style.css  # Dark terminal theme
│       └── app.js      # UI logic (nav, forms, fetch)
├── cli.py                 # CLI entry point
├── tui.py                 # Interactive TUI
├── logs/
│   └── bot.log
├── .env
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd trading_bot
pip install -r requirements.txt
```

### 2. Create a Binance Demo Trading account

1. Go to: https://www.binance.com/en/futures/demo
2. Enable Demo Trading
3. Generate API keys
4. Copy API Key and Secret

### 3. Configure credentials

Create a `.env` file:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

## Running the Bot

### Web terminal (browser UI)

```bash
pip install flask
python web/app.py
```

Then open http://localhost:5000

### Interactive TUI

```bash
python cli.py
```

### Direct TUI

```bash
python tui.py
```

## Web Terminal

The web interface is a single-page browser terminal with four views:

- **Trade** — Place Market and Limit orders with side/type toggles, conditional price fields, dry-run mode, and a live confirmation panel
- **Wallet** — Summary cards (total balance, available, unrealized PnL) and a per-asset breakdown table
- **Positions** — Open futures positions with size, entry price, and color-coded PnL
- **History** — Order history by symbol with configurable limit and status tags (FILLED / NEW / CANCELED)

The Flask server at `web/app.py` imports directly from the `bot/` package, so all validation and order logic is shared with the CLI and TUI.

### Web API routes

| Method | Route | Description |
| ------ | ----- | ----------- |
| GET | `/` | Web terminal UI |
| GET | `/api/balances` | Account summary and asset balances |
| GET | `/api/positions` | Open futures positions |
| GET | `/api/history?symbol=BTCUSDT&limit=10` | Recent order history |
| POST | `/api/order` | Place a new order |

## CLI Commands

### Market order

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01
```

### Limit order

```bash
python cli.py place-order --symbol BTCUSDT --side SELL --order-type LIMIT --quantity 0.01 --price 95000
```

### Dry run (simulation mode)

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01 --dry-run
```

Simulates the order without sending it to Binance.

### Wallet balance

```bash
python cli.py balance
```

### Open positions

```bash
python cli.py positions
```

### Trade history

```bash
python cli.py history --symbol BTCUSDT --limit 10
```

### CLI Help

```bash
python cli.py --help
python cli.py place-order --help
```

## Features

* Market and Limit
* BUY and SELL support
* Browser-based web terminal (Flask)
* CLI and interactive TUI interface
* Structured architecture (client, orders, validation, services separation)
* Logging with rotating file support
* Retry handling for network failures
* Input validation with clear error messages
* Order preview before execution
* Dry-run mode for safe simulation
* Trade history viewer
* Open positions tracking
* Risk guard for high-exposure trades

## Risk Guard

Before placing an order, Mockance estimates trade size relative to available balance.

* Warns if trade uses more than 50 percent of balance
* Requires confirmation if above 80 percent
* Applies in both the CLI and web terminal

## Futures Trading Note

In USDT-M Futures:

* You do not own assets like BTC or ETH
* Trades create positions instead of wallet holdings
* Balance remains in USDT
* Use the Positions view or `positions` command to view active trades

## Logging

Logs are written to:

```
logs/bot.log
```

| Destination | Level |
| ----------- | ----- |
| Console     | INFO  |
| File        | DEBUG |

All three interfaces (web, CLI, TUI) write to the same log file.

## Error Handling

Handles:

* Invalid inputs with user-friendly messages
* Exchange rejections (invalid symbol, insufficient balance, etc.)
* Network failures with retries
* Missing credentials
* Unexpected runtime errors

## Demo Trading Notes

* Market orders may initially return `NEW` before being filled
* The bot polls order status for accurate execution details
* Demo trading has stricter limits than mainnet
* Use small quantities for testing

## Requirements

```
requests
python-dotenv
rich
typer
urllib3
flask
```

## Assumptions

* USDT-M Futures only
* Demo Trading API is used
* Orders use GTC where applicable

## Summary

Mockance demonstrates:

* Clean API client design
* Structured backend architecture with separation of concerns
* Shared service layer reused across web, CLI, and TUI
* Robust error handling and logging
* Practical understanding of futures trading systems
* Safe execution practices through validation and risk control