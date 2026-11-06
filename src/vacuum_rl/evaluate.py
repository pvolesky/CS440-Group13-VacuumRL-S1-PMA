"""Greedy evaluation (epsilon 0, separate env instance, no updates)."""
from __future__ import annotations

from typing import Any
from vacuum_rl.env import VacuumGridEnv


def evaluate_greedy(
    agent: Any, env: VacuumGridEnv, episodes: int, seed: int
) -> dict[str, float]:
    """Return mean greedy return, mean length and success rate across evaluation episodes."""
    returns: list[float] = []
    lengths: list[int] = []
    successes: int = 0

    for ep in range(episodes):
        ep_seed = seed + ep
        state = env.reset(seed=ep_seed)
        ep_return = 0.0
        steps = 0
        terminated = False
        truncated = False

        while not (terminated or truncated):
            s_idx = env.encode_state(state)
            action = agent.select_action(s_idx, explore=False)
            state, reward, terminated, truncated, _ = env.step(action)
            ep_return += reward
            steps += 1

        returns.append(ep_return)
        lengths.append(steps)
        # Success: reached dock (positive terminal reward >= 9.0)
        if terminated and ep_return > 0:
            successes += 1

    n_episodes = max(len(returns), 1)
    return {
        "mean_return": float(sum(returns) / n_episodes),
        "mean_length": float(sum(lengths) / n_episodes),
        "success_rate": float(successes / n_episodes),
    }
