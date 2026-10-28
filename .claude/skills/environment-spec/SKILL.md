---
name: environment-spec
description: Procedure for defining, implementing, changing, or reviewing the vacuum-robot grid-world environment, covering layout, cell semantics, rewards, termination, slip, and the reset/step interface. Use whenever work touches src/vacuum_rl/env.py, configs/default.toml [environment], docs/environment.md, or when the user clarifies or changes environment rules, even if they only mention walls, hazards, the dock, rewards, or the grid.
---

# Environment specification and change procedure

The environment is the only place where the transition function T and reward function R exist. Everything else treats it as a black box. Keeping that boundary sharp is what makes this a Q-learning problem rather than a planning problem.

## Invariants (change only with a logged decision)

- Interface (Gymnasium-style, no hard dependency on gymnasium):
  - `reset(seed: int | None = None) -> state`
  - `step(action) -> (next_state, reward, terminated, truncated, info)`
- Public `n_states`, `n_actions` and `encode_state(state) -> int` describe the spaces. These are part of the interface; the agent may use them, and it works on integer state indices.
- `state` is a hashable `(row, col)` tuple (provisional, D-007, open question Q-003).
- `terminated` means a terminal cell was reached (true end of the MDP). `truncated` means `max_episode_steps` was hit (a time limit). Keep them separate: the Q-learning target treats them differently.
- All randomness comes from a seed passed to the constructor or `reset`. No global RNG.
- T and R are private (`_transition`, `_reward`). `info` must not leak them.
- Every numeric value comes from `configs/default.toml`. The layout token meanings are documented in that file's header and in `docs/environment.md`.

## Oracle view (tests and analysis only)

Verifying Q-learning needs ground truth. Expose one clearly named test-only method (for example `oracle_model()` returning T and R as arrays) and use it only from `tests/` or analysis scripts to compute the optimal Q* by value iteration (AIMA Ch. 17). `agent.py` must never import or call it; `tests/test_model_free_invariant.py` enforces the import side of this.

## Changing environment semantics

1. Confirm the change with the user, or record it as provisional. Never guess silently.
2. Edit `configs/default.toml` first (single source of truth), then the code that parses it.
3. Update `docs/environment.md`.
4. Update `tests/test_env_contract.py` and add a test for the new behavior.
5. Draft a memory proposal: a decision entry, plus resolution of the matching open question (Q-001 to Q-004). See skill `memory-curation`.
6. Update the status line if the phase changed. Run `make validate` and `make test`.

## Implementation checklist (when asked to implement `env.py`)

- Parse layout tokens: `start`, `X`, `0`, numeric tokens.
- Movement: apply the action; if the target is off-grid or an obstacle, apply the `blocked_move` rule from config.
- Reward for a step: `step_cost` plus the value of the entered cell token (plus `bump_penalty` if blocked and configured). The combination rule is documented in `docs/environment.md`; if it changes, change it there too.
- Terminate on terminal tokens; truncate at `max_episode_steps`.
- Slip: with probability `slip_probability`, replace the intended action with one of the two perpendicular actions, split evenly (AIMA's 4x3 world: 0.8 intended, 0.1 each side).
- Provide a text `render()` for debugging.
