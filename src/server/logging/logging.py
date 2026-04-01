"""JSONL logging, rotation, and OpenTelemetry trace correlation filters."""

from __future__ import annotations

import atexit
import json
import logging
import os
import queue
from datetime import UTC, datetime
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from typing import Any

from .config import Settings, ensure_runtime_dirs, get_settings

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

_LOGGING_CONFIGURED = False
_LOG_QUEUE: queue.SimpleQueue[logging.LogRecord] | None = None
_QUEUE_LISTENER: QueueListener | None = None
_FILE_HANDLER: logging.Handler | None = None

_RESERVED_RECORD_KEYS = set(
    logging.LogRecord(
        name="template",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="template",
        args=(),
        exc_info=None,
    ).__dict__.keys()
) | {"message", "asctime"}


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    return repr(value)


def _coerce_level(level_name: str) -> int:
    level = getattr(logging, level_name.upper(), None)
    if not isinstance(level, int):
        raise ValueError(f"Invalid logging level: {level_name}")
    return level


def _current_file_path(settings: Settings) -> Path:
    service = settings.observability.service_name
    pid = os.getpid()
    return settings.log_current_path / f"{service}-{pid}.jsonl"


# ------------------------------------------------------------------------------
# Trace correlation
# ------------------------------------------------------------------------------


class TraceContextFilter(logging.Filter):
    """Enrich log records with service metadata and trace identifiers.

    Injects common app and process fields plus trace and span IDs when
    OpenTelemetry context is available. Keeps the JSONL schema stable even if
    OTel logging auto-instrumentation is not enabled.
    """

    def __init__(self, settings: Settings) -> None:
        """Capture service name and environment from settings."""
        super().__init__()
        self._service = settings.observability.service_name
        self._environment = settings.app.env

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach correlation fields to ``record``; always return True."""
        record.service = self._service
        record.environment = self._environment
        record.pid = os.getpid()
        record.process_name = getattr(record, "processName", None)

        trace_id = None
        span_id = None

        try:
            from opentelemetry import trace  # optional runtime dependency

            span = trace.get_current_span()
            span_context = span.get_span_context() if span else None
            if span_context and getattr(span_context, "is_valid", False):
                trace_id = format(span_context.trace_id, "032x")
                span_id = format(span_context.span_id, "016x")
        except Exception:
            # Logging must never fail because telemetry is unavailable.
            trace_id = None
            span_id = None

        record.trace_id = trace_id
        record.span_id = span_id
        return True


# ------------------------------------------------------------------------------
# JSONL formatter
# ------------------------------------------------------------------------------


class JsonLineFormatter(logging.Formatter):
    """Format each log record as one JSON object per line.

    Suitable for local ``jq``, Loki or Grafana Alloy tails, and trace fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Return a single JSON line for ``record``."""
        message = record.getMessage()

        payload: dict[str, Any] = {
            "ts": _utc_now_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "service": getattr(record, "service", None),
            "environment": getattr(record, "environment", None),
            "trace_id": getattr(record, "trace_id", None),
            "span_id": getattr(record, "span_id", None),
            "pid": getattr(record, "pid", None),
            "process_name": getattr(record, "process_name", None),
            "thread_name": record.threadName,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "pathname": record.pathname,
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        extra: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_KEYS:
                continue
            if key.startswith("_"):
                continue
            if key in payload:
                continue
            extra[key] = value

        if extra:
            payload["extra"] = extra

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=_json_default,
        )


# ------------------------------------------------------------------------------
# Rotating file handler that archives rotated files into logs/archive
# ------------------------------------------------------------------------------


class ArchivingRotatingFileHandler(RotatingFileHandler):
    """Rotate the hot JSONL file and move rolled files under the archive path.

    Example:
        hot: ``logs/current/yourapp-12345.jsonl``
        archive: ``logs/archive/20260401-153012.123456Z-yourapp-12345.jsonl``

    """

    def __init__(
        self,
        *,
        archive_dir: Path,
        service_name: str,
        **kwargs: Any,
    ) -> None:
        """Configure rotation with a dedicated archive directory."""
        self.archive_dir = archive_dir
        self.service_name = service_name
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(**kwargs)

    def _archive_path(self) -> Path:
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S.%fZ")
        pid = os.getpid()
        base = self.archive_dir / f"{ts}-{self.service_name}-{pid}.jsonl"

        if not base.exists():
            return base

        i = 1
        while True:
            candidate = self.archive_dir / f"{ts}-{self.service_name}-{pid}-{i}.jsonl"
            if not candidate.exists():
                return candidate
            i += 1

    def _prune_archives(self) -> None:
        if self.backupCount <= 0:
            return

        pid = os.getpid()
        pattern = f"*-{self.service_name}-{pid}*.jsonl"
        files = sorted(
            self.archive_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for old_file in files[self.backupCount :]:
            try:
                old_file.unlink()
            except FileNotFoundError:
                pass

    def doRollover(self) -> None:
        """Move the current file to the archive and continue logging."""
        if self.stream:
            self.stream.close()
            self.stream = None

        current_path = Path(self.baseFilename)
        if current_path.exists():
            archive_path = self._archive_path()
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(current_path, archive_path)

        if not self.delay:
            self.stream = self._open()

        self._prune_archives()


# ------------------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------------------


def configure_logging(settings: Settings | None = None) -> None:
    """Configure process-local logging once (FastAPI lifespan or worker entry)."""
    global _LOGGING_CONFIGURED, _LOG_QUEUE, _QUEUE_LISTENER, _FILE_HANDLER

    if _LOGGING_CONFIGURED:
        return

    settings = settings or get_settings()
    ensure_runtime_dirs(settings)

    level = _coerce_level(settings.logging.level)
    current_file = _current_file_path(settings)

    formatter = JsonLineFormatter()
    context_filter = TraceContextFilter(settings)

    file_handler = ArchivingRotatingFileHandler(
        filename=str(current_file),
        archive_dir=settings.log_archive_path,
        service_name=settings.observability.service_name,
        maxBytes=settings.logging.max_mb * 1024 * 1024,
        backupCount=settings.logging.backup_count,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    log_queue: queue.SimpleQueue[logging.LogRecord] = queue.SimpleQueue()
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(level)

    queue_listener = QueueListener(
        log_queue,
        file_handler,
        respect_handler_level=True,
    )
    queue_listener.start()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(queue_handler)

    # Let framework loggers flow into the root logger.
    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True

    logging.captureWarnings(True)

    _LOG_QUEUE = log_queue
    _QUEUE_LISTENER = queue_listener
    _FILE_HANDLER = file_handler
    _LOGGING_CONFIGURED = True


def shutdown_logging() -> None:
    """Stop the queue listener and close the file handler."""
    global _LOGGING_CONFIGURED, _LOG_QUEUE, _QUEUE_LISTENER, _FILE_HANDLER

    if _QUEUE_LISTENER is not None:
        _QUEUE_LISTENER.stop()
        _QUEUE_LISTENER = None

    if _FILE_HANDLER is not None:
        _FILE_HANDLER.close()
        _FILE_HANDLER = None

    _LOG_QUEUE = None
    _LOGGING_CONFIGURED = False


def reconfigure_logging(settings: Settings | None = None) -> None:
    """Tear down logging and rebuild handlers with optional new settings."""
    shutdown_logging()
    configure_logging(settings=settings)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return the application logger or a named child logger."""
    return logging.getLogger(name if name else "yourapp")


atexit.register(shutdown_logging)
