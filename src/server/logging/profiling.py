"""Grafana Pyroscope continuous profiling setup and OpenTelemetry span bridge."""

from __future__ import annotations

import atexit
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

import pyroscope
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from server.config import Settings, get_settings

_profiling_configured = False
_span_processor_registered = False


def _build_tags(
    settings: Settings,
    *,
    process_role: str,
    extra_tags: Mapping[str, str] | None,
) -> dict[str, str]:
    """Build stable profile labels aligned with OTel resource attributes."""
    tags: dict[str, str] = {
        "service_name": settings.observability.service_name,
        "environment": settings.app.env,
        "process_role": process_role,
    }
    if extra_tags:
        for key, value in extra_tags.items():
            if key and value is not None:
                tags[str(key)] = str(value)
    return tags


def _register_span_profiles() -> None:
    """Attach ``PyroscopeSpanProcessor`` to the global SDK ``TracerProvider``."""
    global _span_processor_registered

    if _span_processor_registered:
        return

    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        # Tracing was not configured (or only a no-op proxy is registered).
        return

    from pyroscope.otel import PyroscopeSpanProcessor

    provider.add_span_processor(PyroscopeSpanProcessor())
    _span_processor_registered = True


def configure_profiling(
    settings: Settings | None = None,
    *,
    process_role: str = "api",
    extra_tags: Mapping[str, str] | None = None,
) -> None:
    """Start continuous profiling for this process (idempotent).

    When ``profiling.span_profiles_enabled`` is true and a real OpenTelemetry
    ``TracerProvider`` is already registered (i.e. tracing was configured
    first), also installs the Pyroscope span processor so Tempo can link
    spans to profiles.
    """
    global _profiling_configured

    if _profiling_configured:
        return

    resolved: Settings = settings if settings is not None else get_settings()
    cfg = resolved.profiling

    tags = _build_tags(resolved, process_role=process_role, extra_tags=extra_tags)

    configure_kwargs: dict[str, Any] = {
        "application_name": resolved.observability.service_name,
        "server_address": cfg.server_address,
        "sample_rate": cfg.sample_rate,
        "oncpu": cfg.oncpu,
        "gil_only": cfg.gil_only,
        "enable_logging": cfg.enable_logging,
        "report_pid": cfg.report_pid,
        "report_thread_id": cfg.report_thread_id,
        "report_thread_name": cfg.report_thread_name,
        "tags": tags,
    }

    if cfg.basic_auth_username:
        configure_kwargs["basic_auth_username"] = cfg.basic_auth_username
    if cfg.basic_auth_password:
        configure_kwargs["basic_auth_password"] = cfg.basic_auth_password
    if cfg.tenant_id:
        configure_kwargs["tenant_id"] = cfg.tenant_id

    pyroscope.configure(**configure_kwargs)
    _profiling_configured = True

    if cfg.span_profiles_enabled:
        _register_span_profiles()


def shutdown_profiling() -> None:
    """Stop the Pyroscope agent for this process if it was started."""
    global _profiling_configured, _span_processor_registered

    if not _profiling_configured:
        _span_processor_registered = False
        return

    pyroscope.shutdown()
    _profiling_configured = False
    # Span processors cannot be removed from TracerProvider; flag only tracks
    # whether we already added one in this process (avoids double-add on restart).
    _span_processor_registered = False


def is_profiling_configured() -> bool:
    """Return True when ``configure_profiling`` has successfully run."""
    return _profiling_configured


def reset_profiling_for_tests() -> None:
    """Clear profiling module flags (for tests; does not call the native agent)."""
    global _profiling_configured, _span_processor_registered
    _profiling_configured = False
    _span_processor_registered = False


@contextmanager
def profile_tags(tags: Mapping[str, str]) -> Iterator[None]:
    """Apply temporary profile labels for the duration of a code block.

    Example::

        with profile_tags({"pipeline.stage": "embed"}):
            run_embed()
    """
    with pyroscope.tag_wrapper(dict(tags)):
        yield


_ = atexit.register(shutdown_profiling)
