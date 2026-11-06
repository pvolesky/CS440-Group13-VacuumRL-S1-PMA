"""Environment contract tests.

Contract source: .gemini/skills/environment-spec/SKILL.md and docs/environment.md.
"""
from __future__ import annotations

import numpy as np
import pytest

from vacuum_rl.config import load_config
from vacuum_rl.env import Action, VacuumGridEnv


@pytest.fixture
def env():
    return VacuumGridEnv(load_config())


def test_reset_returns_start_state(env: VacuumGridEnv):
    """reset() returns the cell marked 'start' as a (row, col) tuple."""
    state = env.reset()
    assert state == (0, 0)
    assert isinstance(state, tuple)
    assert len(state) == 2


def test_step_returns_five_tuple(env: VacuumGridEnv):
    """step() -> (next_state, reward, terminated, truncated, info)."""
    env.reset()
    next_state, reward, terminated, truncated, info = env.step(Action.RIGHT)
    assert isinstance(next_state, tuple)
    assert len(next_state) == 2
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_obstacle_blocks_movement(env: VacuumGridEnv):
    """Moving into 'X' leaves the robot in place (provisional blocked_move rule)."""
    env.reset()
    # Move to (1, 0)
    s1, r1, term1, trunc1, _ = env.step(Action.DOWN)
    assert s1 == (1, 0)

    # Attempt to move RIGHT into (1, 1) which has obstacle 'X'
    s2, r2, term2, trunc2, _ = env.step(Action.RIGHT)
    assert s2 == (1, 0)
    assert r2 == pytest.approx(env.step_cost)
    assert not term2
    assert not trunc2


def test_boundary_blocks_movement(env: VacuumGridEnv):
    """Moving off the grid leaves the robot in place."""
    env.reset()
    # Attempt to move UP from (0, 0)
    s, r, term, trunc, _ = env.step(Action.UP)
    assert s == (0, 0)
    assert r == pytest.approx(env.step_cost)
    assert not term
    assert not trunc

    # Attempt to move LEFT from (0, 0)
    s, r, term, trunc, _ = env.step(Action.LEFT)
    assert s == (0, 0)
    assert r == pytest.approx(env.step_cost)
    assert not term
    assert not trunc


def test_entering_terminal_cell_terminates(env: VacuumGridEnv):
    """Entering terminal cells sets terminated=True and truncated=False."""
    # 1. Dock terminal cell at (3, 3) with +10 reward
    env.reset()
    for a in [Action.RIGHT, Action.RIGHT, Action.RIGHT, Action.DOWN, Action.DOWN]:
        s, r, term, trunc, _ = env.step(a)
        assert not term
        assert not trunc

    # Move DOWN into (3, 3)
    s, r, term, trunc, _ = env.step(Action.DOWN)
    assert s == (3, 3)
    assert term is True
    assert trunc is False
    assert r == pytest.approx(10.0 + env.step_cost)

    # 2. Hazard terminal cell at (3, 1) with -1 reward
    env.reset()
    # Path to (2, 1): DOWN to (1, 0), DOWN to (2, 0), RIGHT to (2, 1)
    env.step(Action.DOWN)   # (1, 0)
    env.step(Action.DOWN)   # (2, 0)
    env.step(Action.RIGHT)  # (2, 1)

    # Move DOWN into (3, 1)
    s, r, term, trunc, _ = env.step(Action.DOWN)
    assert s == (3, 1)
    assert term is True
    assert trunc is False
    assert r == pytest.approx(-1.0 + env.step_cost)


def test_truncation_at_max_episode_steps():
    """After max_episode_steps non-terminal steps: truncated=True, terminated=False."""
    cfg = load_config()
    cfg["environment"]["max_episode_steps"] = 10
    short_env = VacuumGridEnv(cfg)
    short_env.reset()

    for step in range(1, 10):
        # Bump up at (0, 0)
        _, _, term, trunc, _ = short_env.step(Action.UP)
        assert not term
        assert not trunc

    # 10th step should trigger truncation
    _, _, term, trunc, _ = short_env.step(Action.UP)
    assert not term
    assert trunc is True


def test_same_seed_gives_same_trajectory():
    """Two envs with the same seed and actions produce identical trajectories."""
    cfg = load_config()
    cfg["environment"]["slip_probability"] = 0.3

    env1 = VacuumGridEnv(cfg, seed=42)
    env2 = VacuumGridEnv(cfg, seed=42)
    env3 = VacuumGridEnv(cfg, seed=99)

    actions = [Action.RIGHT, Action.DOWN, Action.RIGHT, Action.DOWN] * 5

    env1.reset(seed=42)
    env2.reset(seed=42)
    env3.reset(seed=99)

    traj1 = [env1.step(a)[:4] for a in actions]
    traj2 = [env2.step(a)[:4] for a in actions]
    traj3 = [env3.step(a)[:4] for a in actions]

    assert traj1 == traj2
    # With slip=0.3 over 20 steps, different seeds should diverge
    assert traj1 != traj3


def test_info_does_not_leak_model(env: VacuumGridEnv):
    """info must not expose transition probabilities or the reward function."""
    env.reset()
    _, _, _, _, info = env.step(Action.RIGHT)
    forbidden_substrings = ["transition", "reward", "prob", "oracle", "model"]
    for key in info:
        for forbidden in forbidden_substrings:
            assert forbidden not in key.lower()


def test_oracle_matches_documented_semantics(env: VacuumGridEnv):
    """oracle_model() T and R agree with step() on every (state, action) pair."""
    oracle = env.oracle_model()
    T, R = oracle.T, oracle.R

    assert T.shape == (env.n_states, env.n_actions, env.n_states)
    assert R.shape == (env.n_states, env.n_actions, env.n_states)

    # Probabilities must sum to 1 across next states
    assert np.allclose(T.sum(axis=-1), 1.0)

    # In deterministic mode, every valid transition has probability 1.0
    for s_idx in range(env.n_states):
        st = env.decode_state(s_idx)
        if st in env._obstacle_states or st in env._terminal_states:
            # Absorbing state
            for a in range(env.n_actions):
                assert T[s_idx, a, s_idx] == 1.0
                assert R[s_idx, a, s_idx] == 0.0
            continue

        for a in range(env.n_actions):
            next_indices = np.where(T[s_idx, a] > 0)[0]
            assert len(next_indices) == 1
            next_idx = next_indices[0]
            assert T[s_idx, a, next_idx] == 1.0

            # Step manually from st
            expected_next, expected_r, _ = env._transition_and_reward(st, a)
            assert next_idx == env.encode_state(expected_next)
            assert R[s_idx, a, next_idx] == pytest.approx(expected_r)


def test_scripted_optimal_path_return(env: VacuumGridEnv):
    """Sanity check: optimal 6-step path return is 6 * (-0.01) + 10 = +9.94 (D-009)."""
    env.reset()
    path = [
        Action.RIGHT,  # to (0, 1)
        Action.RIGHT,  # to (0, 2)
        Action.RIGHT,  # to (0, 3)
        Action.DOWN,   # to (1, 3)
        Action.DOWN,   # to (2, 3)
        Action.DOWN,   # to (3, 3) - dock (+10)
    ]
    total_reward = 0.0
    for a in path:
        _, r, term, _, _ = env.step(a)
        total_reward += r

    assert term is True
    assert total_reward == pytest.approx(9.94)
