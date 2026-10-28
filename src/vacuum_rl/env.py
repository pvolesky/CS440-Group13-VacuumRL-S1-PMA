"""Vacuum-robot grid world. STUB: implement in Phase 1.

Procedure and invariants: .claude/skills/environment-spec/SKILL.md
Semantics (provisional): docs/environment.md and configs/default.toml

This class OWNS the transition function T and reward function R. The agent never
sees them. The agent-facing surface is exactly:

    reset(seed=None) -> state
    step(action)     -> (next_state, reward, terminated, truncated, info)
    n_states, n_actions, encode_state(state) -> int

`terminated` = a terminal cell was reached. `truncated` = max_episode_steps hit.
"""
from __future__ import annotations

from enum import IntEnum
from typing import Any

State = tuple[int, int]  # (row, col), row 0 at the top. Provisional: see Q-003.


class Action(IntEnum):
    """Order matches `actions` in configs/default.toml."""

    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


class VacuumGridEnv:
    n_states: int
    n_actions: int

    def __init__(self, config: dict[str, Any], seed: int | None = None) -> None:
        raise NotImplementedError("Phase 1: implement per skill `environment-spec`.")

    def reset(self, seed: int | None = None) -> State:
        raise NotImplementedError

    def step(self, action: int) -> tuple[State, float, bool, bool, dict[str, Any]]:
        raise NotImplementedError

    def encode_state(self, state: State) -> int:
        raise NotImplementedError

    def render(self) -> str:
        raise NotImplementedError

    # ---- TEST-ONLY ORACLE ------------------------------------------------------------
    # Exposes T and R so tests can compute Q* by value iteration (AIMA Ch. 17).
    # agent.py must never import or call this (tests/test_model_free_invariant.py).
    def oracle_model(self) -> Any:
        raise NotImplementedError
