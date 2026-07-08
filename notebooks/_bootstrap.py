"""Shared notebook setup — import or ``%run`` this in the first cell."""

from __future__ import annotations

from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parent
DATA_DIR = NOTEBOOKS_DIR / "data"

for subdir in ("raw", "interim", "compiled"):
    (DATA_DIR / subdir).mkdir(parents=True, exist_ok=True)

from server.config.settings import REPO_ROOT, get_settings  # noqa: E402

settings = get_settings()

__all__ = ["DATA_DIR", "NOTEBOOKS_DIR", "REPO_ROOT", "get_settings", "settings"]
