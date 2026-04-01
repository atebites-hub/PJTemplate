"""Process-wide telemetry setup: logging, metrics, and distributed tracing."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.config import Settings, ensure_runtime_dirs, get_settings

from .logging import configure_logging, shutdown_logging
from .metrics import setup_metrics
from .tracing import configure_tracing, shutdown_tracing

_telemetry_configured = False


def setup_telemetry(
    app: FastAPI | None = None,
    settings: Settings | None = None,
) -> None:
    """Initialize logging, tracing, and metrics for this process.

    Pass ``app`` in the API process to enable FastAPI metrics; omit it in
    workers that only need logging and tracing.
    """
    global _telemetry_configured

    if _telemetry_configured:
        return

    resolved: Settings = settings if settings is not None else get_settings()

    ensure_runtime_dirs(resolved)
    configure_logging(resolved)

    if resolved.observability.tracing_enabled:
        configure_tracing(app=app, settings=resolved)

    if app is not None and resolved.observability.metrics_enabled:
        setup_metrics(app, resolved)

    _telemetry_configured = True


def shutdown_telemetry() -> None:
    """Shut down tracing and logging for this process."""
    global _telemetry_configured

    shutdown_tracing()
    shutdown_logging()

    _telemetry_configured = False


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
