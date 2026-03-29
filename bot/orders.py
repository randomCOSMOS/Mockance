import time
from bot.client import BinanceClient
from bot.logging_config import get_logger

logger = get_logger("bot.orders")

_POLL_INTERVAL = 1   
_POLL_ATTEMPTS = 8     


def _poll_until_filled(client: BinanceClient, symbol: str, order_id: int) -> dict:

    for attempt in range(1, _POLL_ATTEMPTS + 1):
        time.sleep(_POLL_INTERVAL)
        order = client.get_order(symbol=symbol, order_id=order_id)
        status = order.get("status")
        logger.debug("Poll #%d | id=%s status=%s", attempt, order_id, status)
        if status == "FILLED":
            return order
    logger.warning("Order %s not FILLED after %d polls — returning last known state",
                   order_id, _POLL_ATTEMPTS)
    return order


def place_market_order(client: BinanceClient, symbol, side, quantity):
    resp = client.place_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity,
    )
    order_id = resp.get("orderId")
    logger.info("Market order submitted | id=%s status=%s", order_id, resp.get("status"))

    filled = _poll_until_filled(client, symbol, order_id)
    logger.info("Market order result   | id=%s status=%s executedQty=%s avgPrice=%s",
                filled.get("orderId"), filled.get("status"),
                filled.get("executedQty"), filled.get("avgPrice"))
    return filled


def place_limit_order(client: BinanceClient, symbol, side, quantity, price):
    resp = client.place_order(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=quantity,
        price=price,
        timeInForce="GTC",
    )
    logger.info("Limit order placed | id=%s status=%s price=%s",
                resp.get("orderId"), resp.get("status"), resp.get("price"))
    return resp

def estimate_notional(quantity: float, price: float | None, fallback_price: float = 60000):
    p = price if price else fallback_price
    return quantity * p


def place_stop_limit_order(client: BinanceClient, symbol, side, quantity, price, stop_price):
    resp = client.place_order(
        symbol=symbol,
        side=side,
        type="STOP",
        quantity=quantity,
        price=price,
        stopPrice=stop_price,
        timeInForce="GTC",
    )
    logger.info("Stop-Limit order placed | id=%s status=%s stopPrice=%s limitPrice=%s",
                resp.get("orderId"), resp.get("status"), stop_price, price)
    return resp