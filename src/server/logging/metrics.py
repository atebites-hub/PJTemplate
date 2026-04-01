"""Prometheus metrics, HTTP middleware, and pipeline instrumentation helpers."""

from __future__ import annotations

import os
import time
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from dataclasses import dataclass

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    make_asgi_app,
    multiprocess,
)

from server.config import Settings, get_settings

# ------------------------------------------------------------------------------
# Small config note:
#
# This file assumes your Settings model has:
#
# class MetricsConfig(BaseModel):
#     path: str = "/metrics"
#     namespace: str = "yourapp"
#     subsystem: str = "api"
#     process_metrics_enabled: bool = True
#
# and:
#     metrics: MetricsConfig = MetricsConfig()
# ------------------------------------------------------------------------------


def _is_multiprocess_enabled() -> bool:
    """Return True when Prometheus multiprocess mode is enabled via env."""
    value = os.getenv("PROMETHEUS_MULTIPROC_DIR", "").strip()
    return bool(value)


def _route_template(request: Request) -> str:
    """Prefer the FastAPI route template path for metric labels; else raw path."""
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return request.url.path


def _make_metrics_asgi_app():
    """Build the ASGI application that exposes Prometheus metrics.

    Uses the default registry unless ``PROMETHEUS_MULTIPROC_DIR`` is set; then
    attaches ``MultiProcessCollector`` to a fresh ``CollectorRegistry``.
    """
    if _is_multiprocess_enabled():
        registry = CollectorRegistry()
        _ = multiprocess.MultiProcessCollector(registry)
        return make_asgi_app(registry=registry)

    return make_asgi_app()


@dataclass(slots=True)
class Metrics:
    """Prometheus counters, histograms, and gauges used by the API and workers."""

    # HTTP / API metrics
    http_requests_total: Counter
    http_request_duration_seconds: Histogram
    http_requests_in_progress: Gauge

    # Worker / pipeline metrics
    worker_processes_active: Gauge
    pipeline_stage_total: Counter
    pipeline_stage_duration_seconds: Histogram
    pipeline_stage_failures_total: Counter
    pipeline_queue_depth: Gauge

    # App / lifecycle metrics
    config_write_total: Counter

    @classmethod
    def create(cls, settings: Settings) -> Metrics:
        """Construct metric instruments using namespace and subsystem from settings."""
        namespace = settings.metrics.namespace
        subsystem = settings.metrics.subsystem

        return cls(
            http_requests_total=Counter(
                name="http_requests_total",
                documentation="Total HTTP requests handled by the API.",
                labelnames=("method", "path", "status"),
                namespace=namespace,
                subsystem=subsystem,
            ),
            http_request_duration_seconds=Histogram(
                name="http_request_duration_seconds",
                documentation="HTTP request latency in seconds.",
                labelnames=("method", "path", "status"),
                namespace=namespace,
                subsystem=subsystem,
                buckets=(
                    0.001,
                    0.0025,
                    0.005,
                    0.0075,
                    0.01,
                    0.015,
                    0.02,
                    0.03,
                    0.05,
                    0.075,
                    0.1,
                    0.25,
                    0.5,
                    1.0,
                    2.5,
                    5.0,
                ),
            ),
            http_requests_in_progress=Gauge(
                name="http_requests_in_progress",
                documentation="In-flight HTTP requests.",
                labelnames=(),
                namespace=namespace,
                subsystem=subsystem,
                multiprocess_mode="livesum",
            ),
            worker_processes_active=Gauge(
                name="workers_active",
                documentation="Worker processes currently active.",
                labelnames=("worker_type",),
                namespace=namespace,
                subsystem=subsystem,
                multiprocess_mode="livesum",
            ),
            pipeline_stage_total=Counter(
                name="pipeline_stage_total",
                documentation="Total pipeline stage executions.",
                labelnames=("stage", "status"),
                namespace=namespace,
                subsystem=subsystem,
            ),
            pipeline_stage_duration_seconds=Histogram(
                name="pipeline_stage_duration_seconds",
                documentation="Duration of pipeline stages in seconds.",
                labelnames=("stage", "status"),
                namespace=namespace,
                subsystem=subsystem,
                buckets=(
                    0.0005,
                    0.001,
                    0.0025,
                    0.005,
                    0.0075,
                    0.01,
                    0.015,
                    0.02,
                    0.03,
                    0.05,
                    0.075,
                    0.1,
                    0.25,
                    0.5,
                    1.0,
                    2.5,
                ),
            ),
            pipeline_stage_failures_total=Counter(
                name="pipeline_stage_failures_total",
                documentation="Total failed pipeline stage executions.",
                labelnames=("stage", "error_type"),
                namespace=namespace,
                subsystem=subsystem,
            ),
            pipeline_queue_depth=Gauge(
                name="pipeline_queue_depth",
                documentation="Current pipeline queue depth.",
                labelnames=("queue_name",),
                namespace=namespace,
                subsystem=subsystem,
                multiprocess_mode="livemostrecent",
            ),
            config_write_total=Counter(
                name="config_write_total",
                documentation="Total writes to persisted config.",
                labelnames=("result",),
                namespace=namespace,
                subsystem=subsystem,
            ),
        )


