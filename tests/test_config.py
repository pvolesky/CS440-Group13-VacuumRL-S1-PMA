"""Sanity checks for configs/default.toml (the single source of truth for values)."""
from __future__ import annotations

import sys

from _helpers import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))
from vacuum_rl.config import load_config  # noqa: E402


def test_default_config_loads_with_expected_sections():
    cfg = load_config()
    assert {"environment", "agent", "training"} <= set(cfg)


def test_layout_is_rectangular_with_one_start():
    layout = load_config()["environment"]["layout"]
    assert len({len(row) for row in layout}) == 1
    assert sum(cell == "start" for row in layout for cell in row) == 1


def test_layout_tokens_are_known():
    cfg = load_config()["environment"]
    for row in cfg["layout"]:
        for token in row:
            if token in {"start", "X"}:
                continue
            float(token)  # remaining tokens are numeric rewards


def test_terminal_and_obstacle_tokens_exist_in_layout():
    cfg = load_config()["environment"]
    tokens = {t for row in cfg["layout"] for t in row}
    assert set(cfg["terminal_tokens"]) <= tokens
    assert set(cfg["obstacle_tokens"]) <= tokens


def test_hyperparameters_are_in_valid_ranges():
    agent = load_config()["agent"]
    assert 0.0 < agent["alpha"] <= 1.0
    assert 0.0 <= agent["gamma"] <= 1.0
    assert 0.0 <= agent["epsilon_end"] <= agent["epsilon_start"] <= 1.0
