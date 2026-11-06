---
name: rl-debugging
description: Systematic debugging checklist for reinforcement-learning code in this repo (Q-learning not converging, policies that loop or oscillate, Q-values exploding or staying zero, rewards that look wrong, results that differ between seeds). Use whenever the agent or environment behaves unexpectedly, training stalls or diverges, or a test around learning fails, even if the user only says "it's not working" or "the numbers look off".
---

# Debugging reinforcement learning

RL bugs rarely crash. They produce plausible-looking, slightly wrong learning. Debug from the bottom of the stack upward, so each layer is trusted before you blame the next.

## Order of checks

1. **Environment by hand.** Run a random policy for a few hundred steps and a scripted optimal path. Do the rewards, terminations and blocked moves match `docs/environment.md`? Print `render()` at each step of the scripted path.
2. **Single-transition update test.** Feed one `(s, a, r, s', terminated)` tuple to the agent and compare with hand arithmetic (examples in skill `q-learning-implementation`).
3. **Oracle comparison.** Compute Q* with value iteration through the test-only oracle. Compare the greedy policy and the Q-values. The first disagreeing state usually points at the bug.
4. **Exploration.** Log epsilon per episode and the visit count per state-action pair. Unvisited pairs mean a dead end in exploration, not a failure of the update rule.
5. **Hyperparameters.** Only now sweep alpha, gamma and epsilon (skill `rl-experiment-protocol`), with multiple seeds.

## Symptom guide

| Symptom | Likely causes |
|---|---|
| Q-values stay at initial value | Update never called; wrong index into Q; learning rate 0; episodes end before any reward |
| Values grow without bound | Bootstrapping through terminal states; gamma >= 1 with a reachable positive loop; alpha too high |
| Policy loops or bounces between two cells | Step cost too small or zero; epsilon decayed before the goal was found; ties broken by index |
| Never reaches the dock under greedy evaluation | Terminal not wired to `terminated`; evaluation episode limit too short; obstacle blocks the only path in the layout parsing |
| Works for some seeds only | Too little exploration; seeds shared between the agent and the environment; epsilon floor of zero with pessimistic init |
| Good training return, bad greedy return | Training return benefited from lucky exploration; check evaluation uses epsilon 0 and a separate environment |
| Off-by-one in positions | `(row, col)` vs `(x, y)` swapped; row 0 assumed at the bottom; action deltas mismatched with action names |
| Reward looks doubled or missing | Reward counted at both leaving and entering a cell; step cost and cell value combined differently than documented |
| `truncated` treated as terminal | Time-limit endings cut the bootstrap, which teaches the agent that late states are worth zero |

## Habits that save time

- Fix a seed before debugging; compare runs, not impressions.
- Add a regression test for every bug found, then propose a lessons-learned entry (skill `memory-curation`).
- Change one thing at a time. If two fixes seem needed, apply them separately and confirm each.
