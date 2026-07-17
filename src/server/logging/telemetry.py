"""Process-wide telemetry setup: logging, metrics, tracing, and profiling."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.config import Settings, ensure_runtime_dirs, get_settings

from .logging import configure_logging, shutdown_logging
from .metrics import setup_metrics
from .profiling import configure_profiling, shutdown_profiling
from .tracing import configure_tracing, shutdown_tracing

_telemetry_configured = False


def reset_telemetry_for_tests() -> None:
    """Clear the telemetry configured flag (for tests only)."""
    global _telemetry_configured
    _telemetry_configured = False


def setup_telemetry(
    app: FastAPI | None = None,
    settings: Settings | None = None,
) -> None:
    """Initialize logging, tracing, profiling, and metrics for this process.

    Pass ``app`` in the API process to enable FastAPI metrics; omit it in
    workers that only need logging, tracing, and (optionally) profiling.

    Order matters: tracing must run before profiling so the OpenTelemetry
    ``TracerProvider`` exists when span-profile bridging is enabled.
    """
    global _telemetry_configured

    if _telemetry_configured:
        return

    resolved: Settings = settings if settings is not None else get_settings()

    ensure_runtime_dirs(resolved)
    configure_logging(resolved)

    if resolved.observability.tracing_enabled:
        configure_tracing(app=app, settings=resolved)

    if resolved.observability.profiling_enabled:
        process_role = "api" if app is not None else "worker"
        configure_profiling(resolved, process_role=process_role)

    if app is not None and resolved.observability.metrics_enabled:
        setup_metrics(app, resolved)

    _telemetry_configured = True


def shutdown_telemetry() -> None:
    """Shut down profiling, tracing, and logging for this process."""
    global _telemetry_configured

    shutdown_profiling()
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
