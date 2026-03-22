import json
import logging
import time
from contextlib import contextmanager
from typing import Any


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields added via `extra=` kwarg
        for key in ("stage", "latency_ms", "query_id", "doc_id", "provider",
                     "model", "num_chunks", "score", "error_type"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = str(record.exc_info[1])

        return json.dumps(log_data, default=str)


def setup_logging(json_format: bool = True, level: int = logging.INFO) -> None:
    """Configure root logger with optional JSON formatting."""
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
    root.addHandler(handler)


@contextmanager
def log_latency(logger: logging.Logger, stage: str, **extra: Any):
    """Context manager that logs the latency of a pipeline stage."""
    start = time.time()
    extra_fields = {"stage": stage, **extra}
    logger.info(f"{stage} started", extra=extra_fields)
    try:
        yield
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        logger.error(
            f"{stage} failed after {elapsed:.1f}ms: {e}",
            extra={**extra_fields, "latency_ms": round(elapsed, 1), "error_type": type(e).__name__},
        )
        raise
    else:
        elapsed = (time.time() - start) * 1000
        logger.info(
            f"{stage} completed in {elapsed:.1f}ms",
            extra={**extra_fields, "latency_ms": round(elapsed, 1)},
        )
