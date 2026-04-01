# src/yourapp/core/telemetry.py

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

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
    """
    Initialize telemetry for the current process.

    FastAPI process:
        setup_telemetry(app)

    Worker / subprocess:
        setup_telemetry()
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
    """
    Clean shutdown for process-local telemetry.
    """
    global _TELEMETRY_CONFIGURED

    shutdown_tracing()
    shutdown_logging()

    _TELEMETRY_CONFIGURED = False


@asynccontextmanager
async def telemetry_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan helper.

    Usage:
        app = FastAPI(lifespan=telemetry_lifespan)
    """
    setup_telemetry(app=app)
    try:
        yield
    finally:
        shutdown_telemetry()