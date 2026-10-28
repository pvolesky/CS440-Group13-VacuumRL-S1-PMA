"""Config loading. configs/default.toml is the single source of truth for values."""
from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "default.toml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load a TOML config; defaults to configs/default.toml."""
    with open(path or DEFAULT_CONFIG_PATH, "rb") as handle:
        return tomllib.load(handle)
