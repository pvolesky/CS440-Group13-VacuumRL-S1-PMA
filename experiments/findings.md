# Experiment Findings: Tabular Q-Learning Baseline and Sweeps

This document records the empirical results of Phase 3 conducted in accordance with [`.gemini/skills/rl-experiment-protocol/SKILL.md`](../.gemini/skills/rl-experiment-protocol/SKILL.md). Raw artifact outputs reside in `experiments/runs/` and relational metrics are stored in `experiments/runs.db`.

---

## 1. Research Questions & Executive Summary

* **Q1: Does the default configuration reliably converge to the optimal policy?**
  - **Answer:** Yes. Across all 5 random seeds (0 through 4), the agent consistently achieves a 100.0% greedy evaluation success rate and converges to the theoretical optimal undiscounted return of $+9.94$ (6 steps: avoid obstacle at `(1,1)`, avoid terminal hazard at `(3,1)`, reach terminal dock at `(3,3)`).
* **Q2: How does the exploration decay rate ($\epsilon_{\text{decay}}$) impact policy discovery?**
  - **Answer:** While aggressive decay ($\epsilon = 0.95$) reaches the dock early, it stops exploring non-optimal grid cells prematurely, taking 500 episodes to attain 100% agreement with the global value-iteration oracle across all cells. Moderate decay ($0.99$) and gradual decay ($0.995$) ensure complete state-space coverage and match the global oracle policy by episode 100.
* **Q3: How does the learning rate ($\alpha$) affect tabular convergence?**
  - **Answer:** In a deterministic grid world, learning rates from $\alpha = 0.05$ to $\alpha = 0.2$ all converge reliably to optimal return $+9.94$ with negligible variance across seeds.

---

## 2. Experimental Setup

- **Environment:** 4x4 GridWorld per [Decision D-009](../memory/decisions.md) (deterministic transitions, step cost $-0.01$, dock reward $+10$, hazard reward $-1$).
- **Oracle Benchmark:** Exact optimal value function $V^*(s)$ and policy $\pi^*(s)$ derived from the test-only [`OracleModel`](../src/vacuum_rl/env.py) via value iteration (AIMA 4e Ch. 17).
- **Protocol:**
  - Evaluated every 100 episodes over 20 greedy evaluation episodes ($\epsilon = 0$) on independent seeds.
  - Tracked agreement with the value-iteration oracle policy across all valid non-terminal, non-obstacle states.
  - Recorded 5 independent runs per condition (seeds 0, 1, 2, 3, 4).

---

## 3. Aggregate Results Across Seeds (Mean $\pm$ Std)

| Experiment Name | $\alpha$ | $\epsilon_{\text{decay}}$ | Final Return | Final Success Rate | First Eval $\ge 95\%$ Success | Full Oracle Policy Agreement |
|---|---|---|---|---|---|---|
| **`baseline`** | 0.1 | 0.99 | **9.94 $\pm$ 0.00** | **100.0%** | Episode 100 | Episode 100 |
| **`sweep_epsilon_decay_0.95`** | 0.1 | 0.95 | **9.94 $\pm$ 0.00** | **100.0%** | Episode 100 | Episode 500 |
| **`sweep_epsilon_decay_0.995`**| 0.1 | 0.995| **9.94 $\pm$ 0.00** | **100.0%** | Episode 100 | Episode 100 |
| **`sweep_alpha_0.05`** | 0.05 | 0.99 | **9.94 $\pm$ 0.00** | **100.0%** | Episode 100 | Episode 100 |
| **`sweep_alpha_0.2`** | 0.2 | 0.99 | **9.94 $\pm$ 0.00** | **100.0%** | Episode 100 | Episode 100 |

---

## 4. Key Observations

1. **Optimal Path Recovery:**
   The shortest path avoiding both the obstacle `(1,1)` and hazard `(3,1)` requires exactly 6 steps:
   $$(0,0) \to (0,1) \to (0,2) \to (0,3) \to (1,3) \to (2,3) \to (3,3)$$
   or equivalently:
   $$(0,0) \to (1,0) \to (2,0) \to (2,1) \to (2,2) \to (2,3) \to (3,3)$$
   Total undiscounted return: $5 \times (-0.01) + (-0.01 + 10.0) = +9.94$.
   Every seed of every experiment successfully converged to one of these optimal trajectories.

2. **Global Policy Coverage vs Greedy Task Completion:**
   Even when an agent achieves 100% evaluation success from the initial state $(0,0)$, its policy in peripheral cells (e.g. cells around the obstacle or near the hazard) may remain sub-optimal if exploration drops too quickly. With $\epsilon_{\text{decay}} = 0.95$, exploration falls to the 0.01 floor within ~90 episodes, delaying convergence of non-trajectory states until episode 500.

---

## 5. Caveats and Limitations

- **Deterministic Environment:** All runs above were conducted with `slip_probability = 0.0`. In a stochastic environment (e.g. slip = 0.2), variance across seeds will be substantially higher and convergence will require more episodes.
- **Fixed Starting State:** The agent always starts at `(0, 0)`. Exploring unvisited regions relies entirely on $\epsilon$-greedy exploratory actions during early episodes.
- **Tabular State Space:** The state space consists of 16 discrete coordinates. These findings do not generalize directly to high-dimensional state spaces without function approximation (AIMA Ch. 22).
