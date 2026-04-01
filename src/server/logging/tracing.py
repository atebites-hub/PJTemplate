"""OpenTelemetry tracing setup, FastAPI instrumentation, and propagation helpers."""

from __future__ import annotations

import atexit
import os
import re
from collections.abc import Iterator, Mapping, MutableMapping
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.trace import Span, SpanKind, Tracer

from .config import Settings, get_settings

_TRACING_CONFIGURED = False
_FASTAPI_INSTRUMENTED = False
_TRACER_PROVIDER: TracerProvider | None = None

TRACEPARENT_ENV_KEY = "YOURAPP_TRACEPARENT"
BAGGAGE_ENV_KEY = "YOURAPP_BAGGAGE"


def _build_resource(settings: Settings) -> Resource:
    return Resource.create(
        {
            "service.name": settings.observability.service_name,
            "deployment.environment": settings.app.env,
        }
    )


def _build_sampler(settings: Settings):
    ratio = settings.observability.sample_ratio
    return ParentBased(TraceIdRatioBased(ratio))


def _excluded_urls(settings: Settings) -> str:
    paths: list[str] = []

    # Avoid noisy self-scrapes and docs endpoints by default.
    metrics_path = getattr(getattr(settings, "metrics", None), "path", None)
    if metrics_path:
        paths.append(metrics_path)

    fastapi_cfg = getattr(settings, "fastapi", None)
    if fastapi_cfg is not None:
        for attr in ("docs_url", "redoc_url", "openapi_url"):
            value = getattr(fastapi_cfg, attr, None)
            if value:
                paths.append(value)

    # FastAPIInstrumentor expects comma-delimited regexes.
    return ",".join(re.escape(path) for path in paths if path)


def configure_tracing(
    app: FastAPI | None = None,
    settings: Settings | None = None,
) -> None:
    """Configure OpenTelemetry tracing once per process (API or worker)."""
    global _TRACING_CONFIGURED, _TRACER_PROVIDER

    if _TRACING_CONFIGURED:
        if app is not None:
            instrument_fastapi(app, settings=settings)
        return

    settings = settings or get_settings()

    provider = TracerProvider(
        resource=_build_resource(settings),
        sampler=_build_sampler(settings),
    )

    exporter = OTLPSpanExporter(
        endpoint=settings.observability.otlp_endpoint,
        insecure=settings.tracing.insecure,
        timeout=settings.tracing.timeout_ms / 1000.0,
    )

    span_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(span_processor)

    trace.set_tracer_provider(provider)

    _TRACER_PROVIDER = provider
    _TRACING_CONFIGURED = True

    if app is not None:
        instrument_fastapi(app, settings=settings)


def instrument_fastapi(
    app: FastAPI,
    settings: Settings | None = None,
) -> None:
    """Instrument FastAPI routes; no-op if already instrumented."""
    global _FASTAPI_INSTRUMENTED

    if _FASTAPI_INSTRUMENTED:
        return

    settings = settings or get_settings()

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=_excluded_urls(settings),
    )

    _FASTAPI_INSTRUMENTED = True


def shutdown_tracing() -> None:
    """Flush and shut down the global tracer provider if configured."""
    global _TRACING_CONFIGURED, _TRACER_PROVIDER

    if _TRACER_PROVIDER is not None:
        _TRACER_PROVIDER.shutdown()
        _TRACER_PROVIDER = None

    _TRACING_CONFIGURED = False


def get_tracer(name: str | None = None) -> Tracer:
    """Return a named tracer, defaulting to the configured service name."""
    settings = get_settings()
    return trace.get_tracer(name or settings.observability.service_name)


@contextmanager
def start_span(
    name: str,
    *,
    tracer_name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Mapping[str, Any] | None = None,
    context: Any | None = None,
) -> Iterator[Span]:
    """Start a span and optionally set attributes on the current context.

    Example:
        with start_span("pipeline.embed", attributes={"job_id": job_id}) as span:
            ...

    """
    tracer = get_tracer(tracer_name)

    with tracer.start_as_current_span(name, context=context, kind=kind) as span:
        if attributes:
            set_span_attributes(span, attributes)
        yield span


def set_span_attributes(span: Span, attributes: Mapping[str, Any]) -> None:
    """Apply key-value attributes to an open span."""
    for key, value in attributes.items():
        span.set_attribute(key, value)


def add_span_event(
    name: str,
    *,
    attributes: Mapping[str, Any] | None = None,
) -> None:
    """Add a named event to the current span, if any."""
    span = trace.get_current_span()
    if span is not None:
        span.add_event(name, attributes=dict(attributes or {}))


def inject_trace_context(
    carrier: MutableMapping[str, str] | None = None,
) -> dict[str, str]:
    """Inject current trace context into a carrier dict.

    Typical output keys:
      - traceparent
      - baggage
    """
    carrier = carrier or {}
    ctx = trace.get_current_span().get_span_context()
    _ = ctx  # keeps intent obvious; injection uses current context

    from opentelemetry.trace.propagation.tracecontext import (
        TraceContextTextMapPropagator,
    )

    TraceContextTextMapPropagator().inject(carrier)
    W3CBaggagePropagator().inject(carrier)
    return dict(carrier)


def extract_trace_context(
    carrier: Mapping[str, str] | None,
) -> Any:
    """Extract an OpenTelemetry context from a W3C trace carrier mapping."""
    from opentelemetry.trace.propagation.tracecontext import (
        TraceContextTextMapPropagator,
    )

    carrier = dict(carrier or {})
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
    ctx = W3CBaggagePropagator().extract(carrier, context=ctx)
    return ctx


def make_subprocess_trace_env() -> dict[str, str]:
    """Serialize the current trace context into environment variables for a child.

    Parent:
        env = os.environ.copy()
        env.update(make_subprocess_trace_env())
        subprocess.Popen(..., env=env)

    Child:
        ctx = extract_trace_context_from_env()
        with start_span("worker.run", context=ctx):
            ...
    """
    carrier = inject_trace_context({})
    env: dict[str, str] = {}

    traceparent = carrier.get("traceparent")
    baggage = carrier.get("baggage")

    if traceparent:
        env[TRACEPARENT_ENV_KEY] = traceparent
    if baggage:
        env[BAGGAGE_ENV_KEY] = baggage

    return env


def extract_trace_context_from_env(
    env: Mapping[str, str] | None = None,
) -> Any | None:
    """Rebuild trace context from env vars produced by ``make_subprocess_trace_env``."""
    env = env or os.environ

    carrier: dict[str, str] = {}
    traceparent = env.get(TRACEPARENT_ENV_KEY)
    baggage = env.get(BAGGAGE_ENV_KEY)

    if traceparent:
        carrier["traceparent"] = traceparent
    if baggage:
        carrier["baggage"] = baggage

    if not carrier:
        return None

    return extract_trace_context(carrier)


@contextmanager
def pipeline_stage(
    stage: str,
    *,
    attributes: Mapping[str, Any] | None = None,
    context: Any | None = None,
) -> Iterator[Span]:
    """Open a span named ``pipeline.<stage>`` with standard pipeline attributes."""
    attrs = {"pipeline.stage": stage}
    if attributes:
        attrs.update(attributes)

    with start_span(
        f"pipeline.{stage}",
        attributes=attrs,
        context=context,
    ) as span:
        yield span


atexit.register(shutdown_tracing)
