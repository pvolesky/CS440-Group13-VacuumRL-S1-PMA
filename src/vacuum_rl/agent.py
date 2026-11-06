"""Tabular Q-learning agent.

Procedure: .gemini/skills/q-learning-implementation/SKILL.md

MODEL-FREE BOUNDARY: this module must not import vacuum_rl.env or touch T/R.
It receives only (state_index, action, reward, next_state_index, terminated).
tests/test_model_free_invariant.py enforces this statically.
"""
from __future__ import annotations

from typing import Any
import numpy as np


class QLearningAgent:
    """Tabular Q-learning agent operating on integer state and action indices."""

    def __init__(
        self,
        n_states: int,
        n_actions: int,
        config: dict[str, Any],
        seed: int | None = None,
    ) -> None:
        agent_cfg = config.get("agent", config)
        self.n_states = n_states
        self.n_actions = n_actions

        self.alpha: float = float(agent_cfg.get("alpha", 0.1))
        self.gamma: float = float(agent_cfg.get("gamma", 0.9))
        self.epsilon: float = float(agent_cfg.get("epsilon_start", 1.0))
        self.epsilon_min: float = float(agent_cfg.get("epsilon_min", 0.01))
        self.epsilon_decay: float = float(agent_cfg.get("epsilon_decay", 0.99))
        self.optimistic_init: float = float(agent_cfg.get("optimistic_init", 0.0))

        self._rng = np.random.default_rng(seed)
        self.q_table = np.full(
            (self.n_states, self.n_actions),
            fill_value=self.optimistic_init,
            dtype=np.float64,
        )

    def select_action(self, state: int, explore: bool = True) -> int:
        """Epsilon-greedy when explore=True, greedy otherwise. Random tie-breaking."""
        if explore and self._rng.random() < self.epsilon:
            return int(self._rng.integers(0, self.n_actions))

        # Greedy choice with random tie-breaking among maximal actions
        q_row = self.q_table[state]
        max_q = np.max(q_row)
        best_actions = np.flatnonzero(np.isclose(q_row, max_q))
        return int(self._rng.choice(best_actions))

    def update(
        self,
        state: int,
        action: int,
        reward: float,
        next_state: int,
        terminated: bool,
    ) -> None:
        """Q(s,a) += alpha * (target - Q(s,a)); target = r if terminated else r + gamma*max Q(s')."""
        if terminated:
            target = reward
        else:
            target = reward + self.gamma * np.max(self.q_table[next_state])

        current_q = self.q_table[state, action]
        self.q_table[state, action] = current_q + self.alpha * (target - current_q)

    def end_episode(self) -> None:
        """Hook for per-episode schedules (e.g. epsilon decay)."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def greedy_policy(self) -> list[int]:
        """Return the greedy action for each state (deterministic argmax)."""
        return [int(np.argmax(self.q_table[s])) for s in range(self.n_states)]
