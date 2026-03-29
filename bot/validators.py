from bot.logging_config import get_logger

logger = get_logger("bot.validators")


class ValidationError(ValueError):
    pass


def validate_all(symbol, side, order_type, quantity, price, stop_price=None):
    # Symbol
    symbol = symbol.upper().strip()
    if not symbol.isalnum() or len(symbol) < 3:
        raise ValidationError(f"Invalid symbol '{symbol}'. Example: BTCUSDT")

    # Side
    side = side.upper().strip()
    if side not in ("BUY", "SELL"):
        raise ValidationError(f"Side must be BUY or SELL, got '{side}'")

    # Order type
    order_type = order_type.upper().strip()
    if order_type not in ("MARKET", "LIMIT", "STOP-LIMIT"):
        raise ValidationError(f"Order type must be MARKET, LIMIT, or STOP-LIMIT, got '{order_type}'")

    # Quantity
    if quantity <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {quantity}")

    # Price rules per type
    if order_type == "MARKET":
        if price is not None:
            logger.warning("Price is ignored for MARKET orders")
        price = None

    elif order_type == "LIMIT":
        if price is None or price <= 0:
            raise ValidationError("Price is required and must be > 0 for LIMIT orders")

    elif order_type == "STOP-LIMIT":
        if stop_price is None or stop_price <= 0:
            raise ValidationError("Stop price is required and must be > 0 for STOP-LIMIT orders")
        if price is None or price <= 0:
            raise ValidationError("Limit price is required and must be > 0 for STOP-LIMIT orders")

    logger.debug("Validation passed: symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
                 symbol, side, order_type, quantity, price, stop_price)

    return symbol, side, order_type, quantity, price, stop_price