_metrics_singleton: Metrics | None = None


def get_metrics(settings: Settings | None = None) -> Metrics:
    """Return the lazily created process-wide ``Metrics`` bundle."""
    global _metrics_singleton
    if _metrics_singleton is None:
        resolved: Settings = settings if settings is not None else get_settings()
        _metrics_singleton = Metrics.create(resolved)
    return _metrics_singleton


def reset_metrics_for_tests() -> None:
    """Clear the metrics singleton (for tests in a fresh interpreter)."""
    global _metrics_singleton
    _metrics_singleton = None


def mount_metrics_endpoint(app: FastAPI, settings: Settings | None = None) -> None:
    """Mount the Prometheus scrape endpoint on the FastAPI app."""
    resolved: Settings = settings if settings is not None else get_settings()
    app.mount(resolved.metrics.path, _make_metrics_asgi_app())


def install_http_metrics_middleware(app: FastAPI, settings: Settings | None = None) -> None:
    """Register middleware that records request counts, latency, and in-flight gauge."""
    resolved: Settings = settings if settings is not None else get_settings()
    metrics = get_metrics(resolved)

    # Avoid double-install if called twice.
    if getattr(app.state, "_http_metrics_installed", False):
        return

    @app.middleware("http")
    async def prometheus_http_metrics(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Record HTTP metrics for each request (count, duration, in-flight)."""
        method = request.method
        path = _route_template(request)

        metrics.http_requests_in_progress.inc()
        start = time.perf_counter()

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start
            status = str(status_code)

            metrics.http_requests_total.labels(
                method=method,
                path=path,
                status=status,
            ).inc()

            metrics.http_request_duration_seconds.labels(
                method=method,
                path=path,
                status=status,
            ).observe(duration)

            metrics.http_requests_in_progress.dec()

    app.state._http_metrics_installed = True


def setup_metrics(app: FastAPI, settings: Settings | None = None) -> None:
    """Mount ``/metrics`` and install HTTP request metrics middleware."""
    resolved: Settings = settings if settings is not None else get_settings()
    mount_metrics_endpoint(app, resolved)
    install_http_metrics_middleware(app, resolved)


@contextmanager
def worker_active(worker_type: str = "pipeline"):
    """Increment active worker gauge for the block duration.

    Example:
        with worker_active("bot"):
            run_worker()

    """
    metrics = get_metrics()
    gauge = metrics.worker_processes_active.labels(worker_type=worker_type)
    gauge.inc()
    try:
        yield
    finally:
        gauge.dec()


@contextmanager
def pipeline_stage(stage: str):
    """Time a pipeline stage and record success, duration, or failure counts.

    Example:
        with pipeline_stage("embed"):
            run_embedding_step()

    """
    metrics = get_metrics()
    start = time.perf_counter()
    status = "ok"

    try:
        yield
    except Exception as exc:
        status = "error"
        metrics.pipeline_stage_failures_total.labels(
            stage=stage,
            error_type=type(exc).__name__,
        ).inc()
        raise
    finally:
        duration = time.perf_counter() - start
        metrics.pipeline_stage_total.labels(stage=stage, status=status).inc()
        metrics.pipeline_stage_duration_seconds.labels(
            stage=stage,
            status=status,
        ).observe(duration)


def observe_pipeline_stage(stage: str, duration_seconds: float, status: str = "ok") -> None:
    """Record pipeline stage totals and duration when timing is done manually."""
    metrics = get_metrics()
    metrics.pipeline_stage_total.labels(stage=stage, status=status).inc()
    metrics.pipeline_stage_duration_seconds.labels(
        stage=stage,
        status=status,
    ).observe(duration_seconds)


def record_pipeline_failure(stage: str, error_type: str) -> None:
    """Increment the failure counter for a pipeline stage and error type."""
    metrics = get_metrics()
    metrics.pipeline_stage_failures_total.labels(
        stage=stage,
        error_type=error_type,
    ).inc()


def set_queue_depth(queue_name: str, depth: int) -> None:
    """Set the labeled queue depth gauge for pipeline backpressure."""
    metrics = get_metrics()
    metrics.pipeline_queue_depth.labels(queue_name=queue_name).set(depth)


def record_config_write(success: bool) -> None:
    """Count persisted configuration writes by success or error result."""
    metrics = get_metrics()
    metrics.config_write_total.labels(result="ok" if success else "error").inc()
