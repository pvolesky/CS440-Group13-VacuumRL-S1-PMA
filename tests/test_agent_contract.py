"""Q-learning agent contract tests.

Procedure and hand-computed numbers: .gemini/skills/q-learning-implementation/SKILL.md
"""
from __future__ import annotations

import numpy as np
import pytest

from vacuum_rl.agent import QLearningAgent
from vacuum_rl.config import load_config
from vacuum_rl.env import VacuumGridEnv
from vacuum_rl.train import run_training


def test_update_matches_hand_computation():
    """Q=0, alpha=0.5, gamma=0.9, r=1, max Q(s')=2 -> new Q == 1.4."""
    agent = QLearningAgent(
        n_states=5,
        n_actions=4,
        config={"agent": {"alpha": 0.5, "gamma": 0.9, "optimistic_init": 0.0}},
        seed=0,
    )
    # Set max Q(s'=1) = 2.0
    agent.q_table[1, 0] = 2.0
    agent.update(state=0, action=0, reward=1.0, next_state=1, terminated=False)
    assert agent.q_table[0, 0] == pytest.approx(1.4)


def test_terminal_update_ignores_next_state_value():
    """Same setup with terminated=True -> new Q == 0.5."""
    agent = QLearningAgent(
        n_states=5,
        n_actions=4,
        config={"agent": {"alpha": 0.5, "gamma": 0.9, "optimistic_init": 0.0}},
        seed=0,
    )
    # Set max Q(s'=1) = 2.0
    agent.q_table[1, 0] = 2.0
    agent.update(state=0, action=0, reward=1.0, next_state=1, terminated=True)
    assert agent.q_table[0, 0] == pytest.approx(0.5)


def test_truncated_transition_still_bootstraps():
    """terminated=False (even if the episode was truncated) uses r + gamma*max Q(s')."""
    agent = QLearningAgent(
        n_states=5,
        n_actions=4,
        config={"agent": {"alpha": 0.5, "gamma": 0.9, "optimistic_init": 0.0}},
        seed=0,
    )
    agent.q_table[2, 3] = 3.0
    # On truncation, terminated is False, so target should include gamma * max Q(next_state)
    agent.update(state=0, action=1, reward=0.5, next_state=2, terminated=False)
    # target = 0.5 + 0.9 * 3.0 = 3.2. new Q = 0 + 0.5 * (3.2 - 0) = 1.6
    assert agent.q_table[0, 1] == pytest.approx(1.6)


def test_greedy_ties_are_broken_randomly():
    """With equal Q-values, repeated greedy choices cover all tied actions."""
    agent = QLearningAgent(
        n_states=2,
        n_actions=4,
        config={"agent": {"optimistic_init": 0.0}},
        seed=42,
    )
    chosen_actions = {agent.select_action(state=0, explore=False) for _ in range(200)}
    assert chosen_actions == {0, 1, 2, 3}


def test_same_seed_gives_identical_q_table():
    """Training twice with one seed gives identical Q-tables."""
    cfg = load_config()
    cfg["training"]["episodes"] = 50

    run1 = run_training(cfg, seed=42)
    run2 = run_training(cfg, seed=42)

    assert np.array_equal(run1["agent"].q_table, run2["agent"].q_table)


def test_greedy_policy_matches_value_iteration_oracle():
    """After training, greedy policy equals the oracle policy on visited states."""
    cfg = load_config()
    cfg["training"]["episodes"] = 1000
    gamma = float(cfg["agent"]["gamma"])

    env = VacuumGridEnv(cfg)
    oracle = env.oracle_model()
    T, R = oracle.T, oracle.R

    # Compute optimal Q* via value iteration (AIMA Ch. 17)
    V = np.zeros(env.n_states)
    for _ in range(1000):
        V_next = np.copy(V)
        for s in range(env.n_states):
            if s in oracle.terminal_states or s in {env.encode_state(o) for o in env._obstacle_states}:
                V_next[s] = 0.0
                continue
            q_sa = np.sum(T[s] * (R[s] + gamma * V), axis=-1)
            V_next[s] = np.max(q_sa)
        if np.max(np.abs(V_next - V)) < 1e-8:
            break
        V = V_next

    oracle_q = np.zeros((env.n_states, env.n_actions))
    for s in range(env.n_states):
        oracle_q[s] = np.sum(T[s] * (R[s] + gamma * V), axis=-1)

    # Train agent
    run = run_training(cfg, seed=42)
    agent = run["agent"]

    # Verify that the agent finds an optimal 6-step path with return +9.94
    state = env.reset()
    visited_states = []
    total_reward = 0.0
    for _ in range(20):
        s_idx = env.encode_state(state)
        visited_states.append(s_idx)
        action = agent.select_action(s_idx, explore=False)
        state, r, term, trunc, _ = env.step(action)
        total_reward += r
        if term or trunc:
            break

    # Must reach dock in optimal 6 steps with +9.94 return
    assert term is True
    assert len(visited_states) == 6
    assert total_reward == pytest.approx(9.94)

    # Verify that on all states visited along this optimal path, the agent's action
    # attains the maximal oracle Q* value
    for s_idx in visited_states:
        greedy_act = agent.greedy_policy()[s_idx]
        max_oracle_q = np.max(oracle_q[s_idx])
        assert oracle_q[s_idx, greedy_act] == pytest.approx(max_oracle_q, abs=1e-5)
