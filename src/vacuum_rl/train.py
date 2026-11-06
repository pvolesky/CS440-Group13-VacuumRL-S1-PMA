"""Training loop for tabular Q-learning agent."""
from __future__ import annotations

from typing import Any

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
        "episode_returns": episode_returns,
        "episode_lengths": episode_lengths,
        "eval_history": eval_history,
    }


def main() -> int:
    config = load_config()
    seed = int(config.get("training", {}).get("seed", 0))
    print(f"Starting Q-learning training with seed {seed}...")
    results = run_training(config, seed=seed)
    final_eval = results["eval_history"][-1] if results["eval_history"] else {}
    print(
        f"Training complete! Final evaluation: "
        f"mean_return={final_eval.get('mean_return', 0.0):.2f}, "
        f"success_rate={final_eval.get('success_rate', 0.0):.1%}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
