#!/usr/bin/env python3
"""Experiment harness for tabular Q-learning per rl-experiment-protocol.

Features:
- Multi-seed runs (n_seeds >= 5) with isolated RNGs
- Directory artifact layout: config.toml, metrics.csv, eval.csv, summary.json, Q-tables
- SQLite database logging to experiments/runs.db (usable via sqlite MCP server)
- Oracle agreement computation via value iteration (AIMA Ch. 17)
- Aggregate reporting across seeds (mean +/- std)
"""
from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
import numpy as np

from vacuum_rl.agent import QLearningAgent
from vacuum_rl.config import load_config
from vacuum_rl.env import VacuumGridEnv
from vacuum_rl.evaluate import evaluate_greedy


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "experiments" / "runs.db"


def get_git_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def compute_oracle(env: VacuumGridEnv, gamma: float) -> tuple[np.ndarray, np.ndarray, set[int]]:
    """Compute optimal V* and Q* via value iteration (AIMA Ch. 17)."""
    oracle = env.oracle_model()
    T, R = oracle.T, oracle.R
    terminal_and_obstacles = oracle.terminal_states | {
        env.encode_state(obs) for obs in env._obstacle_states
    }

    V = np.zeros(env.n_states)
    for _ in range(1000):
        V_next = np.copy(V)
        for s in range(env.n_states):
            if s in terminal_and_obstacles:
                V_next[s] = 0.0
                continue
            q_sa = np.sum(T[s] * (R[s] + gamma * V), axis=-1)
            V_next[s] = np.max(q_sa)
        if np.max(np.abs(V_next - V)) < 1e-9:
            break
        V = V_next

    Q_star = np.zeros((env.n_states, env.n_actions))
    for s in range(env.n_states):
        Q_star[s] = np.sum(T[s] * (R[s] + gamma * V), axis=-1)

    valid_states = set(range(env.n_states)) - terminal_and_obstacles
    return V, Q_star, valid_states


