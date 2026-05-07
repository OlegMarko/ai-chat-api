import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.context import current_request_id


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rid = current_request_id()
        payload: dict[str, Any] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        extras = getattr(record, "extras", None)
        if isinstance(extras, dict):
            payload.update(extras)
        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    root = logging.getLogger()
    root.handlers.clear()

    if json_logs:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            ),
        )

    root.addHandler(handler)
    root.setLevel(level)


class LogExtras(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        merged = dict(self.extra or {})
        if isinstance(extra, dict):
            merged.update(extra)
        kwargs["extra"] = {"extras": merged}
        return msg, kwargs


def bind_logger(logger: logging.Logger, **extras: Any) -> logging.LoggerAdapter:
    return LogExtras(logger, extras)
