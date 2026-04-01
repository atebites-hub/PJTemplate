"""Application configuration loaded from TOML and secret files."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import ClassVar, cast, override

from pydantic import BaseModel, SecretStr, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)
from tomlkit import document, dumps, parse, table

# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------

# Assumes this file lives at: src/server/config/settings.py
REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "config"
APP_CONFIG_PATH = CONFIG_DIR / "defaults.toml"

# Dev-first, container-second. If both exist, the later one in the list wins.
LOCAL_SECRETS_DIR = CONFIG_DIR / "secrets"
RUNTIME_SECRETS_DIR = Path("/run/secrets")


# ------------------------------------------------------------------------------
# Nested config models
# ------------------------------------------------------------------------------


class AppConfig(BaseModel):
    """Identity and runtime mode for the application."""

    name: str = "yourapp"
    env: str = "development"
    debug: bool = False


class ServerConfig(BaseModel):
    """HTTP server bind address and port."""

    host: str = "127.0.0.1"
    port: int = 8080


class WorkersConfig(BaseModel):
    """Worker process pool limits and timeouts."""

    max_processes: int = 8
    spawn_mode: str = "subprocess"
    request_timeout_ms: int = 2_000


class LoggingConfig(BaseModel):
    """Log directory layout, level, and rotation policy."""

    root: str = "logs"
    current_dir: str = "logs/current"
    archive_dir: str = "logs/archive"
    level: str = "INFO"
    format: str = "jsonl"
    max_mb: int = 128
    backup_count: int = 50

    @field_validator("level")
    @classmethod
    def normalize_level(cls, value: str) -> str:
        """Return an upper-case level name from the allowed set."""
        value = value.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value not in allowed:
            raise ValueError(f"logging.level must be one of {sorted(allowed)}")
        return value

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        """Require JSONL log format."""
        value = value.lower()
        if value != "jsonl":
            raise ValueError("logging.format must be 'jsonl'")
        return value


class ObservabilityConfig(BaseModel):
    """Service naming, toggles, and OTLP endpoint for telemetry."""

    service_name: str = "yourapp"
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    log_correlation_enabled: bool = True
    otlp_endpoint: str = "http://localhost:4317"
    sample_ratio: float = 0.1

    @field_validator("sample_ratio")
    @classmethod
    def validate_sample_ratio(cls, value: float) -> float:
        """Validate that the trace sampling ratio is between 0.0 and 1.0."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("observability.sample_ratio must be between 0.0 and 1.0")
        return value


class FeaturesConfig(BaseModel):
    """Feature flags for optional product behavior."""

    web_ui_writes_config: bool = True


class MetricsConfig(BaseModel):
    """Prometheus metrics endpoint and metric naming."""

    path: str = "/metrics"
    namespace: str = "yourapp"
    subsystem: str = "api"
    process_metrics_enabled: bool = True


class TracingConfig(BaseModel):
    """OpenTelemetry OTLP exporter options."""

    exporter: str = "otlp"
    protocol: str = "grpc"
    insecure: bool = True
    timeout_ms: int = 5000


# ------------------------------------------------------------------------------
# Main settings model
# ------------------------------------------------------------------------------


class Settings(BaseSettings):
    """Application settings.

    Non-secret values come from ``config/defaults.toml``.
    Secret values come from mounted secret files.
    Init kwargs are allowed so tests can override settings cleanly.
    """

    # Pyright's pydantic-settings stubs do not match runtime kwargs; values are valid at runtime.
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(  # pyright: ignore[reportCallIssue]
        extra="ignore",
        validate_default=True,
        toml_file=str(APP_CONFIG_PATH),
        secrets_dir=[str(LOCAL_SECRETS_DIR), str(RUNTIME_SECRETS_DIR)],
        secrets_dir_missing="ok",
    )

    # Structured non-secret config
    app: AppConfig = AppConfig()
    server: ServerConfig = ServerConfig()
    workers: WorkersConfig = WorkersConfig()
    logging: LoggingConfig = LoggingConfig()
    observability: ObservabilityConfig = ObservabilityConfig()
    features: FeaturesConfig = FeaturesConfig()
    metrics: MetricsConfig = MetricsConfig()
    tracing: TracingConfig = TracingConfig()

    # Top-level secrets: each field maps to one file in the secrets dir
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    jwt_signing_key: SecretStr | None = None
    postgres_password: SecretStr | None = None
    redis_password: SecretStr | None = None

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Order settings sources: init kwargs, TOML, then secret files (no env)."""
        # Your chosen standard:
        # 1. explicit init overrides (great for tests)
        # 2. config/app.toml
        # 3. mounted secret files
        #
        # Deliberately excludes env vars and .env files.
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    def non_secret_dump(self) -> dict[str, dict[str, object]]:
        """Return only the writable, non-secret config sections."""
        return cast(
            dict[str, dict[str, object]],
            self.model_dump(
                mode="python",
                exclude={
                    "openai_api_key",
                    "anthropic_api_key",
                    "jwt_signing_key",
                    "postgres_password",
                    "redis_password",
                },
            ),
        )

    @property
    def log_root_path(self) -> Path:
        """Absolute path to the log tree root under the repo."""
        return (REPO_ROOT / self.logging.root).resolve()

    @property
    def log_current_path(self) -> Path:
        """Absolute path to the active (hot) JSONL log directory."""
        return (REPO_ROOT / self.logging.current_dir).resolve()

    @property
    def log_archive_path(self) -> Path:
        """Absolute path to rotated log archives."""
        return (REPO_ROOT / self.logging.archive_dir).resolve()


# ------------------------------------------------------------------------------
# Singleton access for FastAPI
# ------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached ``Settings`` instance."""
    return Settings()


def reload_settings() -> Settings:
    """Clear the settings cache and load a fresh ``Settings`` instance."""
    get_settings.cache_clear()
    return get_settings()


# ------------------------------------------------------------------------------
# Filesystem helpers
# ------------------------------------------------------------------------------


def ensure_runtime_dirs(settings: Settings | None = None) -> None:
    """Create log current and archive directories if they are missing."""
    resolved: Settings = settings if settings is not None else get_settings()
    resolved.log_current_path.mkdir(parents=True, exist_ok=True)
    resolved.log_archive_path.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------------------
# TOML write-back helpers
# ------------------------------------------------------------------------------


def save_settings(
    settings: Settings,
    path: Path = APP_CONFIG_PATH,
) -> None:
    """Write non-secret settings back to the TOML config file.

    Uses TOML Kit so formatting and comments are preserved when possible.
    Secrets are never written to this file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        doc = parse(path.read_text(encoding="utf-8"))
    else:
        doc = document()

    payload = settings.non_secret_dump()

    # Replace each top-level section with the current validated values.
    for section_name, section_values in payload.items():
        section_table = table()
        for key, value in section_values.items():
            section_table[key] = value
        doc[section_name] = section_table

    toml_out = dumps(doc)
    _ = path.write_text(toml_out, encoding="utf-8")
