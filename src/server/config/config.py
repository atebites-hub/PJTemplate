from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)
from tomlkit import document, dumps, parse, table
from pydantic import BaseModel

# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------

# Assumes this file lives at: src/yourapp/core/config.py
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
    name: str = "yourapp"
    env: str = "development"
    debug: bool = False


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080


class WorkersConfig(BaseModel):
    max_processes: int = 8
    spawn_mode: str = "subprocess"
    request_timeout_ms: int = 2_000


class LoggingConfig(BaseModel):
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
        value = value.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value not in allowed:
            raise ValueError(f"logging.level must be one of {sorted(allowed)}")
        return value

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        value = value.lower()
        if value != "jsonl":
            raise ValueError("logging.format must be 'jsonl'")
        return value


class ObservabilityConfig(BaseModel):
    service_name: str = "yourapp"
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    log_correlation_enabled: bool = True
    otlp_endpoint: str = "http://localhost:4317"
    sample_ratio: float = 0.1

    @field_validator("sample_ratio")
    @classmethod
    def validate_sample_ratio(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("observability.sample_ratio must be between 0.0 and 1.0")
        return value


class FeaturesConfig(BaseModel):
    web_ui_writes_config: bool = True


# ------------------------------------------------------------------------------
# Main settings model
# ------------------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Application settings.

    Non-secret values come from config/app.toml.
    Secret values come from mounted secret files.
    Init kwargs are allowed so tests can override settings cleanly.
    """

    model_config = SettingsConfigDict(
        # Pydantic settings behavior
        extra="ignore",
        validate_default=True,

        # TOML source path
        toml_file=str(APP_CONFIG_PATH),

        # Mounted secrets
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

    # Top-level secrets: each field maps to one file in the secrets dir
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    jwt_signing_key: SecretStr | None = None
    postgres_password: SecretStr | None = None
    redis_password: SecretStr | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
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

    def non_secret_dump(self) -> dict[str, Any]:
        """Return only the writable, non-secret config sections."""
        return self.model_dump(
            mode="python",
            exclude={
                "openai_api_key",
                "anthropic_api_key",
                "jwt_signing_key",
                "postgres_password",
                "redis_password",
            },
        )

    @property
    def log_root_path(self) -> Path:
        return (REPO_ROOT / self.logging.root).resolve()

    @property
    def log_current_path(self) -> Path:
        return (REPO_ROOT / self.logging.current_dir).resolve()

    @property
    def log_archive_path(self) -> Path:
        return (REPO_ROOT / self.logging.archive_dir).resolve()


# ------------------------------------------------------------------------------
# Singleton access for FastAPI
# ------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


# ------------------------------------------------------------------------------
# Filesystem helpers
# ------------------------------------------------------------------------------

def ensure_runtime_dirs(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    settings.log_current_path.mkdir(parents=True, exist_ok=True)
    settings.log_archive_path.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------------------
# TOML write-back helpers
# ------------------------------------------------------------------------------

def save_settings(
    settings: Settings,
    path: Path = APP_CONFIG_PATH,
) -> None:
    """
    Write non-secret settings back to config/app.toml.

    Uses TOML Kit so formatting/comments are preserved as much as possible.
    Secrets are never written into app.toml.
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

    path.write_text(dumps(doc), encoding="utf-8")

# ------------------------------------------------------------------------------
# Prometheus Metrics
# ------------------------------------------------------------------------------

class MetricsConfig(BaseModel):
    path: str = "/metrics"
    namespace: str = "yourapp"
    subsystem: str = "api"
    process_metrics_enabled: bool = True

class TracingConfig(BaseModel):
    exporter: str = "otlp"
    protocol: str = "grpc"
    insecure: bool = True
    timeout_ms: int = 5000