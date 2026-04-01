"""Smoke tests so CI collects at least one passing test."""

import pytest

from server.config import get_settings


@pytest.mark.e2e
def test_settings_loads() -> None:
    """Application settings load from the template defaults TOML."""
    settings = get_settings()
    assert settings.app.name
    assert settings.server.port > 0
