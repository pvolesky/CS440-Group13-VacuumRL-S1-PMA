"""Vacuum-robot grid world environment.

Procedure and invariants: .gemini/skills/environment-spec/SKILL.md
Semantics: docs/environment.md and configs/default.toml (Decision D-009)

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
import numpy as np

from vacuum_rl.config import load_config

State = tuple[int, int]  # (row, col), row 0 at the top.


class Action(IntEnum):
    """Order matches `actions` in configs/default.toml."""

    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


DELTAS: dict[int, tuple[int, int]] = {
    Action.UP: (-1, 0),
    Action.RIGHT: (0, 1),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
}

PERPENDICULAR_ACTIONS: dict[int, tuple[int, int]] = {
    Action.UP: (Action.LEFT, Action.RIGHT),
    Action.RIGHT: (Action.UP, Action.DOWN),
    Action.DOWN: (Action.RIGHT, Action.LEFT),
    Action.LEFT: (Action.DOWN, Action.UP),
}


class OracleModel:
    """Test-only model of the environment exposing T and R (AIMA Ch. 17).

    Supports unpacking (T, R = oracle) as well as attribute access.
    agent.py must NEVER import or use this class.
    """

    def __init__(
        self,
        T: np.ndarray,
        R: np.ndarray,
        terminal_states: set[int] | None = None,
        expected_R: np.ndarray | None = None,
    ) -> None:
        self.T = T
        self.R = R
        self.terminal_states = terminal_states if terminal_states is not None else set()
        self.expected_R = expected_R if expected_R is not None else np.sum(T * R, axis=-1)

    def __iter__(self):
        return iter((self.T, self.R))

    def __getitem__(self, index: int):
        return (self.T, self.R)[index]


class VacuumGridEnv:
    """Grid-world environment for the vacuum cleaner agent."""

    n_states: int
    n_actions: int

    def __init__(self, config: dict[str, Any] | None = None, seed: int | None = None) -> None:
        if config is None:
            config = load_config()

        env_cfg = config.get("environment", config)
        self._raw_config = config
        self._layout: list[list[str]] = [list(row) for row in env_cfg["layout"]]
        self._n_rows = len(self._layout)
        self._n_cols = len(self._layout[0])

        self.n_states = self._n_rows * self._n_cols
        self.n_actions = len(Action)

        self.obstacle_tokens = set(env_cfg.get("obstacle_tokens", ["X"]))
        self.terminal_tokens = set(env_cfg.get("terminal_tokens", ["10", "-1"]))
        self.blocked_move = env_cfg.get("blocked_move", "stay")
        self.step_cost = float(env_cfg.get("step_cost", -0.01))
        self.slip_probability = float(env_cfg.get("slip_probability", 0.0))
        self.max_episode_steps = int(env_cfg.get("max_episode_steps", 100))

        # Identify special coordinates
        self._start_state: State | None = None
        self._obstacle_states: set[State] = set()
        self._terminal_states: set[State] = set()

        for r in range(self._n_rows):
            for c in range(self._n_cols):
                tok = self._layout[r][c]
                if tok == "start":
                    self._start_state = (r, c)
                elif tok in self.obstacle_tokens:
                    self._obstacle_states.add((r, c))
                elif tok in self.terminal_tokens:
                    self._terminal_states.add((r, c))

        if self._start_state is None:
            raise ValueError("Layout missing 'start' cell.")

        self._rng = np.random.default_rng(seed)
        self._current_state: State = self._start_state
        self._step_count = 0

    def reset(self, seed: int | None = None) -> State:
        """Reset the environment to the start state."""
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        self._current_state = self._start_state
        self._step_count = 0
        return self._current_state

    def step(self, action: int) -> tuple[State, float, bool, bool, dict[str, Any]]:
        """Take an action in the environment.

        Returns: (next_state, reward, terminated, truncated, info)
        """
        # Determine actual action after possible slip
        actual_action = self._resolve_slip(action)

        # Transition dynamics
        next_state, reward, terminated = self._transition_and_reward(
            self._current_state, actual_action
        )

        self._current_state = next_state
        self._step_count += 1

        truncated = False
        if terminated:
            truncated = False
        elif self._step_count >= self.max_episode_steps:
            truncated = True

        info: dict[str, Any] = {"step": self._step_count}
        return next_state, reward, terminated, truncated, info

    def encode_state(self, state: State) -> int:
        """Convert a (row, col) state tuple to a scalar index."""
        return state[0] * self._n_cols + state[1]

    def decode_state(self, index: int) -> State:
        """Convert a scalar state index back to a (row, col) tuple."""
        return (index // self._n_cols, index % self._n_cols)

    def render(self) -> str:
        """Return a string rendering of the grid and the agent's current location."""
        lines = []
        for r in range(self._n_rows):
            cells = []
            for c in range(self._n_cols):
                if (r, c) == self._current_state:
                    cells.append("@")
                else:
                    cells.append(self._layout[r][c])
            lines.append(" ".join(f"{tok:>5}" for tok in cells))
        return "\n".join(lines)

    # ---- PRIVATE MODEL (T and R) -----------------------------------------------------

    def _resolve_slip(self, action: int) -> int:
        if self.slip_probability <= 0.0:
            return action

        roll = self._rng.random()
        perp = PERPENDICULAR_ACTIONS[action]
        half_slip = self.slip_probability / 2.0
        if roll < half_slip:
            return perp[0]
        elif roll < self.slip_probability:
            return perp[1]
        return action

    def _transition_and_reward(
        self, state: State, action: int
    ) -> tuple[State, float, bool]:
        """Private transition and reward calculation for a specific action."""
        if state in self._terminal_states:
            # Absorbing terminal state
            return state, 0.0, True

        r, c = state
        dr, dc = DELTAS[action]
        nr, nc = r + dr, c + dc

        # Check grid boundaries and obstacle cells
        is_blocked = (
            nr < 0
            or nr >= self._n_rows
            or nc < 0
            or nc >= self._n_cols
            or (nr, nc) in self._obstacle_states
        )

        if is_blocked:
            next_state = state if self.blocked_move == "stay" else state
            reward = self.step_cost
            terminated = False
            return next_state, reward, terminated

        next_state = (nr, nc)
        token = self._layout[nr][nc]

        if token == "start" or token == "0":
            cell_reward = 0.0
        else:
            cell_reward = float(token)

        reward = self.step_cost + cell_reward
        terminated = token in self.terminal_tokens
        return next_state, reward, terminated

    # ---- TEST-ONLY ORACLE ------------------------------------------------------------
    # Exposes T and R so tests can compute Q* by value iteration (AIMA Ch. 17).
    # agent.py must never import or call this (tests/test_model_free_invariant.py).

    def oracle_model(self) -> OracleModel:
        """Construct and return the true MDP transition probabilities T and rewards R."""
        T = np.zeros((self.n_states, self.n_actions, self.n_states), dtype=np.float64)
        R = np.zeros((self.n_states, self.n_actions, self.n_states), dtype=np.float64)
        terminal_indices = {self.encode_state(s) for s in self._terminal_states}

        for s_idx in range(self.n_states):
            state = self.decode_state(s_idx)

            if state in self._obstacle_states:
                # Impassable cell: self-loop with 0 reward
                for a in range(self.n_actions):
                    T[s_idx, a, s_idx] = 1.0
                    R[s_idx, a, s_idx] = 0.0
                continue

            if state in self._terminal_states:
                # Absorbing terminal cell: self-loop with 0 reward
                for a in range(self.n_actions):
                    T[s_idx, a, s_idx] = 1.0
                    R[s_idx, a, s_idx] = 0.0
                continue

            for a in range(self.n_actions):
                # Outcomes and probabilities under possible slip
                if self.slip_probability <= 0.0:
                    outcomes = [(a, 1.0)]
                else:
                    perp = PERPENDICULAR_ACTIONS[a]
                    half_slip = self.slip_probability / 2.0
                    outcomes = [
                        (a, 1.0 - self.slip_probability),
                        (perp[0], half_slip),
                        (perp[1], half_slip),
                    ]

                for act, prob in outcomes:
                    next_st, rew, _ = self._transition_and_reward(state, act)
                    next_s_idx = self.encode_state(next_st)
                    T[s_idx, a, next_s_idx] += prob
                    R[s_idx, a, next_s_idx] = rew

        return OracleModel(T=T, R=R, terminal_states=terminal_indices)
