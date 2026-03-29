# Mockance — Binance Futures Demo Trading Bot

Mockance is a command-line trading bot for Binance USDT-M Futures (Demo Trading environment) built with Python.
It supports Market, Limit, and Stop-Limit orders with both an interactive TUI and a flag-based CLI.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, retries, error handling)
│   ├── orders.py          # Order placement logic + fill polling
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Rotating file + console logger
├── cli.py                 # CLI entry point
├── tui.py                 # Interactive TUI
├── logs/
│   └── bot.log
├── .env
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd trading_bot
pip install -r requirements.txt
```

---

### 2. Create a Binance Demo Trading account

1. Go to: https://www.binance.com/en/futures/demo
2. Enable Demo Trading
3. Generate API keys
4. Copy API Key and Secret

---

### 3. Configure credentials

Create a `.env` file:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

---

## API Endpoint

Binance has migrated Futures Testnet to Demo Trading.

This project uses:

```
https://demo-fapi.binance.com
```

---

## Running the Bot

### Interactive mode

```bash
python cli.py
```

### Direct TUI

```bash
python tui.py
```

---

## CLI Commands

### Market order

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01
```

---

### Limit order

```bash
python cli.py place-order --symbol BTCUSDT --side SELL --order-type LIMIT --quantity 0.01 --price 95000
```

---

### Stop-Limit order

```bash
python cli.py place-order --symbol BTCUSDT --side SELL --order-type STOP-LIMIT --quantity 0.01 --stop-price 90000 --price 89500
```

---

### Dry run (simulation mode)

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01 --dry-run
```

Simulates the order without sending it to Binance. Useful for validation and testing.

---

### Account balance

```bash
python cli.py balance
```

---

### Trade history

```bash
python cli.py history --symbol BTCUSDT --limit 10
```

Displays recent orders for a given symbol.

---

### CLI Help

```bash
python cli.py --help
python cli.py place-order --help
```

---

## Features

* Market, Limit, and Stop-Limit orders
* BUY and SELL support
* CLI and interactive TUI interface
* Structured architecture (client, orders, validation separation)
* Logging with rotating file support
* Retry handling for network failures
* Input validation with clear error messages
* Order preview before execution
* Dry-run mode for safe simulation
* Trade history viewer
* Risk guard for high-exposure trades

---

## Risk Guard

Before placing an order, Mockance estimates trade size relative to available balance.

* Warns if trade uses more than 50 percent of balance
* Requires confirmation if above 80 percent
* Helps prevent accidental large positions

---

## Logging

Logs are written to:

```
logs/bot.log
```

| Destination | Level |
| ----------- | ----- |
| Console     | INFO  |
| File        | DEBUG |

---

## Error Handling

Handles:

* Invalid symbols
* Incorrect parameters
* Insufficient margin
* Exchange constraints (precision, min notional)
* Network failures with retries
* Missing credentials

---

## Demo Trading Notes

* Market orders may initially return `NEW` before being filled
* The bot polls order status for accurate execution details
* Demo trading has stricter limits than mainnet
* Use small quantities for testing

---

## Requirements

```
requests
python-dotenv
rich
typer
urllib3
```

---

## Assumptions

* USDT-M Futures only
* Demo Trading API is used
* Orders use GTC where applicable
* Stop-Limit implemented via Binance Futures STOP type

---

## Summary

Mockance demonstrates:

* Clean API client design
* Structured backend architecture
* Robust error handling and logging
* Practical understanding of trading systems
* Safe execution practices through validation and risk control

---
