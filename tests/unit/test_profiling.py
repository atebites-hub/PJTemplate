"""Unit tests for continuous profiling wiring (Pyroscope + OTel span bridge)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pyroscope.otel as pyroscope_otel
import pytest
from opentelemetry.sdk.trace import TracerProvider
from pydantic import ValidationError

from server.config.settings import (
    AppConfig,
    ObservabilityConfig,
    ProfilingConfig,
    Settings,
)
from server.logging import profiling as profiling_mod
from server.logging import telemetry as telemetry_mod


def _settings(
    *,
    profiling_enabled: bool = True,
    tracing_enabled: bool = True,
    span_profiles: bool = True,
    metrics_enabled: bool = False,
) -> Settings:
    return Settings(
        app=AppConfig(name="yourapp", env="test"),
        observability=ObservabilityConfig(
            service_name="yourapp",
            metrics_enabled=metrics_enabled,
            tracing_enabled=tracing_enabled,
            profiling_enabled=profiling_enabled,
            sample_ratio=1.0,
        ),
        profiling=ProfilingConfig(
            server_address="http://pyroscope:4040",
            sample_rate=50,
            span_profiles_enabled=span_profiles,
            oncpu=True,
            gil_only=True,
            enable_logging=False,
        ),
    )


@pytest.fixture(autouse=True)
def _reset_profiling_state(monkeypatch: pytest.MonkeyPatch):
    """Keep module flags and SDK side effects isolated per test."""
    profiling_mod.reset_profiling_for_tests()
    telemetry_mod.reset_telemetry_for_tests()

    mock_pyroscope = MagicMock()
    monkeypatch.setattr(profiling_mod, "pyroscope", mock_pyroscope)

    yield mock_pyroscope

    profiling_mod.reset_profiling_for_tests()
    telemetry_mod.reset_telemetry_for_tests()


def test_configure_profiling_calls_sdk_with_aligned_tags(
    _reset_profiling_state: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_pyroscope = _reset_profiling_state
    settings = _settings()

    # No real TracerProvider → span bridge is a no-op (still configures agent).
    monkeypatch.setattr(
        "opentelemetry.trace.get_tracer_provider",
        lambda: object(),
    )

    profiling_mod.configure_profiling(settings, process_role="api")

    mock_pyroscope.configure.assert_called_once()
    kwargs = mock_pyroscope.configure.call_args.kwargs
    assert kwargs["application_name"] == "yourapp"
    assert kwargs["server_address"] == "http://pyroscope:4040"
    assert kwargs["sample_rate"] == 50
    assert kwargs["tags"]["service_name"] == "yourapp"
    assert kwargs["tags"]["environment"] == "test"
    assert kwargs["tags"]["process_role"] == "api"
    assert profiling_mod.is_profiling_configured() is True


def test_configure_profiling_idempotent(_reset_profiling_state: MagicMock) -> None:
    mock_pyroscope = _reset_profiling_state
    settings = _settings()

    profiling_mod.configure_profiling(settings)
    profiling_mod.configure_profiling(settings)

    assert mock_pyroscope.configure.call_count == 1


def test_configure_profiling_registers_span_processor(
    _reset_profiling_state: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(span_profiles=True)
    provider = TracerProvider()
    add_mock = MagicMock()
    monkeypatch.setattr(provider, "add_span_processor", add_mock)
    monkeypatch.setattr(
        "opentelemetry.trace.get_tracer_provider",
        lambda: provider,
    )

    fake_processor = object()
    fake_cls = MagicMock(return_value=fake_processor)
    monkeypatch.setattr(pyroscope_otel, "PyroscopeSpanProcessor", fake_cls)

    try:
        profiling_mod.configure_profiling(settings, process_role="worker")
    finally:
        provider.shutdown()

    fake_cls.assert_called_once_with()
    add_mock.assert_called_once_with(fake_processor)


def test_configure_profiling_skips_span_bridge_when_disabled(
    _reset_profiling_state: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(span_profiles=False)
    provider = TracerProvider()
    add_mock = MagicMock()
    monkeypatch.setattr(provider, "add_span_processor", add_mock)
    monkeypatch.setattr(
        "opentelemetry.trace.get_tracer_provider",
        lambda: provider,
    )

    try:
        profiling_mod.configure_profiling(settings)
    finally:
        provider.shutdown()

    add_mock.assert_not_called()


def test_shutdown_profiling_calls_sdk(
    _reset_profiling_state: MagicMock,
) -> None:
    mock_pyroscope = _reset_profiling_state
    settings = _settings()
    profiling_mod.configure_profiling(settings)
    profiling_mod.shutdown_profiling()

    mock_pyroscope.shutdown.assert_called_once()
    assert profiling_mod.is_profiling_configured() is False


def test_shutdown_profiling_noop_when_not_configured(
    _reset_profiling_state: MagicMock,
) -> None:
    mock_pyroscope = _reset_profiling_state
    profiling_mod.shutdown_profiling()
    mock_pyroscope.shutdown.assert_not_called()


def test_profile_tags_uses_tag_wrapper(
    _reset_profiling_state: MagicMock,
) -> None:
    mock_pyroscope = _reset_profiling_state
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    mock_pyroscope.tag_wrapper.return_value = cm

    with profiling_mod.profile_tags({"pipeline.stage": "embed"}):
        pass

    mock_pyroscope.tag_wrapper.assert_called_once_with({"pipeline.stage": "embed"})


def test_setup_telemetry_skips_profiling_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
    _reset_profiling_state: MagicMock,
) -> None:
    settings = _settings(profiling_enabled=False)
    calls: list[str] = []

    def _dirs(_s: Settings) -> None:
        calls.append("dirs")

    def _log(_s: Settings) -> None:
        calls.append("log")

    def _trace(**_kwargs: Any) -> None:
        calls.append("trace")

    def _profile(*_a: Any, **_k: Any) -> None:
        calls.append("profile")

    def _metrics(*_a: Any, **_k: Any) -> None:
        calls.append("metrics")

    monkeypatch.setattr(telemetry_mod, "ensure_runtime_dirs", _dirs)
    monkeypatch.setattr(telemetry_mod, "configure_logging", _log)
    monkeypatch.setattr(telemetry_mod, "configure_tracing", _trace)
    monkeypatch.setattr(telemetry_mod, "configure_profiling", _profile)
    monkeypatch.setattr(telemetry_mod, "setup_metrics", _metrics)

    telemetry_mod.setup_telemetry(app=None, settings=settings)

    assert calls == ["dirs", "log", "trace"]
    assert "profile" not in calls


def test_setup_telemetry_enables_profiling_after_tracing(
    monkeypatch: pytest.MonkeyPatch,
    _reset_profiling_state: MagicMock,
) -> None:
    settings = _settings(profiling_enabled=True, tracing_enabled=True)
    order: list[str] = []

    def _dirs(_s: Settings) -> None:
        order.append("dirs")

    def _log(_s: Settings) -> None:
        order.append("log")

    def _trace(**_kwargs: Any) -> None:
        order.append("trace")

    def _profile(_settings_arg: Settings, process_role: str = "api") -> None:
        order.append(f"profile:{process_role}")

    def _metrics(*_a: Any, **_k: Any) -> None:
        order.append("metrics")

    monkeypatch.setattr(telemetry_mod, "ensure_runtime_dirs", _dirs)
    monkeypatch.setattr(telemetry_mod, "configure_logging", _log)
    monkeypatch.setattr(telemetry_mod, "configure_tracing", _trace)
    monkeypatch.setattr(telemetry_mod, "configure_profiling", _profile)
    monkeypatch.setattr(telemetry_mod, "setup_metrics", _metrics)

    telemetry_mod.setup_telemetry(app=None, settings=settings)

    assert order == ["dirs", "log", "trace", "profile:worker"]


def test_setup_telemetry_api_process_role(
    monkeypatch: pytest.MonkeyPatch,
    _reset_profiling_state: MagicMock,
) -> None:
    settings = _settings(profiling_enabled=True, tracing_enabled=False, metrics_enabled=False)
    roles: list[str] = []

    def _noop_settings(_s: Settings) -> None:
        return None

    def _profile(
        _settings_arg: Settings,
        process_role: str = "api",
        **_kwargs: Any,
    ) -> None:
        roles.append(process_role)

    monkeypatch.setattr(telemetry_mod, "ensure_runtime_dirs", _noop_settings)
    monkeypatch.setattr(telemetry_mod, "configure_logging", _noop_settings)
    monkeypatch.setattr(telemetry_mod, "configure_profiling", _profile)

    app = MagicMock()
    telemetry_mod.setup_telemetry(app=app, settings=settings)

    assert roles == ["api"]


def test_profiling_config_rejects_bad_sample_rate() -> None:
    with pytest.raises(ValidationError):
        ProfilingConfig(sample_rate=0)


def test_profiling_config_rejects_empty_server_address() -> None:
    with pytest.raises(ValidationError):
        ProfilingConfig(server_address="   ")
