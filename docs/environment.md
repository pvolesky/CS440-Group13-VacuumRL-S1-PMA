# Environment specification (PROVISIONAL)

Status: provisional (decision D-007). Open items: Q-001 to Q-004 in `memory/open-questions.md`.
Numeric values live in `configs/default.toml`; this document explains meaning and does not restate them.

## Problem statement as given

```
[[start, 0, 0, 0],
 [0,     X, 0, 0],
 [0,     0, 0, 0],
 [0,    -1, 0, 10]]
```

The transition function T and reward function R are not available to the agent, so the agent learns by interaction (Q-learning).

## Cell semantics (provisional)

Coordinates are `(row, col)` with row 0 at the top.

| Token | Cell | Meaning |
|---|---|---|
| `start` | (0, 0) | Initial position of the robot |
| `X` | (1, 1) | Impassable obstacle (furniture or wall) |
| `-1` | (3, 1) | Hazard: entering it yields -1; episode continues |
| `10` | (3, 3) | Charging dock: entering it yields +10; episode terminates |
| `0` | elsewhere | Empty floor |

## Dynamics and rewards (provisional)

- **Actions:** UP, RIGHT, DOWN, LEFT (order matches `Action` in `src/vacuum_rl/env.py`).
- **Blocked moves:** moving off the grid or into an obstacle leaves the robot in place (`blocked_move = "stay"`).
- **Reward for a step:** `step_cost` plus the numeric value of the entered cell token (0 for `0` and `start`). A blocked move still pays `step_cost` (plus `bump_penalty` if configured).
- **Termination:** entering a cell listed in `terminal_tokens`.
- **Truncation:** `max_episode_steps` reached without termination.
- **Stochasticity:** with probability `slip_probability` the intended action is replaced by one of the two perpendicular actions, split evenly (AIMA's 4x3 world uses 0.8 intended, 0.1 each side). Default is 0, i.e. deterministic.

## Sanity reference (valid only while D-007 holds)

Shortest path from start to dock is 6 moves, for example RIGHT, RIGHT, RIGHT, DOWN, DOWN, DOWN. It avoids both the obstacle and the hazard. With the default step cost the undiscounted return of that path is 6 x step_cost + 10. Use this for the "scripted optimal path" check in skill `rl-debugging`, and update it if the semantics change.

## Task environment (AIMA 4e Ch. 2, PEAS)

| | |
|---|---|
| **Performance measure** | Discounted cumulative reward: reach the dock, avoid the hazard, waste few steps |
| **Environment** | Small grid with one obstacle, one hazard cell and a dock |
| **Actuators** | Move up, right, down, left |
| **Sensors** | Current cell coordinates |

Properties (provisional): fully observable, single agent, deterministic, sequential, static, discrete, and **unknown** (the agent has no model of T or R). The last property is what makes model-free learning appropriate. If Q-003 adds per-cell dirt, observability and state space change; revisit this table.

## Interface contract

```python
env.reset(seed=None) -> state                                   # state = (row, col)
env.step(action)     -> (next_state, reward, terminated, truncated, info)
env.n_states, env.n_actions, env.encode_state(state) -> int     # public spaces
```

- `terminated` and `truncated` are distinct: the Q-learning target bootstraps on truncation but not on termination.
- T and R are private to the environment. A test-only `oracle_model()` exposes them for value-iteration checks (AIMA Ch. 17); agent code must never use it.
- All randomness is seeded.

## If an assumption turns out different

| If the answer to ... | Change |
|---|---|
| Q-001: `-1` is terminal | Add `"-1"` to `terminal_tokens`; add a test; revisit the sanity reference |
| Q-001: `X` is a penalty rather than a wall | Remove it from `obstacle_tokens` and give it a numeric value; the layout parser needs a rule for it |
| Q-002: transitions are stochastic | Set `slip_probability`; expect noisier learning, wider oracle tolerances, and a nonzero epsilon floor |
| Q-002: different cost or discount | Edit `configs/default.toml` only; log a decision |
| Q-003: add "suck" and dirt | New action and a larger state; the tabular table grows with the dirt configurations; reconsider representation |
| Q-004: different episode limit | Edit `max_episode_steps`; log a decision |

Follow the change procedure in skill `environment-spec`.
