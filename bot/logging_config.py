import logging
import logging.handlers
import uuid
from contextvars import ContextVar
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "logs" / "bot.log"

# ── Request correlation ID ─────────────────────────────────────────────────────
# Set this at the start of any operation (CLI command, TUI action, web request)
# so every log line in that flow shares the same short ID.
#
# Usage:
#   from bot.logging_config import new_request_id
#   new_request_id()   # call once at the top of a command/handler
#
_request_id: ContextVar[str] = ContextVar("request_id", default="--------")

def new_request_id() -> str:
    rid = uuid.uuid4().hex[:8]
    _request_id.set(rid)
    return rid

def get_request_id() -> str:
    return _request_id.get()


# ── Correlation filter ─────────────────────────────────────────────────────────
class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.rid = _request_id.get()
        return True


# ── Formatters ─────────────────────────────────────────────────────────────────
_CONSOLE_FMT = logging.Formatter(
    "%(levelname)-8s %(asctime)s [%(rid)s] | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

_FILE_FMT = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | [%(rid)s] | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ── Public factory ─────────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    filt = _RequestIdFilter()

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(_CONSOLE_FMT)
    console.addFilter(filt)

    LOG_FILE.parent.mkdir(exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_FILE_FMT)
    file_handler.addFilter(filt)

    logger.addHandler(console)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger