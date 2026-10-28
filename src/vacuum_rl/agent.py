"""Tabular Q-learning agent. STUB: implement only when the user asks.

Procedure: .claude/skills/q-learning-implementation/SKILL.md

MODEL-FREE BOUNDARY: this module must not import vacuum_rl.env or touch T/R.
It receives only (state_index, action, reward, next_state_index, terminated).
tests/test_model_free_invariant.py enforces this statically.
"""
from __future__ import annotations

from typing import Any


class QLearningAgent:
    def __init__(self, n_states: int, n_actions: int, config: dict[str, Any], seed: int) -> None:
        raise NotImplementedError("Phase 2: implement per skill `q-learning-implementation`.")

    def select_action(self, state: int, explore: bool = True) -> int:
        """Epsilon-greedy when explore=True, greedy otherwise. Random tie-breaking."""
        raise NotImplementedError

    def update(self, state: int, action: int, reward: float, next_state: int, terminated: bool) -> None:
        """Q(s,a) += alpha * (target - Q(s,a)); target = r if terminated else r + gamma*max Q(s')."""
        raise NotImplementedError

    def end_episode(self) -> None:
        """Hook for per-episode schedules (e.g. epsilon decay)."""
        raise NotImplementedError

    def greedy_policy(self) -> list[int]:
        raise NotImplementedError
