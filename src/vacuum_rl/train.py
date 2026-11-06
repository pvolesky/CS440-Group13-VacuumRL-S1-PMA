"""Training loop for tabular Q-learning agent."""
from __future__ import annotations

from typing import Any
import numpy as np

from vacuum_rl.agent import QLearningAgent
from vacuum_rl.config import load_config
from vacuum_rl.env import VacuumGridEnv
from vacuum_rl.evaluate import evaluate_greedy


def run_training(config: dict[str, Any], seed: int) -> dict[str, Any]:
    """Train one agent for one seed and return metrics and trained agent."""
    env = VacuumGridEnv(config, seed=seed)
    agent = QLearningAgent(env.n_states, env.n_actions, config, seed=seed)

    train_cfg = config.get("training", {})
    episodes = int(train_cfg.get("episodes", 2000))
    eval_every = int(train_cfg.get("eval_every", 100))
    eval_episodes = int(train_cfg.get("eval_episodes", 20))

    episode_returns: list[float] = []
    episode_lengths: list[int] = []
    eval_history: list[dict[str, Any]] = []

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
        episode_returns.append(ep_return)
        episode_lengths.append(steps)

        if eval_every > 0 and (ep + 1) % eval_every == 0:
            eval_env = VacuumGridEnv(config, seed=seed + 10_000)
            metrics = evaluate_greedy(
                agent, eval_env, episodes=eval_episodes, seed=seed + 10_000
            )
            metrics["episode"] = ep + 1
            metrics["epsilon"] = agent.epsilon
            eval_history.append(metrics)

    return {
        "agent": agent,
        "env": env,
        "episode_returns": episode_returns,
        "episode_lengths": episode_lengths,
        "eval_history": eval_history,
    }


def format_q_table(agent: QLearningAgent, env: VacuumGridEnv) -> str:
    """Format the Q-table and greedy policy into human-readable tables."""
    lines = []
    lines.append("=" * 82)
    lines.append("LEARNED Q-TABLE (Expected Future Discounted Rewards for Each State-Action Pair)")
    lines.append("=" * 82)
    lines.append(
        f"{'State (r, c)':<15} | {'UP (0)':>9} | {'RIGHT (1)':>9} | {'DOWN (2)':>9} | "
        f"{'LEFT (3)':>9} | {'Best Action':<11} | {'max Q(s)':>8}"
    )
    lines.append("-" * 82)

    action_names = ["UP", "RIGHT", "DOWN", "LEFT"]
    for s_idx in range(env.n_states):
        r, c = env.decode_state(s_idx)
        tok = env._layout[r][c]
        label = f"({r}, {c})"
        if tok == "X":
            label += " [Obstacle]"
        elif tok == "10":
            label += " [Dock]"
        elif tok == "-1":
            label += " [Hazard]"
        elif tok == "start":
            label += " [Start]"

        q = agent.q_table[s_idx]
        best_act = action_names[int(np.argmax(q))]
        max_q = float(np.max(q))

        if tok == "X":
            lines.append(
                f"{label:<15} | {'--':>9} | {'--':>9} | {'--':>9} | {'--':>9} | {'--':<11} | {'--':>8}"
            )
        elif tok in env.terminal_tokens:
            lines.append(
                f"{label:<15} | {q[0]:>9.2f} | {q[1]:>9.2f} | {q[2]:>9.2f} | {q[3]:>9.2f} | "
                f"{'Terminal':<11} | {max_q:>8.2f}"
            )
        else:
            lines.append(
                f"{label:<15} | {q[0]:>9.2f} | {q[1]:>9.2f} | {q[2]:>9.2f} | {q[3]:>9.2f} | "
                f"{best_act:<11} | {max_q:>8.2f}"
            )

    lines.append("=" * 82)
    lines.append("\nLEARNED POLICY & MAXIMUM STATE VALUES V(s) = max_a Q(s, a):")
    lines.append("  Policy Grid (^ > v <)                     Value Grid V(s)")
    arrows = {0: "^", 1: ">", 2: "v", 3: "<"}
    for r in range(env._n_rows):
        pol_cells = []
        val_cells = []
        for c in range(env._n_cols):
            s_idx = env.encode_state((r, c))
            tok = env._layout[r][c]
            if tok == "X":
                pol_cells.append("  X  ")
                val_cells.append("   --   ")
            elif tok == "10":
                pol_cells.append(" Dock")
                val_cells.append(f"{float(np.max(agent.q_table[s_idx])):8.2f}")
            elif tok == "-1":
                pol_cells.append(" Haz ")
                val_cells.append(f"{float(np.max(agent.q_table[s_idx])):8.2f}")
            else:
                best_act = int(np.argmax(agent.q_table[s_idx]))
                pol_cells.append(f"  {arrows[best_act]}  ")
                val_cells.append(f"{float(np.max(agent.q_table[s_idx])):8.2f}")
        lines.append(f"  {' '.join(pol_cells)}          {' '.join(val_cells)}")
    lines.append("=" * 82)
    return "\n".join(lines)


def main() -> int:
    config = load_config()
    seed = int(config.get("training", {}).get("seed", 0))
    print(f"Starting Q-learning training with seed {seed}...")
    results = run_training(config, seed=seed)
    agent = results["agent"]
    env = results.get("env") or VacuumGridEnv(config, seed=seed)

    final_eval = results["eval_history"][-1] if results["eval_history"] else {}
    print(
        f"\nTraining complete! Final evaluation: "
        f"mean_return={final_eval.get('mean_return', 0.0):.2f}, "
        f"success_rate={final_eval.get('success_rate', 0.0):.1%}\n"
    )

    print(format_q_table(agent, env))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
