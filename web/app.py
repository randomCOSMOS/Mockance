import sys
import os

# Allow importing from parent trading_bot directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from bot.client import BinanceAPIError, BinanceClient
from bot.orders import place_limit_order, place_market_order
from bot.services import fetch_balances, fetch_order_history, fetch_positions
from bot.validators import ValidationError, validate_all
from bot.logging_config import new_request_id

app = Flask(__name__)


def get_client():
    key = os.getenv("BINANCE_API_KEY", "").strip()
    secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not key or not secret:
        raise RuntimeError("Missing API credentials in .env")
    return BinanceClient(key, secret)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/balances")
def api_balances():
    new_request_id()
    try:
        client = get_client()
        balances = fetch_balances(client)
        account = client.get_account(context="web-balance-view")
        return jsonify({
            "ok": True,
            "balances": balances,
            "totalWalletBalance": account.get("totalWalletBalance", "0"),
            "availableBalance": account.get("availableBalance", "0"),
            "totalUnrealizedProfit": account.get("totalUnrealizedProfit", "0"),
        })
    except BinanceAPIError as e:
        return jsonify({"ok": False, "code": e.code, "msg": e.msg}), 400
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/api/positions")
def api_positions():
    new_request_id()
    try:
        client = get_client()
        positions = fetch_positions(client)
        return jsonify({"ok": True, "positions": positions})
    except BinanceAPIError as e:
        return jsonify({"ok": False, "code": e.code, "msg": e.msg}), 400
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/api/history")
def api_history():
    new_request_id()
    symbol = request.args.get("symbol", "").upper().strip()
    limit = int(request.args.get("limit", 10))
    if not symbol:
        return jsonify({"ok": False, "msg": "symbol is required"}), 400
    try:
        client = get_client()
        orders = fetch_order_history(client, symbol, limit)
        return jsonify({"ok": True, "orders": orders[::-1]})
    except BinanceAPIError as e:
        return jsonify({"ok": False, "code": e.code, "msg": e.msg}), 400
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/api/order", methods=["POST"])
def api_place_order():
    new_request_id()
    body = request.get_json(force=True)
    symbol = body.get("symbol", "")
    side = body.get("side", "")
    order_type = body.get("orderType", "")
    quantity = body.get("quantity")
    price = body.get("price")

    try:
        quantity = float(quantity)
        price = float(price) if price not in (None, "") else None
    except (TypeError, ValueError) as e:
        return jsonify({"ok": False, "msg": f"Invalid numeric value: {e}"}), 400

    try:
        client = get_client()
        if order_type == "MARKET":
            resp = place_market_order(client, symbol, side, quantity)
        elif order_type == "LIMIT":
            resp = place_limit_order(client, symbol, side, quantity, price)
        else:
            return jsonify({"ok": False, "msg": "STOP-LIMIT orders are no longer supported."}), 400
        return jsonify({"ok": True, "order": resp})
    except BinanceAPIError as e:
        return jsonify({"ok": False, "code": e.code, "msg": e.msg}), 400
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)