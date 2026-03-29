import hashlib
import hmac
import time
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.logging_config import get_logger

logger = get_logger("bot.client")

BASE_URL = "https://demo-fapi.binance.com"

class BinanceAPIError(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        super().__init__(f"[{code}] {msg}")

class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self._key = api_key
        self._secret = api_secret

        retry = Retry(total=3, backoff_factor=1.5,
                      status_forcelist=[429, 500, 502, 503, 504])
        self._session = requests.Session()
        self._session.mount("https://", HTTPAdapter(max_retries=retry))
        self._session.headers["X-MBX-APIKEY"] = self._key

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        params["signature"] = hmac.new(
            self._secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        return params

    def _get(self, path: str, params: dict) -> dict:
        params = {k: v for k, v in params.items() if v is not None}
        params = self._sign(params)
        url = BASE_URL + path
        logger.debug("GET %s", url)
        try:
            resp = self._session.get(url, params=params, timeout=10)
        except requests.exceptions.ConnectionError as e:
            logger.error("Network error: %s", e)
            raise
        logger.debug("Response %s: %s", resp.status_code, resp.text[:300])
        data = resp.json()
        if not resp.ok:
            raise BinanceAPIError(data.get("code", resp.status_code), data.get("msg", resp.text))
        return data

    def _post(self, path: str, params: dict) -> dict:
        params = {k: v for k, v in params.items() if v is not None}
        params = self._sign(params)
        url = BASE_URL + path
        logger.debug("POST %s params=%s", url,
                     {k: "***" if k == "signature" else v for k, v in params.items()})
        try:
            resp = self._session.post(url, data=params, timeout=10)
        except requests.exceptions.ConnectionError as e:
            logger.error("Network error: %s", e)
            raise
        logger.debug("Response %s: %s", resp.status_code, resp.text[:300])
        data = resp.json()
        if not resp.ok:
            raise BinanceAPIError(data.get("code", resp.status_code), data.get("msg", resp.text))
        return data

    def place_order(self, **kwargs) -> dict:
        logger.info("Placing %s %s | symbol=%s qty=%s price=%s",
                    kwargs.get("side"), kwargs.get("type"),
                    kwargs.get("symbol"), kwargs.get("quantity"),
                    kwargs.get("price", "MARKET"))
        return self._post("/fapi/v1/order", kwargs)

    def get_order(self, symbol: str, order_id: int) -> dict:
        return self._get("/fapi/v1/order", {"symbol": symbol, "orderId": order_id})

    def get_account(self) -> dict:
        return self._get("/fapi/v2/account", {})

    def get_all_orders(self, symbol: str, limit: int = 10) -> list:
        return self._get("/fapi/v1/allOrders", {"symbol": symbol, "limit": limit})