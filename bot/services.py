from bot.client import BinanceClient

def fetch_positions(client: BinanceClient):
    data = client.get_account()
    return [
        p for p in data.get("positions", [])
        if float(p.get("positionAmt", 0)) != 0
    ]

def fetch_balances(client: BinanceClient):
    data = client.get_account()
    return [
        a for a in data.get("assets", [])
        if float(a.get("walletBalance", 0)) > 0
    ]

def fetch_order_history(client: BinanceClient, symbol: str, limit: int = 10):
    return client.get_all_orders(symbol=symbol.upper(), limit=limit)