def compute_oracle_agreement(
    agent: QLearningAgent, Q_star: np.ndarray, valid_states: set[int]
) -> float:
    """Fraction of valid states where agent greedy action attains maximal Q*."""
    optimal_matches = 0
    for s in valid_states:
        greedy_act = agent.greedy_policy()[s]
        max_q = np.max(Q_star[s])
        if np.isclose(Q_star[s, greedy_act], max_q, atol=1e-5):
            optimal_matches += 1
    return float(optimal_matches / max(len(valid_states), 1))


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS experiment_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE,
                experiment_name TEXT,
                git_sha TEXT,
                timestamp TEXT,
                n_seeds INTEGER,
                episodes INTEGER,
                alpha REAL,
                gamma REAL,
                epsilon_decay REAL,
                mean_final_return REAL,
                std_final_return REAL,
                mean_final_length REAL,
                mean_success_rate REAL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS eval_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                seed INTEGER,
                episode INTEGER,
                greedy_return REAL,
                greedy_length REAL,
                success_rate REAL,
                oracle_agreement REAL
            );
            """
        )
        conn.commit()


def save_config_toml(path: Path, config: dict[str, Any]) -> None:
    env_c = config["environment"]
    agt_c = config["agent"]
    trn_c = config["training"]

    lines = [
        "# Frozen configuration snapshot for experiment run",
        "[environment]",
        f"layout = {json.dumps(env_c['layout'])}",
        f"actions = {json.dumps(env_c['actions'])}",
        f"obstacle_tokens = {json.dumps(env_c['obstacle_tokens'])}",
        f"terminal_tokens = {json.dumps(env_c['terminal_tokens'])}",
        f"blocked_move = {json.dumps(env_c.get('blocked_move', 'stay'))}",
        f"step_cost = {env_c.get('step_cost', -0.01)}",
        f"slip_probability = {env_c.get('slip_probability', 0.0)}",
        f"max_episode_steps = {env_c.get('max_episode_steps', 100)}",
        "",
        "[agent]",
        f"algorithm = {json.dumps(agt_c.get('algorithm', 'tabular_q_learning'))}",
        f"gamma = {agt_c['gamma']}",
        f"alpha = {agt_c['alpha']}",
        f"epsilon_start = {agt_c['epsilon_start']}",
        f"epsilon_decay = {agt_c['epsilon_decay']}",
        f"epsilon_min = {agt_c['epsilon_min']}",
        f"optimistic_init = {agt_c.get('optimistic_init', 0.0)}",
        "",
        "[training]",
        f"episodes = {trn_c['episodes']}",
        f"seed = {trn_c.get('seed', 0)}",
        f"n_seeds = {trn_c.get('n_seeds', 5)}",
        f"eval_every = {trn_c.get('eval_every', 100)}",
        f"eval_episodes = {trn_c.get('eval_episodes', 20)}",
        f"output_dir = {json.dumps(trn_c.get('output_dir', 'experiments/runs'))}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_experiment(
    experiment_name: str,
    question: str,
    config: dict[str, Any],
    seeds: list[int] | None = None,
) -> Path:
    """Run a multi-seed experiment per rl-experiment-protocol."""
    git_sha = get_git_sha()
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().isoformat()
    run_dir_name = f"{date_str}_{experiment_name}_{git_sha}"
    run_dir = REPO_ROOT / config["training"].get("output_dir", "experiments/runs") / run_dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    if seeds is None:
        base_seed = int(config["training"].get("seed", 0))
        n_seeds = int(config["training"].get("n_seeds", 5))
        seeds = [base_seed + i for i in range(n_seeds)]
    else:
        n_seeds = len(seeds)

    episodes = int(config["training"].get("episodes", 2000))
    eval_every = int(config["training"].get("eval_every", 100))
    eval_episodes = int(config["training"].get("eval_episodes", 20))
    gamma = float(config["agent"]["gamma"])

    env_ref = VacuumGridEnv(config, seed=0)
    _, Q_star, valid_states = compute_oracle(env_ref, gamma)

    metrics_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []

    final_greedy_returns: list[float] = []
    final_greedy_lengths: list[float] = []
    final_success_rates: list[float] = []
    episodes_to_criterion: list[int | None] = []
    first_ep_full_oracle: list[int | None] = []

    print(f"=== Experiment: {experiment_name} ({n_seeds} seeds: {seeds}) ===")
    print(f"Question: {question}")

    for seed in seeds:
        print(f"  Running seed {seed}...")
        env = VacuumGridEnv(config, seed=seed)
        agent = QLearningAgent(env.n_states, env.n_actions, config, seed=seed)

        hit_criterion: int | None = None
        hit_oracle: int | None = None

        for ep in range(episodes):
            ep_seed = seed * 100_000 + ep
            state = env.reset(seed=ep_seed)
            ep_return = 0.0
            steps = 0
            terminated = False
            truncated = False

            while not (terminated or truncated):
                s_idx = env.encode_state(state)
                action = agent.select_action(s_idx, explore=True)
                next_state, reward, terminated, truncated, _ = env.step(action)
                next_s_idx = env.encode_state(next_state)

                agent.update(s_idx, action, reward, next_s_idx, terminated)
                state = next_state
                ep_return += reward
                steps += 1

            agent.end_episode()
            metrics_rows.append(
                {
                    "seed": seed,
                    "episode": ep + 1,
                    "return": round(ep_return, 4),
                    "length": steps,
                    "epsilon": round(agent.epsilon, 4),
                    "terminated": int(terminated),
                    "truncated": int(truncated),
                }
            )

            # Evaluation check
            if eval_every > 0 and (ep + 1) % eval_every == 0:
                eval_env = VacuumGridEnv(config, seed=seed + 10_000)
                eval_metrics = evaluate_greedy(
                    agent, eval_env, episodes=eval_episodes, seed=seed + 10_000
                )
                oracle_agr = compute_oracle_agreement(agent, Q_star, valid_states)

                eval_rows.append(
                    {
                        "seed": seed,
                        "episode": ep + 1,
                        "greedy_return": round(eval_metrics["mean_return"], 4),
                        "greedy_length": round(eval_metrics["mean_length"], 2),
                        "success_rate": round(eval_metrics["success_rate"], 4),
                        "oracle_agreement": round(oracle_agr, 4),
                    }
                )

                if hit_criterion is None and eval_metrics["success_rate"] >= 0.95:
                    hit_criterion = ep + 1
                if hit_oracle is None and np.isclose(oracle_agr, 1.0):
                    hit_oracle = ep + 1

        # Final eval at end of seed
        eval_env = VacuumGridEnv(config, seed=seed + 20_000)
        final_eval = evaluate_greedy(agent, eval_env, episodes=eval_episodes, seed=seed + 20_000)
        final_greedy_returns.append(final_eval["mean_return"])
        final_greedy_lengths.append(final_eval["mean_length"])
        final_success_rates.append(final_eval["success_rate"])
        episodes_to_criterion.append(hit_criterion)
        first_ep_full_oracle.append(hit_oracle)

        # Save Q-table
        np.save(run_dir / f"q_table_seed{seed}.npy", agent.q_table)

    # Save artifacts
    save_config_toml(run_dir / "config.toml", config)

    # Write metrics.csv
    with open(run_dir / "metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["seed", "episode", "return", "length", "epsilon", "terminated", "truncated"]
        )
        writer.writeheader()
        writer.writerows(metrics_rows)

    # Write eval.csv
    with open(run_dir / "eval.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["seed", "episode", "greedy_return", "greedy_length", "success_rate", "oracle_agreement"]
        )
        writer.writeheader()
        writer.writerows(eval_rows)

    # Compute summary aggregates
    valid_crit_eps = [e for e in episodes_to_criterion if e is not None]
    valid_orcl_eps = [e for e in first_ep_full_oracle if e is not None]

    summary = {
        "experiment_name": experiment_name,
        "question": question,
        "git_sha": git_sha,
        "timestamp": timestamp_str,
        "n_seeds": n_seeds,
        "seeds": seeds,
        "episodes": episodes,
        "parameters": {
            "alpha": float(config["agent"]["alpha"]),
            "gamma": float(config["agent"]["gamma"]),
            "epsilon_start": float(config["agent"]["epsilon_start"]),
            "epsilon_decay": float(config["agent"]["epsilon_decay"]),
            "epsilon_min": float(config["agent"]["epsilon_min"]),
            "slip_probability": float(config["environment"].get("slip_probability", 0.0)),
        },
        "results": {
            "mean_final_return": float(np.mean(final_greedy_returns)),
            "std_final_return": float(np.std(final_greedy_returns)),
            "mean_final_length": float(np.mean(final_greedy_lengths)),
            "std_final_length": float(np.std(final_greedy_lengths)),
            "mean_success_rate": float(np.mean(final_success_rates)),
            "std_success_rate": float(np.std(final_success_rates)),
            "episodes_to_95pct_criterion_mean": float(np.mean(valid_crit_eps)) if valid_crit_eps else None,
            "episodes_to_full_oracle_agreement_mean": float(np.mean(valid_orcl_eps)) if valid_orcl_eps else None,
        },
    }

    with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Record into SQLite DB
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO experiment_runs (
                run_id, experiment_name, git_sha, timestamp, n_seeds, episodes,
                alpha, gamma, epsilon_decay, mean_final_return, std_final_return,
                mean_final_length, mean_success_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_dir_name,
                experiment_name,
                git_sha,
                timestamp_str,
                n_seeds,
                episodes,
                summary["parameters"]["alpha"],
                summary["parameters"]["gamma"],
                summary["parameters"]["epsilon_decay"],
                summary["results"]["mean_final_return"],
                summary["results"]["std_final_return"],
                summary["results"]["mean_final_length"],
                summary["results"]["mean_success_rate"],
            ),
        )

        for row in eval_rows:
            cursor.execute(
                """
                INSERT INTO eval_checkpoints (
                    run_id, seed, episode, greedy_return, greedy_length, success_rate, oracle_agreement
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_dir_name,
                    row["seed"],
                    row["episode"],
                    row["greedy_return"],
                    row["greedy_length"],
                    row["success_rate"],
                    row["oracle_agreement"],
                ),
            )
        conn.commit()

    print(f"Results saved to: {run_dir}")
    print(
        f"Summary: Final Return = {summary['results']['mean_final_return']:.2f} +/- {summary['results']['std_final_return']:.2f}, "
        f"Success Rate = {summary['results']['mean_success_rate']:.1%}"
    )
    return run_dir


