---
name: aima-grounding
description: Maps this project's concepts, naming, and design choices onto AIMA (Russell and Norvig, "Artificial Intelligence - A Modern Approach", 4th edition) and sets the citation convention. Use when writing docs, docstrings, or explanations that should be grounded in AIMA, when choosing between algorithms (Q-learning vs SARSA vs model-based/ADP), when describing the task environment (PEAS, environment properties), or whenever the user mentions AIMA, Russell, Norvig, MDPs, value iteration, or textbook terminology.
---

# Grounding in AIMA, 4th edition

AIMA is the project's reference text (decision D-004). Use its vocabulary so docs, code names and explanations line up with the book. Cite by chapter only.

## Chapter map

| Chapter | Topic | Where it applies here |
|---|---|---|
| Ch. 2, Intelligent Agents | Agents and environments, rationality, PEAS, properties of task environments, agent architectures, the vacuum-cleaner world | Framing the robot as a learning agent; the PEAS table in `docs/environment.md` |
| Ch. 17, Making Complex Decisions | Sequential decision problems, MDPs, the 4x3 grid example, Bellman equation, value iteration, policy iteration | The environment's formal model; value iteration as the test oracle for Q* |
| Ch. 22, Reinforcement Learning | Learning from rewards, passive RL (direct utility estimation, adaptive dynamic programming, TD), active RL (exploration, TD Q-learning), generalization, policy search | The algorithm itself; exploration strategy; later extensions |

## Concept to code mapping

| AIMA concept | In this repo |
|---|---|
| Task environment (PEAS) | `docs/environment.md` |
| Transition model P(s'\|s,a) | `env._transition`, hidden from the agent |
| Reward function R(s,a,s') | `env._reward`, hidden from the agent |
| Discount factor gamma | `[agent].gamma` |
| Utility U(s) | `max_a Q(s,a)` |
| Policy pi(s) | `argmax_a Q(s,a)` |
| Optimal values / policy | value-iteration oracle, tests only |
| Learning agent: performance element, learning element, critic, problem generator | greedy or epsilon-greedy action choice; the Q update; the environment's reward signal; the exploration mechanism |
| Known vs unknown environment | Unknown: the agent has no model. This is why model-free Q-learning fits |
| Active RL, TD Q-learning | `QLearningAgent` (when implemented) |
| 4x3 world (R = -0.04 per step, 0.8/0.1/0.1 slip) | Illustrative inspiration for the default step cost and the optional slip model |

Notation may differ slightly between editions and printings. If an exact symbol or definition matters, ask the user to check their copy.

## Citation convention

- Format: `AIMA 4e Ch. 22`. Add the topic name in words if helpful (for example "AIMA 4e Ch. 22, active reinforcement learning").
- Do not quote the book and do not invent page or section numbers. If the user wants section-level citations, ask them to confirm numbers from their copy and record them in `docs/`.
- Prefer one short citation per claim over a bibliography dump.

## Using AIMA to choose designs

- **Model-free (Q-learning) vs model-based (adaptive dynamic programming).** AIMA presents both. Q-learning is the project's requirement; learning T and R and then solving the MDP is a natural comparison baseline for a later phase.
- **On-policy vs off-policy.** Q-learning is off-policy; SARSA is the on-policy relative. Either is a reasonable comparison.
- **Exploration.** Use AIMA's framing: exploration vs exploitation, GLIE schemes. State plainly when a schedule is a practical shortcut.
- **Generalization.** Tabular is fine for 4x4. Function approximation is the book's answer to larger spaces; treat it as a future extension.
