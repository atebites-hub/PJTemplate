"""Process-wide telemetry setup: logging, metrics, and distributed tracing."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import Settings, ensure_runtime_dirs, get_settings
from .logging import configure_logging, shutdown_logging
from .metrics import setup_metrics
from .tracing import configure_tracing, shutdown_tracing

_TELEMETRY_CONFIGURED = False


def setup_telemetry(
    app: FastAPI | None = None,
    settings: Settings | None = None,
) -> None:
    """Initialize logging, tracing, and metrics for this process.

    Pass ``app`` in the API process to enable FastAPI metrics; omit it in
    workers that only need logging and tracing.
    """
    global _TELEMETRY_CONFIGURED

    if _TELEMETRY_CONFIGURED:
        return

    settings = settings or get_settings()

    ensure_runtime_dirs(settings)
    configure_logging(settings)

    if settings.observability.tracing_enabled:
        configure_tracing(app=app, settings=settings)

    if app is not None and settings.observability.metrics_enabled:
        setup_metrics(app, settings)

    _TELEMETRY_CONFIGURED = True


def shutdown_telemetry() -> None:
    """Shut down tracing and logging for this process."""
    global _TELEMETRY_CONFIGURED

    shutdown_tracing()
    shutdown_logging()

    _TELEMETRY_CONFIGURED = False


@asynccontextmanager
async def telemetry_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Yield after startup telemetry; shut down telemetry on app exit.

    Usage:

        app = FastAPI(lifespan=telemetry_lifespan)

    """
    setup_telemetry(app=app)
    try:
        yield
    finally:
        shutdown_telemetry()