def main() -> int:
    base_cfg = load_config()

    # 1. Baseline Experiment (5 seeds, default hyperparameters)
    run_experiment(
        experiment_name="baseline",
        question="How reliably does the default Q-learning configuration converge to the optimal policy across 5 seeds?",
        config=base_cfg,
    )

    # 2. Hyperparameter sweep on epsilon decay (exploration speed: 0.95 vs 0.99 vs 0.995)
    cfg_fast_decay = load_config()
    cfg_fast_decay["agent"]["epsilon_decay"] = 0.95
    run_experiment(
        experiment_name="sweep_epsilon_decay_0.95",
        question="Does faster epsilon decay (0.95) reach optimal policy faster without getting stuck?",
        config=cfg_fast_decay,
    )

    cfg_slow_decay = load_config()
    cfg_slow_decay["agent"]["epsilon_decay"] = 0.995
    run_experiment(
        experiment_name="sweep_epsilon_decay_0.995",
        question="Does slower epsilon decay (0.995) explore more thoroughly before settling on the policy?",
        config=cfg_slow_decay,
    )

    # 3. Hyperparameter sweep on learning rate alpha (0.05 vs 0.1 vs 0.2)
    cfg_low_alpha = load_config()
    cfg_low_alpha["agent"]["alpha"] = 0.05
    run_experiment(
        experiment_name="sweep_alpha_0.05",
        question="How does a smaller learning rate (alpha=0.05) affect convergence rate and stability?",
        config=cfg_low_alpha,
    )

    cfg_high_alpha = load_config()
    cfg_high_alpha["agent"]["alpha"] = 0.2
    run_experiment(
        experiment_name="sweep_alpha_0.2",
        question="How does a larger learning rate (alpha=0.2) affect convergence speed in a deterministic grid world?",
        config=cfg_high_alpha,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
